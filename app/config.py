import os

# Configuration
# Root directory is the parent of the 'app' directory containing this config file
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(DATA_DIR, "camera_config.json")
WEB_UI_PORT = 5552
MEDIAMTX_PORT = 8554
MEDIAMTX_API_PORT = 9997


