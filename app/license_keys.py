"""
Addon license key verification.

Keys are signed with an Ed25519 private key that lives ONLY in the separate
"Tonys Addon Keygen" app (kept out of this repository). This file holds the
matching public key, which can check keys but cannot create them.
"""
import base64
import datetime
import hashlib
import struct

# Public key of the keygen app. Set with:  python keygen.py install-pubkey <path to this app folder>
PUBLIC_KEY_HEX = '5dedbd53c4c816d34c29333b891e8a9334a8770c3ed00fb9e331bd7333751ce7'

VERSION = 1
EPOCH = datetime.date(2024, 1, 1)
GROUP = 5


_p = 2 ** 255 - 19
_L = 2 ** 252 + 27742317777372353535851937790883648493
_d = -121665 * pow(121666, _p - 2, _p) % _p
_SQRT_M1 = pow(2, (_p - 1) // 4, _p)


def _H(m):
    return hashlib.sha512(m).digest()


def _inv(x):
    return pow(x, _p - 2, _p)


def _add(P, Q):
    A = (P[1] - P[0]) * (Q[1] - Q[0]) % _p
    B = (P[1] + P[0]) * (Q[1] + Q[0]) % _p
    C = 2 * P[3] * Q[3] * _d % _p
    D = 2 * P[2] * Q[2] % _p
    E, F, G, H = B - A, D - C, D + C, B + A
    return (E * F % _p, G * H % _p, F * G % _p, E * H % _p)


def _mul(s, P):
    Q = (0, 1, 1, 0)
    while s > 0:
        if s & 1:
            Q = _add(Q, P)
        P = _add(P, P)
        s >>= 1
    return Q


def _equal(P, Q):
    return (P[0] * Q[2] - Q[0] * P[2]) % _p == 0 and (P[1] * Q[2] - Q[1] * P[2]) % _p == 0


def _recover_x(y, sign):
    if y >= _p:
        return None
    x2 = (y * y - 1) * _inv(_d * y * y + 1) % _p
    if x2 == 0:
        return None if sign else 0
    x = pow(x2, (_p + 3) // 8, _p)
    if (x * x - x2) % _p != 0:
        x = x * _SQRT_M1 % _p
    if (x * x - x2) % _p != 0:
        return None
    if (x & 1) != sign:
        x = _p - x
    return x


_gy = 4 * _inv(5) % _p
_gx = _recover_x(_gy, 0)
_G = (_gx, _gy, 1, _gx * _gy % _p)


def _compress(P):
    zi = _inv(P[2])
    x, y = P[0] * zi % _p, P[1] * zi % _p
    return int.to_bytes(y | ((x & 1) << 255), 32, 'little')


def _decompress(s):
    if len(s) != 32:
        return None
    y = int.from_bytes(s, 'little')
    sign = y >> 255
    y &= (1 << 255) - 1
    x = _recover_x(y, sign)
    if x is None:
        return None
    return (x, y, 1, x * y % _p)


def _expand(secret):
    if len(secret) != 32:
        raise ValueError('Bad private key length')
    h = _H(secret)
    a = int.from_bytes(h[:32], 'little')
    a &= (1 << 254) - 8
    a |= 1 << 254
    return a, h[32:]


def _verify(public, msg, signature):
    if len(public) != 32 or len(signature) != 64:
        return False
    A = _decompress(public)
    R = _decompress(signature[:32])
    if A is None or R is None:
        return False
    s = int.from_bytes(signature[32:], 'little')
    if s >= _L:
        return False
    h = int.from_bytes(_H(signature[:32] + public + msg), 'little') % _L
    return _equal(_mul(s, _G), _add(R, _mul(h, A)))



def encode_payload(module_id, serial, licensee='', issued=None):
    mid = module_id.strip().lower().encode()
    name = (licensee or '').strip().encode('utf-8')[:60]
    day = ((issued or datetime.date.today()) - EPOCH).days
    return struct.pack('>BIH', VERSION, serial & 0xFFFFFFFF, day) + bytes([len(mid)]) + mid + bytes([len(name)]) + name


def decode_payload(data):
    version, serial, day = struct.unpack('>BIH', data[:7])
    if version != VERSION:
        raise ValueError('Unknown key version')
    i = 7
    n = data[i]; mid = data[i + 1:i + 1 + n].decode(); i += 1 + n
    n = data[i]; name = data[i + 1:i + 1 + n].decode('utf-8'); i += 1 + n
    if i != len(data):
        raise ValueError('Bad key length')
    return {'module_id': mid, 'serial': serial, 'licensee': name,
            'issued': (EPOCH + datetime.timedelta(days=day)).isoformat()}


def to_text(module_id, blob):
    b32 = base64.b32encode(blob).decode().rstrip('=')
    groups = [b32[i:i + GROUP] for i in range(0, len(b32), GROUP)]
    return module_id.upper() + '-' + '-'.join(groups)


def from_text(key):
    """-> (module_id_prefix, payload, signature) or raises ValueError."""
    key = ''.join(key.split()).upper()
    if '-' not in key:
        raise ValueError('Not a license key')
    prefix, rest = key.split('-', 1)
    b32 = rest.replace('-', '')
    b32 += '=' * (-len(b32) % 8)
    try:
        blob = base64.b32decode(b32)
    except Exception:
        raise ValueError('Not a license key')
    if len(blob) < 64 + 9:
        raise ValueError('Not a license key')
    return prefix.lower(), blob[:-64], blob[-64:]


def decode_license_key(key):
    """Verified key details {'module_id','serial','licensee','issued'} or None."""
    if not PUBLIC_KEY_HEX or not key:
        return None
    try:
        prefix, payload, sig = from_text(key)
        if not _verify(bytes.fromhex(PUBLIC_KEY_HEX), payload, sig):
            return None
        info = decode_payload(payload)
    except (ValueError, IndexError, struct.error):
        return None
    if info['module_id'] != prefix:
        return None
    return info


def validate_license_key(module_id, key):
    info = decode_license_key(key)
    return bool(info and info['module_id'] == (module_id or '').strip().lower())
