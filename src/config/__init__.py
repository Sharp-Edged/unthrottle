from pathlib import Path

ROOT_PATH = Path(__file__).parents[2]
TORRC_TEMPLATE_PATH = ROOT_PATH / "static" / "torrc.temp"
TOR_CONFIGS_PATH = ROOT_PATH / "data" / "tor-configs"
TOR_DATAS_PATH = ROOT_PATH / "data" / "tor-datas"
FIREFOX_PROFILE_PATH = ROOT_PATH / "data" / "firefox-profile"
