from . import TorInstance
from config import TORRC_TEMPLATE_PATH

class TorManager:
    instances: list[TorInstance]
    config_template: str

    def __init__(self):
        self.instances = []
        self.config_template = open(TORRC_TEMPLATE_PATH, "r").read()
        
    def spawn_instance(self):
        i = len(self.instances)
        port = 9050 + i
        self.instances.append(TorInstance(port, self.config_template))
