from string import Template
from subprocess import Popen
import subprocess
from config import TOR_DATAS_PATH, TOR_CONFIGS_PATH
from pathlib import Path
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

        # Run the tor instance
        self.instance = Popen(["tor", "-f", self.config_file.absolute()], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        # Wait until it has properly setup the proxy.
        for line in self.instance.stdout: # What is this retarded LSP error?
            if b"(ready)" in line:
                break

        # Acquire the actual url
        self.acquire_url(open_url)

    def content_length(self) -> int:
        sess = requests.session()
        sess.proxies = {
            "http": self.proxy,
            "https": self.proxy
        }
        return int(sess.head(self.url).headers["Content-Length"])

    def open_chromium(self, url):
        subprocess.run(shlex.split(f"chromium --proxy-server=\"{self.proxy}\" {url}"))

    def acquire_url(self, open_url):
        self.open_chromium(open_url)
        self.url = input("Enter the download link: ")

    def __del__(self):
        self.instance.terminate()
