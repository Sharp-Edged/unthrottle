from pathlib import Path

# Paths
ROOT_PATH = Path(__file__).parents[2]
TORRC_TEMPLATE_PATH = ROOT_PATH / "static" / "torrc.temp"
DATA_PATH = ROOT_PATH / "data"
TOR_CONFIGS_PATH = DATA_PATH / "tor-configs"
TOR_DATAS_PATH = DATA_PATH / "tor-datas"
DOWNLOAD_PATH = DATA_PATH / "download"

# We download the file in chunks of this many bytes
CHUNK_BYTES = 256 * 1024

# Chrome Debugging Protocol port
CDP_PORT = 9222
