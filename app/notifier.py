"""
notifier.py — System Notifications Engine
Supports: Pushover, ntfy, Gotify, Bark, Apprise, SMTP Email
Handles: per-camera AI cooldowns, schedule windows, and event filtering
"""

import threading
import smtplib
import time
import logging
from datetime import datetime, time as dtime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from concurrent.futures import ThreadPoolExecutor

try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# All known notification event keys and their human-readable labels
# ─────────────────────────────────────────────────────────────────────────────
NOTIFICATION_EVENTS = {
    'server_started':           'Server Started',
    'server_stopping':          'Server Stopping',
    'server_restarted':         'Server Restarted',
    'server_rebooted':          'System Rebooted',
    'cameras_all_started':      'All Cameras Started',
    'cameras_all_stopped':      'All Cameras Stopped',
    'camera_started':           'Camera Started',
    'camera_stopped':           'Camera Stopped',
    'camera_stream_error':      'Camera Stream Error',
    'camera_stream_recovered':  'Camera Stream Recovered',
    'ai_detection':             'AI Object Detection',
    'update_available':         'New Version Available',
    'config_restored':          'Configuration Restored',
    'mediamtx_restarted':       'MediaMTX Restarted',
    'watchdog_triggered':       'Watchdog Auto-Recovery',
}

# Default events that are enabled out of the box
DEFAULT_ENABLED_EVENTS = [
    'server_started',
    'server_stopping',
    'camera_stream_error',
    'update_available',
]


