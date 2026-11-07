"""
Offline activation token — for air-gapped machines that never touch the
internet, and as the tamper-resistant local record for online activations.

A token binds ONE addon to ONE machine fingerprint, signed by the keygen's
Ed25519 private key. The app verifies it with the public key it already
ships (app/license_keys.py PUBLIC_KEY_HEX) — no secret on the customer PC,
so it verifies forever, offline.

Text form:  <MODULE_ID>.<base32 of payload+signature>

payload = version(1) | fingerprint(16 bytes) | len(mid) mid
          | len(licensee) licensee(utf-8)
signature = Ed25519(payload)  (64 bytes)
"""
import base64
import struct

from . import ed25519_min as ed

VERSION = 1
FP_LEN = 16   # first 16 bytes of the 32-hex fingerprint


def _fp_bytes(fingerprint):
    fp = fingerprint.strip().lower()
    return bytes.fromhex(fp)[:FP_LEN].ljust(FP_LEN, b"\0")


def encode_payload(module_id, fingerprint, licensee=""):
    mid = module_id.strip().lower().encode()
    name = (licensee or "").strip().encode("utf-8")[:60]
    return (struct.pack(">B", VERSION) + _fp_bytes(fingerprint)
            + bytes([len(mid)]) + mid + bytes([len(name)]) + name)


def decode_payload(data):
    if data[0] != VERSION:
        raise ValueError("Unknown token version")
    i = 1
    fp = data[i:i + FP_LEN].hex(); i += FP_LEN
    n = data[i]; mid = data[i + 1:i + 1 + n].decode(); i += 1 + n
    n = data[i]; name = data[i + 1:i + 1 + n].decode("utf-8"); i += 1 + n
    if i != len(data):
        raise ValueError("Bad token length")
    return {"module_id": mid, "fingerprint16": fp, "licensee": name}


def make_token(private_key, module_id, fingerprint, licensee=""):
    """KEYGEN SIDE (needs the private key). Returns the token text."""
    payload = encode_payload(module_id, fingerprint, licensee)
    blob = payload + ed.sign(private_key, payload)
    b32 = base64.b32encode(blob).decode().rstrip("=")
    groups = [b32[i:i + 5] for i in range(0, len(b32), 5)]
    return module_id.upper() + "." + "-".join(groups)


def _from_text(token):
    token = "".join(token.split())
    if "." not in token:
        raise ValueError("Not a token")
    prefix, rest = token.split(".", 1)
    b32 = rest.replace("-", "").upper()
    b32 += "=" * (-len(b32) % 8)
    blob = base64.b32decode(b32)
    if len(blob) < 64 + 3:
        raise ValueError("Not a token")
    return prefix.lower(), blob[:-64], blob[-64:]


def verify_token(public_key_hex, token, fingerprint):
    """APP SIDE. Returns decoded info dict if the token is valid AND bound to
    this machine, else None. Needs only the public key — works offline."""
    if not public_key_hex or not token:
        return None
    try:
        prefix, payload, sig = _from_text(token)
        if not ed.verify(bytes.fromhex(public_key_hex), payload, sig):
            return None
        info = decode_payload(payload)
    except (ValueError, IndexError, struct.error):
        return None
    if info["module_id"] != prefix:
        return None
    # Must be bound to THIS machine.
    if info["fingerprint16"] != _fp_bytes(fingerprint).hex():
        return None
    return info
