from __future__ import annotations
from string import Template
from subprocess import Popen
import subprocess
from config import TOR_DATAS_PATH, TOR_CONFIGS_PATH, CHUNK_BYTES, DOWNLOAD_PATH
from pathlib import Path
from tqdm import tqdm
from typing import TYPE_CHECKING
import shlex
import httpx
import aiofiles

# :vomit:
if TYPE_CHECKING:
    from . import TorManager

class TorInstance:
    instance: Popen
    port: int
    proxy: str
    config_file: Path
    data_dir: Path
    url: str
    client: httpx.AsyncClient
    manager: TorManager

    @classmethod
    async def create(cls, port: int, config_file_template: str, open_url: str, manager: TorManager) -> TorInstance:
        self = cls()
        self.port = port
        self.proxy = f"socks5://127.0.0.1:{port}"
        self.manager = manager

        # Make tor data directory
        self.data_dir = TOR_DATAS_PATH / f"tor.{port}"
        self.data_dir.mkdir(exist_ok=True)

        # Make tor config file
        self.config_file = TOR_CONFIGS_PATH / f"torrc.{port}"
        config = Template(config_file_template).substitute({ "port": port, "data_dir": self.data_dir.absolute() })
        self.config_file.write_text(config)

        # Keep trying to acquire a tor instance and the proper download URL.
        while True:
            # Run the tor instance
            self.instance = Popen(["tor", "-f", self.config_file.absolute()], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

            # Wait until it has properly setup the proxy.
            for line in self.instance.stdout: # What is this retarded LSP error?
                if b"(ready)" in line:
                    break

            self.client = httpx.AsyncClient(proxy=self.proxy)

            if self.acquire_url(open_url):
                # Successfuly acquired the URL
                break

            # Didn't acquire the URL, kill tor instance and try again.
            self.instance.terminate()
            await self.client.aclose()
        return self

    # Disgusting shared state via [chunk_id] (???) TODO: Avoid vomit
    async def run(self, size_bytes: int, pbar: tqdm | None = None):
        while True:
            chunk_id = self.manager.chunk_id
            self.manager.chunk_id += 1

            low = chunk_id * CHUNK_BYTES
            if low >= size_bytes:
                break
            rng = (low, min(size_bytes, low + CHUNK_BYTES) - 1)
            data = await self.get_range(rng)
            async with aiofiles.open(DOWNLOAD_PATH / f"chunk.{chunk_id}", "wb") as f:
                await f.write(data)

            if pbar:
                pbar.update(rng[1] - rng[0] + 1)

    async def content_length(self) -> int:
        return int((await self.client.head(self.url)).headers["Content-Length"])

    async def get_range(self, rng: tuple[int, int]) -> bytes:
        return (await self.client.get(self.url, headers={"Range": f"bytes={rng[0]}-{rng[1]}"})).content

    def open_chromium(self, url):
        subprocess.run(shlex.split(f"chromium --proxy-server=\"{self.proxy}\" {url}"))

    def acquire_url(self, open_url) -> bool:
        self.open_chromium(open_url)
        self.url = input("Enter the download link (or press Enter to retry): ")
        return self.url != ""

    async def terminate(self):
        self.instance.terminate()
        await self.client.aclose()
