"""
End-to-end lab tests with real MediaMTX and FFmpeg, no real camera.

A "camera" MediaMTX instance serves a synthetic H.264 + AAC (16 kHz mono)
stream over RTSP and RTSPS with a self-signed "Wyze Labs / RTSP Server"
certificate that has no IP SAN (like a Wyze camera). The gateway is this
project's MediaMTXManager + config generator, and the StreamHealthMonitor
classifies what it sees.

Requires a mediamtx binary (MEDIAMTX_BIN or on PATH; the Docker image ships
v1.18.2) and ffmpeg/ffprobe. Skipped otherwise. Uses ports 8888/8889 for the
gateway's HLS/WebRTC listeners, so don't run it next to a live install.
"""
import datetime
import http.server
import ipaddress
import os
import shutil
import subprocess
import threading
import time

import pytest
import requests

from tests.conftest import free_port, make_camera

MEDIAMTX = os.environ.get('MEDIAMTX_BIN') or shutil.which('mediamtx')
FFMPEG = shutil.which('ffmpeg')
FFPROBE = shutil.which('ffprobe')

pytestmark = pytest.mark.skipif(not (MEDIAMTX and FFMPEG and FFPROBE),
                                reason='needs mediamtx (MEDIAMTX_BIN) and ffmpeg/ffprobe')

# MediaMTX's internal users only allow a limited charset; this still covers
# characters that must be percent-encoded in a URL (! @ # & $).
CAM_USER = 'wy@ze'
CAM_PASS = 'p!a@ss#w&rd$'


# ---- certificates -----------------------------------------------------------

def _make_cert(tmp, name, cn='RTSP Server', org='Wyze Labs', san_ips=(), issuer=None, is_ca=False):
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COUNTRY_NAME, 'US'),
                         x509.NameAttribute(NameOID.ORGANIZATION_NAME, org),
                         x509.NameAttribute(NameOID.COMMON_NAME, cn)])
    now = datetime.datetime.now(datetime.timezone.utc)
    issuer_name, issuer_key = (issuer[0].subject, issuer[1]) if issuer else (subject, key)
    b = (x509.CertificateBuilder().subject_name(subject).issuer_name(issuer_name)
         .public_key(key.public_key()).serial_number(x509.random_serial_number())
         .not_valid_before(now - datetime.timedelta(days=1))
         .not_valid_after(now + datetime.timedelta(days=30)))
    if is_ca:
        b = b.add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        b = b.add_extension(x509.KeyUsage(digital_signature=True, key_cert_sign=True, crl_sign=True,
                                          content_commitment=False, key_encipherment=False,
                                          data_encipherment=False, key_agreement=False,
                                          encipher_only=False, decipher_only=False), critical=True)
    if san_ips:
        b = b.add_extension(x509.SubjectAlternativeName(
            [x509.IPAddress(ipaddress.ip_address(i)) for i in san_ips]), critical=False)
    cert = b.sign(issuer_key, hashes.SHA256())
    crt = os.path.join(tmp, f'{name}.crt')
    keyf = os.path.join(tmp, f'{name}.key')
    with open(crt, 'wb') as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    with open(keyf, 'wb') as f:
        f.write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL,
                                  serialization.NoEncryption()))
    return crt, keyf, cert.fingerprint(hashes.SHA256()).hex(), (cert, key)


# ---- the synthetic "camera" -------------------------------------------------

