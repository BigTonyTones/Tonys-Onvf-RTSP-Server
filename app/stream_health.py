"""
Per-camera stream health.

A camera being "running" only means its virtual ONVIF service is up. This
monitor works out whether video is actually flowing from the source, and why
not when it isn't, so the dashboard can show Streaming / Connecting /
Reconnecting / Authentication failed / TLS verification failed / Source
unavailable / Error instead of a single green dot.

Signals, cheapest first:
  1. MediaMTX path API: 'available' + a video track + inbound bytes growing.
     (MediaMTX 1.18 reports 'online: true' even for a failing source, so that
     flag is not used.)
  2. Errors MediaMTX logged for the path (parsed by MediaMTXManager).
  3. For idle on-demand paths, an FFprobe on loopback that must return a
     video stream. Healthy idle paths are re-verified every few minutes.
"""
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import requests

from .config import MEDIAMTX_API_PORT
from . import stream_source as ss

VIDEO_CODECS = {'H264', 'H265', 'AV1', 'VP8', 'VP9', 'MJPEG', 'M-JPEG', 'MPEG-4 VIDEO',
                'MPEG-1/2 VIDEO', 'MPEG-4 Video', 'MPEG-1/2 Video'}

FAILURE_STATES = (ss.STATE_AUTH_FAILED, ss.STATE_TLS_FAILED, ss.STATE_UNAVAILABLE, ss.STATE_ERROR)


