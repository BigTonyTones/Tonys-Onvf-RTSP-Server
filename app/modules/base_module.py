"""
Base Module — Abstract base class that all addon modules must extend.

Provides the interface for modules to hook into the application lifecycle,
register routes, inject UI elements, respond to camera / AI events, and
persist their own configuration.

Storage layout (all under data/addons/<module_id>/):
    config.json   — global settings + per-camera settings ("cameras": {id: {...}})
    ...           — anything else the module wants (databases, media, models)
"""

import copy
import functools
import json
import logging
import os
import threading
import time
from collections import deque

logger = logging.getLogger(__name__)

SECRET_PLACEHOLDER = '********'


_FFMPEG_CACHE = {}


def find_ffmpeg(name='ffmpeg'):
    """Locate ffmpeg/ffprobe without side effects: the app's bundled copy
    (<root>/ffmpeg/), then PATH, then common install locations."""
    if name in _FFMPEG_CACHE:
        return _FFMPEG_CACHE[name]
    import shutil
    from app.config import ROOT_DIR
    exe = f'{name}.exe' if os.name == 'nt' else name
    candidates = [os.path.join(ROOT_DIR, 'ffmpeg', exe), shutil.which(exe),
                  f'/usr/bin/{name}', f'/usr/local/bin/{name}', f'/opt/homebrew/bin/{name}']
    for c in candidates:
        if c and os.path.exists(c):
            _FFMPEG_CACHE[name] = os.path.abspath(c)
            return _FFMPEG_CACHE[name]
    return exe


def _deep_merge(base, override):
    """Return a new dict with ``override`` merged on top of ``base`` (recursively)."""
    result = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


