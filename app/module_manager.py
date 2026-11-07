"""
Module Manager — Core registry for addon modules.

Discovers, loads, validates, and manages addon modules with license key
activation and trial support. Modules are discovered from the app/modules/
directory and can inject routes, nav items, camera tabs, settings, and
receive camera / AI events.
"""

import os
import sys
import json
import time
import logging
import importlib
import threading
import subprocess
from datetime import datetime, timezone, timedelta

from .config import DATA_DIR

logger = logging.getLogger(__name__)

# Legacy Ed25519 license keys are signed by the separate keygen app (not in
# this repository); license_keys.py only holds the public key used to check them.
from .license_keys import validate_license_key, decode_license_key, PUBLIC_KEY_HEX  # noqa: E402

# New licensing: Lemon Squeezy online activation + offline machine-bound tokens.
from .licensing import machine_id, ls_client, license_store, offline_token  # noqa: E402

import re  # noqa: E402

MODULES_STATE_FILE = os.path.join(DATA_DIR, 'modules.json')
MODULES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules')

# A Lemon Squeezy license key looks like 8-4-4-4-12 hex (UUID shape).
_LS_KEY_RE = re.compile(r'^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-'
                        r'[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$')

_MACHINE_FP = None


def machine_fingerprint():
    """This machine's stable fingerprint (computed once)."""
    global _MACHINE_FP
    if _MACHINE_FP is None:
        try:
            _MACHINE_FP = machine_id.fingerprint()
        except Exception as e:
            logger.error(f"Could not compute machine fingerprint: {e}")
            _MACHINE_FP = 'unknown'
    return _MACHINE_FP


def _requirement_installed(req):
    """Check whether a manifest requirement is importable."""
    import importlib.util
    name = req.get('import') if isinstance(req, dict) else None
    if not name:
        return True
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


