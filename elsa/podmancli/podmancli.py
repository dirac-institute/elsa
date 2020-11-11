import subprocess
import time
import json
import logging

log = logging.getLogger("podmancli")

class PodmanCli():
    def __init__(self, loglevel=logging.WARN):
        log.setLevel(loglevel)
        self.call = self._call_and_pipe_output
        self.call_and_wait = lambda cmd : self._wait_until_done(self.call(cmd))
        self.call_and_get_output = lambda cmd : self._wait_and_get_output(self.call(cmd))

    @staticmethod
    def _call_and_pipe_output(cmd):
        log.debug("Running command: %s", " ".join(cmd))
        return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    @staticmethod
    def _wait_until_done(p):
        status_code = p.wait()        
        
        return p, status_code

    @staticmethod
    def _wait_and_get_output(p):
        p, return_code = PodmanCli._wait_until_done(p)

        out = p.stdout.read()
        err = p.stderr.read()

        if return_code != 0:
            raise Exception(f"Process exited with non-zero exit code {return_code}: {err.decode().strip()}")
        
        return out, err

    def _run(self, image, flags, command, args):
        # runs:
        # podman run {flags} {image} {command} {args}

        cmd = [
            "podman",
            "run"
        ] + flags + [
            image
        ] + [
            command
        ] + args

        return self.call(cmd)

    def run(self, image, flags, command, args):
        p = self._run(image, flags, command, args)
        out, err = PodmanCli._wait_and_get_output(p)

        return out, err

    def _kill(self, container_id):
        cmd = [
            "podman",
            "container",
            "kill",
            container_id
        ]

        return self.call(cmd)

    def kill(self, container_id):
        p = self._kill(container_id)
        out, err = self._wait_and_get_output(p)
        ret = out.decode().strip()
        return ret

    def _rm_container(self, container_id):
        cmd = [
            "podman",
            "container",
            "rm",
            container_id
        ]

        return self.call(cmd)

    def rm_container(self, container_id):
        p = self._rm_container(container_id)
        out, err = self._wait_and_get_output(p)
        ret = out.decode().strip()
        return ret

    def _rm_image(self, image_id):
        cmd = [
            "podman",
            "image",
            "rm",
            image_id
        ]

        return self.call(cmd)

    def rm_image(self, image_id):
        p = self._rm_image(image_id)
        out, err = self._wait_and_get_output(p)
        ret = out.decode().strip()
        return ret

    def _exec(self, container_id, flags, command):
        cmd = [
            "podman",
            "container",
            "exec"
        ] + flags + [
            container_id
        ] + command

        return self.call(cmd)

    def exec(self, container_id, flag, command):
        p = self._exec(container_id, flag, command)
        out, err = self._wait_and_get_output(p)
        return out, err

    def _inspect_container(self, container_id):
        cmd = [
            "podman",
            "container",
            "inspect"
        ] + [
            container_id
        ]
        
        return self.call(cmd)

    def inspect_container(self, container_id):
        p = self._inspect_container(container_id)
        out, err = self._wait_and_get_output(p)
        inspect = json.loads(out)
        return inspect

    def _inspect_image(self, image_id):
        cmd = [
            "podman",
            "image",
            "inspect"
        ] + [
            image_id
        ]
        
        return self.call(cmd)

    def inspect_image(self, image_id):
        p = self._inspect_image(image_id)
        out, err = self._wait_and_get_output(p)
        inspect = json.loads(out)
        return inspect

    def _pull(self, image):
        cmd = [
            "podman",
            "image",
            "pull",
            image
        ]

        return self.call(cmd)

    def pull(self, image):
        p = self._pull(image)
        out, err = self._wait_and_get_output(p)
        return out.decode("utf-8")

    def _start(self, container_id):
        cmd = [
            "podman",
            "container",
            "start",
            container_id
        ]

        return self.call(cmd)

    def start(self, container_id):
        p = self._start(container_id)
        out, err = self._wait_and_get_output(p)
        return out

    def _checkpoint(self, container_id, flags):
        cmd = [
            "podman",
            "container",
            "checkpoint"
        ] + flags + [
            container_id
        ]

        return self.call(cmd)

    def checkpoint(self, container_id, flags):
        p = self._checkpoint(container_id, flags)
        out, err = self._wait_and_get_output(p)
        res = out.decode().strip()
        return res

    def _restore(self, container_id, flags):
        cmd = [
            "podman",
            "container",
            "restore"
        ] + flags

        if container_id:
            cmd += [container_id]

        return self.call(cmd)

    def restore(self, container_id, flags):
        p = self._restore(container_id, flags)
        out, err = self._wait_and_get_output(p)
        res = out.decode().strip()
        return res

class SSHPodmanCli(PodmanCli):
    host = None
    user = None
    key = None
    options = [
        "StrictHostKeyChecking=no"
    ]

    def __init__(self, host, user, key, options=[], **kwargs):
        super().__init__(**kwargs)
        self.host = host
        self.user = user
        self.key = key
        self.options += options
        self.call = lambda cmd : self._ssh_call_and_pipe_output(
            self.host, self.user, self.key, self.options, cmd
        )

    @staticmethod
    def _ssh_call_and_pipe_output(host, user, key, options, cmd):
        _cmd = [
            "ssh"
        ]
        if key:
            _cmd += [
                "-i",
                key
            ]
        if options:
            for option in options:
                _cmd += [
                    "-o",
                    option
                ]
        _cmd += [
            "{}@{}".format(user, host)
        ]
        final_cmd = _cmd + cmd

        log.debug("Running command '%s' as %s on %s", " ".join(final_cmd), user, host)
        p = subprocess.Popen(final_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return p
