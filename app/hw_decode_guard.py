#!/usr/bin/env python3
"""
GPU-decode safety net (issue #73).

MediaMTX starts this small launcher instead of FFmpeg when "Also decode camera
streams on the GPU" is on. It runs the GPU-decoding FFmpeg command and watches
its error output. If the GPU decoder fails (for example an HEVC stream the VA
driver cannot decode), it switches that one stream to the same command with CPU
decoding, so the stream keeps working. GPU encoding stays on either way.

Usage: hw_decode_guard.py <commands.json> <key>
Linux / macOS only. Standalone on purpose: no imports from the app package.
"""
import json
import os
import shlex
import signal
import subprocess
import sys
import time

# Messages FFmpeg prints when a hardware decoder (VAAPI / NVDEC / QSV) breaks.
HW_FAIL_MARKERS = (
    b'hardware accelerator failed to decode picture',
    b'Failed to end picture decode',
    b'Failed to transfer data to output frame',
    b'Failed to sync surface',
    b'hwaccel initialisation returned error',
    b'Failed setup for format vaapi',
    b'Failed setup for format cuda',
    b'Failed setup for format qsv',
    b'No decoder surfaces left',
)
FAILS_BEFORE_FALLBACK = 2
RESTART_DELAY = 2.0

_child = None
_stopping = False


def _log(msg):
    sys.stderr.write(f'[hw-decode-guard] {msg}\n')
    sys.stderr.flush()


def _stop(signum, _frame):
    global _stopping
    _stopping = True
    if _child and _child.poll() is None:
        try:
            _child.send_signal(signal.SIGINT)
        except Exception:
            pass


def _die_with_parent():
    """Linux: have the kernel kill FFmpeg if this launcher is killed outright."""
    try:
        import ctypes
        ctypes.CDLL('libc.so.6', use_errno=True).prctl(1, signal.SIGKILL)  # PR_SET_PDEATHSIG
    except Exception:
        pass


def _run(cmd):
    """Run one FFmpeg command, pass its output through. Returns (exit code, hw_failed)."""
    global _child
    hw_failed = False
    _child = subprocess.Popen(shlex.split(cmd), stdin=subprocess.DEVNULL,
                              stderr=subprocess.PIPE, preexec_fn=_die_with_parent)
    out = getattr(sys.stderr, 'buffer', None)
    tail = b''
    fd = _child.stderr.fileno()
    while True:
        try:
            chunk = os.read(fd, 8192)
        except InterruptedError:
            continue
        except OSError:
            break
        if not chunk:
            break
        if out:
            try:
                out.write(chunk)
                out.flush()
            except Exception:
                pass
        if not hw_failed:
            window = tail + chunk
            if any(m in window for m in HW_FAIL_MARKERS):
                hw_failed = True
            tail = window[-200:]
    code = _child.wait()
    return code, hw_failed


def main():
    if len(sys.argv) != 3:
        _log('usage: hw_decode_guard.py <commands.json> <key>')
        return 2
    try:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            entry = json.load(f)[sys.argv[2]]
        primary, fallback = entry['primary'], entry['fallback']
        name = entry.get('name') or sys.argv[2]
    except Exception as e:
        _log(f'cannot load command for {sys.argv[2]}: {e}')
        return 2

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    use_fallback = False
    hw_fails = 0
    while not _stopping:
        try:
            code, hw_failed = _run(fallback if use_fallback else primary)
        except Exception as e:
            _log(f'{name}: could not start FFmpeg: {e}')
            return 1
        if _stopping:
            break
        if not use_fallback and hw_failed:
            hw_fails += 1
            if hw_fails >= FAILS_BEFORE_FALLBACK:
                use_fallback = True
                _log(f'{name}: GPU decoding failed {hw_fails} times. Switching this stream to '
                     f'CPU decoding (GPU encoding stays on) until the server restarts.')
            else:
                _log(f'{name}: GPU decoding failed, retrying once before falling back to CPU decoding.')
        time.sleep(RESTART_DELAY)

    if _child and _child.poll() is None:
        try:
            _child.wait(timeout=3)
        except Exception:
            try:
                _child.kill()
            except Exception:
                pass
    return 0


if __name__ == '__main__':
    sys.exit(main())
