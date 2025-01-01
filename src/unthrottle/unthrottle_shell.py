import asyncio
from tor import TorManager
from config import CHUNK_BYTES, DOWNLOAD_PATH
from prompt_toolkit import PromptSession
import shutil

"""Main async shell for running the program."""
class UnthrottleShell:
    prompt = "> "
    intro = "Welcome to the Unthrottle shell. Type ? to list commands."

    tor_manager: TorManager

    running: bool
    prompt_session: PromptSession

    def __init__(self, open_url: str):
        print(self.intro)

        self.running = True
        DOWNLOAD_PATH.mkdir(exist_ok=True)

        self.tor_manager = TorManager(open_url)
        self.prompt_session = PromptSession(self.prompt)

    async def __aenter__(self):
        await self.do_clean()
        await self.tor_manager.__aenter__()
        return self

    async def __aexit__(self, *args):
        await self.tor_manager.__aexit__(*args)

    async def cmd_loop(self):
        while self.running:
            try:
                cmd = await self.prompt_session.prompt_async()
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

    async def do_status(self):
        """
        Print the status of all running instances.
        """
        self.tor_manager.print_status()

    async def do_spawn(self):
        """
        Spawns a new tor instance.
        After spawning, opens a new browser tab at the provided URL using it as a proxy.
        The script should automatically navigate up to the point of the CAPTCHA.
        After solving the CAPTCHA (or if there was no CAPTCHA) it will fetch the link and close the tab.

        You can manually close the tab to regenerate the proxy in case something goes wrong - like the
        page blocking you from getting to the download link or the countdown timer being too long.
        """
        asyncio.create_task(self.tor_manager.spawn_instance())

    async def do_clear(self):
        """
        Clears all the downloaded chunks.
        Should be called every time you change the file you are downloading.
        """
        ans = await self.prompt_session.prompt_async("Are you sure you want to clear the downloaded data? (y/N): ")
        if ans.lower() in ['y', 'yes']:
            # Slightly nasty but IDC rn :shrug:
            shutil.rmtree(DOWNLOAD_PATH) # await?
            DOWNLOAD_PATH.mkdir()

    async def do_clean(self):
        """
        Cleans up incorrectly downloaded chunks.
        """
        for f in DOWNLOAD_PATH.iterdir():
            if not f.name.startswith("chunk"):
                continue
            if f.stat().st_size != CHUNK_BYTES:
                print(f"Removing incorrect chunk {f.name.split(".")[1]}")
                f.unlink()

    # TODO: Implement
    async def do_load(self):
        """
        Loads previously downloaded chunks.
        """
        self.tor_manager.load_chunks()

    async def do_help(self, arg):
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
            print("  list          List all active tor instances")
            print("  spawn       Spawn a new tor instance")
            print("  clear       Clear all the downloaded chunks")
            print("  help [cmd]  Show help information for <cmd>")
            print("  exit        Exit this shell")

    async def do_collect(self):
        """
        Collects all the downloaded chunks into a single file.
        """
        self.tor_manager.collect_into_file("downloaded_file")

    async def do_wait(self):
        await self.tor_manager.wait_for_tasks()

    async def do_exit(self):
        self.running = False
        print("Exiting...")
