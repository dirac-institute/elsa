
from jupyterhub.auth import DummyAuthenticator
from jinja2 import Template
import checkpoint_demo

c.JupyterHub.spawner_class = checkpoint_demo.spawner.PodmanSpawner
c.JupyterHub.authenticator_class = DummyAuthenticator

c.PodmanSpawner.scheduler_image = "72522808"
c.PodmanSpawner.scheduler_region = "sfo3"
c.PodmanSpawner.scheduler_vpc = "ed580488-6eb8-4fc2-84e9-184502790372"
c.PodmanSpawner.scheduler_ssh_key = "/root/.ssh/id_rsa_podman.pub"

c.PodmanSpawner.options_form = Template("""
<div class='form-group' id='host-list'>
    <div class='col-md-12'>
        <strong>Hosts</strong>
    </div>
    {% for size in sizes %}
    <label for='host-{{ loop.index }}' class='form-control input-group'>
        <div class='col-md-1'>
            <input type='radio' name='host' id='host-{{ loop.index - 1 }}' value='{{ loop.index - 1 }}'{% if loop.index == 1 %} checked{% endif %} />
        </div>
        <div class='col-md-11'>
            {{ size }}
        </div>
    </label>
    {% endfor %}
</div>
""").render(sizes=checkpoint_demo.spawner.PodmanSpawner.sizes)

c.JupyterHub.hub_ip = "0.0.0.0"
c.JupyterHub.hub_connect_ip = "10.124.0.4"
# c.ConfigurableHTTPProxy.should_start = False
c.ConfigurableHTTPProxy.command = [
    "configurable-http-proxy",
    "--ip=127.0.0.1",
    "--port=8000",
    "--api-ip=127.0.0.1",
    "--api-port=8001",
    "--default-target=http://localhost:8081",
    "--error-target=http://localhost:8081/hub/error"
]

c.JupyterHub.ssl_key = '/etc/letsencrypt/live/adass.dirac.institute/privkey.pem'
c.JupyterHub.ssl_cert = '/etc/letsencrypt/live/adass.dirac.institute/fullchain.pem'