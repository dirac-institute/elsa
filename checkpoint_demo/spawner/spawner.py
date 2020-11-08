from concurrent.futures import ThreadPoolExecutor
# import podman
import jupyterhub
from jupyterhub.spawner import Spawner
from jupyterhub.utils import random_port
# from dockerspawner import DockerSpawner
from tornado import gen, web
from textwrap import dedent
from escapism import escape
from copy import deepcopy
from traitlets import (
    Bool,
    Dict,
    Integer,
    List,
    Unicode,
    Union,
    default,
    observe,
    validate,
)
import subprocess

import os
import logging
from jinja2 import Template
from tornado.concurrent import run_on_executor
import asyncio
import time
from ..podmancli import PodmanCli, SSHPodmanCli
from ..scheduler import DOScheduler

_jupyterhub_xy = "%i.%i" % (jupyterhub.version_info[:2])

class PodmanSpawner(Spawner):
    podman = None
    events = []
    executor = None

    image = Unicode(
        "docker://astronomycommons/adass-notebook:deploy",
        config=True,
    )
    
    scheduler_image = Unicode(
        config=True,
    )
    scheduler_region = Unicode(
        config=True,
    )
    scheduler_vpc = Unicode(
        config=True
    )
    scheduler_ssh_key = Unicode(
        config=True
    )

    # sizes = [size.slug for size in scheduler.manager.get_all_sizes()]
    sizes = [
        "s-1vcpu-1gb",
        "s-1vcpu-2gb",
        "s-1vcpu-3gb",
    ]

    start_timeout = 60 * 5

    def log_event(self, message):
        import time
        return self.events.append(f"[{time.ctime()}] {message}")

    def get_image(self):
        self.log_event(f"Pulling image {self.image}")
        self.podman.pull(self.image)
        return self.image

    # def get_container(self):
    #     return self.client.containers.get(self.container_name)

    # options_form = Template(options_form_html).render(sizes=sizes)

    def options_from_form(self, form_data):
        self.log.info("got form data: %s", form_data)
        return {
            'size' : self.sizes[int(form_data.get('host')[0])]
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.__class__.executor is None:
            self.log.debug(
                'Starting executor thread pool with %d workers', 1
            )
            self.__class__.executor = ThreadPoolExecutor(
                max_workers=1
            )

        self.scheduler = DOScheduler(
            self.scheduler_image, 
            self.scheduler_region, 
            # self.scheduler_vpc,
            ssh_key=self.scheduler_ssh_key,
            event_queue=self.events,
        )

    def get_env(self):
        try:
            env = super().get_env()
        except:
            env = {}

        env['JUPYTER_IMAGE_SPEC'] = self.image
        env['NB_USER'] = self.user.name
        # env['NB_UID'] = 1001

        # fix permissions on /home/jovyan in restored container
        env['CHOWN_HOME'] = 'yes'
        self.log.debug("Starting with environment: %s", env)
        return env

    def get_container(self, container_name):
        try:
            inspect = self.podman.inspect_container(container_name)
            return inspect
        except Exception as e:
            self.log.error("Error: %s", str(e))
            # container missing
            return None

    def start_server(self, name, host_port=None):
        if host_port is None:
            host_port = random_port()
        
        # # get image
        # image = self.get_image()

        # detach container
        flags = [
            "--detach"
        ]

        # start as root user
        flags += [
            "--user",
            "root"
        ]

        # set hostname
        flags += [
            "--hostname",
            self.container_name
        ]

        # set environment
        _env = self.get_env()
        self.log.debug("Got env: %s", _env)
        if 'PATH' in _env:
            _path = _env.pop('PATH')
        
        nb_user = _env.get("NB_USER")

        # _env['JUPYTERHUB_API_URL'] = "10.88.0.1:8081/"

        for k, v in _env.items():
            flags += [
                "-e",
                f"{k}={v}"
            ]

        # Connect port
        image_details = self.podman.inspect_image(self.image)
        if 'ExposedPorts' in image_details[0]['Config']:
            internal_port = list(image_details[0]['Config']['ExposedPorts'].keys())[0]
        else:
            internal_port = "8888"
        flags += [
            "-p",
            f"{host_port}:{internal_port}"
        ]

        # set container name
        flags += [
            "--name",
            name
        ]
        
        # mount home
        flags += [
            "-v",
            "/nfs/home:/home",
            # "-v",
            # "/nfs/home/{nb_user}:/home/{nb_user}".format(nb_user=nb_user),
            "-v",
            "/nfs/lsst:/nfs/lsst"
        ]

        flags += [
            "--tmpfs",
            "/tmp"
        ]

        return self.podman.run(self.image, flags, "start-singleuser.sh", ["--NotebookNotary.db_file=':memory:'"])

    def get_ip_and_port(self, container_name):
        self.log.info("in get_ip_and_port")
        inspect = self.podman.inspect_container(container_name)
        
        networksettings = inspect[0]['NetworkSettings']
        ip = networksettings['IPAddress']
        ports = networksettings['Ports']
        self.log.info(ports)
        port = int(ports[list(ports.keys())[0]][0]['HostPort'])
        
        if self.podman.host is not None:
            ip = self.podman.host
        else:
            ip = "0.0.0.0"
        return ip, port

    def checkpoint_server(self, container_name):
        self.log.debug("Checkpointing container: %s", container_name)
        res = self.podman.checkpoint(
            container_name, 
            [
                "--export", 
                f"/nfs/checkpoints/{container_name}.tar.gz",
                "--tcp-established",
                "--keep"
            ]
        )
        # res = self.podman.rm_container(container_name)
        return res

    def restore_server(self, container_name):
        res = self.podman.restore(
            None,
            [
                "--import",
                f"/nfs/checkpoints/{container_name}.tar.gz",
                "--tcp-established",
                "--keep"
            ]
        )
        return res

    def checkpoint_exists(self, container_name):
        checkpoint_name = f"/nfs/checkpoints/{container_name}.tar.gz"
        # works if /nfs is mounted, but it might not be
        p = self.podman.call(["stat", checkpoint_name])
        p, exit_code = self.podman._wait_until_done(p)
        exists = exit_code == 0
        # exists = os.path.exists(checkpoint_name)

        self.log.debug(
            "Looking for checkpointed container: %s, exists = %s", checkpoint_name, exists
        )
        return exists

    def get_token(self, container_name):
        inspect = self.podman.inspect_container(container_name)
        env = inspect[0]['Config']['Env']
        env = [
            (i.split("=")[0], i.split("=")[1]) for i in env
        ]
        env = {
            k : v for k, v in env
        }
        self.log.debug("Env: %s", env)
        if 'JUPYTERHUB_API_TOKEN' in env:
            self.log.debug("Removing old api token: %s", self.api_token)
            self.api_token = env.get('JUPYTERHUB_API_TOKEN')
            self.log.debug("Found token in container: %s", self.api_token)
        
        return self.api_token

    async def _start(self):
        # for i in range(10):
        #     self.log_event(f"progress: {i}")
        #     logging.debug(f"in _start: progress: {i}")
        #     await self.asynchronize(time.sleep(3))
        # return ("127.0.0.1", 8888)

        self.log.info("Got user options: %s", self.user_options)
        # request VM
        vm_id, vm_ip = await self.asynchronize(
            self.scheduler.get_vm, self.user_options.get("size")
        )
        self.vm_id = vm_id
        # connect to VM for executing Podman
        self.podman = SSHPodmanCli(
            host=vm_ip, 
            loglevel=logging.DEBUG,
            user="root",
            key="/root/.ssh/id_rsa_podman"
        )
        
        self.log.info("Ensuring image exists")
        await self.asynchronize(
            self.get_image
        )

        # self.log.critical(self.db)
        self.log.info("Spawning for user: %s", self.user.name)
        self.container_name = f"jupyter-{self.user.name}"
        env = super().get_env()
        self.log.debug("Environment for server: %s", env)

        poll_result = await self.poll()
        self.log.info("Poll result: %s", poll_result)
        if poll_result is None:
            # server running
            # get API token from running server
            await self.asynchronize(
                self.get_token, self.container_name
            )
            # get ip and port from running server
        else:
            # server not running
            # try cleaning up old container
            # try:
            #     self.podman.rm_container(self.container_name)
            # except Exception as e:
            #     self.log.error("Error emoving container: %s", str(e))

            # check for checkpoint
            checkpoint_exists = await self.asynchronize(
                self.checkpoint_exists, self.container_name
            )
            if checkpoint_exists:
                # restore if exists
                try:
                    self.log_event("Restoring checkpointed server")
                    await self.asynchronize(
                        self.restore_server, self.container_name
                    )
                except Exception as e:
                    self.log.error("Error restoring server: %s", e)
                    self.log_event("Error restoring server")
                    try:
                        self.log_event("Starting server")
                        await self.asynchronize(
                            self.podman.start, self.container_name
                        )
                    except Exception as e:
                        raise Exception(f"Error starting restored container: {str(e)}")
                
                await self.asynchronize(
                    self.get_token, self.container_name
                )
            else:
                ip = "127.0.0.1"
                port = random_port()

                out, err = await self.asynchronize(
                    self.start_server, self.container_name, host_port=port
                )
                self.container_id = out.decode().strip()            
                
        ip, port = await self.asynchronize(
            self.get_ip_and_port, self.container_name
        )
        self.ip = ip
        self.port = port
        return ip, port

    def start(self):
        self._start_future = asyncio.ensure_future(self._start())
        return self._start_future

    async def progress(self):
        """
        From KubeSpawner
        """
        # if not self.events_enabled:
        #     return

        start_future = self._start_future
        progress = 0
        next_event = 0

        break_while_loop = False
        while True:
            # Ensure we always capture events following the start_future
            # signal has fired.
            if start_future.done():
                break_while_loop = True
            events = self.events
            self.log.debug("[Progress] got events: {}".format(events))

            len_events = len(events)
            if next_event < len_events:
                for i in range(next_event, len_events):
                    event = events[i]
                    # move the progress bar.
                    # Since we don't know how many events we will get,
                    # asymptotically approach 90% completion with each event.
                    # each event gets 33% closer to 90%:
                    # 30 50 63 72 78 82 84 86 87 88 88 89
                    progress += (100 - progress) / 3

                    yield {
                        'progress': int(progress),
                        # 'raw_event': event,
                        'message':  event
                    }
                next_event = len_events

            if break_while_loop:
                break
            await asyncio.sleep(1)
        self.events.clear()

    @run_on_executor
    def asynchronize(self, method, *args, **kwargs):
        return method(*args, **kwargs)


    @gen.coroutine
    def poll(self):
        container = self.get_container(self.container_name)
        if container:
            state = container[0]['State']
            running = state['Running']
            exitcode = state['ExitCode']
            if running:
                return None
            else:
                return exitcode
                return None
        else:
            # no container
            return -1
            # return None

    # @gen.coroutine
    async def stop(self):
        self.log.debug("Stopping container %s for user %s", self.container_name, self.user.name)
        await self.asynchronize(
            self.checkpoint_server, self.container_name
        )
        # self.podman.kill(self.container_name)
        await self.asynchronize(
            self.podman.rm_container, self.container_name
        )    
        await self.asynchronize(
            self.scheduler.release_vm, self.vm_id
        )

    def get_state(self):
        """get the current state"""
        state = super().get_state()
        if self.container_name:
            state['container_name'] = self.container_name
        if self.vm_id:
            state['vm_id'] = self.vm_id

        # if self.checkpoint_api_token:
        #     state['checkpoint_api_token'] = self.checkpoint_api_token

        self.log.debug("Setting state: %s", state)
        return state

    def load_state(self, state):
        """load state from the database"""
        self.log.debug("Loading state: %s", state)
        super().load_state(state)
        if 'container_name' in state:
            self.container_name = state['container_name']
            self.vm_id = state['vm_id']

    def clear_state(self):
        """clear any state (called after shutdown)"""
        self.log.debug("Clearing state")
        super().clear_state()
        self.container_name = None
        self.vm_id = None
        self.events.clear()

