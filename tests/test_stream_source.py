"""URL construction, credential encoding/redaction, fingerprints and error classification."""
import datetime
import socket
import ssl
import threading

import pytest

from app import stream_source as ss


# ---- URL construction -------------------------------------------------------

def test_rtsp_url_is_unchanged_for_existing_cameras():
    url = ss.build_source_url('rtsp', '192.168.1.100', 554, 'admin', 'secret', '/stream1')
    assert url == 'rtsp://admin:secret@192.168.1.100:554/stream1'


def test_rtsps_url_uses_rtsps_scheme():
    url = ss.build_source_url('rtsps', '10.0.0.124', 322, 'USERNAME', 'PASSWORD', '/stream0')
    assert url == 'rtsps://USERNAME:PASSWORD@10.0.0.124:322/stream0'


def test_default_ports_per_protocol():
    assert ss.build_source_url('rtsps', '10.0.0.124', '', '', '', '/stream0') == 'rtsps://10.0.0.124:322/stream0'
    assert ss.build_source_url('rtsp', '10.0.0.124', None, '', '', 'stream0') == 'rtsp://10.0.0.124:554/stream0'


@pytest.mark.parametrize('user,password', [
    ('admin', 'p!ss'),
    ('ad@min', 'p@ss'),
    ('user:name', 'pa:ss'),
    ('u', 'p!@:#?/%&=+ $'),
    ('üser', 'pässwörd'),
])
def test_special_characters_round_trip(user, password):
    url = ss.build_source_url('rtsps', '10.0.0.124', 322, user, password, '/stream0')
    # Only one '@' separates userinfo from host; nothing unescaped leaks into the authority
    authority = url.split('://', 1)[1].split('/', 1)[0]
    assert authority.count('@') == 1
    userinfo, hostport = authority.rsplit('@', 1)
    assert hostport == '10.0.0.124:322'
    assert userinfo.count(':') == 1
    parsed = ss.parse_source_url(url)
    assert parsed['username'] == user
    assert parsed['password'] == password
    assert parsed['host'] == '10.0.0.124'
    assert parsed['port'] == 322
    assert parsed['path'] == '/stream0'
    assert parsed['protocol'] == 'rtsps'


def test_username_only_and_no_credentials():
    assert ss.build_source_url('rtsp', 'cam.local', 554, 'admin', '', '/s') == 'rtsp://admin@cam.local:554/s'
    assert ss.build_source_url('rtsp', 'cam.local', 554, '', '', '/s') == 'rtsp://cam.local:554/s'


def test_ipv6_host_is_bracketed():
    url = ss.build_source_url('rtsps', 'fe80::1', 322, 'a', 'b', '/stream0')
    assert url == 'rtsps://a:b@[fe80::1]:322/stream0'
    assert ss.parse_source_url(url)['host'] == 'fe80::1'


@pytest.mark.parametrize('bad', [
    'rtsps://10.0.0.124:322/stream0',       # the original "Port missing in uri" bug
    'rtsp://10.0.0.124',
    'user:pass@10.0.0.124',
    '10.0.0.124/stream0',
    '10.0.0.124:322',
    'bad host',
    '',
])
def test_host_field_rejects_urls_and_junk(bad):
    with pytest.raises(ValueError):
        ss.build_source_url('rtsps', bad, 322, 'u', 'p', '/stream0')


def test_path_must_not_be_a_url():
    with pytest.raises(ValueError):
        ss.build_source_url('rtsps', '10.0.0.124', 322, 'u', 'p', 'rtsps://10.0.0.124:322/stream0')


def test_invalid_protocol_and_port():
    with pytest.raises(ValueError):
        ss.build_source_url('http', '10.0.0.124', 322, '', '', '/x')
    with pytest.raises(ValueError):
        ss.build_source_url('rtsp', '10.0.0.124', 70000, '', '', '/x')


def test_path_keeps_query_string():
    url = ss.build_source_url('rtsp', '10.0.0.5', 554, '', '', '/cam/realmonitor?channel=1&subtype=0')
    assert ss.parse_source_url(url)['path'] == '/cam/realmonitor?channel=1&subtype=0'


# ---- Redaction --------------------------------------------------------------

def test_redact_url_masks_userinfo():
    url = ss.build_source_url('rtsps', '10.0.0.124', 322, 'USERNAME', 'p@ss:w!rd', '/stream0')
    red = ss.redact_url(url)
    assert red == 'rtsps://***@10.0.0.124:322/stream0'
    assert 'USERNAME' not in red and 'p%40ss' not in red


def test_redact_text_masks_urls_in_ffmpeg_errors():
    line = ("[tcp @ 0x55] Connection to tcp://10.0.0.124:322 failed\n"
            "rtsps://bob:hunter2%21@10.0.0.124:322/stream0: Connection refused")
    out = ss.redact_text(line)
    assert 'hunter2' not in out and 'bob' not in out
    assert 'rtsps://***@10.0.0.124:322/stream0' in out


def test_redact_text_masks_raw_unencoded_at_in_password():
    out = ss.redact_text('rtsp://user:p@ss@10.0.0.1:554/x')
    assert out == 'rtsp://***@10.0.0.1:554/x'


