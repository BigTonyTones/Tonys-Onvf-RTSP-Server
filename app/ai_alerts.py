import json
import os
import re
import time
import threading

from .config import DATA_DIR

# Directory where annotated AI detection snapshots are stored
ALERTS_DIR = os.path.join(DATA_DIR, "ai_alerts")

# Default cap on stored images to avoid filling the disk (user-adjustable)
MAX_ALERTS = 500

# Allowed range for the user-configurable cap
MIN_ALERTS_CAP = 10
MAX_ALERTS_CAP = 10000

# Persisted store settings (currently just the cap)
_SETTINGS_FILE = os.path.join(DATA_DIR, "ai_alerts_settings.json")

# Filename format: <epoch_ms>_<camera_id>_<tag1-tag2>[_lp-PLATE].jpg
_FILENAME_RE = re.compile(r'^(\d+)_(\d+)_([a-z0-9\-]+)(?:_lp-([a-zA-Z0-9\-]+))?\.jpg$')


class AIAlertStore:
    """Stores annotated AI detection snapshots on disk, capped at MAX_ALERTS.

    All metadata (timestamp, camera id, detected tags) is encoded in the
    filename so no separate index file is needed.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.max_alerts = MAX_ALERTS
        try:
            os.makedirs(ALERTS_DIR, exist_ok=True)
        except Exception as e:
            print(f"  [AI Alerts] Could not create alerts dir: {e}")
        try:
            with open(_SETTINGS_FILE, 'r') as f:
                saved = json.load(f)
            self.max_alerts = self._clamp_cap(saved.get('max_alerts', MAX_ALERTS))
        except Exception:
            pass

    @staticmethod
    def _clamp_cap(value):
        try:
            return max(MIN_ALERTS_CAP, min(MAX_ALERTS_CAP, int(value)))
        except (TypeError, ValueError):
            return MAX_ALERTS

    def set_max_alerts(self, value):
        """Set and persist the stored-image cap, pruning immediately."""
        self.max_alerts = self._clamp_cap(value)
        try:
            with open(_SETTINGS_FILE, 'w') as f:
                json.dump({'max_alerts': self.max_alerts}, f)
        except Exception as e:
            print(f"  [AI Alerts] Could not persist settings: {e}")
        with self._lock:
            self._prune()
        return self.max_alerts

    def save(self, camera_id, tags, image_bytes, license_plate=None):
        """Save an annotated JPEG and prune history beyond MAX_ALERTS."""
        if not image_bytes:
            return
        ts_ms = int(time.time() * 1000)
        tag_str = '-'.join(sorted(set(t.lower() for t in tags)))
        tag_str = re.sub(r'[^a-z0-9\-]', '', tag_str) or 'unknown'
        if license_plate:
            cleaned_plate = re.sub(r'[^a-zA-Z0-9\-]', '', license_plate).upper()
            if cleaned_plate:
                filename = f"{ts_ms}_{int(camera_id)}_{tag_str}_lp-{cleaned_plate}.jpg"
            else:
                filename = f"{ts_ms}_{int(camera_id)}_{tag_str}.jpg"
        else:
            filename = f"{ts_ms}_{int(camera_id)}_{tag_str}.jpg"
        with self._lock:
            try:
                with open(os.path.join(ALERTS_DIR, filename), 'wb') as f:
                    f.write(image_bytes)
                self._prune()
            except Exception as e:
                print(f"  [AI Alerts] Failed to save alert image: {e}")

    def _prune(self):
        """Delete oldest images beyond the cap. Caller must hold the lock."""
        try:
            files = [f for f in os.listdir(ALERTS_DIR) if _FILENAME_RE.match(f)]
        except Exception:
            return
        if len(files) <= self.max_alerts:
            return
        # Millisecond epoch prefixes are fixed-width, so a plain sort is chronological
        files.sort()
        for old in files[:len(files) - self.max_alerts]:
            try:
                os.remove(os.path.join(ALERTS_DIR, old))
            except Exception:
                pass

    def list_alerts(self, camera_id=None):
        """Return alert metadata, newest first, optionally filtered by camera."""
        try:
            files = os.listdir(ALERTS_DIR)
        except Exception:
            return []
        alerts = []
        for f in files:
            m = _FILENAME_RE.match(f)
            if not m:
                continue
            cid = int(m.group(2))
            if camera_id is not None and cid != camera_id:
                continue
            alerts.append({
                'file': f,
                'ts': int(m.group(1)),
                'camera_id': cid,
                'tags': m.group(3).split('-'),
                'license_plate': m.group(4),
            })
        alerts.sort(key=lambda a: a['ts'], reverse=True)
        return alerts

    def get_image_path(self, filename):
        """Return the absolute path for a stored image, or None if invalid."""
        if not _FILENAME_RE.match(filename or ''):
            return None
        path = os.path.join(ALERTS_DIR, filename)
        return path if os.path.isfile(path) else None

    def delete_files(self, filenames):
        """Delete specific alert images by filename. Returns count removed."""
        removed = 0
        with self._lock:
            for f in filenames or []:
                if not _FILENAME_RE.match(f or ''):
                    continue
                try:
                    os.remove(os.path.join(ALERTS_DIR, f))
                    removed += 1
                except Exception:
                    pass
        return removed

    def clear(self, camera_id=None):
        """Delete all stored alerts, optionally only for one camera."""
        removed = 0
        with self._lock:
            try:
                files = os.listdir(ALERTS_DIR)
            except Exception:
                return 0
            for f in files:
                m = _FILENAME_RE.match(f)
                if not m:
                    continue
                if camera_id is not None and int(m.group(2)) != camera_id:
                    continue
                try:
                    os.remove(os.path.join(ALERTS_DIR, f))
                    removed += 1
                except Exception:
                    pass
        return removed


# Shared singleton used by the camera detection loops and the web API
alert_store = AIAlertStore()