class FakeCamera:
    def __init__(self, tmp, crt, key, fingerprint):
        self.tmp = tmp
        self.crt, self.key, self.fingerprint = crt, key, fingerprint
        self.rtsp_port = free_port()
        self.rtsps_port = free_port()
        self.proc = None
        self.pub = None

    def start(self):
        cfg = os.path.join(self.tmp, f'camera_{self.rtsps_port}.yml')
        with open(cfg, 'w') as f:
            f.write(f"""
logLevel: info
rtspAddress: :{self.rtsp_port}
rtspsAddress: :{self.rtsps_port}
rtspEncryption: optional
rtspTransports: [tcp]
rtspServerKey: {self.key}
rtspServerCert: {self.crt}
rtmp: false
hls: false
webrtc: false
srt: false
api: false
authInternalUsers:
  - user: "{CAM_USER}"
    pass: "{CAM_PASS}"
    ips: []
    permissions:
      - action: read
      - action: publish
paths:
  stream0:
""")
        self.proc = subprocess.Popen([MEDIAMTX, cfg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
        self.start_publisher()

    def start_publisher(self):
        from urllib.parse import quote
        url = f"rtsp://{quote(CAM_USER, safe='')}:{quote(CAM_PASS, safe='')}@127.0.0.1:{self.rtsp_port}/stream0"
        self.pub = subprocess.Popen(
            [FFMPEG, '-hide_banner', '-loglevel', 'error', '-re',
             '-f', 'lavfi', '-i', 'testsrc=size=1280x720:rate=20',
             '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=16000',
             '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-preset', 'ultrafast', '-tune', 'zerolatency', '-g', '20',
             '-c:a', 'aac', '-ac', '1', '-ar', '16000',
             '-f', 'rtsp', '-rtsp_transport', 'tcp', url],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2.5)

    def stop_publisher(self):
        if self.pub:
            self.pub.kill()
            self.pub.wait()
            self.pub = None

    def stop(self):
        self.stop_publisher()
        if self.proc:
            self.proc.kill()
            self.proc.wait()


@pytest.fixture(scope='module')
def lab(tmp_path_factory):
    tmp = str(tmp_path_factory.mktemp('lab'))
    crt, key, fp, _ = _make_cert(tmp, 'wyze')
    cam = FakeCamera(tmp, crt, key, fp)
    cam.start()
    _, _, wrong_fp, _ = _make_cert(tmp, 'other', org='Someone Else')
    # A CA-signed camera cert (with IP SAN) for 'verify' mode with a custom CA
    ca_crt, _, _, ca = _make_cert(tmp, 'ca', cn='Home Lab CA', org='Home', is_ca=True)
    srv_crt, srv_key, srv_fp, _ = _make_cert(tmp, 'casigned', san_ips=('127.0.0.1',), issuer=ca)
    ca_cam = FakeCamera(tmp, srv_crt, srv_key, srv_fp)
    ca_cam.start()
    yield {'cam': cam, 'wrong_fp': wrong_fp, 'ca_cam': ca_cam, 'ca_crt': ca_crt, 'tmp': tmp}
    cam.stop()
    ca_cam.stop()


class _Auth(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, *a):
        pass


@pytest.fixture(scope='module')
def auth_port():
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), _Auth)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv.server_address[1]
    srv.shutdown()


@pytest.fixture
def gateway(tmp_path, monkeypatch, auth_port):
    from app import mediamtx_manager as mm
    from app.ffmpeg_manager import FFmpegManager
    from app.stream_health import StreamHealthMonitor
    monkeypatch.setattr(FFmpegManager, 'get_ffmpeg_path', lambda self: FFMPEG)
    monkeypatch.setattr(FFmpegManager, 'get_ffprobe_path', lambda self: FFPROBE)
    api_port = free_port()
    monkeypatch.setattr(mm, 'MEDIAMTX_API_PORT', api_port)
    data_dir = tmp_path / 'data'
    data_dir.mkdir()
    monkeypatch.setattr(mm, 'DATA_DIR', str(data_dir))
    m = mm.MediaMTXManager()
    m.executable = MEDIAMTX
    m.config_file = str(data_dir / 'mediamtx.yml')
    monkeypatch.setattr(m, 'download_mediamtx', lambda: True)

    class Stub:
        pass
    g = Stub()
    g.mtx = m
    g.rtsp_port = free_port()
    g.api_port = api_port
    g.data_dir = data_dir
    g.cameras = []
    g.restarts = 0

    def start(cams):
        for c in cams:
            c.status = 'running'
            c.rtsp_port = g.rtsp_port
        g.cameras = cams
        assert m.start(cams, rtsp_port=g.rtsp_port, web_port=auth_port)

    def restart_mediamtx(wait=False):
        g.restarts += 1
        m.restart(g.cameras, rtsp_port=g.rtsp_port, web_port=auth_port)
        g.monitor.notify_restart()

    mgr = Stub()
    mgr.cameras = g.cameras
    mgr.mediamtx = m
    mgr.rtsp_port = g.rtsp_port
    mgr.restart_mediamtx = restart_mediamtx
    g.mgr = mgr
    g.start = lambda cams: (start(cams), setattr(mgr, 'cameras', cams))
    g.monitor = StreamHealthMonitor(mgr, api_port=api_port)
    g.monitor.START_GRACE = 0
    g.monitor.PROBE_INTERVAL = 0
    g.monitor.VERIFIED_TTL = 0

    def probe(path):
        out = subprocess.run([FFPROBE, '-v', 'error', '-rtsp_transport', 'tcp', '-show_entries',
                              'stream=codec_name,width,height,sample_rate,channels', '-of', 'json',
                              f'rtsp://127.0.0.1:{g.rtsp_port}/{path}'],
                             capture_output=True, text=True, timeout=30)
        import json
        return json.loads(out.stdout or '{}').get('streams', []), out.stderr
    g.probe = probe

    def api(path):
        return requests.get(f'http://127.0.0.1:{api_port}/v3/paths/get/{path}', timeout=3).json()
    g.api = api

    def health_until(cam, states, timeout=40):
        deadline = time.time() + timeout
        h = None
        while time.time() < deadline:
            h = g.monitor.check_camera(cam)
            if h['state'] in states:
                return h
            time.sleep(1)
        return h
    g.health_until = health_until
    yield g
    m.stop()


