import os

# Configuration
# Root directory is the parent of the 'app' directory containing this config file
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(ROOT_DIR, "camera_config.json")
WEB_UI_PORT = 5552
MEDIAMTX_PORT = 8554
MEDIAMTX_API_PORT = 9997


