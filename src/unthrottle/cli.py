import cmd
from tor import TorManager

class Cli(cmd.Cmd):
    prompt = "> "
    intro = "Welcome to the unthrottle CLI. Type ? to list commands."
    tor_manager: TorManager
    open_url: str
    file_size_bytes: int

    def __init__(self, open_url):
        super().__init__()
        self.open_url = open_url
        self.tor_manager = TorManager(open_url)

    def do_ls(self, arg):
        """
        List all running tor instances.
        """
        if len(self.tor_manager.instances) == 0:
            print("No currently running tor instances.")
        else:
            print("Currently running instances:")
            for instance in self.tor_manager.instances:
                print(instance.proxy)

    def do_sp(self, arg):
        """
        Spawns a new tor instance.
        After spawning, opens Chromium at the provided URL using it as a proxy.
        Now, you will have to navigate the opened tab and get to the proper download link.
        Copy the download URL and close chromium.
        Paste the copied link into the prompt.
        """
        self.tor_manager.spawn_instance()
        if not self.file_size_bytes:
            self.file_size_bytes = self.tor_manager.instances[0].content_length()

    def do_dl(self, arg):
        """
        Start the download. (Should this even exist?)
        """
        print("dl...")

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
            print("  dl          Start the download")
            print("  help [cmd]  Show help information for <cmd>")
            print("  exit        Exit this shell")

    def do_exit(self, arg) -> bool:
        print("Exiting...")
        return True