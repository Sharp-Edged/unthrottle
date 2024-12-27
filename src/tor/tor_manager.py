from . import TorInstance
from config import TORRC_TEMPLATE_PATH

class TorManager:
    instances: list[TorInstance]
    config_template: str
    open_url: str

    def __init__(self, open_url):
        self.instances = []
        self.config_template = open(TORRC_TEMPLATE_PATH, "r").read()
        self.open_url = open_url
        
    def spawn_instance(self):
        i = len(self.instances)
        port = 9050 + i
        self.instances.append(TorInstance(port, self.config_template, self.open_url))
