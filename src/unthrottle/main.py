from .tor_shell import TorShell
import argparse
import shutil
import asyncio

def main():
    asyncio.run(async_main())

async def async_main():
    if not shutil.which("chromium"):
        print("You need to have chromium to run this program.")
        exit(1)
    if not shutil.which("tor"):
        print("You need to have tor to run this program.")
        exit(2)

    argparser = argparse.ArgumentParser("unthrottle")
    argparser.add_argument("open_url", help="URL where the the download URL is located.", type=str)

    args = argparser.parse_args()

    # Game
    cmd = TorShell(open_url=args.open_url)
    await cmd.cmd_loop()
