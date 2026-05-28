"""AI device selection and shared model cache for local inference.

Selects the best available compute device (NVIDIA CUDA, Apple Silicon MPS, or CPU)
and manages a thread-safe cache of loaded YOLO models. On Apple Silicon,
MPS uses unified memory so there is no CPU↔GPU copy overhead.
"""

import threading

_AI_MODELS = {}
_AI_MODEL_LOCK = threading.Lock()
AI_INFERENCE_LOCK = threading.Lock()


def select_device():
    """Return the best available PyTorch device string for inference.

    Prefers 'cuda' on NVIDIA GPUs, 'mps' (Metal Performance Shaders) on Apple Silicon,
    falls back to 'cpu' everywhere else.
    """
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    return "cpu"


def get_shared_model(model_name):
    """Load (or return cached) YOLO model on the best available device.

    Thread-safe: multiple cameras share a single model instance per
    model_name, avoiding redundant memory usage.
    """
    global _AI_MODELS
    with _AI_MODEL_LOCK:
        if model_name not in _AI_MODELS:
            from ultralytics import YOLO
            try:
                import torch
                import os as _os
                _cpu_count = _os.cpu_count()
                _env_threads = _os.environ.get("AI_TORCH_THREADS")
                if _env_threads is not None:
                    try:
                        _thread_count = max(1, int(_env_threads))
                    except ValueError:
                        print(f"  [AI] Warning: AI_TORCH_THREADS={_env_threads!r} is not a valid integer, using default")
                        _thread_count = min(4, max(1, (_cpu_count or 2) // 2))
                else:
                    _thread_count = min(4, max(1, (_cpu_count or 2) // 2))
                torch.set_num_threads(_thread_count)
                print(f"  [AI] PyTorch using {_thread_count} threads (cpu_count={_cpu_count})")
            except Exception:
                pass
            device = select_device()
            is_apple = (device == "mps")

            # CoreML export (first-run) can take 30-60s while holding _AI_MODEL_LOCK.
            # Moving it outside the lock would risk two threads exporting simultaneously.
            # The skip marker in coreml_cache limits this to one slow startup per model.
            loaded = False
            if is_apple:
                from .coreml_cache import get_coreml_model_path
                from .config import ROOT_DIR
                coreml_path = get_coreml_model_path(model_name, ROOT_DIR)
                if coreml_path:
                    try:
                        model = YOLO(coreml_path)
                        _AI_MODELS[model_name] = model
                        print(f"  [AI] Loaded {model_name} via CoreML (Apple Neural Engine)")
                        loaded = True
                    except Exception as e:
                        print(f"  [AI] CoreML model load failed ({e}), falling back")

            if not loaded:
                model = YOLO(model_name)
                try:
                    model.to(device)
                except Exception as e:
                    if device != "cpu":
                        print(f"  [AI] Warning: {device} failed ({e}), falling back to CPU")
                        device = "cpu"
                        model.to(device)
                    else:
                        raise
                _AI_MODELS[model_name] = model
                print(f"  [AI] Loaded {model_name} on device: {device}")
        return _AI_MODELS[model_name]


def clear_models():
    """Clear the model cache. Intended for testing."""
    global _AI_MODELS
    with _AI_MODEL_LOCK:
        _AI_MODELS.clear()
