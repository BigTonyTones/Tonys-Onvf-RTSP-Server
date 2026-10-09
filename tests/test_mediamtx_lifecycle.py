"""MediaMTX process ownership: no duplicate listeners, safe stale cleanup."""
import os
import socket
import subprocess
import sys
import textwrap
import threading
import time

import psutil
import pytest

from app import mediamtx_manager as mm
from app.ffmpeg_manager import FFmpegManager
from tests.conftest import free_port

FAKE = textwrap.dedent('''\
    #!{python}
    # Stand-in for the mediamtx binary: binds the RTSP and API ports from the
    # config file exactly like MediaMTX does, and fails the same way if taken.
    import re, socket, sys, time, signal
    cfg = open(sys.argv[1]).read()
    socks = []
    for key in ('rtspAddress', 'apiAddress'):
        port = int(re.search(key + r":\\s*'?:(\\d+)", cfg).group(1))
        s = socket.socket()
        try:
            s.bind(('0.0.0.0', port))
        except OSError:
            print(f"ERR: listen tcp :{{port}}: bind: address already in use", flush=True)
            sys.exit(1)
        s.listen(5)
        socks.append(s)
    print("INF fake mediamtx ready", flush=True)
    signal.signal(signal.SIGTERM, lambda *a: sys.exit(0))
    while True:
        time.sleep(0.2)
''')


@pytest.fixture
def mgr(tmp_path, monkeypatch):
    exe = tmp_path / 'mediamtx'
    exe.write_text(FAKE.format(python=sys.executable))
    exe.chmod(0o755)
    monkeypatch.setattr(FFmpegManager, 'get_ffmpeg_path', lambda self: '/usr/bin/ffmpeg')
    api_port = free_port()
    monkeypatch.setattr(mm, 'MEDIAMTX_API_PORT', api_port)
    m = mm.MediaMTXManager()
    m.executable = str(exe)
    m.config_file = str(tmp_path / 'mediamtx.yml')
    monkeypatch.setattr(m, 'download_mediamtx', lambda: True)
    monkeypatch.setattr(mm.time, 'sleep', lambda s: time_sleep(min(s, 0.6)))
    m.rtsp_port = free_port()
    yield m
    m.stop()
    for p in m.find_owned_processes():
        p.kill()


time_sleep = time.sleep


def owned_alive(m):
    procs = list(m.find_owned_processes())
    if m.is_running():
        procs.append(psutil.Process(m.process.pid))
    return [p for p in procs if p.is_running() and p.status() != psutil.STATUS_ZOMBIE]


def test_start_writes_pid_file_and_stop_removes_it(mgr):
    assert mgr.start([], rtsp_port=mgr.rtsp_port)
    assert open(mgr.pid_file).read().strip() == str(mgr.process.pid)
    mgr.stop()
    assert not os.path.exists(mgr.pid_file)
    assert owned_alive(mgr) == []


def test_second_start_replaces_instead_of_duplicating(mgr):
    assert mgr.start([], rtsp_port=mgr.rtsp_port)
    first = mgr.process.pid
    assert mgr.start([], rtsp_port=mgr.rtsp_port)
    assert mgr.process.pid != first
    assert not psutil.pid_exists(first) or psutil.Process(first).status() == psutil.STATUS_ZOMBIE
    assert len(owned_alive(mgr)) == 1


def test_concurrent_restarts_leave_exactly_one_instance(mgr):
    assert mgr.start([], rtsp_port=mgr.rtsp_port)
    errors = []

    def restart():
        if not mgr.restart([], rtsp_port=mgr.rtsp_port):
            errors.append('restart failed')

    threads = [threading.Thread(target=restart) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(60)
    assert errors == []
    assert len(owned_alive(mgr)) == 1
    assert not any('address already in use' in l for l in mgr.log_buffer)


def test_stale_instance_from_previous_run_is_cleaned_up(mgr):
    # Simulate a crashed previous run: same binary + same config, not our child
    mgr.create_config([], rtsp_port=mgr.rtsp_port)
    stale = subprocess.Popen([os.path.abspath(mgr.executable), os.path.abspath(mgr.config_file)],
                             stdout=subprocess.DEVNULL, start_new_session=True)
    with open(mgr.pid_file, 'w') as f:
        f.write(str(stale.pid))
    time_sleep(0.5)
    assert mgr.start([], rtsp_port=mgr.rtsp_port)
    stale.wait(timeout=5)
    assert len(owned_alive(mgr)) == 1


def test_foreign_process_on_rtsp_port_is_not_killed(mgr):
    s = socket.socket()
    s.bind(('0.0.0.0', mgr.rtsp_port))
    s.listen(1)
    foreign = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
    try:
        assert mgr.start([], rtsp_port=mgr.rtsp_port) is False
        assert 'in use' in (mgr.last_start_error or '')
        assert foreign.poll() is None          # untouched
        assert owned_alive(mgr) == []
    finally:
        s.close()
        foreign.kill()


def test_unrelated_mediamtx_with_other_config_is_not_ours(mgr, tmp_path):
    other_cfg = tmp_path / 'other.yml'
    other_cfg.write_text(f"rtspAddress: :{free_port()}\napiAddress: :{free_port()}\n")
    other = subprocess.Popen([os.path.abspath(mgr.executable), str(other_cfg)], stdout=subprocess.DEVNULL)
    try:
        time_sleep(0.5)
        assert all(p.pid != other.pid for p in mgr.find_owned_processes())
        assert mgr.cleanup_stale_instances() == 0
        assert other.poll() is None
    finally:
        other.kill()


# ---- CameraManager restart coalescing ---------------------------------------

class _FakeMtx:
    def __init__(self):
        self.calls = 0
        self.active = 0
        self.max_active = 0
        self.lock = threading.Lock()

    def restart(self, cameras, **kw):
        with self.lock:
            self.calls += 1
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        time_sleep(0.3)
        with self.lock:
            self.active -= 1
        return True


def _fake_manager():
    from app.manager import CameraManager
    m = CameraManager.__new__(CameraManager)
    m._restart_state_lock = threading.Lock()
    m._restart_pending = False
    m._restart_worker = None
    m.mediamtx = _FakeMtx()
    m.cameras = []
    m.rtsp_port = 8554
    m.global_username = m.global_password = 'admin'
    m.rtsp_auth_enabled = False
    m.debug_mode = False
    m.advanced_settings = {}
    m.web_port = 5552
    m.grid_fusion_layouts = []
    m.grid_fusion_looks = []
    m.health_monitor = None

    class N:
        def send(self, *a, **k):
            pass
    m.notifier = N()
    return m


def test_burst_of_restart_requests_is_coalesced():
    m = _fake_manager()
    for _ in range(10):
        m.restart_mediamtx()
    m.restart_mediamtx(wait=True)
    assert 1 <= m.mediamtx.calls <= 3
    assert m.mediamtx.max_active == 1