class BaseModule:
    """Abstract base class for addon modules.

    Subclasses override only the hooks they need. Every hook has a safe
    default implementation.

    Class attributes subclasses may set:
        wants_frames   — True to receive ``on_ai_frame`` calls from the AI loop.
        secret_fields  — global config keys that are masked in the API/UI.
        camera_secret_fields — per-camera config keys that are masked.
    """

    wants_frames = False
    secret_fields = ()
    camera_secret_fields = ()

    def __init__(self, manifest, module_manager):
        self.module_id = manifest.get('id', 'unknown')
        self.name = manifest.get('name', 'Unknown Module')
        self.description = manifest.get('description', '')
        self.version = manifest.get('version', '1.0.0')
        self.icon = manifest.get('icon', 'fas fa-puzzle-piece')
        self.color = manifest.get('color', '#6366f1')
        self.author = manifest.get('author', 'Unknown')
        self.price = manifest.get('price', '')
        self.trial_days = manifest.get('trial_days', 14)
        self.requirements = manifest.get('requirements', [])
        self.manifest = manifest
        self.module_manager = module_manager

        self._config_lock = threading.RLock()
        self._config_cache = None
        self._activity = deque(maxlen=200)

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------

    def is_active(self):
        """Check if this module is currently active (licensed or on trial, and enabled)."""
        return self.module_manager.is_module_active(self.module_id)

    @property
    def camera_manager(self):
        """The core CameraManager (available after server startup)."""
        return getattr(self.module_manager, '_manager', None)

    def get_camera(self, camera_id):
        mgr = self.camera_manager
        if not mgr:
            return None
        try:
            camera_id = int(camera_id)
        except (TypeError, ValueError):
            return None
        for cam in getattr(mgr, 'cameras', []):
            if cam.id == camera_id:
                return cam
        return None

    def get_cameras(self):
        mgr = self.camera_manager
        return list(getattr(mgr, 'cameras', [])) if mgr else []

    # ------------------------------------------------------------------
    # Activity log (shown on the addon page)
    # ------------------------------------------------------------------

    def log(self, message, level='info'):
        """Record a line in the module's activity log and the Python log."""
        entry = {'ts': time.time(), 'level': level, 'message': str(message)}
        self._activity.append(entry)
        log_fn = getattr(logger, level if level in ('debug', 'info', 'warning', 'error') else 'info')
        log_fn(f"[{self.name}] {message}")
        if level in ('warning', 'error'):
            print(f"  [{self.name}] {message}")

    def get_activity(self, limit=50):
        return list(self._activity)[-limit:][::-1]

    # ------------------------------------------------------------------
    # Storage & configuration
    # ------------------------------------------------------------------

    @property
    def data_dir(self):
        """Per-module data directory (created on demand)."""
        from app.config import DATA_DIR
        path = os.path.join(DATA_DIR, 'addons', self.module_id)
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def config_path(self):
        return os.path.join(self.data_dir, 'config.json')

    def default_config(self):
        """Global configuration defaults. Override in subclasses."""
        return {}

    def default_camera_config(self):
        """Per-camera configuration defaults. Override in subclasses."""
        return {}

    def _read_config_file(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
        except Exception as e:
            self.log(f"Could not read config, using defaults: {e}", 'warning')
        return {}

    def _write_config_file(self, data):
        tmp = self.config_path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, self.config_path)

    def _raw_config(self):
        with self._config_lock:
            if self._config_cache is None:
                self._config_cache = self._read_config_file()
            return self._config_cache

    def get_config(self):
        """Return the merged global config (defaults + saved values)."""
        with self._config_lock:
            raw = dict(self._raw_config())
            raw.pop('cameras', None)
            return _deep_merge(self.default_config(), raw)

    def validate_config(self, config):
        """Validate/normalise a full global config dict. Raise ValueError to reject."""
        return config

    def update_config(self, patch):
        """Merge ``patch`` into the global config, validate, persist and notify."""
        patch = dict(patch or {})
        patch.pop('cameras', None)
        with self._config_lock:
            old = self.get_config()
            for key in self.secret_fields:
                if patch.get(key) == SECRET_PLACEHOLDER:
                    patch.pop(key)
            new = self.validate_config(_deep_merge(old, patch))
            raw = dict(self._raw_config())
            cams = raw.get('cameras', {})
            raw = dict(new)
            raw['cameras'] = cams
            self._write_config_file(raw)
            self._config_cache = raw
        try:
            self.on_config_changed(old, new)
        except Exception as e:
            self.log(f"Error applying new settings: {e}", 'error')
        return new

    def get_camera_config(self, camera_id):
        """Return the merged per-camera config for ``camera_id``."""
        with self._config_lock:
            saved = self._raw_config().get('cameras', {}).get(str(camera_id), {})
            return _deep_merge(self.default_camera_config(), saved)

    def get_all_camera_configs(self):
        return {str(cam.id): self.get_camera_config(cam.id) for cam in self.get_cameras()}

    def validate_camera_config(self, camera_id, config):
        """Validate/normalise a per-camera config. Raise ValueError to reject."""
        return config

    def update_camera_config(self, camera_id, patch):
        """Merge ``patch`` into a camera's config, validate, persist and notify."""
        patch = dict(patch or {})
        with self._config_lock:
            old = self.get_camera_config(camera_id)
            for key in self.camera_secret_fields:
                if patch.get(key) == SECRET_PLACEHOLDER:
                    patch.pop(key)
            new = self.validate_camera_config(camera_id, _deep_merge(old, patch))
            raw = dict(self._raw_config())
            cams = dict(raw.get('cameras', {}))
            cams[str(camera_id)] = new
            raw['cameras'] = cams
            self._write_config_file(raw)
            self._config_cache = raw
        camera = self.get_camera(camera_id)
        try:
            self.on_camera_config_changed(camera_id, camera, old, new)
        except Exception as e:
            self.log(f"Error applying camera settings: {e}", 'error')
        return new

    def public_config(self):
        """Global config with secret fields masked (for the browser)."""
        cfg = self.get_config()
        for key in self.secret_fields:
            if cfg.get(key):
                cfg[key] = SECRET_PLACEHOLDER
        return cfg

    def public_camera_config(self, camera_id):
        cfg = self.get_camera_config(camera_id)
        for key in self.camera_secret_fields:
            if cfg.get(key):
                cfg[key] = SECRET_PLACEHOLDER
        return cfg

    def on_config_changed(self, old, new):
        """Called after the global config was saved."""
        pass

    def on_camera_config_changed(self, camera_id, camera, old, new):
        """Called after a camera's config was saved. ``camera`` may be None."""
        pass

    # ------------------------------------------------------------------
    # Shared helpers for media work
    # ------------------------------------------------------------------

    def rtsp_port(self):
        mgr = self.camera_manager
        try:
            return int(getattr(mgr, 'rtsp_port', None) or 8554)
        except (TypeError, ValueError):
            return 8554

    def local_rtsp_url(self, camera, stream='main'):
        """Loopback MediaMTX URL for a running camera (loopback is auth-exempt)."""
        suffix = '_sub' if stream == 'sub' and camera.sub_stream_url and not getattr(camera, 'disable_substream', False) else '_main'
        return f"rtsp://127.0.0.1:{self.rtsp_port()}/{camera.path_name}{suffix}"

    def ffmpeg_path(self):
        return find_ffmpeg()

    @staticmethod
    def subprocess_flags():
        import subprocess
        return subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

    def grab_snapshot(self, camera, stream='main', timeout=15):
        """Return JPEG bytes of the camera's current frame, or None."""
        import subprocess
        if getattr(camera, 'status', '') != 'running':
            return None
        cmd = [self.ffmpeg_path(), '-hide_banner', '-loglevel', 'error',
               '-rtsp_transport', 'tcp', '-i', self.local_rtsp_url(camera, stream),
               '-frames:v', '1', '-q:v', '2', '-f', 'image2', '-c:v', 'mjpeg', 'pipe:1']
        try:
            res = subprocess.run(cmd, capture_output=True, timeout=timeout,
                                 creationflags=self.subprocess_flags())
            if res.returncode == 0 and res.stdout:
                return res.stdout
        except Exception as e:
            self.log(f"Snapshot failed for {camera.name}: {e}", 'warning')
        return None

    def notify(self, title, message, image_bytes=None, event_key='addon'):
        """Send a push notification through the app's configured providers."""
        mgr = self.camera_manager
        notifier = getattr(mgr, 'notifier', None) if mgr else None
        if not notifier:
            return False
        try:
            # Addon alerts are opt-in per addon, so they go straight to the
            # configured providers instead of the core's event allow-list.
            cfg = notifier.get_config()
            notifier._executor.submit(notifier._dispatch, cfg, title, message, image_bytes)
            return True
        except Exception as e:
            self.log(f"Notification failed: {e}", 'warning')
            return False

    def log_camera_event(self, camera, topic, data_name, value, tags=None, extra=None):
        """Add an entry to the camera's event log (shown in the core Events UI)."""
        from datetime import datetime
        evt = {
            'topic': topic,
            'value': value,
            'data_name': data_name,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'camera_id': getattr(camera, 'id', None),
            'camera_name': getattr(camera, 'name', ''),
            'tags': list(tags or []),
            'type': self.module_id,
        }
        if extra:
            evt.update(extra)
        try:
            logs = getattr(camera, 'event_logs', None)
            if logs is not None:
                logs.append(evt)
                if len(logs) > 50:
                    logs.pop(0)
            mgr = self.camera_manager
            if mgr is not None:
                if not hasattr(mgr, 'onvif_events'):
                    mgr.onvif_events = []
                mgr.onvif_events.append(evt)
                if len(mgr.onvif_events) > 200:
                    mgr.onvif_events.pop(0)
        except Exception:
            pass
        return evt

    def emit_event(self, camera, event_type, payload=None):
        """Broadcast an addon event (e.g. 'audio', 'face', 'plate') to other modules."""
        try:
            self.module_manager.dispatch_addon_event(self.module_id, camera, event_type, payload or {})
        except Exception as e:
            self.log(f"emit_event failed: {e}", 'warning')

    # ------------------------------------------------------------------
    # Route helper
    # ------------------------------------------------------------------

    def api_route(self, app, login_required, rule, methods=('GET',), require_active=True):
        """Decorator: register ``/api/addons/<module_id><rule>`` with auth,
        active-license check and JSON error handling."""
        from flask import jsonify
        module = self

        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if require_active and not module.is_active():
                    return jsonify({'success': False, 'error': f'{module.name} is not active'}), 403
                try:
                    return func(*args, **kwargs)
                except ValueError as e:
                    return jsonify({'success': False, 'error': str(e)}), 400
                except Exception as e:
                    module.log(f"API error on {rule}: {e}", 'error')
                    return jsonify({'success': False, 'error': str(e)}), 500

            endpoint = f"addon_{module.module_id}_{func.__name__}"
            app.add_url_rule(f"/api/addons/{module.module_id}{rule}", endpoint,
                             login_required(wrapper), methods=list(methods))
            return wrapper
        return decorator

    # ------------------------------------------------------------------
    # UI Registration Hooks
    # ------------------------------------------------------------------

    def register_routes(self, app, manager, login_required):
        """Register Flask routes. Routes are registered once at boot whether or
        not the module is active, so they must check ``is_active()`` (the
        ``api_route`` helper does this for you)."""
        pass

    def has_page(self):
        return bool(self.register_settings_sections() or self.register_camera_tabs() or self.get_page_html())

    def register_nav_items(self):
        """Return navigation button definitions (default: link to the addon page)."""
        if self.has_page():
            return [{
                'id': f'nav-addon-{self.module_id}',
                'label': self.manifest.get('nav_label', self.name),
                'icon': self.icon,
                'href': f'/addon/{self.module_id}',
                'requires_active': True
            }]
        return []

    def register_camera_tabs(self):
        """Return camera tab definitions shown on the addon page.

        Keys: id, label, icon, html, css, js, and optionally on_populate /
        on_reset / on_collect (names of global JS functions). If the callbacks
        are omitted, every element inside ``html`` with a ``data-field``
        attribute is populated from / collected into the camera config
        automatically (checkbox → bool, number → number, multi-select → list,
        data-type="list" → comma list, data-type="json" → JSON).
        """
        return []

    def register_settings_sections(self):
        """Return global settings sections (id, label, icon, html, css, js).
        Fields use ``data-field="config_key"`` and are saved automatically."""
        return []

    def get_page_html(self):
        """Extra HTML (dashboards, tables, actions) rendered on the addon page
        below the settings. May include <script>; the page provides
        ``addonApi(path, method, body)`` for calling this module's API."""
        return ''

    def get_status(self):
        """Small dict of status values shown at the top of the addon page."""
        return {}

    # ------------------------------------------------------------------
    # Camera Lifecycle Hooks
    # ------------------------------------------------------------------

    def on_camera_save(self, camera, data):
        """Called when a camera is saved from the main camera editor."""
        pass

    def on_camera_start(self, camera):
        pass

    def on_camera_stop(self, camera):
        pass

    def on_camera_delete(self, camera_id):
        pass

    # ------------------------------------------------------------------
    # AI hooks
    # ------------------------------------------------------------------

    def on_ai_event(self, camera, event):
        """AI detection state change.

        ``event`` keys: state ('start' | 'update' | 'end'), tags (list),
        confidences (dict tag->0..1), license_plate (str|None),
        snapshot (JPEG bytes|None), timestamp (epoch seconds).
        Called from the camera's AI thread — keep it quick.
        """
        pass

    def on_ai_frame(self, camera, frame, detections, license_plate=None):
        """Every analysed frame with detections (only if ``wants_frames``).

        ``frame`` is the BGR numpy array used for inference (do not modify;
        copy it if you keep it). ``detections`` is a list of dicts:
        {'tag', 'class_id', 'confidence', 'box': [x1, y1, x2, y2] (0..1)}.
        Called from the camera's AI thread — hand heavy work to a worker.
        """
        pass

    def on_addon_event(self, source_module_id, camera, event_type, payload):
        """Event emitted by another addon via ``emit_event``."""
        pass

    # ------------------------------------------------------------------
    # Application Lifecycle Hooks
    # ------------------------------------------------------------------

    def on_startup(self, manager):
        """Called at server startup (if active) or when the module becomes active."""
        pass

    def on_shutdown(self, manager):
        """Called at server shutdown or when the module becomes inactive."""
        pass