def cam_cfg(lab_cam, protocol='rtsps', mode='pinned', fp=None, sub='/stream0', password=CAM_PASS, **kw):
    from app.stream_source import build_source_url
    port = lab_cam.rtsps_port if protocol == 'rtsps' else lab_cam.rtsp_port
    main = build_source_url(protocol, '127.0.0.1', port, CAM_USER, password, '/stream0')
    subu = build_source_url(protocol, '127.0.0.1', port, CAM_USER, password, sub)
    cfg = dict(mainStreamUrl=main, subStreamUrl=subu, sourceProtocol=protocol, tlsMode=mode,
               tlsFingerprint=lab_cam.fingerprint if fp is None else fp,
               mainWidth=1280, mainHeight=720, mainFramerate=20, enableAudio=True, password=password)
    cfg.update(kw)
    return make_camera(**cfg)


def codecs(streams):
    return sorted(s.get('codec_name') for s in streams)


# ---- tests ------------------------------------------------------------------

def test_existing_rtsp_camera_still_works(lab, gateway):
    cam = cam_cfg(lab['cam'], protocol='rtsp', mode='verify', fp='')
    gateway.start([cam])
    streams, err = gateway.probe('alex_room_main')
    assert codecs(streams) == ['aac', 'h264'], err
    assert gateway.health_until(cam, {'streaming'})['state'] == 'streaming'


def test_rtsps_pinned_relays_video_and_audio_without_transcoding(lab, gateway):
    cam = cam_cfg(lab['cam'])
    gateway.start([cam])
    streams, err = gateway.probe('alex_room_main')
    assert codecs(streams) == ['aac', 'h264'], err
    video = next(s for s in streams if s['codec_name'] == 'h264')
    audio = next(s for s in streams if s['codec_name'] == 'aac')
    assert (video['width'], video['height']) == (1280, 720)     # original resolution
    assert (audio['sample_rate'], audio['channels']) == ('16000', 1)
    # Passthrough: the path is a native RTSPS pull, no FFmpeg process involved
    assert gateway.api('alex_room_main')['source']['type'] == 'rtspSource'
    h = gateway.health_until(cam, {'streaming'})
    assert h['state'] == 'streaming'
    assert h['main']['info']['width'] == 1280


def test_rtsps_default_verify_rejects_self_signed_certificate(lab, gateway):
    cam = cam_cfg(lab['cam'], mode='verify', fp='')
    gateway.start([cam])
    streams, _ = gateway.probe('alex_room_main')
    assert streams == []
    h = gateway.health_until(cam, {'tls_failed'})
    assert h['state'] == 'tls_failed', h
    assert 'Pinned' in h['message']


