"""
Source stream helpers: URL building/parsing, TLS (RTSPS) policy, credential
redaction and source error classification.

Everything that turns camera settings into a URL, or a URL/log line into
something shown to the operator, should go through this module so the
protocol, TLS policy and redaction rules are applied consistently.
"""
import hashlib
import ipaddress
import os
import re
import socket
import ssl
import threading
from urllib.parse import quote, unquote, urlsplit

PROTOCOL_RTSP = 'rtsp'
PROTOCOL_RTSPS = 'rtsps'
PROTOCOLS = (PROTOCOL_RTSP, PROTOCOL_RTSPS)
DEFAULT_PORTS = {PROTOCOL_RTSP: 554, PROTOCOL_RTSPS: 322}

# TLS policy for RTSPS sources.
#   verify   - full certificate chain + hostname verification (system CAs plus
#              any CA files in data/tls/ca). Default.
#   pinned   - accept only the certificate whose SHA-256 fingerprint matches
#              the configured value. Use for self-signed camera certs (Wyze).
#   insecure - accept any certificate. Diagnostic use on trusted networks only.
TLS_VERIFY = 'verify'
TLS_PINNED = 'pinned'
TLS_INSECURE = 'insecure'
TLS_MODES = (TLS_VERIFY, TLS_PINNED, TLS_INSECURE)
DEFAULT_TLS_MODE = TLS_VERIFY

INSECURE_WARNING = (
    "TLS certificate verification is DISABLED for this camera. The connection "
    "is still encrypted, but the camera's identity is not checked, so a device "
    "on your network could impersonate it and capture its credentials. Use only "
    "for diagnostics on a trusted network, then switch to 'Pinned certificate'."
)


# --------------------------------------------------------------------------
# Redaction
# --------------------------------------------------------------------------

_secrets = set()
_secrets_lock = threading.Lock()

# scheme://userinfo@  -> scheme://***@   (greedy to the last '@' before a '/')
_URL_USERINFO_RE = re.compile(r'([A-Za-z][A-Za-z0-9+.\-]*://)[^/\s"\'<>]*@')


def register_secret(value):
    """Register a secret (e.g. a camera password) so redact_text() masks it
    even when it appears outside a URL. Very short values are ignored to avoid
    mangling ordinary log text."""
    if not value or not isinstance(value, str) or len(value) < 4:
        return
    with _secrets_lock:
        _secrets.add(value)
        encoded = quote(value, safe='')
        if encoded != value:
            _secrets.add(encoded)


def redact_url(url):
    """Mask the userinfo part of a URL: rtsps://u:p@h/x -> rtsps://***@h/x"""
    if not url:
        return url
    return _URL_USERINFO_RE.sub(r'\1***@', str(url))


def redact_text(text):
    """Mask credentials in arbitrary text (log lines, error messages)."""
    if not text:
        return text
    text = _URL_USERINFO_RE.sub(r'\1***@', str(text))
    with _secrets_lock:
        secrets = sorted(_secrets, key=len, reverse=True)
    for s in secrets:
        if s in text:
            text = text.replace(s, '***')
    return text


# --------------------------------------------------------------------------
# URL building / parsing
# --------------------------------------------------------------------------

def normalize_protocol(protocol):
    p = (protocol or PROTOCOL_RTSP).strip().lower()
    if p not in PROTOCOLS:
        raise ValueError(f"Unsupported source protocol '{protocol}'. Use rtsp or rtsps.")
    return p


def normalize_tls_mode(mode):
    m = (mode or DEFAULT_TLS_MODE).strip().lower()
    if m not in TLS_MODES:
        raise ValueError(f"Unsupported TLS mode '{mode}'. Use verify, pinned or insecure.")
    return m


def validate_host(host):
    """Return a cleaned host or raise ValueError with an actionable message.

    The host field must be a bare hostname or IP. A full URL pasted into it
    used to produce rtsp://user:pass@rtsps://host:port/... (malformed)."""
    if host is None:
        raise ValueError("Camera host is required")
    h = str(host).strip()
    if not h:
        raise ValueError("Camera host is required")
    if '://' in h:
        raise ValueError(
            "Camera host must be an IP address or hostname only (for example 10.0.0.124). "
            "Choose RTSP or RTSPS in the Protocol field instead of typing a URL here.")
    if h.startswith('[') and h.endswith(']'):
        h = h[1:-1]
    try:
        ipaddress.ip_address(h)
        return h
    except ValueError:
        pass
    if any(c in h for c in '@/?#\\ \t') or ':' in h:
        raise ValueError(
            "Camera host contains invalid characters. Enter only the IP address or "
            "hostname; put the port, path and credentials in their own fields.")
    if not re.match(r'^[A-Za-z0-9._\-]+$', h):
        raise ValueError("Camera host contains invalid characters.")
    return h


def validate_port(port):
    try:
        p = int(str(port).strip())
    except (TypeError, ValueError):
        raise ValueError(f"Invalid port '{port}'")
    if not 1 <= p <= 65535:
        raise ValueError(f"Port {p} is out of range (1-65535)")
    return p


