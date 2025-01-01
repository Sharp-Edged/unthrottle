from __future__ import annotations
import asyncio
from asyncio.subprocess import Process
from string import Template

from playwright.async_api import Route, Error
from config import TOR_DATAS_PATH, TOR_CONFIGS_PATH, CHUNK_BYTES, DOWNLOAD_PATH
from pathlib import Path
from typing import TYPE_CHECKING, Iterator
from contextlib import AsyncExitStack
import httpx
import aiofiles
from utils import terminate_and_wait, get_download_url
from itertools import chain

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
    url: str = ""
    client: httpx.AsyncClient
    tor_manager: TorManager
    downloaded_chunks: int = 0
    ip: str
    state: str = "Alive"

    _astack: AsyncExitStack

    def __init__(self, port: int, config_file_template: str, open_url: str, tor_manager: TorManager):
        self.port = port
        self.proxy = f"socks5://127.0.0.1:{port}"
        self.open_url = open_url
        self.tor_manager = tor_manager

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
                    astack_inner.push_async_callback(terminate_and_wait, self.instance)

                    # 2) Wait until Tor is 'Ready'
                    while True:
                        line = await self.instance.stdout.readline()
                        if not line:
                            self.log("Tor didn't get ready... (do you have tor running already?)")
                            exit(64)
                        if b"(ready)" in line:
                            break

                    self.client = await astack_inner.enter_async_context(httpx.AsyncClient(proxy=self.proxy))

                    # 3) Try to acquire the URL
                    if await self.acquire_url():
                        # Successfuly acquired the URL
                        self.ip = await self.get_ip()
                        self.log(f"Started at ip: {self.ip}")
                        # TODO: Hmm...
                        astack_inner.pop_all()
                        astack.push_async_exit(self.client)
                        astack.push_async_callback(terminate_and_wait, self.instance)
                        break

                    self.log("Didn't acquire the URL, did you close the page?")
                    self.log("Retrying...")
            self._astack = astack.pop_all()
        return self

    def log(self, msg):
        print(f"({self.port}) {msg}")

    async def __aexit__(self, *args):
        await self._astack.__aexit__(*args)

    # Start downloading file at self.url in chunks.
    async def run(self, size_bytes: int):
        if self.tor_manager.remaining_chunks is None:
            print("Started downloading without chunks being ready??")
            exit(420)
        while len(self.tor_manager.remaining_chunks) > 0:
            chunk_id = self.tor_manager.remaining_chunks.popleft()

            low = chunk_id * CHUNK_BYTES
            rng = (low, min(size_bytes, low + CHUNK_BYTES) - 1)

            data = await self.get_range(rng)
            if len(data) != CHUNK_BYTES:
                self.log("Failed to fetch chunk, dying...")
                # Put the chunk back as we failed to download it...
                self.tor_manager.remaining_chunks.appendleft(chunk_id)
                break
            self.downloaded_chunks += 1
            async with aiofiles.open(DOWNLOAD_PATH / f"chunk.{chunk_id}", "wb") as f:
                await f.write(data)
        self.state = "Dead"

    async def content_length(self) -> int:
        return int((await self.client.head(self.url)).headers["Content-Length"])

    async def get_range(self, rng: tuple[int, int]) -> bytes:
        data = (await self.client.get(self.url, headers={"Range": f"bytes={rng[0]}-{rng[1]}"})).content
        return data

    async def get_ip(self) -> str:
        return (await self.client.get("https://httpbin.org/ip")).json()["origin"]

    # Route requests through proxy
    async def handle_route(self, route: Route) -> None:
        try:
            request = route.request
            if request.method.lower() in ["post", "put", "patch"]:
                response = await self.client.request(
                    method = request.method,
                    url = request.url,
                    content = request.post_data_buffer,
                    headers = await request.all_headers()
                )
            else:
                response = await self.client.request(
                    method = request.method,
                    url = request.url,
                    headers = await request.all_headers()
                )
            await route.fulfill(
                status = response.status_code,
                body = response.content,
                headers = dict(response.headers)
            )
        except Error as e:
            # print(f"Playwright error: {e}")
            await route.abort()
        except Exception as e:
            # Probably from httpx
            # print(f"Unexpected error: {e}")
            await route.abort()

    async def acquire_url(self) -> bool:
        try:
            # Open new browser page with self.open_url
            page = await self.tor_manager.browser_context.new_page()
            # Reroute through the correct proxy
            await page.route("http://**/*", self.handle_route)
            await page.route("https://**/*", self.handle_route)
            await page.goto(self.open_url)

            self.url = await get_download_url(page)
            print(self.url)
        except Error as e:
            pass
            # print(e)
        finally:
            if not page.is_closed():
                await page.close()

        return self.url != ""
