"""
protect_listener.py — UniFi Protect ONVIF Event Listener health & installer.

The "Send Smart ONVIF Topics" feature depends on danielwoz's onvif-recorder
service running ON the UniFi NVR. UniFi Protect firmware updates wipe that
(unmanaged) package, silently breaking smart detections. This module:

  - Stores one or more NVR SSH targets (host/port/user + encrypted password).
  - Periodically SSHes in and checks `systemctl is-active onvif-recorder`.
  - Notifies the user (via the NotificationManager) when a listener goes down.
  - Can (re)install the listener remotely by running the upstream installer:
        curl -fsSL https://danielwoz.github.io/ubiquiti-protect-onvif-event-listener/install.sh | sh

SSH host keys are auto-accepted (trust-on-first-use) per the product decision;
the fetched fingerprint is surfaced to the UI for transparency.
"""

import time
import uuid
import threading
import logging

from .secrets_manager import secrets_manager

logger = logging.getLogger(__name__)

try:
    import paramiko
    _HAS_PARAMIKO = True
except ImportError:
    _HAS_PARAMIKO = False

INSTALL_CMD = (
    "curl -fsSL "
    "https://danielwoz.github.io/ubiquiti-protect-onvif-event-listener/install.sh "
    "| sh"
)
SERVICE_NAME = "onvif-recorder"

# Single command that reports both service state and whether the binary exists,
# so we can tell "installed but stopped" apart from "not installed at all".
STATUS_CMD = (
    "A=$(systemctl is-active %s 2>/dev/null); "
    "if [ -x /usr/bin/%s ] || command -v %s >/dev/null 2>&1; then B=INSTALLED; "
    "else B=MISSING; fi; "
    'echo "STATUS=${A:-unknown} BIN=$B"'
) % (SERVICE_NAME, SERVICE_NAME, SERVICE_NAME)

MIN_INTERVAL_MINUTES = 5
DEFAULT_INTERVAL_MINUTES = 30


