"""
Lemon Squeezy License API client.

Talks to the public license endpoints (no store API key needed — the
customer's license key is the credential):

    POST https://api.lemonsqueezy.com/v1/licenses/activate
    POST https://api.lemonsqueezy.com/v1/licenses/validate
    POST https://api.lemonsqueezy.com/v1/licenses/deactivate

Used at activation time (online). After a successful activation the app
stores the result locally and runs offline from then on (see token.py).
"""
import json
import urllib.parse
import urllib.request

API_BASE = "https://api.lemonsqueezy.com/v1/licenses"
TIMEOUT = 15


class LSError(Exception):
    pass


def _post(path, fields):
    data = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(
        f"{API_BASE}/{path}",
        data=data,
        headers={"Accept": "application/json",
                 "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        # The license API returns JSON (with an "error" field) even on 4xx.
        try:
            return json.loads(e.read().decode())
        except Exception:
            raise LSError(f"HTTP {e.code} from Lemon Squeezy")
    except Exception as e:
        raise LSError(f"Could not reach Lemon Squeezy: {e}")


def activate(license_key, instance_name):
    """Activate a key on this machine. instance_name = our machine fingerprint.

    Returns the parsed response. Key fields:
      resp['activated']           -> bool
      resp['instance']['id']      -> store this; needed to validate/deactivate later
      resp['license_key']['status'], ['activation_limit'], ['activation_usage']
      resp['meta']['variant_id'], ['variant_name'], ['product_id'], ['customer_name']
      resp['error']               -> set when activation failed (e.g. limit reached)
    """
    return _post("activate", {"license_key": license_key.strip(),
                              "instance_name": instance_name})


def validate(license_key, instance_id=None):
    """Check a key (and optionally a specific activation instance) is still valid."""
    fields = {"license_key": license_key.strip()}
    if instance_id:
        fields["instance_id"] = instance_id
    return _post("validate", fields)


def deactivate(license_key, instance_id):
    """Release an activation (frees a machine slot, e.g. when moving PCs)."""
    return _post("deactivate", {"license_key": license_key.strip(),
                                "instance_id": instance_id})


# Map a Lemon Squeezy purchase to one of our addons.
# Exact variant-id overrides (most reliable); filled in as we learn them.
VARIANT_TO_MODULE = {
    "2338062": "advanced_ai",
    # <variant_id>: "<module_id>",  (others added as needed)
}

NAME_TO_MODULE = {
    "nvr pro": "nvr_pro",
    "advanced ai: lpr & facial recognition": "advanced_ai",
    "audio analytics & acoustic detection": "audio_analytics",
    "ptz auto-tracking & patrols": "ptz_tracking",
    "cloud backup & offsite sync": "cloud_backup",
    "multi-site central management (cms)": "cms_master",
    "apple homekit integration": "homekit",
    "advanced smart home bridge": "mqtt_bridge",
    "time-lapse generator": "timelapse",
    "ai people counter & business analytics": "people_counter",
    "people counter": "people_counter",
}


def module_for(resp):
    """Which addon does this license response belong to? -> module_id or None."""
    meta = resp.get("meta") or {}
    vid = str(meta.get("variant_id") or "")
    if vid in VARIANT_TO_MODULE:
        return VARIANT_TO_MODULE[vid]
    # Single-variant products report variant_name "Default", so match on the
    # product name (which equals the catalog name).
    name = (meta.get("product_name") or "").strip().lower()
    return NAME_TO_MODULE.get(name)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: python ls_client.py <license_key> [instance_name]")
        raise SystemExit(1)
    key = sys.argv[1]
    inst = sys.argv[2] if len(sys.argv) > 2 else "test-machine"
    print("validate:")
    print(json.dumps(validate(key), indent=2))
    print("\nactivate:")
    r = activate(key, inst)
    print(json.dumps(r, indent=2))
    print("\nmapped module:", module_for(r))