def _format_host(host):
    try:
        if ipaddress.ip_address(host).version == 6:
            return f'[{host}]'
    except ValueError:
        pass
    return host


def normalize_path(path):
    p = (path or '').strip()
    if not p:
        return ''
    if '://' in p:
        raise ValueError("Stream path must be a path like /stream0, not a full URL.")
    if not p.startswith('/'):
        p = '/' + p
    return p


def build_source_url(protocol, host, port, username='', password='', path=''):
    """Build an rtsp:// or rtsps:// source URL with properly encoded credentials."""
    scheme = normalize_protocol(protocol)
    h = _format_host(validate_host(host))
    p = validate_port(port if port not in (None, '') else DEFAULT_PORTS[scheme])
    path = normalize_path(path)
    user_enc = quote(username, safe='') if username else ''
    pass_enc = quote(password, safe='') if password else ''
    if user_enc and pass_enc:
        auth = f"{user_enc}:{pass_enc}@"
    elif user_enc:
        auth = f"{user_enc}@"
    elif pass_enc:
        auth = f":{pass_enc}@"
    else:
        auth = ''
    return f"{scheme}://{auth}{h}:{p}{path}"


def parse_source_url(url):
    """Split a source URL into its parts (credentials decoded).

    Returns a dict with protocol, host, port, username, password, path.
    The path includes any query string. Raises ValueError for non-RTSP URLs.
    """
    if not url:
        raise ValueError("Empty URL")
    parts = urlsplit(url)
    scheme = (parts.scheme or '').lower()
    if scheme not in PROTOCOLS:
        raise ValueError(f"Unsupported URL scheme '{scheme}'")
    host = parts.hostname or ''
    try:
        port = parts.port
    except ValueError:
        port = None
    path = parts.path or ''
    if parts.query:
        path += '?' + parts.query
    return {
        'protocol': scheme,
        'host': host,
        'port': port or DEFAULT_PORTS[scheme],
        'username': unquote(parts.username) if parts.username else '',
        'password': unquote(parts.password) if parts.password else '',
        'path': path,
    }


def protocol_of(url):
    try:
        return (urlsplit(url or '').scheme or PROTOCOL_RTSP).lower()
    except Exception:
        return PROTOCOL_RTSP


# --------------------------------------------------------------------------
# Certificates
# --------------------------------------------------------------------------

def normalize_fingerprint(value):
    """Accept 'AA:BB:..', 'aabb..', 'SHA256 Fingerprint=AA:..' or a PEM
    certificate, and return a 64-char lowercase hex SHA-256 fingerprint.
    Returns '' for empty input; raises ValueError for anything else."""
    if value is None:
        return ''
    v = str(value).strip()
    if not v:
        return ''
    if '-----BEGIN CERTIFICATE-----' in v:
        return fingerprint_from_pem(v)
    if '=' in v:
        v = v.split('=', 1)[1]
    v = re.sub(r'[\s:]', '', v).lower()
    if not re.fullmatch(r'[0-9a-f]{64}', v):
        raise ValueError(
            "Certificate fingerprint must be a SHA-256 fingerprint (64 hex characters, "
            "colons optional) or a PEM certificate.")
    return v


def fingerprint_from_der(der):
    return hashlib.sha256(der).hexdigest()


def fingerprint_from_pem(pem):
    m = re.search(r'-----BEGIN CERTIFICATE-----(.+?)-----END CERTIFICATE-----', pem, re.S)
    if not m:
        raise ValueError("No PEM certificate found")
    der = ssl.PEM_cert_to_DER_cert(m.group(0))
    return fingerprint_from_der(der)


def format_fingerprint(fp):
    fp = (fp or '').upper()
    return ':'.join(fp[i:i + 2] for i in range(0, len(fp), 2))


def _describe_der(der):
    info = {'sha256': fingerprint_from_der(der)}
    try:
        from cryptography import x509
        cert = x509.load_der_x509_certificate(der)
        info['subject'] = cert.subject.rfc4514_string()
        info['issuer'] = cert.issuer.rfc4514_string()
        try:
            info['notBefore'] = cert.not_valid_before_utc.isoformat()
            info['notAfter'] = cert.not_valid_after_utc.isoformat()
        except AttributeError:  # cryptography < 42
            info['notBefore'] = cert.not_valid_before.isoformat()
            info['notAfter'] = cert.not_valid_after.isoformat()
        info['selfSigned'] = cert.subject == cert.issuer
        try:
            san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
            info['subjectAltNames'] = [str(n.value) for n in san]
        except Exception:
            info['subjectAltNames'] = []
    except Exception:
        pass
    info['pem'] = ssl.DER_cert_to_PEM_cert(der)
    return info


def fetch_server_certificate(host, port, timeout=8):
    """Connect to host:port over TLS and return the server certificate details.

    Verification is intentionally off: this only *reads* the certificate so
    the operator can inspect it and decide whether to pin it. Nothing is
    trusted until the fingerprint is saved to the camera."""
    host = validate_host(host)
    port = validate_port(port)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with socket.create_connection((host, port), timeout=timeout) as sock:
        server_hostname = None
        try:
            ipaddress.ip_address(host)
        except ValueError:
            server_hostname = host
        with ctx.wrap_socket(sock, server_hostname=server_hostname) as tls:
            der = tls.getpeercert(binary_form=True)
            version = tls.version()
    if not der:
        raise ValueError("Server did not present a certificate")
    info = _describe_der(der)
    info['tlsVersion'] = version
    return info


