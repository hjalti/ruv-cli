import sys
from pathlib import Path

CONFIG_DIR = Path.home() / '.config' / 'ruvcli'
CONFIG_PATH = CONFIG_DIR / 'config.py'

sys.path.append(str(CONFIG_DIR))

from .default_config import *
if CONFIG_PATH.exists():
    from config import *

def config_exists():
    return CONFIG_PATH.exists()

def copy_config():
    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(parents=True)
    default_config = (Path(__file__).parent / 'default_config.py').read_text()
    CONFIG_PATH.write_text(default_config)

