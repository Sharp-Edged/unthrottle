from asyncio.subprocess import Process
from collections import deque
from pathlib import Path
from typing import Iterator, Deque
from . import TorInstance
from config import DOWNLOAD_PATH, TORRC_TEMPLATE_PATH, CHUNK_BYTES, CDP_PORT
from utils import ceil_div
from contextlib import AsyncExitStack
from rich.progress import track
from utils import terminate_and_wait
from playwright.async_api import Browser, BrowserContext, async_playwright, Playwright
from typing import Any
import asyncio

class TorManager:
    instances: list[TorInstance]
    config_template: str
    open_url: str
    # Chunks to download
    remaining_chunks: Deque[int] | None = None
    tasks: list[asyncio.Task] = []
    file_size_bytes: int | None = None
    # id to assign to a new instance
    new_instance_id: int = 0

    browser_process: Process
    browser: Browser
    browser_context: BrowserContext
    playwright: Playwright

    _astack: AsyncExitStack

    def __init__(self, open_url: str):
        self.instances = []
        self.config_template = open(TORRC_TEMPLATE_PATH, "r").read()
        self.open_url = open_url

    async def __aenter__(self):
        async with AsyncExitStack() as astack:
            self.browser_process = await asyncio.create_subprocess_exec("chromium", f"--remote-debugging-port={CDP_PORT}", stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            astack.push_async_callback(terminate_and_wait, self.browser_process)
            self.playwright = await astack.enter_async_context(async_playwright())
            self.browser = await self.playwright.chromium.connect_over_cdp(f"http://localhost:{CDP_PORT}")
            astack.push_async_callback(self.browser.close)
            self.browser_context = self.browser.contexts[0]

            # Disable timeouts
            self.browser_context.set_default_timeout(0)

            self._astack = astack.pop_all()
        return self

    async def __aexit__(self, *args):
        await self._astack.__aexit__(*args)
        
    async def spawn_instance(self):
        id = self.new_instance_id
        self.new_instance_id += 1
        port = 9050 + id
        instance = await self._astack.enter_async_context(TorInstance(port, self.config_template, self.open_url, self))

        # First instance
        if self.file_size_bytes is None:
            self.file_size_bytes = await instance.content_length()
        if self.remaining_chunks is None:
            self.load_chunks()

        self.instances.append(instance)
        self.tasks += [asyncio.create_task(instance.run(self.file_size_bytes))]

    # "Load" all previously downloaded chunks
    def load_chunks(self):
        if self.file_size_bytes is None:
            print("Uhh...")
            exit(69)
        num_chunks = ceil_div(self.file_size_bytes, CHUNK_BYTES)
        completed_chunks = [int(f.name.split(".")[1]) for f in DOWNLOAD_PATH.iterdir() if f.name.startswith("chunk")]
        self.remaining_chunks = deque([i for i in range(num_chunks) if i not in completed_chunks])
        print(f"Number of remaining chunks: {len(list(self.remaining_chunks))}")

    # Collects all the chunks into a file
    def collect_into_file(self, out_file_path: str):
        chunk_files = sorted(
            [f for f in DOWNLOAD_PATH.iterdir() if f.name.startswith("chunk")],
            key=lambda f: int(f.name.split(".")[1])
        )
        chunk_names = map(lambda f: f.name, chunk_files)
        num_chunks = len(chunk_files)
        for i in range(1, num_chunks):
            if f"chunk.{i}" not in chunk_names:
                print(f"Missing chunk {i}!")
        with open(out_file_path, "wb") as out_file:
            for chunk_file_path in chunk_files:
                with chunk_file_path.open("rb") as chunk_file:
                    out_file.write(chunk_file.read())

    def print_status(self):
        if self.instances == []:
            print("No currently running tor instances.")
        else:
            print("Currently running instances:")
            for instance in self.instances:
                print(f"({instance.state}) {instance.port} - downloaded chunks: {instance.downloaded_chunks}, public ip: {instance.ip}")

    async def wait_for_tasks(self):
        if self.tasks != []:
            await asyncio.gather(*self.tasks)
