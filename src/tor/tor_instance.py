from string import Template
from subprocess import Popen
from config import TOR_DATAS_PATH, TOR_CONFIGS_PATH
from pathlib import Path
import requests

class TorInstance:
    instance: Popen
    port: int
    proxy: str
    config_file: Path
    data_dir: Path

    def gen_config_file(self):
        pass

    def __init__(self, port: int, config_file_template: str):
        self.port = port
        self.proxy = f"socks5://127.0.0.1:{port}"

        # Make tor data directory
        self.data_dir = TOR_DATAS_PATH / f"tor.{port}"
        self.data_dir.mkdir()

        # Make tor config file
        self.config_file = TOR_CONFIGS_PATH / f"torrc.{port}"
        config = Template(config_file_template).substitute({ "port": port, "data_dir": self.data_dir.absolute() })
        self.config_file.write_text(config)

        # Run the tor instance
        self.instance = Popen(["tor", "-f", self.config_file.absolute()])

    def get(self, url: str) -> str:
        sess = requests.session()
        sess.proxies = {
            "http": self.proxy,
            "https": self.proxy
        }
        return sess.get(url).text

    def __del__(self):
        self.instance.terminate()