def test_rtsps_wrong_pinned_fingerprint_is_rejected(lab, gateway):
    cam = cam_cfg(lab['cam'], fp=lab['wrong_fp'])
    gateway.start([cam])
    h = gateway.health_until(cam, {'tls_failed'})
    assert h['state'] == 'tls_failed', h
    assert 'fingerprint' in h['message']


def test_rtsps_verify_with_custom_ca(lab, gateway):
    ca_dir = gateway.data_dir / 'tls' / 'ca'
    ca_dir.mkdir(parents=True)
    shutil.copy(lab['ca_crt'], ca_dir / 'homelab-ca.pem')
    cam = cam_cfg(lab['ca_cam'], mode='verify', fp='')
    gateway.start([cam])
    streams, err = gateway.probe('alex_room_main')
    assert 'h264' in codecs(streams), err


def test_rtsps_insecure_mode_works_but_is_flagged(lab, gateway):
    cam = cam_cfg(lab['cam'], mode='insecure', fp='')
    gateway.start([cam])
    streams, err = gateway.probe('alex_room_main')
    assert codecs(streams) == ['aac', 'h264'], err
    h = gateway.health_until(cam, {'streaming'})
    assert 'verification is disabled' in h['message']


def test_wrong_password_is_reported_as_auth_failure(lab, gateway):
    cam = cam_cfg(lab['cam'], password='not-the-password')
    gateway.start([cam])
    h = gateway.health_until(cam, {'auth_failed'})
    assert h['state'] == 'auth_failed', h
    assert 'not-the-password' not in str(h)


def test_missing_substream_falls_back_to_main(lab, gateway):
    cam = cam_cfg(lab['cam'], sub='/stream1')          # this "camera" has no /stream1
    gateway.start([cam])
    deadline = time.time() + 90
    while time.time() < deadline and not cam.substream_fallback_active:
        h = gateway.monitor.check_camera(cam)
        assert h['main']['state'] in ('streaming', 'connecting', 'starting'), h
        time.sleep(1)
    assert cam.substream_fallback_active
    assert gateway.restarts == 1
    streams, err = gateway.probe('alex_room_sub')
    assert 'h264' in codecs(streams), err
    assert gateway.health_until(cam, {'streaming'})['state'] == 'streaming'


def test_source_disconnect_and_automatic_recovery(lab, gateway):
    cam = cam_cfg(lab['cam'])
    gateway.start([cam])
    reader = subprocess.Popen([FFMPEG, '-v', 'quiet', '-rtsp_transport', 'tcp', '-i',
                               f'rtsp://127.0.0.1:{gateway.rtsp_port}/alex_room_main', '-f', 'null', '-'])
    try:
        assert gateway.health_until(cam, {'streaming'})['state'] == 'streaming'
        lab['cam'].stop_publisher()                      # camera goes away
        h = gateway.health_until(cam, {'reconnecting', 'unavailable'}, timeout=40)
        assert h['state'] in ('reconnecting', 'unavailable'), h
        lab['cam'].start_publisher()                     # camera comes back
        reader.kill()
        h = gateway.health_until(cam, {'streaming'}, timeout=60)
        assert h['state'] == 'streaming', h
    finally:
        reader.kill()
        if not lab['cam'].pub:
            lab['cam'].start_publisher()


def test_probe_source_for_stopped_rtsps_camera_uses_policy(lab, gateway):
    gateway.start([])
    good = cam_cfg(lab['cam'])
    info, err = gateway.mtx.probe_source(good, 'main', rtsp_port=gateway.rtsp_port)
    assert info and info['width'] == 1280, err
    bad = cam_cfg(lab['cam'], fp=lab['wrong_fp'])
    info, err = gateway.mtx.probe_source(bad, 'main', rtsp_port=gateway.rtsp_port)
    assert info is None and 'fingerprint' in err


def test_optional_transcode_reads_camera_through_pinned_path(lab, gateway):
    cam = cam_cfg(lab['cam'], transcodeMain=True, mainWidth=640, mainHeight=360)
    gateway.start([cam])
    deadline = time.time() + 40
    streams = []
    while time.time() < deadline:
        streams, err = gateway.probe('alex_room_main')
        if streams:
            break
        time.sleep(2)
    video = next(s for s in streams if s['codec_name'] == 'h264')
    assert (video['width'], video['height']) == (640, 360)
