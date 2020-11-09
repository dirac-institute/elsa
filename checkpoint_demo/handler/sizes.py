from jupyterhub.handlers.base import BaseHandler
from jupyterhub.utils import url_path_join
from traitlets import List, Unicode
from traitlets.config import Configurable
from tornado import web
import json
import os
from .config import MigrateConfig

class SizesHandler(BaseHandler):
    @web.authenticated
    async def get(self):
        _sizes = self.sizes
        self.log.warn(_sizes)
        sizes_json = json.dumps(_sizes)
        self.finish(sizes_json)

    def __init__(self, *args, **kwargs):
        self.sizes = kwargs.get('sizes', [])
        kwargs.pop('sizes')
        super().__init__(*args, **kwargs)