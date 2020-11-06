from jupyterhub.handlers.base import BaseHandler
from jupyterhub.utils import url_path_join
from tornado import web

class MigrateHandler(BaseHandler):
    """Renders migrate page
    """
    @web.authenticated
    async def get(self):
        user = self.current_user
        if user.running:
            # trigger poll_and_notify event in case of a server that died
            await user.spawner.poll_and_notify()

        # def get_argument(arg):
        #     args = self.get_arguments(arg)
        #     # returns list
        #     if len(args) == 0:
        #         return None
        #     else:
        #         return args[0]

        # checkpoint = get_argument("checkpoint")        
        # if checkpoint:
        #     if user.running:
        #         # stop server
        #         await user.spawner.stop()

        # migrate_to = get_argument("migrate_to")
        # if migrate_to:
        #     user.user_options.update({"size" : migrate_to})
        #     await user.spawner.start()
        
        # # send the user to /spawn if they have no active servers,
        # # to establish that this is an explicit spawn request rather
        # # than an implicit one, which can be caused by any link to `/user/:name(/:server_name)`
        # if user.active:
        #     url = url_path_join(self.base_url, 'user', user.escaped_name)
        # else:
        #     url = url_path_join(self.hub.base_url, 'spawn', user.escaped_name)

        # auth_state = await user.get_auth_state()
        html = self.render_template(
            'migrate.html',
        )
        self.finish(html)
