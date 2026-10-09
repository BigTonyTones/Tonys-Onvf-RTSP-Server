"""Credentials never reach logs, MediaMTX output capture or API error strings."""
import sys
import textwrap

from app import stream_source as ss
from app.ffmpeg_manager import FFmpegManager
from app.mediamtx_manager import MediaMTXManager
from app.utils import Logger

SECRET_URL = 'rtsps://alex:Wyze%21Pass%40123@10.0.0.124:322/stream0'


def test_app_logger_redacts_urls(capsys):
    log = Logger()
    log.write(f"Probing stream: {SECRET_URL}\n")
    text = log.get_logs()
    assert 'Wyze' not in text and 'alex:' not in text
    assert 'rtsps://***@10.0.0.124:322/stream0' in text
    assert 'Wyze' not in capsys.readouterr().out


def test_mediamtx_output_is_redacted_and_path_errors_recorded(capsys):
    m = MediaMTXManager()
    m._handle_output_line(f"2026/10/09 22:14:48 ERR [path alex_room_main] [RTSP source] "
                          f"{SECRET_URL}: bad status code: 401 (Unauthorized)\n")
    out = capsys.readouterr().out
    assert 'Wyze' not in out and 'Wyze' not in ' '.join(m.log_buffer)
    ev = m.get_path_event('alex_room_main')
    assert '401' in ev['error'] and 'Wyze' not in ev['error']


def test_repeated_source_errors_are_throttled(capsys):
    m = MediaMTXManager()
    line = "2026/10/09 22:14:48 ERR [path cam_main] [RTSP source] dial tcp 10.0.0.124:322: connect: connection refused\n"
    for _ in range(5):
        m._handle_output_line(line)
    assert capsys.readouterr().out.count('connection refused') == 1


def test_ffprobe_errors_are_redacted(tmp_path, monkeypatch):
    fake = tmp_path / 'ffprobe'
    fake.write_text(textwrap.dedent(f'''\
        #!{sys.executable}
        import sys
        sys.stderr.write(sys.argv[-1] + ": Server returned 401 Unauthorized\\n")
        sys.exit(1)
    '''))
    fake.chmod(0o755)
    monkeypatch.setattr(FFmpegManager, 'get_ffprobe_path', lambda self: str(fake))
    errors = []
    assert FFmpegManager().probe_stream(SECRET_URL, errors=errors) is None
    assert errors and 'Wyze' not in errors[0] and '401' in errors[0]


def test_snapshot_errors_are_redacted(tmp_path, monkeypatch):
    fake = tmp_path / 'ffmpeg'
    fake.write_text(textwrap.dedent(f'''\
        #!{sys.executable}
        import sys
        url = sys.argv[sys.argv.index('-i') + 1]
        sys.stderr.write(url + ": Connection refused\\n")
        sys.exit(1)
    '''))
    fake.chmod(0o755)
    monkeypatch.setattr(FFmpegManager, 'get_ffmpeg_path', lambda self: str(fake))
    ok, err = FFmpegManager().capture_snapshot(SECRET_URL, str(tmp_path / 'x.jpg'))
    assert not ok and 'Wyze' not in err


def test_health_message_set_on_camera_is_redacted(camera_factory):
    cam = camera_factory()
    cam.set_health(ss.STATE_AUTH_FAILED, f"failed: {SECRET_URL}")
    assert 'Wyze' not in cam.to_dict()['streamHealth']['message']
