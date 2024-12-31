from __future__ import annotations
import asyncio
from asyncio.subprocess import Process
from string import Template
from config import TOR_DATAS_PATH, TOR_CONFIGS_PATH, CHUNK_BYTES, DOWNLOAD_PATH
from pathlib import Path
from typing import TYPE_CHECKING, Iterator
from contextlib import AsyncExitStack
import httpx
import aiofiles
from prompt_toolkit.shortcuts import PromptSession

# :vomit:
if TYPE_CHECKING:
    from . import TorManager

class TorInstance:
    instance: Process
    port: int
    proxy: str
    config_file: Path
    data_dir: Path
    open_url: str
    url: str
    client: httpx.AsyncClient

    _astack: AsyncExitStack

    def __init__(self, port: int, config_file_template: str, open_url: str):
        self.port = port
        self.proxy = f"socks5://127.0.0.1:{port}"
        self.open_url = open_url

        # Make tor data directory
        self.data_dir = TOR_DATAS_PATH / f"tor.{port}"
        self.data_dir.mkdir(exist_ok=True)

        # Make tor config file
        self.config_file = TOR_CONFIGS_PATH / f"torrc.{port}"
        config = Template(config_file_template).substitute({ "port": port, "data_dir": self.data_dir.absolute() })
        self.config_file.write_text(config) # async?

    async def __aenter__(self):
        async with AsyncExitStack() as astack:
            # Keep trying to acquire a Tor instance and the proper download URL.
            while True:
                async with AsyncExitStack() as astack_inner:
                    # 1) Run the Tor instance
                    self.instance = await asyncio.create_subprocess_exec("tor", "-f", self.config_file.absolute(), stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE)
                    async def terminate_and_wait(process: Process):
                        if process.returncode is None:
                            process.terminate()
                            await process.wait()
                    astack_inner.push_async_callback(terminate_and_wait, self.instance)

                    # 2) Wait until Tor is 'Ready'
                    while True:
                        line = await self.instance.stdout.readline()
                        if not line:
                            print("Wtf lol?")
                            exit(64)
                        if b"(ready)" in line:
                            break

                    self.client = await astack_inner.enter_async_context(httpx.AsyncClient(proxy=self.proxy))

                    # 3) Try to acquire the URL
                    if await self.acquire_url(self.open_url):
                        # Successfuly acquired the URL
                        # TODO: Hmm...
                        astack_inner.pop_all()
                        astack.push_async_exit(self.client)
                        astack.push_async_callback(terminate_and_wait, self.instance)
                        break
            self._astack = astack.pop_all()
        return self

    async def __aexit__(self, *args):
        await self._astack.__aexit__(*args)

    # Start downloading file at self.url in chunks.
    async def run(self, remaining_chunks: Iterator[int], size_bytes: int):
        while True:
            try:
                chunk_id = next(remaining_chunks)
            except StopIteration:
                break

            low = chunk_id * CHUNK_BYTES
            rng = (low, min(size_bytes, low + CHUNK_BYTES) - 1)

            data = await self.get_range(rng)
            async with aiofiles.open(DOWNLOAD_PATH / f"chunk.{chunk_id}", "wb") as f:
                await f.write(data)

    async def content_length(self) -> int:
        return int((await self.client.head(self.url)).headers["Content-Length"])

    async def get_range(self, rng: tuple[int, int]) -> bytes:
        return (await self.client.get(self.url, headers={"Range": f"bytes={rng[0]}-{rng[1]}"})).content

    def open_chromium(self, url):
        # subprocess.run(shlex.split(f"chromium --proxy-server=\"{self.proxy}\" {url}"))
        pass

    async def acquire_url(self, open_url) -> bool:
        self.open_chromium(open_url)
        sess = PromptSession() # TODO: wow this is disgusting
        self.url = await sess.prompt_async("Enter the download link (or press Enter to retry): ")
        return self.url != ""
