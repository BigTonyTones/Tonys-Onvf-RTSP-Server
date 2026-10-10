import os
import socket
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


def make_camera(**overrides):
    """A VirtualONVIFCamera built from a config dict like the saved JSON."""
    from app.camera import VirtualONVIFCamera
    cfg = {
        'id': 1,
        'name': 'Front Door',
        'mainStreamUrl': 'rtsp://admin:pw@10.0.0.50:554/stream1',
        'subStreamUrl': 'rtsp://admin:pw@10.0.0.50:554/stream2',
        'pathName': 'front_door',
        'username': 'admin',
        'password': 'pw',
    }
    cfg.update(overrides)
    return VirtualONVIFCamera(cfg)


@pytest.fixture
def camera_factory():
    return make_camera
