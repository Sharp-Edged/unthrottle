from . import TorInstance
from config import TORRC_TEMPLATE_PATH, CHUNK_BYTES
from threading import Thread, Lock
from tqdm import tqdm
from utils import ceil_div

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

    def run(self, size_bytes: int):
        "Runs all the instances in parallel, downloading the first 'size_bytes' bytes of the file."
        chunk_id = [0]
        chunk_id_lock = Lock()
        
        with tqdm(total=size_bytes, desc="Downloading", unit="bytes") as pbar:
            threads: list[Thread] = []
            for instance in self.instances:
                thread = Thread(target=instance.run, args=[size_bytes, chunk_id, chunk_id_lock, pbar])
                thread.start()
                threads += [thread]

            for thread in threads:
                thread.join()