def custom_ca_dir(data_dir):
    return os.path.join(data_dir, 'tls', 'ca')


def list_custom_cas(data_dir):
    d = custom_ca_dir(data_dir)
    try:
        return sorted(f for f in os.listdir(d)
                      if f.lower().endswith(('.pem', '.crt', '.cer')) and
                      os.path.isfile(os.path.join(d, f)))
    except OSError:
        return []


# --------------------------------------------------------------------------
# Source error classification
# --------------------------------------------------------------------------

STATE_STOPPED = 'stopped'
STATE_STARTING = 'starting'
STATE_CONNECTING = 'connecting'
STATE_STREAMING = 'streaming'
STATE_RECONNECTING = 'reconnecting'
STATE_AUTH_FAILED = 'auth_failed'
STATE_TLS_FAILED = 'tls_failed'
STATE_UNAVAILABLE = 'unavailable'
STATE_ERROR = 'error'

STATE_LABELS = {
    STATE_STOPPED: 'Stopped',
    STATE_STARTING: 'Starting',
    STATE_CONNECTING: 'Connecting',
    STATE_STREAMING: 'Streaming',
    STATE_RECONNECTING: 'Reconnecting',
    STATE_AUTH_FAILED: 'Authentication failed',
    STATE_TLS_FAILED: 'TLS verification failed',
    STATE_UNAVAILABLE: 'Source unavailable',
    STATE_ERROR: 'Error',
}

# (pattern, state, operator-facing hint). First match wins.
_ERROR_RULES = [
    (r'fingerprint does not match',
     STATE_TLS_FAILED,
     "The camera's certificate no longer matches the pinned fingerprint. If the camera "
     "was reset or its firmware updated, fetch and confirm the new certificate in the "
     "camera's TLS settings. If not, something may be impersonating the camera."),
    (r'x509: certificate signed by unknown authority|self[- ]signed|unable to get local issuer',
     STATE_TLS_FAILED,
     "The camera uses a certificate that is not signed by a trusted CA (Wyze cameras use "
     "a self-signed certificate). Set TLS mode to 'Pinned certificate' and fetch/confirm "
     "the camera's certificate."),
    (r"x509: cannot validate certificate|doesn't contain any IP SANs|certificate is valid for|"
     r"certificate is not valid for",
     STATE_TLS_FAILED,
     "The certificate does not name this host/IP. Self-signed camera certificates usually "
     "can't pass hostname checks; use 'Pinned certificate' mode instead."),
    (r'x509: certificate has expired|certificate has expired',
     STATE_TLS_FAILED,
     "The camera's certificate has expired. Pin the current certificate or renew it on the camera."),
    (r'tls: |x509:|certificate verify failed|SSL routines|handshake failure',
     STATE_TLS_FAILED,
     "The TLS handshake with the camera failed. Check the TLS mode and that the port is the RTSPS port."),
    (r'\b401\b|Unauthorized|authentication failed|\b403\b|Forbidden',
     STATE_AUTH_FAILED,
     "The camera rejected the username or password. Re-enter the credentials exactly as set "
     "in the camera app (special characters are supported)."),
    (r'\b404\b|Not Found|\b400\b|Bad Request|\b454\b|Session Not Found|no stream|'
     r'not found|Invalid data found',
     STATE_UNAVAILABLE,
     "The camera answered but has no stream on this path. Check the stream path "
     "(Wyze: /stream0 main, /stream1 sub if supported)."),
    (r'connection refused',
     STATE_UNAVAILABLE,
     "Nothing is listening on that port. Check the camera IP and port (Wyze RTSPS uses 322) "
     "and that RTSP is enabled in the camera app."),
    (r'no route to host|network is unreachable|i/o timeout|timed out|timeout|deadline exceeded|'
     r'host is down',
     STATE_UNAVAILABLE,
     "The camera did not respond. Check that it is powered on and reachable from the server."),
    (r'connection reset by peer|\bEOF\b|unexpected EOF|malformed|invalid response|bad status',
     STATE_UNAVAILABLE,
     "The camera closed the connection. If the camera uses RTSPS (Wyze port 322), make "
     "sure Protocol is set to RTSPS; plain RTSP to a TLS port is reset like this."),
    (r'no such host|lookup .* on|Name or service not known|Temporary failure in name resolution',
     STATE_UNAVAILABLE,
     "The camera hostname could not be resolved. Use the camera's IP address."),
]


def classify_source_error(text):
    """Map a raw MediaMTX/FFmpeg error to (state, hint). Unknown errors -> STATE_ERROR."""
    if not text:
        return STATE_ERROR, "Unknown error."
    for pattern, state, hint in _ERROR_RULES:
        if re.search(pattern, text, re.I):
            return state, hint
    return STATE_ERROR, "Unexpected error from the stream source. See the server log for details."
