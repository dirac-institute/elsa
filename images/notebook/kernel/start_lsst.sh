#!/usr/bin/env bash
# LSST Science Pipelines
source /nfs/lsst/conda/current/bin/activate
source /nfs/lsst/loadLSST.bash
setup lsst_distrib
if [ $# -ne 0 ]; then
    exec python -m ipykernel $@
fi