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
	( podman container inspect adass-jupyterhub > /dev/null 2>&1 && podman container stop adass-jupyterhub ) || true
	podman run --rm -it \
		-e DIGITALOCEAN_ACCESS_TOKEN=$(do_token) \
		-e GITHUB_CLIENT_ID=a936203117c77fc96e1a \
		-e GITHUB_CLIENT_SECRET=$(github_oauth_secret) \
		-e OAUTH_CALLBACK_URL=https://elsa.dirac.dev/hub/oauth_callback \
		-p 443:8000 \
		-p 8081:8081 \
		-v /nfs/home:/home \
		-v /etc/letsencrypt:/etc/letsencrypt \
		-v ${PWD}/srv:/srv/jupyterhub \
		-v ${PWD}/elsa:/usr/local/lib/python3.8/dist-packages/elsa \
		-v /root/.ssh/id_rsa_podman:/root/.ssh/id_rsa_podman \
		-v /root/.ssh/id_rsa_podman.pub:/root/.ssh/id_rsa_podman.pub \
		--name adass-jupyterhub \
		astronomycommons/adass-jupyterhub:$(tag)

start: build _start_jupyterhub

_start_notebook:
	( podman container inspect adass-notebook > /dev/null 2>&1 && podman container stop adass-notebook ) || true
	podman run --rm -it \
		--user root \
		--name adass-notebook \
		-e NB_USER=mjuric \
		-p 8888:8888 \
		-v /nfs/home:/home \
		-v ${PWD}/images/notebook/nbresuse/nbresuse/static/main.js:/opt/conda/share/jupyter/nbextensions/nbresuse/main.js \
		astronomycommons/adass-notebook:$(tag)

start_notebook: _build_notebook _start_notebook