class NotificationManager:
    """
    Central dispatcher for all system notifications.
    Thread-safe. All sends are non-blocking (dispatched via thread pool).
    """

    def __init__(self, config: dict = None):
        self._config = config or {}
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix='Notifier')
        # Per-camera per-label cooldown tracking: {(camera_id, label): last_sent_timestamp}
        self._ai_cooldown_map: dict = {}

    # ─────────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────────

    def update_config(self, config: dict):
        """Hot-reload config without restart."""
        with self._lock:
            self._config = config

    def get_config(self) -> dict:
        with self._lock:
            return dict(self._config)

    def send(self, event_key: str, title: str, message: str, camera_id: int = None):
        """
        Fire a notification for the given event key.
        Checks whether the event is enabled before dispatching.
        Non-blocking — dispatches to thread pool.
        """
        with self._lock:
            cfg = dict(self._config)

        enabled_events = cfg.get('enabled_events', DEFAULT_ENABLED_EVENTS)
        if event_key not in enabled_events:
            return

        self._executor.submit(self._dispatch, cfg, title, message)

    def send_ai_detection(self, camera_id: int, camera_name: str, detected_labels: list,
                          camera_notify_cfg: dict = None, image_bytes: bytes = None, is_test: bool = False,
                          license_plate: str = None):
        """
        Fire an AI detection notification, subject to:
        - Global 'ai_detection' event being enabled
        - Per-camera notify_ai_enabled flag
        - Per-camera label filter (notifyAiTargets)
        - Per-camera cooldown (notifyAiCooldown seconds)
        - Per-camera schedule window
        """
        with self._lock:
            cfg = dict(self._config)

        if not is_test:
            enabled_events = cfg.get('enabled_events', DEFAULT_ENABLED_EVENTS)
            if 'ai_detection' not in enabled_events:
                return

            if not camera_notify_cfg:
                return

            if not camera_notify_cfg.get('notifyAiEnabled', False):
                return

            # Wildcard matching helper for plates
            import fnmatch
            def matches_plate_filter(plate: str, filter_str: str) -> bool:
                if not filter_str or not filter_str.strip():
                    return True
                if not plate:
                    return False
                patterns = [p.strip().lower() for p in filter_str.split(',') if p.strip()]
                if not patterns:
                    return True
                plate_lower = plate.lower()
                for pattern in patterns:
                    if '*' in pattern or '?' in pattern:
                        if fnmatch.fnmatch(plate_lower, pattern):
                            return True
                    elif pattern == plate_lower:
                        return True
                return False

            # Filter detected labels (against active schedules if enabled, otherwise fallback to camera-wide targets)
            schedules = camera_notify_cfg.get('notifyAiSchedules', [])
            active_schedules = [s for s in schedules if s.get('enabled', True)]
            
            if active_schedules:
                # Find schedules that currently cover the active time
                current_active_schedules = [s for s in active_schedules if self._check_schedule_entry(s)]
                if not current_active_schedules:
                    # Schedules exist but none match the current time -> block
                    return
                
                # Check if detected labels are allowed in any of the currently active schedules
                matched = []
                for s in current_active_schedules:
                    allowed_targets = s.get('targets')
                    if allowed_targets is None:
                        # Fallback to overall camera targets if not defined per schedule (migration/backward compatibility)
                        allowed_targets = camera_notify_cfg.get('notifyAiTargets', [])
                    
                    s_matched = []
                    for lbl in detected_labels:
                        if lbl.lower() in [t.lower() for t in allowed_targets]:
                            if lbl.lower() == 'license_plate':
                                s_plate_filter = s.get('licensePlates', '')
                                if matches_plate_filter(license_plate, s_plate_filter):
                                    s_matched.append(lbl)
                            else:
                                s_matched.append(lbl)
                    matched.extend(s_matched)
                
                if not matched:
                    return
            else:
                # No enabled schedules exist -> check legacy schedule or fallback to camera-wide targets
                if camera_notify_cfg.get('notifyScheduleEnabled', False) and not self._check_schedule(camera_notify_cfg):
                    return
                
                notify_targets = camera_notify_cfg.get('notifyAiTargets', [])
                matched = []
                for lbl in detected_labels:
                    if lbl.lower() in [t.lower() for t in notify_targets]:
                        if lbl.lower() == 'license_plate':
                            camera_plate_filter = camera_notify_cfg.get('notifyAiLicensePlates', '')
                            if matches_plate_filter(license_plate, camera_plate_filter):
                                matched.append(lbl)
                        else:
                            matched.append(lbl)
                if not matched:
                    return

            # Check cooldown — one cooldown per (camera_id, matched_label_set key)
            cooldown = int(camera_notify_cfg.get('notifyAiCooldown', 60))
            cooldown_key = (camera_id, frozenset(m.lower() for m in matched))
            now = time.time()
            with self._lock:
                last_sent = self._ai_cooldown_map.get(cooldown_key, 0)
                if now - last_sent < cooldown:
                    return
                self._ai_cooldown_map[cooldown_key] = now
            matched_labels = matched
        else:
            matched_labels = detected_labels

        capitalized = []
        for m in matched_labels:
            if m.lower() == 'license_plate':
                if license_plate:
                    capitalized.append(f'License Plate ({license_plate.upper()})')
                else:
                    capitalized.append('License Plate')
            else:
                capitalized.append(m.capitalize())
        label_str = ', '.join(sorted(set(capitalized)))
        title = f'{"[TEST] " if is_test else ""}AI Detection — {camera_name}'
        message = f'{"[TEST] " if is_test else ""}Detected: {label_str} on camera "{camera_name}"'
        self._executor.submit(self._dispatch, cfg, title, message, image_bytes)

    def test(self, provider: str = None) -> dict:
        """
        Send a test notification synchronously (for API response).
        Returns {provider: 'ok'|'error: ...'} for each provider tested.
        """
        with self._lock:
            cfg = dict(self._config)

        results = {}
        providers_cfg = cfg.get('providers', {})
        title = '🔔 Test Notification'
        message = 'Your Tonys ONVIF Server notification system is working correctly!'

        targets = [provider] if provider else list(providers_cfg.keys())
        for pname in targets:
            pcfg = providers_cfg.get(pname, {})
            if not pcfg:
                results[pname] = 'not configured'
                continue
            try:
                self._send_to_provider(pname, pcfg, title, message)
                results[pname] = 'ok'
            except Exception as e:
                results[pname] = f'error: {e}'

        return results

    # ─────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _dispatch(self, cfg: dict, title: str, message: str, image_bytes: bytes = None):
        """Send to all enabled providers (runs in thread pool)."""
        providers_cfg = cfg.get('providers', {})
        for pname, pcfg in providers_cfg.items():
            if not pcfg.get('enabled', False):
                continue
            try:
                self._send_to_provider(pname, pcfg, title, message, image_bytes=image_bytes)
            except Exception as e:
                logger.warning(f'[Notifier] Failed to send via {pname}: {e}')

    def _send_to_provider(self, name: str, pcfg: dict, title: str, message: str, image_bytes: bytes = None):
        dispatch = {
            'pushover': self._send_pushover,
            'ntfy':     self._send_ntfy,
            'gotify':   self._send_gotify,
            'bark':     self._send_bark,
            'apprise':  self._send_apprise,
            'smtp':     self._send_smtp,
        }
        fn = dispatch.get(name)
        if fn:
            fn(pcfg, title, message, image_bytes=image_bytes)
        else:
            raise ValueError(f'Unknown provider: {name}')

    # ── Pushover ──────────────────────────────────────────────────────────────
    def _send_pushover(self, cfg: dict, title: str, message: str, image_bytes: bytes = None):
        if not _HAS_REQUESTS:
            raise RuntimeError('requests library not available')
        token = cfg.get('api_token', '').strip()
        user = cfg.get('user_key', '').strip()
        if not token or not user:
            raise ValueError('Pushover api_token and user_key are required')
        data = {'token': token, 'user': user, 'title': title, 'message': message}
        files = None
        if image_bytes:
            files = {'attachment': ('detection.jpg', image_bytes, 'image/jpeg')}
        resp = _requests.post(
            'https://api.pushover.net/1/messages.json',
            data=data,
            files=files,
            timeout=15
        )
        resp.raise_for_status()

    # ── ntfy ──────────────────────────────────────────────────────────────────
    def _send_ntfy(self, cfg: dict, title: str, message: str, image_bytes: bytes = None):
        if not _HAS_REQUESTS:
            raise RuntimeError('requests library not available')
        server = cfg.get('server_url', 'https://ntfy.sh').rstrip('/')
        topic = cfg.get('topic', '').strip()
        if not topic:
            raise ValueError('ntfy topic is required')
        auth = None
        if cfg.get('username') and cfg.get('password'):
            auth = (cfg['username'], cfg['password'])
        if image_bytes:
            headers = {
                'Title': title,
                'Filename': 'detection.jpg',
                'X-Message': message,
                'Content-Type': 'image/jpeg',
            }
            resp = _requests.post(
                f'{server}/{topic}',
                data=image_bytes,
                headers=headers,
                auth=auth,
                timeout=20
            )
        else:
            headers = {'Title': title, 'Content-Type': 'text/plain'}
            resp = _requests.post(
                f'{server}/{topic}',
                data=message.encode('utf-8'),
                headers=headers,
                auth=auth,
                timeout=10
            )
        resp.raise_for_status()

    # ── Gotify ────────────────────────────────────────────────────────────────
    def _send_gotify(self, cfg: dict, title: str, message: str, image_bytes: bytes = None):
        if not _HAS_REQUESTS:
            raise RuntimeError('requests library not available')
        server = cfg.get('server_url', '').rstrip('/')
        token = cfg.get('app_token', '').strip()
        if not server or not token:
            raise ValueError('Gotify server_url and app_token are required')
        resp = _requests.post(
            f'{server}/message',
            json={'title': title, 'message': message, 'priority': 5},
            headers={'X-Gotify-Key': token},
            timeout=10
        )
        resp.raise_for_status()

    # ── Bark ──────────────────────────────────────────────────────────────────
    def _send_bark(self, cfg: dict, title: str, message: str, image_bytes: bytes = None):
        if not _HAS_REQUESTS:
            raise RuntimeError('requests library not available')
        server_url = cfg.get('server_url', '').rstrip('/')
        if not server_url:
            raise ValueError('Bark server_url (with device key) is required')
        import urllib.parse
        encoded_title = urllib.parse.quote(title)
        encoded_msg = urllib.parse.quote(message)
        resp = _requests.get(
            f'{server_url}/{encoded_title}/{encoded_msg}',
            timeout=10
        )
        resp.raise_for_status()

    # ── Apprise ───────────────────────────────────────────────────────────────
    def _send_apprise(self, cfg: dict, title: str, message: str, image_bytes: bytes = None):
        try:
            import apprise
        except ImportError:
            raise RuntimeError(
                'The "apprise" Python package is not installed. '
                'Install it with: pip install apprise'
            )
        url = cfg.get('apprise_url', '').strip()
        if not url:
            raise ValueError('Apprise URL is required')
        a = apprise.Apprise()
        a.add(url)
        attach = None
        if image_bytes:
            try:
                import tempfile, os
                tmp = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                tmp.write(image_bytes)
                tmp.close()
                attach = apprise.AppriseAttachment(tmp.name)
                result = a.notify(body=message, title=title, attach=attach)
                try:
                    os.unlink(tmp.name)
                except Exception:
                    pass
            except Exception:
                result = a.notify(body=message, title=title)
        else:
            result = a.notify(body=message, title=title)
        if not result:
            raise RuntimeError('Apprise notify() returned False — check the URL and credentials')

    # ── SMTP Email ────────────────────────────────────────────────────────────
    def _send_smtp(self, cfg: dict, title: str, message: str, image_bytes: bytes = None):
        host = cfg.get('host', '').strip()
        port = int(cfg.get('port', 587))
        username = cfg.get('username', '').strip()
        password = cfg.get('password', '').strip()
        from_addr = cfg.get('from_addr', '').strip()
        to_addrs_raw = cfg.get('to_addrs', '').strip()
        use_tls = cfg.get('use_tls', True)

        if not host or not from_addr or not to_addrs_raw:
            raise ValueError('SMTP host, from_addr, and to_addrs are required')

        to_addrs = [a.strip() for a in to_addrs_raw.replace(';', ',').split(',') if a.strip()]

        if image_bytes:
            from email.mime.image import MIMEImage
            from email.mime.base import MIMEBase
            msg = MIMEMultipart('mixed')
        else:
            msg = MIMEMultipart('alternative')
        msg['Subject'] = f'[ONVIF Server] {title}'
        msg['From'] = from_addr
        msg['To'] = ', '.join(to_addrs)

        html_body = f"""<html><body style="font-family:Arial,sans-serif;background:#0d1117;color:#c9d1d9;padding:24px">
<div style="max-width:480px;margin:auto;background:#161b22;border-radius:12px;padding:24px;border:1px solid #30363d">
  <h2 style="color:#58a6ff;margin:0 0 12px">{title}</h2>
  <p style="color:#8b949e;margin:0">{message}</p>
  <hr style="border-color:#30363d;margin:16px 0">
  <small style="color:#484f58">Sent by Tonys ONVIF Server &bull; {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small>
</div>
</body></html>"""

        if image_bytes:
            # Build a multipart/related alternative block with embedded image
            from email.mime.image import MIMEImage
            alt_part = MIMEMultipart('alternative')
            alt_part.attach(MIMEText(message, 'plain'))
            html_with_img = html_body.replace(
                '</div>',
                '<br><img src="cid:detection" style="max-width:100%;border-radius:8px;"></div>'
            )
            related = MIMEMultipart('related')
            related.attach(MIMEText(html_with_img, 'html'))
            img_part = MIMEImage(image_bytes, _subtype='jpeg')
            img_part.add_header('Content-ID', '<detection>')
            img_part.add_header('Content-Disposition', 'inline', filename='detection.jpg')
            related.attach(img_part)
            alt_part.attach(related)
            msg.attach(alt_part)
        else:
            msg.attach(MIMEText(message, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))

        if use_tls:
            server = smtplib.SMTP(host, port, timeout=15)
            server.ehlo()
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(host, port, timeout=15)

        try:
            if username and password:
                server.login(username, password)
            server.sendmail(from_addr, to_addrs, msg.as_string())
        finally:
            server.quit()

    # ── Schedule check ────────────────────────────────────────────────────────
    def _check_schedule_entry(self, entry: dict) -> bool:
        """Return True if now falls within a single schedule entry {days, start, end}."""
        now = datetime.now()
        allowed_days = entry.get('days', list(range(7)))
        if now.weekday() not in allowed_days:
            return False
        start_str = entry.get('start', '00:00')
        end_str = entry.get('end', '23:59')
        try:
            sh, sm = map(int, start_str.split(':'))
            eh, em = map(int, end_str.split(':'))
            start_t = dtime(sh, sm)
            end_t = dtime(eh, em)
            current_t = now.time().replace(second=0, microsecond=0)
            if start_t <= end_t:
                return start_t <= current_t <= end_t
            else:
                return current_t >= start_t or current_t <= end_t
        except Exception:
            return True

    def _check_schedule(self, cam_cfg: dict) -> bool:
        """Legacy single-schedule check. Kept for backward compat."""
        return self._check_schedule_entry({
            'days': cam_cfg.get('notifyScheduleDays', list(range(7))),
            'start': cam_cfg.get('notifyScheduleStart', '00:00'),
            'end': cam_cfg.get('notifyScheduleEnd', '23:59'),
        })

    def shutdown(self):
        """Gracefully shut down the thread pool."""
        self._executor.shutdown(wait=False)
