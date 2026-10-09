"""MediaMTX configuration generated for RTSP and RTSPS cameras."""
import yaml
import pytest

from app import mediamtx_manager as mm
from app.ffmpeg_manager import FFmpegManager

FP = 'cd' * 32
RTSPS_MAIN = 'rtsps://USER:P%40SS@10.0.0.124:322/stream0'
RTSPS_SUB = 'rtsps://USER:P%40SS@10.0.0.124:322/stream1'


@pytest.fixture
def mgr(tmp_path, monkeypatch):
    monkeypatch.setattr(FFmpegManager, 'get_ffmpeg_path', lambda self: '/usr/bin/ffmpeg')
    m = mm.MediaMTXManager()
    m.config_file = str(tmp_path / 'mediamtx.yml')
    # Never probe real cameras from unit tests
    monkeypatch.setattr(m, '_get_source_codec', lambda url: 'h264')
    return m


def gen(mgr, cameras, **kw):
    for c in cameras:
        c.status = 'running'
    mgr.create_config(cameras, rtsp_port=8554, **kw)
    with open(mgr.config_file) as f:
        return yaml.safe_load(f)


def rtsps(camera_factory, mode='pinned', fp=FP, **kw):
    return camera_factory(mainStreamUrl=RTSPS_MAIN, subStreamUrl=RTSPS_SUB, sourceProtocol='rtsps',
                          tlsMode=mode, tlsFingerprint=fp, **kw)


def all_commands(cfg):
    out = []
    for p in cfg['paths'].values():
        for k in ('runOnInit', 'runOnDemand'):
            if p.get(k):
                out.append(p[k])
    return out


def test_existing_rtsp_camera_config_unchanged(mgr, camera_factory):
    cam = camera_factory()
    cfg = gen(mgr, [cam])
    main = cfg['paths']['alex_room_main']
    assert main['source'] == 'rtsp://admin:pw@10.0.0.50:554/stream1'
    assert main['sourceOnDemand'] is True
    assert main['rtspTransport'] == 'tcp'
    assert 'sourceFingerprint' not in main
    assert cfg['paths']['alex_room_sub']['source'] == 'rtsp://admin:pw@10.0.0.50:554/stream2'
    assert cfg['rtspAddress'] == ':8554'


def test_rtsps_pinned_is_pulled_natively_with_passthrough(mgr, camera_factory):
    cfg = gen(mgr, [rtsps(camera_factory)])
    main = cfg['paths']['alex_room_main']
    assert main['source'] == RTSPS_MAIN
    assert main['sourceFingerprint'] == FP
    assert 'runOnInit' not in main          # no FFmpeg, no transcoding
    sub = cfg['paths']['alex_room_sub']
    assert sub['source'] == RTSPS_SUB and sub['sourceFingerprint'] == FP


def test_rtsps_verify_mode_has_no_fingerprint(mgr, camera_factory):
    cfg = gen(mgr, [rtsps(camera_factory, mode='verify', fp='')])
    main = cfg['paths']['alex_room_main']
    assert main['source'] == RTSPS_MAIN
    assert 'sourceFingerprint' not in main


@pytest.mark.parametrize('supported', [True, False])
def test_rtsps_insecure_mode_relays_with_ffmpeg_over_tls(mgr, camera_factory, monkeypatch, supported):
    from app import ffmpeg_manager
    monkeypatch.setattr(ffmpeg_manager, 'rtsp_tls_verify_supported', lambda b: supported)
    cfg = gen(mgr, [rtsps(camera_factory, mode='insecure', fp='', enableAudio=True)])
    main = cfg['paths']['alex_room_main']
    assert main['source'] == 'publisher'
    cmd = main['runOnDemand']
    # FFmpeg 7+ verifies RTSPS by default; 6.x has no such option and rejects it
    assert ('-tls_verify 0' in cmd) is supported
    assert "rtsps://USER:P%40SS@10.0.0.124:322/stream0" in cmd   # still RTSPS upstream
    assert '-c:v copy' in cmd and '-c:a copy' in cmd              # passthrough
    assert 'libx264' not in cmd


