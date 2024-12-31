from typing import Iterator
from . import TorInstance
from config import TORRC_TEMPLATE_PATH, CHUNK_BYTES
from utils import ceil_div
from contextlib import AsyncExitStack
import asyncio

class TorManager:
    instances: list[TorInstance]
    config_template: str
    open_url: str
    # Next chunk to download
    remaining_chunks: Iterator[int]
    tasks: list[asyncio.Task] = []
    file_size_bytes: int = -1

    _astack: AsyncExitStack

    def __init__(self, open_url: str):
        self.instances = []
        self.config_template = open(TORRC_TEMPLATE_PATH, "r").read()
        self.open_url = open_url

    async def __aenter__(self):
        self._astack = await AsyncExitStack().__aenter__()
        return self

    async def __aexit__(self, *args):
        await self._astack.__aexit__(*args)
        
    async def spawn_instance(self):
        i = len(self.instances)
        port = 9050 + i
        instance = await self._astack.enter_async_context(TorInstance(port, self.config_template, self.open_url))

        # First instance
        if self.instances == []:
            self.file_size_bytes = await instance.content_length()
            num_chunks = ceil_div(self.file_size_bytes, CHUNK_BYTES)
            self.remaining_chunks = iter(range(num_chunks))

        self.instances.append(instance)
        self.tasks += [asyncio.create_task(instance.run(self.remaining_chunks, self.file_size_bytes))]

    def list_instances(self):
        if self.instances == []:
            print("No currently running tor instances.")
        else:
            print("Currently running instances:")
            for instance in self.instances:
                print(instance.proxy)

    async def wait_for_tasks(self):
        if self.tasks != []:
            await asyncio.gather(*self.tasks)
