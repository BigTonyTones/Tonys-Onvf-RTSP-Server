"""Stream health states, disconnect/reconnect, and missing-substream fallback."""
import time

import pytest

from app import stream_source as ss
from app.stream_health import StreamHealthMonitor

FP = 'ef' * 32


class FakeMtx:
    def __init__(self):
        self.events = {}
        self.running = True
        self.last_start_error = None

    def is_running(self):
        return self.running

    def get_path_event(self, path):
        return dict(self.events.get(path, {}))

    def error(self, path, msg):
        self.events[path] = {'error': msg, 'errorAt': time.time()}


class FakeManager:
    def __init__(self, cams):
        self.cameras = cams
        self.mediamtx = FakeMtx()
        self.rtsp_port = 8554
        self.restarts = 0

    def restart_mediamtx(self, wait=False):
        self.restarts += 1


def ready(nbytes, w=2560, h=1440):
    return {'available': True, 'ready': True, 'online': True, 'inboundBytes': nbytes,
            'tracks2': [{'codec': 'H264', 'codecProps': {'width': w, 'height': h}},
                        {'codec': 'MPEG-4 Audio', 'codecProps': {'sampleRate': 16000, 'channelCount': 1}}]}


NOT_READY = {'available': False, 'ready': False, 'online': True, 'inboundBytes': 0, 'tracks2': []}


@pytest.fixture
def env(camera_factory):
    cam = camera_factory(mainStreamUrl='rtsps://u:p@10.0.0.124:322/stream0',
                         subStreamUrl='rtsps://u:p@10.0.0.124:322/stream1',
                         sourceProtocol='rtsps', tlsMode='pinned', tlsFingerprint=FP)
    cam.status = 'running'
    mgr = FakeManager([cam])
    api = {}
    probes = []

    def probe(url, extra):
        probes.append(url)
        return probe.result

    probe.result = (None, 'timed out waiting for the stream')
    mon = StreamHealthMonitor(mgr, fetch_path=lambda p: api.get(p, {}), probe=probe)
    mon._restart_at = time.time() - 60   # past the start grace period
    return cam, mgr, api, mon, probe, probes


def test_streaming_requires_video_and_growing_bytes(env):
    cam, mgr, api, mon, *_ = env
    api['alex_room_main'] = ready(1000)
    api['alex_room_sub'] = ready(500, 640, 360)
    h = mon.check_camera(cam)
    assert h['state'] == ss.STATE_STREAMING
    assert h['main']['info']['width'] == 2560


def test_audio_only_source_is_not_green(env):
    cam, mgr, api, mon, *_ = env
    api['alex_room_main'] = {'available': True, 'inboundBytes': 10,
                             'tracks2': [{'codec': 'MPEG-4 Audio'}]}
    api['alex_room_sub'] = ready(10)
    assert mon.check_camera(cam)['state'] == ss.STATE_ERROR


def test_online_flag_alone_is_not_streaming(env):
    """MediaMTX 1.18 says online:true for a failing source; that must not be green."""
    cam, mgr, api, mon, probe, _ = env
    api['alex_room_main'] = dict(NOT_READY)
    api['alex_room_sub'] = dict(NOT_READY)
    h = mon.check_camera(cam)
    assert h['state'] != ss.STATE_STREAMING


@pytest.mark.parametrize('err,state', [
    ('source fingerprint does not match: expected aa, got bb', ss.STATE_TLS_FAILED),
    ("tls: failed to verify certificate: x509: cannot validate certificate for 10.0.0.124 because it doesn't contain any IP SANs", ss.STATE_TLS_FAILED),
    ('bad status code: 401 (Unauthorized)', ss.STATE_AUTH_FAILED),
    ('dial tcp 10.0.0.124:322: connect: connection refused', ss.STATE_UNAVAILABLE),
    ('EOF', ss.STATE_UNAVAILABLE),
])
def test_source_errors_are_classified(env, err, state):
    cam, mgr, api, mon, *_ = env
    api['alex_room_main'] = dict(NOT_READY)
    api['alex_room_sub'] = dict(NOT_READY)
    mgr.mediamtx.error('alex_room_main', err)
    mgr.mediamtx.error('alex_room_sub', err)
    h = mon.check_camera(cam)
    assert h['state'] == state
    assert h['message']


