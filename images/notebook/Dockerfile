FROM jupyter/scipy-notebook:4a112c0f11eb

USER root
ADD kernel /opt/conda/share/jupyter/kernels/lsst
ADD start.sh /usr/local/bin/
RUN chown -R $NB_UID:$NB_GID /opt/conda/share/jupyter/kernels \
 && ln -s /nfs/lsst /tmp/lsst

USER $NB_USER
ADD nbresuse /tmp/nbresuse
RUN python -m pip install /tmp/nbresuse/. && \
    jupyter serverextension enable --py nbresuse --sys-prefix && \
    jupyter nbextension install --py nbresuse --sys-prefix && \
    jupyter nbextension enable --py nbresuse --sys-prefix && \
    rm -rf /tmp/nbresuse

ADD jupyter_notebook_config.py /opt/conda/etc/jupyter/jupyter_notebook_config.py