def test_rtsps_transcode_reads_camera_through_pinned_hidden_path(mgr, camera_factory):
    cam = rtsps(camera_factory, transcodeMain=True)
    cfg = gen(mgr, [cam])
    src = cfg['paths']['alex_room_main_src']
    assert src['source'] == RTSPS_MAIN and src['sourceFingerprint'] == FP
    cmd = cfg['paths']['alex_room_main']['runOnInit']
    assert 'rtsp://127.0.0.1:8554/alex_room_main_src' in cmd
    # FFmpeg never connects to the RTSPS camera itself in a verified mode
    for c in all_commands(cfg):
        assert 'rtsps://' not in c


def test_audio_preserved_by_default_in_relay_paths(mgr, camera_factory):
    cam = rtsps(camera_factory, transcodeMain=True, enableAudio=True)
    cmd = gen(mgr, [cam])['paths']['alex_room_main']['runOnInit']
    assert '-c:a copy' in cmd


def test_main_as_sub_for_rtsps_uses_loopback_not_second_camera_connection(mgr, camera_factory):
    cam = rtsps(camera_factory, useMainAsSubstream=True)
    sub = gen(mgr, [cam])['paths']['alex_room_sub']
    assert sub['source'] == 'rtsp://127.0.0.1:8554/alex_room_main'


def test_runtime_substream_fallback(mgr, camera_factory):
    cam = rtsps(camera_factory)
    cam.substream_fallback_active = True
    sub = gen(mgr, [cam])['paths']['alex_room_sub']
    assert sub['source'] == 'rtsp://127.0.0.1:8554/alex_room_main'
    # ONVIF sub profile reports the stream actually served
    assert (cam.sub_width, cam.sub_height) == (cam.main_width, cam.main_height)


def test_disabled_substream_has_no_sub_path(mgr, camera_factory):
    cfg = gen(mgr, [rtsps(camera_factory, disableSubstream=True)])
    assert 'alex_room_sub' not in cfg['paths']


def test_stopped_cameras_have_no_paths(mgr, camera_factory):
    cam = rtsps(camera_factory)
    mgr.create_config([cam], rtsp_port=8554)
    with open(mgr.config_file) as f:
        assert not yaml.safe_load(f)['paths']


def test_loopback_publish_credentials_are_url_encoded(mgr, camera_factory):
    cam = camera_factory(transcodeMain=True)
    cfg = gen(mgr, [cam], rtsp_username='ad@min', rtsp_password='p:ss!')
    cmd = cfg['paths']['alex_room_main']['runOnInit']
    assert 'ad%40min:p%3Ass%21@127.0.0.1:8554' in cmd


def test_rtsps_hevc_autodetect_does_not_probe_camera_directly(mgr, camera_factory, monkeypatch):
    calls = []
    monkeypatch.setattr(mgr, '_get_source_codec', lambda url: calls.append(url) or 'hevc')
    cam = rtsps(camera_factory)
    gen(mgr, [cam])
    assert calls == []
    # once the health monitor has seen HEVC through MediaMTX, it is used
    cam.stream_probe = {'sub': {'codec': 'hevc'}}
    cfg = gen(mgr, [cam])
    assert 'libx264' in cfg['paths']['alex_room_sub']['runOnInit']


def test_tls_verify_capability_is_detected_from_the_build(tmp_path):
    import sys, textwrap
    from app import ffmpeg_manager
    for name, has in (('new', True), ('old', False)):
        fake = tmp_path / name
        fake.write_text(textwrap.dedent(f'''\
            #!{sys.executable}
            print("RTSP demuxer AVOptions:")
            {"print('  -tls_verify  <boolean>  Verify the peer certificate')" if has else ""}
        '''))
        fake.chmod(0o755)
        assert ffmpeg_manager.rtsp_tls_verify_supported(str(fake)) is has
        assert ffmpeg_manager.insecure_tls_input_args(str(fake)) == (['-tls_verify', '0'] if has else [])
    assert ffmpeg_manager.rtsp_tls_verify_supported(str(tmp_path / 'missing')) is False
