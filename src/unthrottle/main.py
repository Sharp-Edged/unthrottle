from time import sleep
from tor import TorManager
from config import FIREFOX_PROFILE_PATH
import subprocess
import argparse
import shutil
import shlex

def run_cmd(cmd) -> int:
    return subprocess.run(shlex.split(cmd)).returncode

def main():
    if not shutil.which("chromium"):
        print("You need to have chromium to run this program.")
        exit(1)
    if not shutil.which("tor"):
        print("You need to have tor to run this program.")
        exit(2)

    argparser = argparse.ArgumentParser("unthrottle")
    argparser.add_argument("url", help="URL where the the download URL is located.", type=str)

    args = argparser.parse_args()

    tor_manager = TorManager()
    tor_manager.spawn_instance()
    # tor_manager.spawn_instance()
    tor_manager.instances[0].open_chromium(args.url)
    # print(tor_manager.instances[1].get("https://httpbin.org/ip"))