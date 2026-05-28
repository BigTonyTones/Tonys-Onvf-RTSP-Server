"""CoreML model export and caching for Apple Neural Engine inference.

On Apple Silicon, YOLO models can be exported to CoreML format (.mlpackage)
which runs on the Apple Neural Engine for 5-10x faster inference at lower
power than MPS/GPU. Exported models are cached to avoid re-export on restart.
"""

import hashlib
import os
import time

_HASH_BYTES = 64 * 1024
_SKIP_TTL = 3600


def _source_hash(model_path):
    """Fast partial hash of the source .pt file for staleness detection."""
    try:
        h = hashlib.sha256()
        with open(model_path, "rb") as f:
            h.update(f.read(_HASH_BYTES))
        return h.hexdigest()
    except Exception:
        return None


def _meta_path(cache_dir, base, suffix):
    """Return path for a sidecar metadata file alongside the .mlpackage."""
    return os.path.join(cache_dir, base + suffix)


def _is_cache_valid(cache_dir, base, source_model_path):
    """Check that a cached CoreML model is complete and not stale."""
    sentinel = _meta_path(cache_dir, base, ".sentinel")
    mlpackage = os.path.join(cache_dir, base + ".mlpackage")

    if not os.path.isfile(sentinel):
        return False
    if not os.path.isdir(mlpackage) or not os.listdir(mlpackage):
        return False

    if os.path.isfile(source_model_path):
        hash_file = _meta_path(cache_dir, base, ".hash")
        if os.path.isfile(hash_file):
            current_hash = _source_hash(source_model_path)
            if current_hash is not None:
                with open(hash_file) as f:
                    cached_hash = f.read().strip()
                if cached_hash != current_hash:
                    return False
            # current_hash is None (read error) — treat as valid, can't verify
    return True


def _should_skip_export(cache_dir, base):
    """Check if a recent export failure marker exists (avoids retry storms)."""
    skip_file = _meta_path(cache_dir, base, ".skip")
    if os.path.isfile(skip_file):
        try:
            age = time.time() - os.path.getmtime(skip_file)
            if age < _SKIP_TTL:
                return True
        except Exception:
            pass
    return False


def _write_skip_marker(cache_dir, base):
    """Write a marker to suppress export retries for _SKIP_TTL seconds."""
    try:
        os.makedirs(cache_dir, exist_ok=True)
        skip_file = _meta_path(cache_dir, base, ".skip")
        with open(skip_file, "w") as f:
            f.write("skip")
    except Exception:
        pass


def get_coreml_model_path(model_name, root_dir):
    """Return cached CoreML model path, or export and cache it.

    Returns the path to the cached .mlpackage on success, None on failure.
    Requires coremltools to be installed for the initial export.
    """
    cache_dir = os.path.join(root_dir, ".coreml_cache")
    base = os.path.splitext(os.path.basename(model_name))[0]
    mlpackage = os.path.join(cache_dir, base + ".mlpackage")

    if _is_cache_valid(cache_dir, base, model_name):
        print(f"  [AI] Using cached CoreML model: {mlpackage}")
        return mlpackage

    for suffix in (".sentinel", ".hash"):
        p = _meta_path(cache_dir, base, suffix)
        if os.path.isfile(p):
            os.remove(p)
    if os.path.exists(mlpackage):
        import shutil
        print(f"  [AI] Removing stale/incomplete CoreML cache: {mlpackage}")
        shutil.rmtree(mlpackage, ignore_errors=True)

    if _should_skip_export(cache_dir, base):
        return None

    try:
        from ultralytics import YOLO
        import shutil
        os.makedirs(cache_dir, exist_ok=True)
        print(f"  [AI] Exporting {model_name} to CoreML (first-run only, may take 30-60s)...")
        tmp_model = YOLO(model_name)
        exported_path = tmp_model.export(format="coreml", imgsz=640, nms=True)
        if exported_path and os.path.exists(exported_path):
            if os.path.exists(mlpackage):
                shutil.rmtree(mlpackage, ignore_errors=True)
            shutil.move(exported_path, mlpackage)
            with open(_meta_path(cache_dir, base, ".sentinel"), "w") as f:
                f.write("ok")
            src_hash = _source_hash(model_name)
            if src_hash:
                with open(_meta_path(cache_dir, base, ".hash"), "w") as f:
                    f.write(src_hash)
            print(f"  [AI] CoreML export cached at: {mlpackage}")
            return mlpackage
    except Exception as e:
        print(f"  [AI] CoreML export failed ({e}), will use standard model")
        if os.path.exists(mlpackage):
            import shutil
            shutil.rmtree(mlpackage, ignore_errors=True)
        for suffix in (".sentinel", ".hash"):
            p = _meta_path(cache_dir, base, suffix)
            if os.path.isfile(p):
                os.remove(p)
        _write_skip_marker(cache_dir, base)
    return None
