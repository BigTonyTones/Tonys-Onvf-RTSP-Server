"""
Local license store — the piece that makes an activated addon run OFFLINE
FOREVER.

Two ways an addon becomes licensed on a machine:

  A) Online activation (normal customers): the app calls Lemon Squeezy once
     (ls_client.activate), then we save a record here bound to this machine's
     fingerprint. Every later start checks that record locally — no internet.

  B) Offline token (air-gapped machines): the customer gives us their machine
     short-code, we run the keygen to make an Ed25519-signed token, they paste
     it in. verify is cryptographic and purely local.

Records live in <data>/addons/licensing/<module_id>.json. A record is bound to
the machine fingerprint, so copying the folder to another PC fails the check.

Honest limit: an online record (A) is not itself signed by a secret, because
the app holds no secret — a determined attacker on the machine could forge one.
That's why the paid addons get compiled/obfuscated later; this module is the
logic, the compile step is the lock. Offline tokens (B) ARE signed and can't be
forged without the private key.
"""
import json
import os
import time

from . import offline_token

STATUS_ACTIVE = "active"
STATUS_NONE = "inactive"
STATUS_WRONG_MACHINE = "wrong_machine"


def _dir(data_dir):
    d = os.path.join(data_dir, "addons", "licensing")
    os.makedirs(d, exist_ok=True)
    return d


def _path(data_dir, module_id):
    return os.path.join(_dir(data_dir), f"{module_id}.json")


def load(data_dir, module_id):
    try:
        with open(_path(data_dir, module_id), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _save(data_dir, module_id, record):
    path = _path(data_dir, module_id)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)
    os.replace(tmp, path)


def save_online_activation(data_dir, module_id, fingerprint, license_key, ls_resp):
    """Persist a successful Lemon Squeezy activation, bound to this machine."""
    meta = ls_resp.get("meta") or {}
    inst = ls_resp.get("instance") or {}
    record = {
        "module_id": module_id,
        "source": "online",
        "fingerprint": fingerprint,
        "license_key": license_key.strip().upper(),
        "instance_id": inst.get("id"),
        "licensee": meta.get("customer_name") or "",
        "product_name": meta.get("product_name") or "",
        "activated_at": int(time.time()),
    }
    _save(data_dir, module_id, record)
    return record


def save_offline_token(data_dir, module_id, fingerprint, token, public_key_hex):
    """Verify an air-gapped token and, if valid for this machine, store it."""
    info = offline_token.verify_token(public_key_hex, token, fingerprint)
    if not info or info["module_id"] != module_id:
        return None
    record = {
        "module_id": module_id,
        "source": "offline_token",
        "fingerprint": fingerprint,
        "token": "".join(token.split()),
        "licensee": info["licensee"],
        "activated_at": int(time.time()),
    }
    _save(data_dir, module_id, record)
    return record


def status(data_dir, module_id, fingerprint, public_key_hex=None):
    """Local, offline licensing status for this addon on this machine."""
    rec = load(data_dir, module_id)
    if not rec or rec.get("module_id") != module_id:
        return STATUS_NONE
    if rec.get("fingerprint") != fingerprint:
        return STATUS_WRONG_MACHINE
    if rec.get("source") == "offline_token":
        # Re-verify the signature every time — cheap and strong.
        info = offline_token.verify_token(public_key_hex, rec.get("token", ""), fingerprint)
        return STATUS_ACTIVE if info else STATUS_NONE
    # Online record: trusted once activated, offline forever.
    return STATUS_ACTIVE


def is_active(data_dir, module_id, fingerprint, public_key_hex=None):
    return status(data_dir, module_id, fingerprint, public_key_hex) == STATUS_ACTIVE


def clear(data_dir, module_id):
    try:
        os.remove(_path(data_dir, module_id))
    except FileNotFoundError:
        pass
