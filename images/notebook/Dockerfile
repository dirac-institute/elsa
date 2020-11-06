FROM jupyter/scipy-notebook:4a112c0f11eb

USER root
ADD kernel /opt/conda/share/jupyter/kernels/lsst
RUN chown -R $NB_UID:$NB_GID /opt/conda/share/jupyter/kernels \
 && ln -s /nfs/lsst /tmp/lsst

RUN python -m pip install nbresuse && \
    jupyter serverextension enable --py nbresuse --sys-prefix && \
    jupyter nbextension install --py nbresuse --sys-prefix && \
    jupyter nbextension enable --py nbresuse --sys-prefix 

USER $NB_USER