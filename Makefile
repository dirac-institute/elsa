_build_hub:
	cd images/jupyterhub && \
	podman build . -t astronomycommons/adass-jupyterhub:$(tag)

_build_notebook:
	cd images/notebook && \
	export BUILDAH_FORMAT=docker && \
	podman build . -t astronomycommons/adass-notebook:$(tag)

build: _build_hub _build_notebook

_push_hub:
	podman push astronomycommons/adass-jupyterhub:$(tag)

_push_notebook:
	podman push astronomycommons/adass-notebook:$(tag)

push: build _push_hub _push_notebook

# start JupyterHub
_start_jupyterhub:
	podman container rm adass-jupyterhub && \
	podman run -it \
		-e DIGITALOCEAN_ACCESS_TOKEN=$(do_token) \
		-p 443:8000 \
		-p 8081:8081 \
		-v /etc/letsencrypt:/etc/letsencrypt \
		-v ${PWD}/srv:/srv/jupyterhub \
		-v ${PWD}/checkpoint_demo:/usr/local/lib/python3.8/dist-packages/checkpoint_demo \
		-v /root/.ssh/id_rsa_podman:/root/.ssh/id_rsa_podman \
		-v /root/.ssh/id_rsa_podman.pub:/root/.ssh/id_rsa_podman.pub \
		--name adass-jupyterhub \
		astronomycommons/adass-jupyterhub:$(tag) \

start: build _start_jupyterhub
