from time import sleep
from tor import TorManager

def main() -> None:
    tor_manager = TorManager()
    tor_manager.spawn_instance()
    tor_manager.spawn_instance()
    input()
    print(tor_manager.instances[0].get("https://httpbin.org/ip"))
    print(tor_manager.instances[1].get("https://httpbin.org/ip"))
