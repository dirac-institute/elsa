import digitalocean
import os
import logging
import random
import string
import base64
import hashlib
import subprocess

def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

def public_key_fingerprint(public_key):
    key = base64.b64decode(public_key.strip().split()[1].encode('ascii'))
    fp_plain = hashlib.md5(key).hexdigest()
    return ':'.join(a+b for a,b in zip(fp_plain[::2], fp_plain[1::2]))

class DOScheduler():
    """
    API:
    (id, ip) = create_vm()
    (status) = remove_vm()
    (vms) = list_vms()
    """
    def __init__(self, image, region, event_queue=None, token=None, ssh_key=None):
        if token is None:
            token = os.environ.get("DIGITALOCEAN_ACCESS_TOKEN", None)
            if token is None:
                raise Exception("Must pass token to scheduler or set DIGITALOCEAN_ACCESS_TOKEN environment variable")
        
        self.manager = digitalocean.Manager(token=token)
        self.token = token

        if ssh_key is None:
            logging.getLogger().warn("No SSH Key passed to scheduler, the machine must be set up with one already.")
        
        if type(ssh_key) == digitalocean.SSHKey:
            self.ssh_key = ssh_key
        else:
            public_key = open(ssh_key, "r").read()
            self.ssh_key = digitalocean.SSHKey(
                token=token,
                name='jupyterhub_do_scheduler',
                public_key=public_key
            )
            try:
                # try making the SSH key for the first time
                self.ssh_key.create()
            except digitalocean.DataReadError:
                # SSH key already exists, try loading it from DO
                fingerprint = public_key_fingerprint(public_key)
                self.ssh_key = digitalocean.SSHKey(
                    token=token,
                    name='jupyterhub_do_scheduler',
                    fingerprint=fingerprint
                )
                self.ssh_key.load()

        self.image = image
        self.region = region
        # self.vpc = self.manager.get_vpc(vpc_id)
        self.events = event_queue if event_queue is not None else []

    def make_droplet(self, name, size_slug, tags=[]):
        droplet = digitalocean.Droplet(
            token=self.token,
            name=name,
            size_slug=size_slug,
            image=self.image,
            region=self.region,
            ssh_keys=[self.ssh_key],
            backups=False,
            private_networking=True,
            # vpc_uuid=self.vpc.id,
        )
        droplet.create()

        # add tags
        for tag in tags:
            tag = digitalocean.Tag(
                token=self.token,
                name=tag
            )
            tag.create()
            tag.add_droplets([droplet.id])

        active = False
        while not active:
            _droplet = self.manager.get_droplet(droplet.id)
            active = _droplet.status == 'active'

        return _droplet

    def initialize_droplet(self, ip):
        self.events.append("Initializing virtual machine")
        # cmd = open("/root/checkpointspawner/repo/bootstrap.sh").read()
        ssh = subprocess.Popen(
            [
                'ssh',
                '-i',
                '/root/.ssh/id_rsa_podman',
                '-o',
                'StrictHostKeyChecking=no',
                f'root@{ip}',
                'bash',
                '-c',
                "/bin/true",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        exit_code = ssh.wait()
        return exit_code, ssh.stdout.read(), ssh.stderr.read()
        

    def get_vm(self, size_slug, tags=[]):
        self.events.append("Finding virtual machine with size {}".format(size_slug))
        # returns (id, hostname, ssh_conn_string)
        free_vms = self.list_vms(sizes=[size_slug], tags=tags + ['free'])

        if len(free_vms) > 0:
            print("found free VMs:", free_vms)
            vm = random.choice(free_vms)
            print("chose random VM:", vm)
            self.events.append("Assigned to virtual machine {}".format(vm))
        else:
            print("no free VMs, making a new one")
            self.events.append("No free virtual machines with size {}, creating a new one".format(size_slug))
            vm = self.make_droplet(f"jupyter-{get_random_string(6)}", size_slug, tags=tags + ['free'])
        
        # TODO: fix race condition
        free_tag = digitalocean.Tag(
            token=self.token,
            name="free"
        )
        free_tag.create()
        free_tag.remove_droplets([vm.id])

        claimed_tag = digitalocean.Tag(
            token=self.token,
            name="claimed"
        )
        claimed_tag.create()
        claimed_tag.add_droplets([vm.id])

        # TODO: support private networks, requires merging VPC support in python-do API
        networks = vm.networks
        ipv4 = networks['v4']
        public_ipv4 = [ip for ip in ipv4 if ip['type'] == 'public'][0]
        public_ip = public_ipv4['ip_address']

        private_ipv4 = [ip for ip in ipv4 if ip['type'] == 'private'][0]
        private_ip = private_ipv4['ip_address']

        exit_code, stdout, stderr = self.initialize_droplet(public_ip)
        if exit_code != 0:
            print(f"[Error] Initialized droplet: exit_code = {exit_code}, stdout = {stdout}, stderr = {stderr}")
            free_tag.add_droplets([vm.id])
            claimed_tag.remove_droplets([vm.id])
            return self.get_vm(size_slug, tags=tags)
        else:
            print("Initialized succesfully")

        initialized_tag = digitalocean.Tag(
            token=self.token,
            name="initialized"
        )
        initialized_tag.create()
        initialized_tag.add_droplets([vm.id])

        return vm.id, private_ip

    def release_vm(self, vm_id):
        claimed_tag = digitalocean.Tag(
            token=self.token,
            name="claimed"
        )
        claimed_tag.create()
        claimed_tag.remove_droplets([vm_id])
        
        free_tag = digitalocean.Tag(
            token=self.token,
            name="free"
        )
        free_tag.create()
        free_tag.add_droplets([vm_id])

        pass

    def list_vms(self, sizes=[], tags=[]):
        droplets = self.manager.get_all_droplets()

        vms = []
        for droplet in droplets:
            if tags:
                has_tag = all([tag in droplet.tags for tag in tags])
            else:
                has_tag = True
            
            if sizes:
                has_size = any([size == droplet.size_slug for size in sizes])
            else:
                has_size = True

            is_active = droplet.status == "active"

            if has_tag and has_size and is_active:
                vms.append(droplet)
        
        return vms
