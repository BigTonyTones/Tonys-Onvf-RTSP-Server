import os

# Configuration
# Root directory is the parent of the 'app' directory containing this config file
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(DATA_DIR, "camera_config.json")

# Migration logic: Move legacy root config files to data/ directory
import shutil
legacy_config = os.path.join(ROOT_DIR, "camera_config.json")
if os.path.exists(legacy_config) and not os.path.exists(CONFIG_FILE):
    try:
        shutil.move(legacy_config, CONFIG_FILE)
        print(f"  [Migration] Moved legacy config file to {CONFIG_FILE}")
    except Exception as e:
        print(f"  [Migration] Error moving config: {e}")

legacy_mediamtx = os.path.join(ROOT_DIR, "mediamtx.yml")
new_mediamtx = os.path.join(DATA_DIR, "mediamtx.yml")
if os.path.exists(legacy_mediamtx) and not os.path.exists(new_mediamtx):
    try:
        shutil.move(legacy_mediamtx, new_mediamtx)
        print(f"  [Migration] Moved legacy mediamtx.yml to {new_mediamtx}")
    except Exception as e:
        print(f"  [Migration] Error moving mediamtx.yml: {e}")
# Camera lookup database (brand/model -> RTSP paths) used by "Look up my camera".
# It ships with the app, so it lives inside app/ (not data/): the GitHub updater
# replaces app/, deploy_to_server.ps1 uploads app/, and Docker's ./data volume
# would hide anything baked into /app/data.
RESOURCES_DIR = os.path.join(ROOT_DIR, "app", "resources")
CAMERA_DB_FILE = os.path.join(RESOURCES_DIR, "cameras.json")
LEGACY_CAMERA_DB_FILE = os.path.join(ROOT_DIR, "cameras.json")

# Migration: older installs kept cameras.json in the project root.
if os.path.exists(LEGACY_CAMERA_DB_FILE):
    try:
        os.makedirs(RESOURCES_DIR, exist_ok=True)
        if not os.path.exists(CAMERA_DB_FILE):
            shutil.move(LEGACY_CAMERA_DB_FILE, CAMERA_DB_FILE)
            print(f"  [Migration] Moved cameras.json to {CAMERA_DB_FILE}")
        else:
            import filecmp
            if filecmp.cmp(LEGACY_CAMERA_DB_FILE, CAMERA_DB_FILE, shallow=False):
                os.remove(LEGACY_CAMERA_DB_FILE)
                print("  [Migration] Removed duplicate root cameras.json (now in app/resources)")
    except Exception as e:
        print(f"  [Migration] Error moving cameras.json: {e}")

# Default Web UI port. Can be overridden via the WEB_UI_PORT environment
# variable (useful for Docker). A port saved in the Settings UI takes
# precedence over this default at runtime.
try:
    WEB_UI_PORT = int(os.environ.get("WEB_UI_PORT", "5552"))
except (ValueError, TypeError):
    WEB_UI_PORT = 5552
MEDIAMTX_PORT = 8554
MEDIAMTX_API_PORT = 9997

# AI Defaults
AI_DEFAULT_MODEL = 'yolov8n.pt'
AI_CONFIDENCE_THRESHOLD = 50
AI_MOTION_SENSITIVITY = 50

# RTSP Grabber Reconnect Backoff
GRABBER_RECONNECT_BASE = 1.0
GRABBER_RECONNECT_MAX = 15.0

# Thread pool size for ONVIF Web services
WSGI_MAX_WORKERS = 20

# AI Inference Settings
AI_INFERENCE_FRAME_WIDTH = 640
AI_COOLDOWN_SECONDS = 5.0
AI_TARGET_INTERVAL = 0.50





