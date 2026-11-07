"""
Stable per-machine fingerprint for license binding.

Produces a short, stable id for THIS computer that we can:
  - send to Lemon Squeezy as the activation "instance name", and
  - bind our own offline license token to, so a copied token/folder
    won't work on a different machine.

No admin rights needed. Best-effort: combines several hardware/OS ids
and hashes them, so the stored value never exposes the raw ids.
"""
import hashlib
import platform
import subprocess
import uuid


def _run(cmd):
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=5)
        return out.decode(errors="ignore").strip()
    except Exception:
        return ""


def _windows_ids():
    ids = []
    # Windows MachineGuid — stable across reboots, unique per install.
    guid = _run('reg query "HKLM\\SOFTWARE\\Microsoft\\Cryptography" /v MachineGuid')
    for line in guid.splitlines():
        if "MachineGuid" in line:
            ids.append(line.split()[-1])
    # Machine UUID from the BIOS/board.
    uuid_out = _run("wmic csproduct get uuid")
    parts = [p.strip() for p in uuid_out.splitlines() if p.strip() and "UUID" not in p]
    if parts:
        ids.append(parts[0])
    return ids


def _linux_ids():
    ids = []
    for path in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
        try:
            with open(path) as f:
                ids.append(f.read().strip())
            break
        except Exception:
            pass
    return ids


def raw_components():
    system = platform.system()
    if system == "Windows":
        ids = _windows_ids()
    elif system == "Linux":
        ids = _linux_ids()
    else:  # macOS / other
        ids = [_run("ioreg -rd1 -c IOPlatformExpertDevice | awk -F'\"' '/IOPlatformUUID/{print $4}'")]
    ids = [i for i in ids if i]
    if not ids:
        # Fall back to the MAC-address-derived node id so we always return something.
        ids = [f"{uuid.getnode():012x}"]
    return ids


def fingerprint():
    """32-hex-char stable id for this machine."""
    joined = "|".join(raw_components()).lower()
    return hashlib.sha256(joined.encode()).hexdigest()[:32]


def short_code(fp=None):
    """Human-friendly code to read out for offline activation, e.g. 7Q3F-8K2M-9XТ4."""
    fp = fp or fingerprint()
    import base64
    raw = bytes.fromhex(fp)[:10]
    b32 = base64.b32encode(raw).decode().rstrip("=")
    return "-".join(b32[i:i + 4] for i in range(0, len(b32), 4))


if __name__ == "__main__":
    fp = fingerprint()
    print("components:", raw_components())
    print("fingerprint:", fp)
    print("short code :", short_code(fp))
