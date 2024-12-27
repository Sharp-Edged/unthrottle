from string import Template
from subprocess import Popen
import subprocess
from config import TOR_DATAS_PATH, TOR_CONFIGS_PATH, CHUNK_BYTES, DOWNLOAD_PATH
from pathlib import Path
from threading import Lock
from tqdm import tqdm
import shlex
import requests

class TorInstance:
    instance: Popen
    port: int
    proxy: str
    config_file: Path
    data_dir: Path
    url: str

    def __init__(self, port: int, config_file_template: str, open_url: str):
        self.port = port
        self.proxy = f"socks5://127.0.0.1:{port}"

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

            if self.acquire_url(open_url):
                # Successfuly acquired the URL
                break
            # Didn't acquire the URL, kill tor instance and try again.
            self.instance.terminate()

    def run(self, size_bytes: int, chunk_id: list[int], chunk_id_lock: Lock, pbar: tqdm | None):
        while True:
            with chunk_id_lock:
                my_chunk_id = chunk_id[0]
                chunk_id[0] += 1
            low = my_chunk_id * CHUNK_BYTES
            if low >= size_bytes:
                break
            rng = (low, min(size_bytes, low + CHUNK_BYTES) - 1)
            data = self.get_range(rng)
            with open(DOWNLOAD_PATH / f"chunk.{my_chunk_id}", "wb") as f:
                f.write(data)

            if pbar:
                pbar.update(rng[1] - rng[0] + 1)

    def content_length(self) -> int:
        sess = requests.session()
        sess.proxies = {
            "http": self.proxy,
            "https": self.proxy
        }
        return int(sess.head(self.url).headers["Content-Length"])

    def get_range(self, rng: tuple[int, int]) -> bytes:
        sess = requests.session()
        sess.proxies = {
            "http": self.proxy,
            "https": self.proxy
        }
        return sess.get(self.url, headers={"Range": f"bytes={rng[0]}-{rng[1]}"}).content

    def open_chromium(self, url):
        subprocess.run(shlex.split(f"chromium --proxy-server=\"{self.proxy}\" {url}"))

    def acquire_url(self, open_url) -> bool:
        self.open_chromium(open_url)
        self.url = input("Enter the download link (or press Enter to retry): ")
        return self.url != ""

    def __del__(self):
        self.instance.terminate()