class ProtectListenerManager:
    """Manages multiple UniFi NVR SSH targets and the onvif-recorder lifecycle."""

    def __init__(self, manager, config=None):
        self.manager = manager  # CameraManager — for save_config() + notifier
        self._lock = threading.Lock()

        cfg = config or {}
        self.monitor_enabled = cfg.get("monitorEnabled", True)
        self.monitor_interval_minutes = max(
            MIN_INTERVAL_MINUTES,
            int(cfg.get("monitorIntervalMinutes", DEFAULT_INTERVAL_MINUTES)),
        )
        self.nvrs = cfg.get("nvrs", [])  # list of dicts (passwords stored encrypted)

        # Runtime-only (not persisted)
        self._status = {}        # nvr_id -> {status, detail, fingerprint, checkedAt}
        self._last_up = {}       # nvr_id -> bool|None, for edge-triggered alerts
        self._install_jobs = {}  # nvr_id -> {status, log, lock}

        self._monitor_thread = None
        self._monitor_running = False

    # ── Persistence ───────────────────────────────────────────────────────────
    def to_config(self) -> dict:
        """Serialisable form persisted inside camera_config.json."""
        with self._lock:
            return {
                "monitorEnabled": self.monitor_enabled,
                "monitorIntervalMinutes": self.monitor_interval_minutes,
                "nvrs": [dict(n) for n in self.nvrs],
            }

    def _persist(self):
        try:
            self.manager.save_config()
        except Exception as e:
            logger.error(f"[ProtectListener] Failed to persist config: {e}")

    def get_public_state(self) -> dict:
        """Config for the web UI: passwords redacted, runtime status merged in."""
        with self._lock:
            nvrs = []
            for n in self.nvrs:
                st = self._status.get(n["id"], {})
                nvrs.append({
                    "id": n["id"],
                    "name": n.get("name", ""),
                    "sshHost": n.get("sshHost", ""),
                    "sshPort": n.get("sshPort", 22),
                    "sshUser": n.get("sshUser", "root"),
                    "intervalMinutes": int(n.get("intervalMinutes") or self.monitor_interval_minutes),
                    "passwordSet": bool(n.get("sshPasswordEnc")),
                    "status": st.get("status", "unknown"),
                    "detail": st.get("detail", ""),
                    "fingerprint": st.get("fingerprint", ""),
                    "checkedAt": st.get("checkedAt", 0),
                })
            return {
                "monitorEnabled": self.monitor_enabled,
                "monitorIntervalMinutes": self.monitor_interval_minutes,
                "cryptoAvailable": secrets_manager.available,
                "sshAvailable": _HAS_PARAMIKO,
                "nvrs": nvrs,
            }

    # ── CRUD ────────────────────────────────────────────────────────────────────
    def _find(self, nvr_id):
        for n in self.nvrs:
            if n["id"] == nvr_id:
                return n
        return None

    def add_nvr(self, data: dict) -> dict:
        nvr = {
            "id": uuid.uuid4().hex,
            "name": (data.get("name") or "").strip() or "UniFi NVR",
            "sshHost": (data.get("sshHost") or "").strip(),
            "sshPort": int(data.get("sshPort") or 22),
            "sshUser": (data.get("sshUser") or "root").strip(),
            "intervalMinutes": max(MIN_INTERVAL_MINUTES, int(data.get("intervalMinutes") or DEFAULT_INTERVAL_MINUTES)),
            "sshPasswordEnc": "",
        }
        pw = data.get("sshPassword")
        if pw:
            nvr["sshPasswordEnc"] = secrets_manager.encrypt(pw)
        with self._lock:
            self.nvrs.append(nvr)
        self._persist()
        return nvr

    def update_nvr(self, nvr_id: str, data: dict) -> bool:
        with self._lock:
            nvr = self._find(nvr_id)
            if not nvr:
                return False
            if "name" in data:
                nvr["name"] = (data.get("name") or "").strip() or nvr["name"]
            if "sshHost" in data:
                nvr["sshHost"] = (data.get("sshHost") or "").strip()
            if "sshPort" in data:
                nvr["sshPort"] = int(data.get("sshPort") or 22)
            if "sshUser" in data:
                nvr["sshUser"] = (data.get("sshUser") or "root").strip()
            if "intervalMinutes" in data:
                nvr["intervalMinutes"] = max(
                    MIN_INTERVAL_MINUTES, int(data.get("intervalMinutes") or DEFAULT_INTERVAL_MINUTES)
                )
            # Only replace the password when a new non-empty one is supplied.
            pw = data.get("sshPassword")
            if pw:
                nvr["sshPasswordEnc"] = secrets_manager.encrypt(pw)
        self._persist()
        return True

    def delete_nvr(self, nvr_id: str) -> bool:
        with self._lock:
            before = len(self.nvrs)
            self.nvrs = [n for n in self.nvrs if n["id"] != nvr_id]
            self._status.pop(nvr_id, None)
            self._last_up.pop(nvr_id, None)
            self._install_jobs.pop(nvr_id, None)
            changed = len(self.nvrs) != before
        if changed:
            self._persist()
        return changed

    def update_monitor_settings(self, enabled=None, interval_minutes=None):
        with self._lock:
            if enabled is not None:
                self.monitor_enabled = bool(enabled)
            if interval_minutes is not None:
                self.monitor_interval_minutes = max(
                    MIN_INTERVAL_MINUTES, int(interval_minutes)
                )
        self._persist()
        # Restart the monitor loop so the new cadence/enabled state takes effect.
        self.restart_monitor()

    # ── SSH primitives ──────────────────────────────────────────────────────────
    def _connect(self, nvr: dict, timeout=10):
        """Open an SSH client to the NVR (trust-on-first-use). Caller closes."""
        if not _HAS_PARAMIKO:
            raise RuntimeError(
                "The 'paramiko' package is not installed. "
                "Install it with: pip install paramiko"
            )
        host = nvr.get("sshHost")
        if not host:
            raise ValueError("SSH host is not set for this NVR.")
        password = secrets_manager.decrypt(nvr.get("sshPasswordEnc", ""))
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=host,
            port=int(nvr.get("sshPort") or 22),
            username=nvr.get("sshUser") or "root",
            password=password,
            timeout=timeout,
            allow_agent=False,
            look_for_keys=False,
        )
        return client

    @staticmethod
    def _fingerprint(client) -> str:
        try:
            import hashlib
            key = client.get_transport().get_remote_server_key()
            digest = hashlib.sha256(key.asbytes()).hexdigest()
            pairs = [digest[i:i + 2] for i in range(0, len(digest), 2)]
            return key.get_name() + " SHA256:" + ":".join(pairs[:16])
        except Exception:
            return ""

    def test_connection(self, nvr_id: str) -> dict:
        nvr = self._find(nvr_id)
        if not nvr:
            return {"ok": False, "error": "NVR not found"}
        client = None
        try:
            client = self._connect(nvr)
            fingerprint = self._fingerprint(client)
            stdin, stdout, stderr = client.exec_command("echo ok", timeout=10)
            out = stdout.read().decode("utf-8", "replace").strip()
            return {
                "ok": out == "ok",
                "fingerprint": fingerprint,
                "error": "" if out == "ok" else "Unexpected response",
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
        finally:
            if client:
                try:
                    client.close()
                except Exception:
                    pass

    def reboot(self, nvr_id: str) -> dict:
        """Reboot the Ubiquiti NVR over SSH. The reboot is deferred a couple of
        seconds so this command returns cleanly before the connection drops."""
        nvr = self._find(nvr_id)
        if not nvr:
            return {"ok": False, "error": "NVR not found"}
        client = None
        try:
            client = self._connect(nvr, timeout=10)
            client.exec_command(
                "nohup sh -c 'sleep 2; reboot' >/dev/null 2>&1 &", timeout=10
            )
            # Mark status unknown — it will be offline shortly.
            with self._lock:
                self._status[nvr_id] = {
                    "status": "unknown",
                    "detail": "Reboot requested",
                    "fingerprint": self._status.get(nvr_id, {}).get("fingerprint", ""),
                    "checkedAt": time.time(),
                }
                self._last_up[nvr_id] = None  # don't fire a "down" alert for a reboot
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}
        finally:
            if client:
                try:
                    client.close()
                except Exception:
                    pass

    def check_status(self, nvr_id: str) -> dict:
        """Returns {status, detail, fingerprint, checkedAt}. status ∈
        active | stopped | not_installed | ssh_error | unknown."""
        nvr = self._find(nvr_id)
        if not nvr:
            return {"status": "unknown", "detail": "NVR not found", "checkedAt": time.time()}

        result = {"status": "unknown", "detail": "", "fingerprint": "", "checkedAt": time.time()}
        client = None
        try:
            client = self._connect(nvr)
            result["fingerprint"] = self._fingerprint(client)
            stdin, stdout, stderr = client.exec_command(STATUS_CMD, timeout=15)
            out = stdout.read().decode("utf-8", "replace").strip()
            # Expected: "STATUS=<active|inactive|failed|unknown> BIN=<INSTALLED|MISSING>"
            svc, binstate = "unknown", "MISSING"
            for tok in out.split():
                if tok.startswith("STATUS="):
                    svc = tok.split("=", 1)[1]
                elif tok.startswith("BIN="):
                    binstate = tok.split("=", 1)[1]
            if binstate == "MISSING":
                result["status"] = "not_installed"
                result["detail"] = "onvif-recorder is not installed"
            elif svc == "active":
                result["status"] = "active"
                result["detail"] = "Service is active"
            else:
                result["status"] = "stopped"
                result["detail"] = f"Service is {svc}"
        except Exception as e:
            result["status"] = "ssh_error"
            result["detail"] = str(e)
        finally:
            if client:
                try:
                    client.close()
                except Exception:
                    pass

        with self._lock:
            self._status[nvr_id] = result
        self._evaluate_alert(nvr, result)
        return result

    def _evaluate_alert(self, nvr: dict, result: dict):
        """Edge-triggered: notify only when an NVR transitions into a down state."""
        nvr_id = nvr["id"]
        is_up = result["status"] == "active"
        prev = self._last_up.get(nvr_id)  # True | False | None (first check)
        self._last_up[nvr_id] = is_up

        # Notify on first-seen-down or any up->down transition. Skip ssh_error to
        # avoid alerting on transient network blips / wrong creds noise.
        if not is_up and result["status"] != "ssh_error" and prev in (True, None):
            try:
                name = nvr.get("name", "NVR")
                host = nvr.get("sshHost", "")
                self.manager.notifier.send(
                    "onvif_listener_down",
                    "Ubiquiti Protect NVR - ONVIF Listener Project Offline",
                    f'The onvif-recorder service is not running on "{name}" ({host}). '
                    f"Detail: {result.get('detail', '')}.",
                )
            except Exception as e:
                logger.warning(f"[ProtectListener] Notify failed: {e}")

    def check_all(self) -> dict:
        out = {}
        with self._lock:
            ids = [n["id"] for n in self.nvrs]
        for nvr_id in ids:
            out[nvr_id] = self.check_status(nvr_id)
        return out

    # ── Remote install (streaming, keyed per NVR) ────────────────────────────────
    def start_install(self, nvr_id: str) -> bool:
        nvr = self._find(nvr_id)
        if not nvr:
            return False
        with self._lock:
            job = self._install_jobs.get(nvr_id)
            if job and job["status"] == "installing":
                return False
            self._install_jobs[nvr_id] = {
                "status": "installing",
                "log": ["Connecting to NVR..."],
                "lock": threading.Lock(),
            }
        threading.Thread(target=self._run_install, args=(nvr_id,), daemon=True).start()
        return True

    def _append_log(self, nvr_id: str, line: str):
        job = self._install_jobs.get(nvr_id)
        if not job:
            return
        with job["lock"]:
            job["log"].append(line)
            if len(job["log"]) > 1000:
                job["log"].pop(0)

    def _run_install(self, nvr_id: str):
        nvr = self._find(nvr_id)
        client = None
        try:
            client = self._connect(nvr, timeout=15)
            self._append_log(nvr_id, "Connected. Running installer (this can take a few minutes)...")
            self._append_log(nvr_id, f"$ {INSTALL_CMD}")
            stdin, stdout, stderr = client.exec_command(INSTALL_CMD, timeout=None, get_pty=True)
            channel = stdout.channel
            channel.set_combine_stderr(True)
            for line in iter(stdout.readline, ""):
                if line:
                    self._append_log(nvr_id, line.rstrip("\n"))
            exit_code = channel.recv_exit_status()
            if exit_code == 0:
                self._append_log(nvr_id, "Installer finished successfully.")
                with self._install_jobs[nvr_id]["lock"]:
                    self._install_jobs[nvr_id]["status"] = "success"
            else:
                self._append_log(nvr_id, f"Installer exited with code {exit_code}.")
                with self._install_jobs[nvr_id]["lock"]:
                    self._install_jobs[nvr_id]["status"] = "failed"
        except Exception as e:
            self._append_log(nvr_id, f"Install error: {e}")
            job = self._install_jobs.get(nvr_id)
            if job:
                with job["lock"]:
                    job["status"] = "failed"
        finally:
            if client:
                try:
                    client.close()
                except Exception:
                    pass
            # Re-check status shortly after install completes.
            try:
                self.check_status(nvr_id)
            except Exception:
                pass

    def start_uninstall(self, nvr_id: str, purge: bool = False) -> bool:
        nvr = self._find(nvr_id)
        if not nvr:
            return False
        with self._lock:
            job = self._install_jobs.get(nvr_id)
            if job and job["status"] == "installing":
                return False
            self._install_jobs[nvr_id] = {
                "status": "installing",
                "log": ["Connecting to NVR..."],
                "lock": threading.Lock(),
            }
        threading.Thread(target=self._run_uninstall, args=(nvr_id, purge), daemon=True).start()
        return True

    def _run_uninstall(self, nvr_id: str, purge: bool = False):
        nvr = self._find(nvr_id)
        # purge also removes /etc/onvif-recorder and state; remove only stops the
        # service and rolls back the UniFi Protect DB changes. -y for non-interactive.
        cmd = (
            "apt-get purge -y onvif-recorder" if purge
            else "apt-get remove -y onvif-recorder"
        )
        client = None
        try:
            client = self._connect(nvr, timeout=15)
            self._append_log(nvr_id, "Connected. Running uninstaller...")
            self._append_log(nvr_id, f"$ {cmd}")
            stdin, stdout, stderr = client.exec_command(cmd, timeout=None, get_pty=True)
            channel = stdout.channel
            channel.set_combine_stderr(True)
            for line in iter(stdout.readline, ""):
                if line:
                    self._append_log(nvr_id, line.rstrip("\n"))
            exit_code = channel.recv_exit_status()
            if exit_code == 0:
                self._append_log(nvr_id, "Uninstall finished successfully.")
                with self._install_jobs[nvr_id]["lock"]:
                    self._install_jobs[nvr_id]["status"] = "success"
            else:
                self._append_log(nvr_id, f"Uninstaller exited with code {exit_code}.")
                with self._install_jobs[nvr_id]["lock"]:
                    self._install_jobs[nvr_id]["status"] = "failed"
        except Exception as e:
            self._append_log(nvr_id, f"Uninstall error: {e}")
            job = self._install_jobs.get(nvr_id)
            if job:
                with job["lock"]:
                    job["status"] = "failed"
        finally:
            if client:
                try:
                    client.close()
                except Exception:
                    pass
            # Re-check status shortly after uninstall completes.
            try:
                self.check_status(nvr_id)
            except Exception:
                pass

    def get_install_progress(self, nvr_id: str) -> dict:
        job = self._install_jobs.get(nvr_id)
        if not job:
            return {"status": "idle", "log": []}
        with job["lock"]:
            return {"status": job["status"], "log": list(job["log"])}

    # ── Monitor loop ──────────────────────────────────────────────────────────
    def start_monitor(self):
        if self._monitor_running:
            return
        if not self.monitor_enabled:
            return
        self._monitor_running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("[ProtectListener] Monitor started.")

    def stop_monitor(self):
        self._monitor_running = False
        self._monitor_thread = None

    def restart_monitor(self):
        self.stop_monitor()
        # Brief pause so the old loop notices the flag before a new one starts.
        time.sleep(0.1)
        self.start_monitor()

    def _monitor_loop(self):
        # Small initial delay so startup isn't blocked by SSH round-trips.
        time.sleep(15)
        # Each NVR is checked on its own cadence (intervalMinutes). The loop wakes
        # on a short base tick and checks whichever NVRs are due.
        base_tick = 30
        next_check = {}  # nvr_id -> epoch seconds when it's next due
        while self._monitor_running:
            if not self.monitor_enabled:
                break
            now = time.time()
            with self._lock:
                nvrs = [dict(n) for n in self.nvrs]
            valid_ids = set()
            for n in nvrs:
                nid = n["id"]
                valid_ids.add(nid)
                interval = max(
                    MIN_INTERVAL_MINUTES,
                    int(n.get("intervalMinutes") or self.monitor_interval_minutes),
                ) * 60
                if now >= next_check.get(nid, 0):
                    try:
                        self.check_status(nid)
                    except Exception as e:
                        logger.warning(f"[ProtectListener] Monitor check failed for {nid}: {e}")
                    next_check[nid] = now + interval
            # Forget schedules for NVRs that were removed.
            for stale in [k for k in next_check if k not in valid_ids]:
                next_check.pop(stale, None)
            # Sleep the base tick in short slices so enable/disable stays responsive.
            waited = 0
            while waited < base_tick and self._monitor_running and self.monitor_enabled:
                time.sleep(2)
                waited += 2
        self._monitor_running = False
