from traitlets import List, Unicode
from traitlets.config import Configurable

class MigrateConfig(Configurable):
    sizes = List(
        trait=Unicode(),
        default_value=[
            "s-1vcpu-1gb",
            "s-1vcpu-2gb",
            "s-1vcpu-3gb",
        ]
    ).tag(
        config=True
    )
    