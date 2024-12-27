import asyncio
import cmd
cmd.Cmd
from tor import TorManager
from config import DOWNLOAD_PATH
from prompt_toolkit import PromptSession
import shutil

class TorShell:
    prompt = "> "
    intro = "Welcome to the unthrottle CLI. Type ? to list commands."

    tor_manager: TorManager

    session: PromptSession
    running: bool

    def __init__(self, open_url: str):
        print(self.intro)

        self.tor_manager = TorManager(open_url)
        self.session = PromptSession()
        self.running = True
        DOWNLOAD_PATH.mkdir(exist_ok=True)

    async def cmd_loop(self):
        while self.running:
            try:
                cmd = await self.session.prompt_async(self.prompt)
                await self.run_cmd(cmd)
            except (EOFError, KeyboardInterrupt):
                print("Exiting...")
                break

    async def run_cmd(self, cmd: str):
        func = getattr(self, "do_" + cmd, None)
        if func:
            await func()
        else:
            print("No such function.")

    async def do_ls(self):
        """
        List all running tor instances.
        """
        self.tor_manager.list_instances()

    async def do_sp(self):
        """
        Spawns a new tor instance.
        After spawning, opens Chromium at the provided URL using it as a proxy.
        Now, you will have to navigate the opened tab and get to the proper download link.
        Copy the download URL and close chromium.
        Paste the copied link into the prompt.
        """
        await self.tor_manager.spawn_instance()

    async def do_cl(self):
        """
        Clears all the downloaded chunks.
        Should be called every time you change the file you are downloading.
        """
        # Slightly nasty but IDC rn :shrug:
        shutil.rmtree(DOWNLOAD_PATH) # await?
        DOWNLOAD_PATH.mkdir()

    def do_help(self, arg):
        if arg:
            try:
                func = getattr(self, 'do_' + arg)
                doc = func.__doc__
                if doc:
                    print(func.__doc__)
                else:
                    print(f"No help available for '{arg}'.")
            except AttributeError:
                print(f"Command '{arg}' doesn't exist. Type ? to list commands.")
        else:
            print("Available commands:")
            print("  ls          List all active tor instances")
            print("  sp          Spawn a new tor instance")
            print("  cl          Clear all the downloaded chunks")
            print("  help [cmd]  Show help information for <cmd>")
            print("  exit        Exit this shell")

    async def do_wait(self):
        self.tor_manager.wait_for_tasks()

    async def do_exit(self):
        self.running = False
        # RAII 4 life
        await self.tor_manager.terminate()
        print("Exiting...")