class ModuleManager:
    """Central registry for addon modules."""

    def __init__(self):
        self.modules = {}           # module_id -> module instance
        self.module_manifests = {}  # module_id -> manifest dict
        self.load_errors = {}       # module_id/folder -> error string
        self._state = {}            # module_id -> license/trial state
        self._manager = None        # CameraManager reference (set on startup)
        self._state_lock = threading.RLock()
        self._started = set()       # module ids whose on_startup has run
        self._lifecycle_lock = threading.RLock()
        self._frame_listeners = []  # cached list of active modules wanting frames
        self._install_jobs = {}     # module_id -> {'running', 'log', 'ok'}
        self._watchdog = None
        self._load_state()
        self._discover_modules()

    # ------------------------------------------------------------------
    # State persistence
    # ------------------------------------------------------------------

    def _load_state(self):
        try:
            if os.path.exists(MODULES_STATE_FILE):
                with open(MODULES_STATE_FILE, 'r') as f:
                    data = json.load(f)
                    self._state = data if isinstance(data, dict) else {}
        except Exception as e:
            logger.error(f"Failed to load module state: {e}")
            self._state = {}

    def _save_state(self):
        with self._state_lock:
            try:
                os.makedirs(os.path.dirname(MODULES_STATE_FILE), exist_ok=True)
                tmp = MODULES_STATE_FILE + '.tmp'
                with open(tmp, 'w') as f:
                    json.dump(self._state, f, indent=2)
                os.replace(tmp, MODULES_STATE_FILE)
            except Exception as e:
                logger.error(f"Failed to save module state: {e}")

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def _discover_modules(self):
        """Scan app/modules/ for addon modules with a module.json manifest."""
        if not os.path.isdir(MODULES_DIR):
            os.makedirs(MODULES_DIR, exist_ok=True)
            return

        for entry in sorted(os.scandir(MODULES_DIR), key=lambda e: e.name):
            if not entry.is_dir() or entry.name.startswith(('_', '.')):
                continue

            manifest_path = os.path.join(entry.path, 'module.json')
            if not os.path.exists(manifest_path):
                continue

            module_id = entry.name
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)

                module_id = manifest.get('id')
                if not module_id:
                    self.load_errors[entry.name] = "module.json has no 'id'"
                    logger.warning(f"Module in {entry.name} has no 'id' in manifest, skipping")
                    continue
                if module_id in self.module_manifests:
                    self.load_errors[entry.name] = f"Duplicate module id '{module_id}'"
                    continue

                entry_point = manifest.get('entry_point', '')
                if not entry_point or '.' not in entry_point:
                    raise ValueError("module.json needs an entry_point like 'file_name.ClassName'")

                module_file, class_name = entry_point.rsplit('.', 1)
                mod = importlib.import_module(f'.modules.{entry.name}.{module_file}', package=__package__ or 'app')
                cls = getattr(mod, class_name)
                instance = cls(manifest, self)

                self.module_manifests[module_id] = manifest
                self.modules[module_id] = instance

                with self._state_lock:
                    if module_id not in self._state:
                        self._state[module_id] = {
                            'license_key': None,
                            'trial_started': None,
                            'trial_days': manifest.get('trial_days', 14),
                            'status': 'inactive',
                            'enabled': True,
                        }
                        self._save_state()

                logger.info(f"Discovered module: {manifest.get('name', module_id)} v{manifest.get('version', '?')}")

            except Exception as e:
                import traceback
                self.load_errors[module_id] = f"{type(e).__name__}: {e}"
                logger.error(f"Failed to load module from {entry.name}: {e}")
                print(f"  [Addons] Failed to load '{entry.name}': {e}")
                traceback.print_exc()

    # ------------------------------------------------------------------
    # License / Trial API
    # ------------------------------------------------------------------

    def get_module_status(self, module_id):
        """Return computed status: 'active', 'trial', 'expired', or 'inactive'."""
        with self._state_lock:
            state = self._state.get(module_id)
            if not state:
                return 'inactive'
            raw_status = state.get('status', 'inactive')

            if raw_status == 'active':
                # Re-validate on every check so a hand-edited modules.json can't
                # unlock an addon, and a copied install fails the machine binding.
                ltype = state.get('license_type')
                if ltype in ('lemonsqueezy', 'offline_token'):
                    if license_store.is_active(DATA_DIR, module_id,
                                               machine_fingerprint(), PUBLIC_KEY_HEX):
                        return 'active'
                else:
                    # Legacy Ed25519 key path.
                    if validate_license_key(module_id, state.get('license_key') or ''):
                        return 'active'
                state['status'] = 'expired' if state.get('trial_started') else 'inactive'
                self._save_state()
                return state['status']

            if raw_status == 'trial':
                if self._trial_expires_at(state) and datetime.now(timezone.utc) < self._trial_expires_at(state):
                    return 'trial'
                state['status'] = 'expired'
                self._save_state()
                return 'expired'

            return raw_status if raw_status in ('inactive', 'expired') else 'inactive'

    @staticmethod
    def _trial_expires_at(state):
        trial_started = state.get('trial_started')
        if not trial_started:
            return None
        try:
            start = datetime.fromisoformat(trial_started)
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            return start + timedelta(days=int(state.get('trial_days', 14)))
        except (ValueError, TypeError):
            return None

    def is_module_active(self, module_id):
        """True if the module is loaded, enabled, and licensed or on a valid trial."""
        if module_id not in self.modules:
            return False
        with self._state_lock:
            if not self._state.get(module_id, {}).get('enabled', True):
                return False
        return self.get_module_status(module_id) in ('active', 'trial')

    def get_trial_remaining(self, module_id):
        with self._state_lock:
            state = dict(self._state.get(module_id, {}))
        if state.get('status') != 'trial':
            return None
        expires = self._trial_expires_at(state)
        if not expires:
            return None
        remaining = expires - datetime.now(timezone.utc)
        if remaining.total_seconds() <= 0:
            return {'days': 0, 'hours': 0, 'expired': True}
        return {'days': remaining.days, 'hours': remaining.seconds // 3600, 'expired': False}

    def activate_trial(self, module_id):
        if module_id not in self.modules:
            return False, "Module not found"

        with self._state_lock:
            state = self._state.get(module_id, {})
            status = self.get_module_status(module_id)
            if status == 'active':
                return False, "Module already activated with a license"
            if status == 'trial':
                return False, "Trial is already active"
            if status == 'expired' or state.get('trial_started'):
                return False, "The trial for this addon has already been used. Please enter a license key."

            manifest = self.module_manifests.get(module_id, {})
            self._state[module_id] = {
                'license_key': None,
                'trial_started': datetime.now(timezone.utc).isoformat(),
                'trial_days': manifest.get('trial_days', 14),
                'status': 'trial',
                'enabled': True
            }
            self._save_state()
        logger.info(f"Trial activated for module '{module_id}'")
        self.sync_lifecycle()
        days = self.module_manifests.get(module_id, {}).get('trial_days', 14)
        return True, f"{days}-day trial activated"

    def activate_license(self, module_id, license_key):
        if module_id not in self.modules:
            return False, "Module not found"
        key = (license_key or '').strip()
        if not key:
            return False, "License key is required"
        fp = machine_fingerprint()

        # 1) Lemon Squeezy online activation (UUID-shaped key).
        if _LS_KEY_RE.match(key):
            return self._activate_lemonsqueezy(module_id, key, fp)

        # 2) Offline machine-bound token (air-gapped): "<MODULEID>.xxxxx".
        if '.' in key and key.split('.', 1)[0].strip().lower() == module_id.lower():
            rec = license_store.save_offline_token(DATA_DIR, module_id, fp, key, PUBLIC_KEY_HEX)
            if not rec:
                return False, "This offline token isn't valid for this addon or this machine."
            self._mark_licensed(module_id, 'offline_token')
            logger.info(f"Offline token accepted for module '{module_id}'")
            self.sync_lifecycle()
            return True, "License activated (offline token)"

        # 3) Legacy Ed25519 key.
        if validate_license_key(module_id, key):
            self._mark_licensed(module_id, 'legacy', license_key=key.upper())
            logger.info(f"Legacy license activated for module '{module_id}'")
            self.sync_lifecycle()
            return True, "License activated successfully"

        return False, "Invalid license key"

    def _activate_lemonsqueezy(self, module_id, key, fp):
        try:
            resp = ls_client.activate(key, f"{module_id}@{fp}")
        except ls_client.LSError:
            return False, ("Couldn't reach the activation server. Connect to the "
                           "internet once to activate this license.")
        lk = resp.get('license_key') or {}
        if resp.get('error') or not resp.get('activated'):
            err = resp.get('error') or ''
            limit = lk.get('activation_limit')
            used = lk.get('activation_usage', 0)
            if 'activation limit' in err.lower() or (limit and used >= limit):
                return False, ("This key is already activated on another computer. "
                               "Deactivate it there first, then activate here.")
            return False, (err or "Activation failed.")
        # The key must belong to THIS addon, not a different one.
        mapped = ls_client.module_for(resp)
        if mapped and mapped != module_id:
            inst = (resp.get('instance') or {}).get('id')
            if inst:
                try:
                    ls_client.deactivate(key, inst)
                except ls_client.LSError:
                    pass
            return False, f"That key is for a different addon ({mapped.replace('_', ' ')})."
        license_store.save_online_activation(DATA_DIR, module_id, fp, key, resp)
        self._mark_licensed(module_id, 'lemonsqueezy', license_key=key.upper(),
                            instance_id=(resp.get('instance') or {}).get('id'))
        logger.info(f"Lemon Squeezy license activated for module '{module_id}'")
        self.sync_lifecycle()
        return True, "License activated successfully"

    def _mark_licensed(self, module_id, license_type, license_key=None, instance_id=None):
        with self._state_lock:
            prev = self._state.get(module_id, {})
            self._state[module_id] = {
                'license_key': license_key,
                'license_type': license_type,
                'instance_id': instance_id,
                'trial_started': prev.get('trial_started'),
                'trial_days': prev.get('trial_days', 14),
                'status': 'active',
                'enabled': True,
            }
            self._save_state()

    def deactivate_module(self, module_id):
        with self._state_lock:
            if module_id not in self._state:
                return False, "Module not found"
            prev = dict(self._state[module_id])

        # Free the Lemon Squeezy activation slot so the key can move to another
        # PC (best-effort — needs internet; the state is cleared regardless).
        note = ""
        if (prev.get('license_type') == 'lemonsqueezy'
                and prev.get('instance_id') and prev.get('license_key')):
            try:
                ls_client.deactivate(prev['license_key'], prev['instance_id'])
            except ls_client.LSError:
                note = (" — note: couldn't reach the activation server to free the "
                        "online slot; release it from your Lemon Squeezy account if needed")
        license_store.clear(DATA_DIR, module_id)

        with self._state_lock:
            prev = self._state.get(module_id, prev)
            trial_still_valid = (prev.get('trial_started') and self._trial_expires_at(prev)
                                 and datetime.now(timezone.utc) < self._trial_expires_at(prev))
            self._state[module_id] = {
                'license_key': None,
                'license_type': None,
                'instance_id': None,
                'trial_started': prev.get('trial_started'),
                'trial_days': prev.get('trial_days', 14),
                # Removing a license falls back to the remaining trial, if any
                'status': 'trial' if trial_still_valid else ('expired' if prev.get('trial_started') else 'inactive'),
                'enabled': prev.get('enabled', True)
            }
            self._save_state()
        logger.info(f"Module '{module_id}' license removed")
        self.sync_lifecycle()
        return True, "License removed" + note

    def toggle_module(self, module_id):
        with self._state_lock:
            if module_id not in self._state:
                return False, "Module not found"
            current = self._state[module_id].get('enabled', True)
            self._state[module_id]['enabled'] = not current
            self._save_state()
        state_str = "disabled" if current else "enabled"
        logger.info(f"Module '{module_id}' {state_str}")
        self.sync_lifecycle()
        return True, f"Module {state_str} successfully"

    # ------------------------------------------------------------------
    # Lifecycle: start/stop modules as their active state changes
    # ------------------------------------------------------------------

    def _running_cameras(self):
        mgr = self._manager
        if not mgr:
            return []
        return [c for c in getattr(mgr, 'cameras', []) if getattr(c, 'status', '') == 'running']

    def _start_module(self, module_id):
        module = self.modules[module_id]
        try:
            module.on_startup(self._manager)
            logger.info(f"Module '{module_id}' started")
        except Exception as e:
            logger.error(f"Error starting module '{module_id}': {e}")
            print(f"  [Addons] Error starting '{module_id}': {e}")
        self._started.add(module_id)

    def _stop_module(self, module_id):
        module = self.modules[module_id]
        for cam in self._running_cameras():
            try:
                module.on_camera_stop(cam)
            except Exception as e:
                logger.error(f"Error in on_camera_stop for module '{module_id}': {e}")
        try:
            module.on_shutdown(self._manager)
        except Exception as e:
            logger.error(f"Error shutting down module '{module_id}': {e}")
        self._started.discard(module_id)

    def sync_lifecycle(self):
        """Start modules that became active and stop ones that became inactive."""
        if self._manager is None:
            return  # before server startup; on_startup() handles it
        with self._lifecycle_lock:
            for module_id in list(self.modules):
                active = self.is_module_active(module_id)
                if active and module_id not in self._started:
                    self._start_module(module_id)
                    # Cameras already running never got on_camera_start for this module
                    for cam in self._running_cameras():
                        try:
                            self.modules[module_id].on_camera_start(cam)
                        except Exception as e:
                            logger.error(f"Error in on_camera_start for module '{module_id}': {e}")
                elif not active and module_id in self._started:
                    self._stop_module(module_id)
            self._refresh_listeners()

    def _refresh_listeners(self):
        self._frame_listeners = [m for mid, m in self.modules.items()
                                 if mid in self._started and getattr(m, 'wants_frames', False)]

    def _watchdog_loop(self):
        """Stops modules whose trial expires while the server is running."""
        while self._manager is not None:
            time.sleep(60)
            try:
                self.sync_lifecycle()
            except Exception as e:
                logger.error(f"Module watchdog error: {e}")

    # ------------------------------------------------------------------
    # Requirements (optional pip packages per addon)
    # ------------------------------------------------------------------

    def get_requirements_status(self, module_id):
        manifest = self.module_manifests.get(module_id, {})
        reqs = manifest.get('requirements', [])
        out = []
        for req in reqs:
            if isinstance(req, str):
                req = {'pip': req, 'import': None}
            out.append({
                'pip': req.get('pip'),
                'import': req.get('import'),
                'purpose': req.get('purpose', ''),
                'optional': bool(req.get('optional', False)),
                'installed': _requirement_installed(req),
            })
        job = self._install_jobs.get(module_id, {})
        return {'requirements': out, 'install': {k: job.get(k) for k in ('running', 'ok', 'log')} if job else None}

    def install_requirements(self, module_id, packages=None):
        """pip-install missing requirements in a background thread."""
        status = self.get_requirements_status(module_id)
        missing = [r['pip'] for r in status['requirements'] if not r['installed'] and r['pip']]
        if packages:
            missing = [p for p in missing if p in packages]
        if not missing:
            return False, "Nothing to install"
        job = self._install_jobs.get(module_id)
        if job and job.get('running'):
            return False, "An install is already running"

        job = {'running': True, 'ok': None, 'log': f"pip install {' '.join(missing)}\n"}
        self._install_jobs[module_id] = job

        def run():
            try:
                cmd = [sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check'] + missing
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                for line in proc.stdout:
                    job['log'] = (job['log'] + line)[-20000:]
                proc.wait()
                job['ok'] = proc.returncode == 0
                job['log'] += "\nDone." if job['ok'] else f"\nFailed (exit code {proc.returncode})."
                importlib.invalidate_caches()
            except Exception as e:
                job['ok'] = False
                job['log'] += f"\nError: {e}"
            finally:
                job['running'] = False
                if job.get('ok') and module_id in self._started:
                    # Restart the module so it picks up the new packages
                    with self._lifecycle_lock:
                        self._stop_module(module_id)
                    self.sync_lifecycle()

        threading.Thread(target=run, daemon=True, name=f"AddonInstall-{module_id}").start()
        return True, "Installing..."

    # ------------------------------------------------------------------
    # Module information
    # ------------------------------------------------------------------

    def get_all_modules_info(self):
        result = []
        for module_id, manifest in self.module_manifests.items():
            status = self.get_module_status(module_id)
            with self._state_lock:
                state = dict(self._state.get(module_id, {}))
            module = self.modules.get(module_id)
            try:
                has_page = bool(module and module.has_page())
            except Exception:
                has_page = False
            reqs = self.get_requirements_status(module_id)['requirements']
            rec = license_store.load(DATA_DIR, module_id) or {}
            licensee = ''
            if status == 'active':
                licensee = (rec.get('licensee')
                            or (decode_license_key(state.get('license_key')) or {}).get('licensee')
                            or '')
            result.append({
                'id': module_id,
                'name': manifest.get('name', module_id),
                'description': manifest.get('description', ''),
                'version': manifest.get('version', '1.0.0'),
                'icon': manifest.get('icon', 'fas fa-puzzle-piece'),
                'color': manifest.get('color', '#6366f1'),
                'author': manifest.get('author', 'Unknown'),
                'price': manifest.get('price', ''),
                'trial_days': manifest.get('trial_days', 14),
                'status': status,
                'has_license': bool(state.get('license_type') or state.get('license_key')),
                'license_type': state.get('license_type'),
                'machine_code': machine_id.short_code(machine_fingerprint()),
                'licensee': licensee,
                'trial_used': bool(state.get('trial_started')),
                'trial_remaining': self.get_trial_remaining(module_id),
                'enabled': state.get('enabled', True),
                'running': module_id in self._started,
                'has_page': has_page,
                'page_url': f'/addon/{module_id}' if has_page else None,
                'missing_requirements': [r['pip'] for r in reqs if not r['installed'] and not r['optional']],
            })
        for name, err in self.load_errors.items():
            if name not in self.module_manifests:
                result.append({
                    'id': name, 'name': name, 'description': f'Failed to load: {err}',
                    'version': '?', 'icon': 'fas fa-triangle-exclamation', 'color': '#e53e3e',
                    'author': '', 'price': '', 'trial_days': 0, 'status': 'error',
                    'load_error': err, 'enabled': False, 'running': False,
                    'has_license': False, 'license_type': None, 'machine_code': '',
                    'trial_used': False, 'trial_remaining': None,
                    'has_page': False, 'page_url': None, 'missing_requirements': [],
                })
        return result

    def get_module(self, module_id):
        return self.modules.get(module_id)

    # ------------------------------------------------------------------
    # Integration hooks
    # ------------------------------------------------------------------

    def register_all_routes(self, app, manager, login_required):
        """Register the generic addon API plus each module's own routes.

        Routes are registered for every loaded module (active or not) because
        Flask can't add routes after the first request; each route checks
        the module's active state when called.
        """
        self._manager = self._manager or manager
        self._register_generic_routes(app, login_required)
        for module_id, module in self.modules.items():
            try:
                module.register_routes(app, manager, login_required)
            except Exception as e:
                logger.error(f"Error registering routes for module '{module_id}': {e}")
                print(f"  [Addons] Error registering routes for '{module_id}': {e}")

    def _register_generic_routes(self, app, login_required):
        from flask import jsonify, request
        mm = self

        def _module_or_404(module_id, require_active=True):
            module = mm.modules.get(module_id)
            if not module:
                return None, (jsonify({'success': False, 'error': 'Module not found'}), 404)
            if require_active and not mm.is_module_active(module_id):
                return None, (jsonify({'success': False, 'error': f'{module.name} is not active'}), 403)
            return module, None

        def addon_get_config(module_id):
            module, err = _module_or_404(module_id)
            if err:
                return err
            return jsonify(module.public_config())

        def addon_set_config(module_id):
            module, err = _module_or_404(module_id)
            if err:
                return err
            try:
                module.update_config(request.get_json(silent=True) or {})
            except ValueError as e:
                return jsonify({'success': False, 'error': str(e)}), 400
            return jsonify({'success': True, 'config': module.public_config()})

        def addon_get_camera_config(module_id, camera_id):
            module, err = _module_or_404(module_id)
            if err:
                return err
            return jsonify(module.public_camera_config(camera_id))

        def addon_set_camera_config(module_id, camera_id):
            module, err = _module_or_404(module_id)
            if err:
                return err
            if module.get_camera(camera_id) is None and mm._manager is not None:
                return jsonify({'success': False, 'error': 'Camera not found'}), 404
            try:
                module.update_camera_config(camera_id, request.get_json(silent=True) or {})
            except ValueError as e:
                return jsonify({'success': False, 'error': str(e)}), 400
            return jsonify({'success': True, 'config': module.public_camera_config(camera_id)})

        def addon_status(module_id):
            module, err = _module_or_404(module_id)
            if err:
                return err
            try:
                status = module.get_status() or {}
            except Exception as e:
                status = {'Error': str(e)}
            return jsonify({'status': status, 'activity': module.get_activity(30),
                            'running': module_id in mm._started})

        def addon_requirements(module_id):
            module, err = _module_or_404(module_id, require_active=False)
            if err:
                return err
            return jsonify(mm.get_requirements_status(module_id))

        def addon_install_requirements(module_id):
            module, err = _module_or_404(module_id)
            if err:
                return err
            ok, msg = mm.install_requirements(module_id)
            return jsonify({'success': ok, 'message': msg}), 200 if ok else 400

        routes = [
            ('/api/addons/<module_id>/config', addon_get_config, ['GET']),
            ('/api/addons/<module_id>/config', addon_set_config, ['POST']),
            ('/api/addons/<module_id>/cameras/<int:camera_id>/config', addon_get_camera_config, ['GET']),
            ('/api/addons/<module_id>/cameras/<int:camera_id>/config', addon_set_camera_config, ['POST']),
            ('/api/addons/<module_id>/status', addon_status, ['GET']),
            ('/api/addons/<module_id>/requirements', addon_requirements, ['GET']),
            ('/api/addons/<module_id>/requirements/install', addon_install_requirements, ['POST']),
        ]
        for rule, fn, methods in routes:
            endpoint = f"{fn.__name__}_{'_'.join(m.lower() for m in methods)}"
            app.add_url_rule(rule, endpoint, login_required(fn), methods=methods)

    def get_all_nav_items(self):
        """Collect nav items from all modules, tagged with module status."""
        items = []
        for module_id, module in self.modules.items():
            try:
                module_items = module.register_nav_items() or []
                status = self.get_module_status(module_id)
                enabled = self._state.get(module_id, {}).get('enabled', True)
                for item in module_items:
                    item['module_id'] = module_id
                    item['module_status'] = status if enabled else 'disabled'
                items.extend(module_items)
            except Exception as e:
                logger.error(f"Error getting nav items from module '{module_id}': {e}")
        return items

    def get_all_camera_tabs(self):
        tabs = []
        for module_id, module in self.modules.items():
            if not self.is_module_active(module_id):
                continue
            try:
                for tab in module.register_camera_tabs() or []:
                    tab['module_id'] = module_id
                    tabs.append(tab)
            except Exception as e:
                logger.error(f"Error getting camera tabs from module '{module_id}': {e}")
        return tabs

    def get_all_settings_sections(self):
        sections = []
        for module_id, module in self.modules.items():
            if not self.is_module_active(module_id):
                continue
            try:
                for sec in module.register_settings_sections() or []:
                    sec['module_id'] = module_id
                    sections.append(sec)
            except Exception as e:
                logger.error(f"Error getting settings sections from module '{module_id}': {e}")
        return sections

    def _for_active(self, hook, *args):
        for module_id, module in list(self.modules.items()):
            if self.is_module_active(module_id):
                try:
                    getattr(module, hook)(*args)
                except Exception as e:
                    logger.error(f"Error in {hook} for module '{module_id}': {e}")

    def on_camera_save(self, camera, data):
        self._for_active('on_camera_save', camera, data)

    def on_camera_start(self, camera):
        # Before server startup modules aren't running yet; on_startup() replays
        # on_camera_start for every camera that is running by then.
        if self._manager is None:
            return
        for module_id in list(self._started):
            module = self.modules.get(module_id)
            if module is None or not self.is_module_active(module_id):
                continue
            try:
                module.on_camera_start(camera)
            except Exception as e:
                logger.error(f"Error in on_camera_start for module '{module_id}': {e}")

    def on_camera_stop(self, camera):
        # Stop hooks go to every started module so nothing is left running
        for module_id in list(self._started) or [m for m in self.modules if self.is_module_active(m)]:
            module = self.modules.get(module_id)
            if not module:
                continue
            try:
                module.on_camera_stop(camera)
            except Exception as e:
                logger.error(f"Error in on_camera_stop for module '{module_id}': {e}")

    def on_camera_delete(self, camera_id):
        self._for_active('on_camera_delete', camera_id)

    # ---- AI event bus -------------------------------------------------

    def dispatch_ai_event(self, camera, event):
        """Called from Camera._trigger_ai_motion on every AI state change."""
        for module_id in list(self._started):
            module = self.modules.get(module_id)
            try:
                module.on_ai_event(camera, event)
            except Exception as e:
                logger.error(f"Error in on_ai_event for module '{module_id}': {e}")

    def has_frame_listeners(self):
        return bool(self._frame_listeners)

    def dispatch_ai_frame(self, camera, frame, detections, license_plate=None):
        """Called from the camera AI loop after each YOLO inference."""
        for module in list(self._frame_listeners):
            try:
                module.on_ai_frame(camera, frame, detections, license_plate)
            except Exception as e:
                logger.error(f"Error in on_ai_frame for module '{module.module_id}': {e}")

    def dispatch_addon_event(self, source_module_id, camera, event_type, payload):
        for module_id in list(self._started):
            if module_id == source_module_id:
                continue
            try:
                self.modules[module_id].on_addon_event(source_module_id, camera, event_type, payload)
            except Exception as e:
                logger.error(f"Error in on_addon_event for module '{module_id}': {e}")

    # ---- Application lifecycle -----------------------------------------

    def on_startup(self, manager):
        """Called during server startup — start every active module."""
        self._manager = manager
        with self._lifecycle_lock:
            for module_id in list(self.modules):
                if self.is_module_active(module_id) and module_id not in self._started:
                    self._start_module(module_id)
                    for cam in self._running_cameras():
                        try:
                            self.modules[module_id].on_camera_start(cam)
                        except Exception as e:
                            logger.error(f"Error in on_camera_start for module '{module_id}': {e}")
            self._refresh_listeners()
        if self._watchdog is None:
            self._watchdog = threading.Thread(target=self._watchdog_loop, daemon=True, name="AddonWatchdog")
            self._watchdog.start()

    def on_shutdown(self, manager):
        """Called during server shutdown — stop every started module."""
        with self._lifecycle_lock:
            for module_id in list(self._started):
                try:
                    self.modules[module_id].on_shutdown(manager)
                except Exception as e:
                    logger.error(f"Error shutting down module '{module_id}': {e}")
            self._started.clear()
            self._frame_listeners = []
        self._manager = None