class StreamHealthMonitor:
    INTERVAL = 10              # seconds between checks
    START_GRACE = 20           # seconds after a (re)start before reporting failures
    PROBE_INTERVAL = 30        # retry an idle, failing path at most this often
    VERIFIED_TTL = 300         # an idle path verified this recently stays green
    STALL_SECONDS = 15         # ready but no new bytes for this long -> reconnecting
    FALLBACK_AFTER = 2         # consecutive sub failures (with main OK) before fallback

    def __init__(self, manager, api_port=MEDIAMTX_API_PORT, probe=None, fetch_path=None):
        self.manager = manager
        self.api_port = api_port
        self._probe_fn = probe            # injectable for tests
        self._fetch_path_fn = fetch_path  # injectable for tests
        self._paths = {}                  # path -> tracking dict
        self._lock = threading.Lock()
        self._running = False
        self._thread = None
        self._restart_at = time.time()
        self._pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix='health')

    # ---- lifecycle ---------------------------------------------------

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name='stream-health')
        self._thread.start()

    def stop(self):
        self._running = False

    def notify_restart(self):
        """MediaMTX restarted: paths come back from scratch."""
        self._restart_at = time.time()
        with self._lock:
            for t in self._paths.values():
                t['lastBytes'] = None

    def _loop(self):
        time.sleep(5)
        while self._running:
            try:
                self.check_all()
            except Exception as e:
                print(f"  [Health] check failed: {ss.redact_text(str(e))}")
            time.sleep(self.INTERVAL)

    def check_all(self):
        cams = [c for c in list(self.manager.cameras) if c.status == 'running']
        list(self._pool.map(self._safe_check, cams))

    def _safe_check(self, cam):
        try:
            self.check_camera(cam)
        except Exception as e:
            cam.set_health(ss.STATE_ERROR, f"Health check error: {e}")

    # ---- signals -----------------------------------------------------

    def _fetch_path(self, path):
        if self._fetch_path_fn:
            return self._fetch_path_fn(path)
        try:
            r = requests.get(f"http://127.0.0.1:{self.api_port}/v3/paths/get/{path}", timeout=2)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:
                return {}
        except Exception:
            pass
        return None  # API unreachable

    def _probe(self, url, extra_args):
        if self._probe_fn:
            return self._probe_fn(url, extra_args)
        from .ffmpeg_manager import FFmpegManager
        errors = []
        info = FFmpegManager().probe_stream(url, timeout=20, input_args=extra_args, errors=errors)
        return info, (errors[0] if errors else '')

    @staticmethod
    def _video_track(api):
        for t in api.get('tracks2') or []:
            codec = str(t.get('codec', ''))
            if codec in VIDEO_CODECS or codec.upper() in VIDEO_CODECS:
                props = t.get('codecProps') or {}
                return {'codec': codec, 'width': props.get('width'), 'height': props.get('height')}
        for codec in api.get('tracks') or []:
            if str(codec) in VIDEO_CODECS or str(codec).upper() in VIDEO_CODECS:
                return {'codec': str(codec)}
        return None

    def _recent_error(self, path, since=0.0):
        mtx = getattr(self.manager, 'mediamtx', None)
        if not mtx or not hasattr(mtx, 'get_path_event'):
            return ''
        ev = mtx.get_path_event(path)
        if ev.get('error') and ev.get('errorAt', 0) >= max(self._restart_at, since) and \
                time.time() - ev['errorAt'] < 90:
            return ev['error']
        return ''

    # ---- per path ----------------------------------------------------

    def _tracker(self, path):
        with self._lock:
            return self._paths.setdefault(path, {
                'state': ss.STATE_CONNECTING, 'lastVideoAt': 0, 'lastProbeAt': 0,
                'lastBytes': None, 'lastBytesAt': 0, 'failures': 0, 'info': {}, 'message': ''})

    def check_path(self, cam, which):
        """Return a dict {state, message, info, verifiedAt} for cam's main/sub path."""
        path = f"{cam.path_name}_{which}"
        t = self._tracker(path)
        now = time.time()
        in_grace = now - self._restart_at < self.START_GRACE
        was_streaming = t['state'] == ss.STATE_STREAMING

        mtx = getattr(self.manager, 'mediamtx', None)
        if mtx is not None and hasattr(mtx, 'is_running') and not mtx.is_running():
            return self._set(t, ss.STATE_ERROR, "The MediaMTX stream server is not running. "
                             + (mtx.last_start_error or "Check the server log."))

        api = self._fetch_path(path)
        if api is None:
            return self._set(t, ss.STATE_STARTING if in_grace else ss.STATE_ERROR,
                             "" if in_grace else "Cannot reach the MediaMTX API.")
        if api == {}:
            return self._set(t, ss.STATE_STARTING if in_grace else ss.STATE_ERROR,
                             "" if in_grace else "This stream is not configured in MediaMTX yet.")

        available = bool(api.get('available', api.get('ready', False)))
        if available:
            video = self._video_track(api)
            nbytes = api.get('inboundBytes', api.get('bytesReceived', 0)) or 0
            if t['lastBytes'] is None or nbytes > t['lastBytes']:
                t['lastBytesAt'] = now
            t['lastBytes'] = nbytes
            if not video:
                return self._set(t, ss.STATE_ERROR, "The source has no video track (audio only?).")
            if now - t['lastBytesAt'] > self.STALL_SECONDS:
                return self._set(t, ss.STATE_RECONNECTING,
                                 f"No data received from the camera for {int(now - t['lastBytesAt'])}s.")
            t['lastVideoAt'] = now
            t['info'] = video
            return self._set(t, ss.STATE_STREAMING, "")

        t['lastBytes'] = None

        # Not available: either an idle on-demand path or a failing source.
        def logged(since=0.0):
            err = self._recent_error(path, since) or self._recent_error(f"{path}_src", since)
            if not err and which == 'sub' and cam.effective_use_main_as_substream:
                err = self._recent_error(f"{cam.path_name}_main", since)
            return err

        err = logged()
        if in_grace:
            if err:
                return self._failure(t, err, was_streaming)
            return self._set(t, ss.STATE_CONNECTING, "Connecting to the camera...")

        # Idle on-demand path verified recently and nothing failed since -> green.
        if not err and t['lastVideoAt'] and now - t['lastVideoAt'] < self.VERIFIED_TTL:
            return self._set(t, ss.STATE_STREAMING, "")

        if now - t['lastProbeAt'] < self.PROBE_INTERVAL:
            # Not time to re-check yet: report what we know.
            if err:
                return self._failure(t, err, was_streaming)
            return self._snapshot(t)

        # Pull through MediaMTX (exactly what Protect and the dashboard do).
        # A logged error can be stale once the camera is back, so re-probe.
        t['lastProbeAt'] = now
        info, probe_err = self._probe(cam.loopback_url(path, getattr(self.manager, 'rtsp_port', None)), [])
        if info and info.get('width'):
            t['lastVideoAt'] = time.time()
            t['info'] = info
            return self._set(t, ss.STATE_STREAMING, "")

        # Prefer what MediaMTX logged during this probe, then earlier errors.
        err = logged(since=now) or err
        if not err:
            # Publisher paths (transcode / insecure relay) don't tag FFmpeg
            # errors with the path; ask the camera directly when policy allows.
            url, extra = cam.ffmpeg_direct_input(which)
            if url:
                _, direct_err = self._probe(url, extra)
                err = direct_err
        return self._failure(t, err or probe_err or "No video received from the source.", was_streaming)

    def _failure(self, t, err, was_streaming):
        state, hint = ss.classify_source_error(err)
        detail = ss.redact_text(err).strip()
        if len(detail) > 300:
            detail = detail[:300] + '...'
        msg = f"{hint} (Source said: {detail})" if detail else hint
        if was_streaming and state in (ss.STATE_UNAVAILABLE, ss.STATE_ERROR):
            # MediaMTX retries automatically; show it as a reconnect first.
            t['failures'] += 1
            t['state'] = ss.STATE_RECONNECTING
            t['message'] = f"Lost the stream, reconnecting. {msg}"
            return self._snapshot(t)
        t['failures'] += 1
        t['state'] = state
        t['message'] = msg
        return self._snapshot(t)

    def _set(self, t, state, message):
        t['state'] = state
        t['message'] = message
        if state == ss.STATE_STREAMING:
            t['failures'] = 0
        elif state in FAILURE_STATES:
            t['failures'] += 1
        return self._snapshot(t)

    @staticmethod
    def _snapshot(t):
        return {'state': t['state'], 'label': ss.STATE_LABELS.get(t['state'], t['state']),
                'message': t['message'], 'info': dict(t.get('info') or {}),
                'verifiedAt': t['lastVideoAt'], 'failures': t['failures']}

    # ---- per camera --------------------------------------------------

    def check_camera(self, cam):
        main = self.check_path(cam, 'main')
        if getattr(cam, 'disable_substream', False):
            sub = {'state': 'disabled', 'label': 'Disabled', 'message': '', 'info': {}, 'failures': 0}
        else:
            sub = self.check_path(cam, 'sub')

        message = main['message']
        state = main['state']

        if state == ss.STATE_STREAMING and sub['state'] in FAILURE_STATES:
            if (cam.substream_fallback and not cam.effective_use_main_as_substream and
                    sub['failures'] >= self.FALLBACK_AFTER):
                cam.substream_fallback_active = True
                print(f"  [Health] {cam.name}: sub stream failed ({sub['label']}); "
                      f"serving the main stream on the sub profile instead.")
                with self._lock:
                    self._paths.pop(f"{cam.path_name}_sub", None)
                self.manager.restart_mediamtx()
                sub = dict(sub, state=ss.STATE_CONNECTING, label=ss.STATE_LABELS[ss.STATE_CONNECTING],
                           message="Switching the sub profile to the main stream...")
            else:
                message = (f"Main stream OK. Sub stream: {sub['label']}. {sub['message']} "
                           "Enable 'Use Main as Substream' if this camera has no second stream.")
        if cam.substream_fallback_active and state == ss.STATE_STREAMING:
            message = ("Main stream OK. This camera's sub stream is unavailable, so the main "
                       "stream is being served on the sub profile.")

        if cam.is_rtsps and cam.tls_mode == ss.TLS_INSECURE:
            message = (message + " " if message else "") + "WARNING: TLS certificate verification is disabled."

        cam.set_health(state, message, main=main, sub=sub)
        return cam.health
