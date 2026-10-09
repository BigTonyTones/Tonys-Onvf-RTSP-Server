"""Camera source settings, TLS policy decisions and migration of old configs."""
import json

import pytest

from app import stream_source as ss
from app.manager import CameraManager

FP = 'ab' * 32


def build(**kw):
    args = dict(host='10.0.0.124', port=322, username='USERNAME', password='PASSWORD',
                main_path='/stream0', sub_path='/stream1', protocol='rtsps',
                tls_mode='pinned', tls_fingerprint=FP)
    args.update(kw)
    return CameraManager._build_source_settings(None, **args)


def test_existing_rtsp_camera_settings():
    s = build(port=554, protocol='rtsp', tls_mode=None, tls_fingerprint='',
              main_path='stream1', sub_path='stream2')
    assert s['main_url'] == 'rtsp://USERNAME:PASSWORD@10.0.0.124:554/stream1'
    assert s['sub_url'] == 'rtsp://USERNAME:PASSWORD@10.0.0.124:554/stream2'
    assert s['protocol'] == 'rtsp'
    assert s['tls_mode'] == 'verify'


def test_new_rtsps_camera_settings():
    s = build()
    assert s['main_url'] == 'rtsps://USERNAME:PASSWORD@10.0.0.124:322/stream0'
    assert s['sub_url'] == 'rtsps://USERNAME:PASSWORD@10.0.0.124:322/stream1'
    assert s['tls_mode'] == 'pinned'
    assert s['tls_fingerprint'] == FP


def test_tls_verification_is_on_by_default():
    s = build(tls_mode=None, tls_fingerprint='')
    assert s['tls_mode'] == ss.TLS_VERIFY


def test_pinned_mode_requires_a_fingerprint():
    with pytest.raises(ValueError, match='fingerprint'):
        build(tls_mode='pinned', tls_fingerprint='')


def test_url_in_host_field_is_rejected_with_guidance():
    with pytest.raises(ValueError, match='Protocol'):
        build(host='rtsps://10.0.0.124:322/stream0')


def test_empty_sub_path_falls_back_to_main_path():
    s = build(sub_path='')
    assert s['sub_url'].endswith('/stream0')


# ---- Migration of configs saved by older versions ---------------------------

LEGACY_RTSP = {
    'id': 3, 'name': 'Garage', 'pathName': 'garage',
    'mainStreamUrl': 'rtsp://admin:p%40ss@192.168.1.20:554/h264Preview_01_main',
    'subStreamUrl': 'rtsp://admin:p%40ss@192.168.1.20:554/h264Preview_01_sub',
    'username': 'admin', 'password': 'p@ss', 'onvifPort': 8003,
}


def test_legacy_rtsp_config_loads_without_changes(camera_factory):
    cam = camera_factory(**LEGACY_RTSP)
    assert cam.source_protocol == 'rtsp'
    assert cam.tls_mode == 'verify'
    assert cam.main_stream_url == LEGACY_RTSP['mainStreamUrl']
    saved = cam.to_config_dict()
    assert saved['mainStreamUrl'] == LEGACY_RTSP['mainStreamUrl']
    assert saved['sourceProtocol'] == 'rtsp'
    assert saved['substreamFallback'] is True
    # FFmpeg may read plain RTSP cameras directly, exactly as before
    assert cam.ffmpeg_direct_input('main') == (LEGACY_RTSP['mainStreamUrl'], [])
    assert cam.mediamtx_source_fields() == {}


def test_legacy_config_with_hand_edited_rtsps_url_is_detected(camera_factory):
    cam = camera_factory(mainStreamUrl='rtsps://u:p@10.0.0.124:322/stream0',
                         subStreamUrl='rtsps://u:p@10.0.0.124:322/stream1')
    assert cam.source_protocol == 'rtsps'
    assert cam.tls_mode == 'verify'          # secure default, not silently insecure
    assert cam.ffmpeg_requires_relay()


def test_config_round_trip_through_json(camera_factory):
    cam = camera_factory(mainStreamUrl='rtsps://u:p@10.0.0.124:322/stream0',
                         subStreamUrl='rtsps://u:p@10.0.0.124:322/stream1',
                         sourceProtocol='rtsps', tlsMode='pinned', tlsFingerprint=FP,
                         substreamFallback=False)
    data = json.loads(json.dumps(cam.to_config_dict()))
    again = camera_factory(**data)
    assert (again.source_protocol, again.tls_mode, again.tls_fingerprint, again.substream_fallback) == \
        ('rtsps', 'pinned', FP, False)


def test_corrupt_tls_values_fall_back_to_secure_defaults(camera_factory):
    cam = camera_factory(mainStreamUrl='rtsps://u:p@h:322/s', subStreamUrl='rtsps://u:p@h:322/s',
                         tlsMode='bogus', tlsFingerprint='nothex')
    assert cam.tls_mode == 'verify'
    assert cam.tls_fingerprint == ''


def test_api_dict_exposes_editor_fields_without_new_secrets(camera_factory):
    cam = camera_factory(mainStreamUrl='rtsps://u:p@10.0.0.124:322/stream0',
                         subStreamUrl='rtsps://u:p@10.0.0.124:322/stream1',
                         sourceProtocol='rtsps', tlsMode='pinned', tlsFingerprint=FP)
    d = cam.to_dict()
    assert d['sourceHost'] == '10.0.0.124'
    assert d['sourcePort'] == 322
    assert d['mainPath'] == '/stream0' and d['subPath'] == '/stream1'
    assert d['streamHealth']['state'] == 'stopped'
    assert d['tlsInsecure'] is False


# ---- TLS policy decisions ----------------------------------------------------

def rtsps_cam(camera_factory, mode, fp=''):
    return camera_factory(mainStreamUrl='rtsps://u:p@10.0.0.124:322/stream0',
                          subStreamUrl='rtsps://u:p@10.0.0.124:322/stream1',
                          sourceProtocol='rtsps', tlsMode=mode, tlsFingerprint=fp)


def test_pinned_mode_sets_mediamtx_fingerprint(camera_factory):
    cam = rtsps_cam(camera_factory, 'pinned', FP)
    assert cam.mediamtx_source_fields() == {'sourceFingerprint': FP}
    # FFmpeg must not touch the camera directly in a verified mode
    assert cam.ffmpeg_direct_input('main') == (None, [])


def test_verify_mode_uses_mediamtx_ca_verification(camera_factory):
    cam = rtsps_cam(camera_factory, 'verify')
    assert cam.mediamtx_source_fields() == {}
    assert cam.ffmpeg_direct_input('main') == (None, [])


def test_pinned_mode_without_fingerprint_never_means_trust_all(camera_factory):
    cam = rtsps_cam(camera_factory, 'pinned', '')
    # No pin -> MediaMTX does full CA verification (fails closed for self-signed)
    assert cam.mediamtx_source_fields() == {}
    assert cam.ffmpeg_requires_relay()


def test_insecure_mode_is_explicit_and_stays_encrypted(camera_factory, monkeypatch):
    from app import ffmpeg_manager
    monkeypatch.setattr(ffmpeg_manager, 'insecure_tls_input_args', lambda binary=None: ['-tls_verify', '0'])
    cam = rtsps_cam(camera_factory, 'insecure')
    url, extra = cam.ffmpeg_direct_input('main')
    assert url.startswith('rtsps://')          # never downgraded to rtsp://
    assert extra == ['-tls_verify', '0']
    assert cam.to_dict()['tlsInsecure'] is True