def test_registered_secrets_are_masked_outside_urls():
    ss.register_secret('Sup3r$ecret!')
    out = ss.redact_text("auth failed for password Sup3r$ecret! and Sup3r%24ecret%21")
    assert 'Sup3r' not in out
    # Short values are not registered (would mangle ordinary text)
    ss.register_secret('ab')
    assert ss.redact_text('ab cab') == 'ab cab'


def test_redaction_leaves_plain_urls_alone():
    assert ss.redact_text('rtsp://127.0.0.1:8554/front_door_main') == 'rtsp://127.0.0.1:8554/front_door_main'


# ---- Fingerprints / certificates -------------------------------------------

def _self_signed(cn='RTSP Server', org='Wyze Labs', san_ips=()):
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID
    import ipaddress
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COUNTRY_NAME, 'US'),
                      x509.NameAttribute(NameOID.ORGANIZATION_NAME, org),
                      x509.NameAttribute(NameOID.COMMON_NAME, cn)])
    now = datetime.datetime.now(datetime.timezone.utc)
    b = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
         .public_key(key.public_key()).serial_number(x509.random_serial_number())
         .not_valid_before(now - datetime.timedelta(days=1))
         .not_valid_after(now + datetime.timedelta(days=30)))
    if san_ips:
        b = b.add_extension(x509.SubjectAlternativeName(
            [x509.IPAddress(ipaddress.ip_address(i)) for i in san_ips]), critical=False)
    cert = b.sign(key, hashes.SHA256())
    cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode()
    key_pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                serialization.NoEncryption()).decode()
    return cert_pem, key_pem, cert.fingerprint(hashes.SHA256()).hex()


def test_normalize_fingerprint_formats():
    fp = 'ab' * 32
    assert ss.normalize_fingerprint(fp.upper()) == fp
    assert ss.normalize_fingerprint(':'.join(['AB'] * 32)) == fp
    assert ss.normalize_fingerprint('sha256 Fingerprint=' + ':'.join(['AB'] * 32)) == fp
    assert ss.normalize_fingerprint('') == ''
    with pytest.raises(ValueError):
        ss.normalize_fingerprint('1234')
    with pytest.raises(ValueError):
        ss.normalize_fingerprint('zz' * 32)


def test_fingerprint_from_pasted_pem_certificate():
    cert_pem, _, expected = _self_signed()
    assert ss.normalize_fingerprint(cert_pem) == expected
    assert ss.format_fingerprint(expected).count(':') == 31


def test_fetch_server_certificate_reads_self_signed_cert(tmp_path):
    cert_pem, key_pem, expected = _self_signed()
    (tmp_path / 'c.pem').write_text(cert_pem)
    (tmp_path / 'k.pem').write_text(key_pem)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(str(tmp_path / 'c.pem'), str(tmp_path / 'k.pem'))
    srv = socket.socket()
    srv.bind(('127.0.0.1', 0))
    srv.listen(1)
    port = srv.getsockname()[1]

    def serve():
        conn, _ = srv.accept()
        try:
            with ctx.wrap_socket(conn, server_side=True) as t:
                t.recv(1)
        except Exception:
            pass

    th = threading.Thread(target=serve, daemon=True)
    th.start()
    info = ss.fetch_server_certificate('127.0.0.1', port, timeout=5)
    srv.close()
    assert info['sha256'] == expected
    assert 'Wyze Labs' in info['subject']
    assert info['selfSigned'] is True
    assert info['tlsVersion'].startswith('TLS')


# ---- Error classification (messages captured from MediaMTX 1.18.2 / FFmpeg) --

@pytest.mark.parametrize('msg,state', [
    ("source fingerprint does not match: expected 0880, got 6d0f", ss.STATE_TLS_FAILED),
    ("tls: failed to verify certificate: x509: cannot validate certificate for 10.0.0.124 because it doesn't contain any IP SANs", ss.STATE_TLS_FAILED),
    ("tls: failed to verify certificate: x509: certificate signed by unknown authority", ss.STATE_TLS_FAILED),
    ("error:0A000086:SSL routines::certificate verify failed", ss.STATE_TLS_FAILED),
    ("bad status code: 401 (Unauthorized)", ss.STATE_AUTH_FAILED),
    ("method DESCRIBE failed: 401 Unauthorized", ss.STATE_AUTH_FAILED),
    ("bad status code: 400 (Bad Request)", ss.STATE_UNAVAILABLE),
    ("bad status code: 404 (Not Found)", ss.STATE_UNAVAILABLE),
    ("dial tcp 10.0.0.124:322: connect: connection refused", ss.STATE_UNAVAILABLE),
    ("read tcp 10.0.0.2:5555->10.0.0.124:322: read: connection reset by peer", ss.STATE_UNAVAILABLE),
    ("EOF", ss.STATE_UNAVAILABLE),
    ("dial tcp 10.0.0.124:322: i/o timeout", ss.STATE_UNAVAILABLE),
    ("something completely different", ss.STATE_ERROR),
])
def test_classify_source_error(msg, state):
    got, hint = ss.classify_source_error(msg)
    assert got == state
    assert hint


def test_protocol_mismatch_hint_mentions_rtsps():
    _, hint = ss.classify_source_error("read: connection reset by peer")
    assert 'RTSPS' in hint