def test_idle_on_demand_path_is_verified_by_loopback_probe(env):
    cam, mgr, api, mon, probe, probes = env
    api['alex_room_main'] = dict(NOT_READY)
    api['alex_room_sub'] = dict(NOT_READY)
    probe.result = ({'width': 2560, 'height': 1440, 'codec': 'h264', 'framerate': 20}, '')
    h = mon.check_camera(cam)
    assert h['state'] == ss.STATE_STREAMING
    assert probes[0] == 'rtsp://127.0.0.1:8554/alex_room_main'
    # RTSPS camera in pinned mode: never probed directly
    assert not any(p.startswith('rtsps://') for p in probes)
    # Verified recently -> stays green without re-probing every cycle
    n = len(probes)
    mon.check_camera(cam)
    assert len(probes) == n


def test_disconnect_then_reconnect(env):
    cam, mgr, api, mon, *_ = env
    api['alex_room_main'] = ready(1000)
    api['alex_room_sub'] = ready(1000)
    assert mon.check_camera(cam)['state'] == ss.STATE_STREAMING
    # camera drops: MediaMTX path goes unavailable and logs the error
    api['alex_room_main'] = dict(NOT_READY)
    mgr.mediamtx.error('alex_room_main', 'read: connection reset by peer')
    h = mon.check_camera(cam)
    assert h['state'] == ss.STATE_RECONNECTING
    # MediaMTX reconnects on its own
    mgr.mediamtx.events.clear()
    api['alex_room_main'] = ready(5000)
    assert mon.check_camera(cam)['state'] == ss.STATE_STREAMING


def test_stalled_stream_reports_reconnecting(env, monkeypatch):
    cam, mgr, api, mon, *_ = env
    api['alex_room_main'] = ready(1000)
    api['alex_room_sub'] = ready(1000)
    mon.check_camera(cam)
    mon._tracker('alex_room_main')['lastBytesAt'] -= 60   # no new bytes for a minute
    assert mon.check_camera(cam)['state'] == ss.STATE_RECONNECTING


def test_missing_substream_falls_back_without_marking_camera_offline(env):
    cam, mgr, api, mon, *_ = env
    api['alex_room_main'] = ready(1000)
    api['alex_room_sub'] = dict(NOT_READY)
    mgr.mediamtx.error('alex_room_sub', 'bad status code: 404 (Not Found)')
    h = mon.check_camera(cam)
    assert h['state'] == ss.STATE_STREAMING           # camera still online
    assert h['sub']['state'] == ss.STATE_UNAVAILABLE
    assert 'Sub stream' in h['message']
    api['alex_room_main'] = ready(2000)
    h = mon.check_camera(cam)
    assert cam.substream_fallback_active is True
    assert mgr.restarts == 1
    assert h['state'] == ss.STATE_STREAMING
    # ONVIF sub profile now reports the main stream's resolution
    assert cam.sub_width == cam.main_width


def test_fallback_can_be_disabled(env):
    cam, mgr, api, mon, *_ = env
    cam.substream_fallback = False
    api['alex_room_main'] = ready(1000)
    api['alex_room_sub'] = dict(NOT_READY)
    mgr.mediamtx.error('alex_room_sub', 'bad status code: 404 (Not Found)')
    for i in range(3):
        api['alex_room_main'] = ready(1000 + i)
        h = mon.check_camera(cam)
    assert cam.substream_fallback_active is False and mgr.restarts == 0
    assert h['state'] == ss.STATE_STREAMING


def test_mediamtx_down_is_an_error(env):
    cam, mgr, api, mon, *_ = env
    mgr.mediamtx.running = False
    mgr.mediamtx.last_start_error = 'RTSP port 8554 is in use by PID 99'
    h = mon.check_camera(cam)
    assert h['state'] == ss.STATE_ERROR and '8554' in h['message']


def test_start_grace_period_shows_starting(env):
    cam, mgr, api, mon, *_ = env
    mon.notify_restart()
    h = mon.check_camera(cam)
    assert h['state'] in (ss.STATE_STARTING, ss.STATE_CONNECTING)


def test_insecure_mode_is_flagged_in_status(env):
    cam, mgr, api, mon, *_ = env
    cam.tls_mode = ss.TLS_INSECURE
    api['alex_room_main'] = ready(1)
    api['alex_room_sub'] = ready(1)
    assert 'verification is disabled' in mon.check_camera(cam)['message']


def test_health_messages_are_redacted(env):
    cam, mgr, api, mon, *_ = env
    api['alex_room_main'] = dict(NOT_READY)
    api['alex_room_sub'] = dict(NOT_READY)
    mgr.mediamtx.error('alex_room_main', 'rtsps://u:SECRETPW@10.0.0.124:322/stream0: 401 Unauthorized')
    h = mon.check_camera(cam)
    assert 'SECRETPW' not in h['message'] and 'SECRETPW' not in str(h)
