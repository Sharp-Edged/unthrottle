from . import TorInstance
from config import TORRC_TEMPLATE_PATH, CHUNK_BYTES
from tqdm import tqdm
from utils import ceil_div
import asyncio

class TorManager:
    instances: list[TorInstance]
    config_template: str
    open_url: str
    # Next chunk to download
    chunk_id: int = 0
    tasks: list[asyncio.Task] = []
    file_size_bytes: int = -1
    progress_bar: tqdm

    def __init__(self, open_url):
        self.instances = []
        self.config_template = open(TORRC_TEMPLATE_PATH, "r").read()
        self.open_url = open_url

    async def terminate(self):
        for instance in self.instances:
            await instance.terminate()
        
    async def spawn_instance(self):
        i = len(self.instances)
        port = 9050 + i
        instance = await TorInstance.create(port, self.config_template, self.open_url, self)

        # First instance
        if self.instances == []:
            self.file_size_bytes = await instance.content_length()
            self.progress_bar = tqdm(total=self.file_size_bytes, desc="Downloading", unit="bytes")

        self.instances.append(instance)
        self.tasks += [asyncio.create_task(instance.run(self.file_size_bytes, self.progress_bar))]

    def list_instances(self):
        if self.instances == []:
            print("No currently running tor instances.")
        else:
            print("Currently running instances:")
            for instance in self.instances:
                print(instance.proxy)

    def wait_for_tasks(self):
        if self.tasks != []:
            asyncio.gather(*self.tasks)

    # async def run(self, size_bytes: int):
    #     "Runs all the instances in parallel, downloading the first 'size_bytes' bytes of the file."
    #     chunk_id = [0]
    #     chunk_id_lock = Lock()
    #     
    #     with tqdm(total=size_bytes, desc="Downloading", unit="bytes") as pbar:
    #         threads: list[Thread] = []
    #         for instance in self.instances:
    #             thread = Thread(target=instance.run, args=[size_bytes, chunk_id, chunk_id_lock, pbar])
    #             thread.start()
    #             threads += [thread]
    #
    #         for thread in threads:
    #             thread.join()

