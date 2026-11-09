"""
Interface style switcher ("Refined" vs "Classic").

The Refined look is a pure presentation layer: every page is still rendered by
its original template, and this module only adds a stylesheet + a small layout
script to the HTML on the way out. Nothing is removed from any page, so every
button, modal and setting keeps working exactly as before.

The Refined look is now the only interface (Tony's choice, 2026-11-02).
To get the original UI back, run restore_classic_ui.bat (option 2), which
restores the backed-up web.py from backups/ui_before_redesign_2026-11-02.

"""

import json
import logging
import os
import re
from urllib.parse import quote

from flask import jsonify, request, redirect, send_from_directory

from .config import DATA_DIR

logger = logging.getLogger(__name__)

STYLES = ('refined', 'classic')
DEFAULT_STYLE = 'refined'
UI_STYLE_FILE = os.path.join(DATA_DIR, 'ui_style.json')
ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ui_refined')
ASSET_VERSION = '2.1.6'

# Pages that must never be touched (the separate Next.js build).
_SKIP_PREFIXES = ('/protect', '/ui/')

_cache = {'mtime': None, 'style': None}


def get_ui_style():
    # Tony chose the Refined interface as the only look (2026-11-02); the
    # Classic switch was removed. restore_classic_ui.bat option 2 still puts
    # the original files back if ever needed.
    return DEFAULT_STYLE


def set_ui_style(style):
    if style not in STYLES:
        raise ValueError(f"Unknown interface style: {style}")
    with open(UI_STYLE_FILE, 'w') as f:
        json.dump({'style': style}, f)
    _cache.update(mtime=None, style=None)
    return style


def _read_asset(name):
    try:
        with open(os.path.join(ASSET_DIR, name), 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Missing UI asset {name}: {e}")
        return ''


def inject_ui_style(html, style):
    """Add the interface-style assets to a rendered HTML page."""
    if not html or 'data-ui-style=' in html:
        return html
    lower = html.lower()
    if '</head>' not in lower or '<html' not in lower:
        return html

    v = ASSET_VERSION
    head = f'<meta name="ui-style" content="{style}">'
    if style == 'refined':
        head += f'<link rel="stylesheet" href="/ui/refined.css?v={v}">'
        try:
            from .version import CURRENT_VERSION
            head += f'<meta name="rf-app-version" content="{CURRENT_VERSION}">'
        except Exception:
            pass

    html = re.sub(r'</head>', head + '</head>', html, count=1, flags=re.IGNORECASE)
    html = re.sub(r'<html\b', f'<html data-ui-style="{style}"', html, count=1, flags=re.IGNORECASE)

    if style == 'refined':
        html = re.sub(r'<html\b([^>]*)>',
                      lambda m: '<html' + _add_class(m.group(1), 'ui-refined') + '>',
                      html, count=1, flags=re.IGNORECASE)
        # Layout script runs synchronously at the end of <body>, after the page's
        # own markup and scripts, so it can rearrange the existing elements.
        script = f'<script data-rf-layout="{v}">{_read_asset("refined.js")}</script>'
        idx = html.lower().rfind('</body>')
        html = html[:idx] + script + html[idx:] if idx != -1 else html + script
    return html


def _add_class(attrs, cls):
    m = re.search(r'class\s*=\s*"([^"]*)"', attrs)
    if m:
        return attrs[:m.start()] + f'class="{m.group(1)} {cls}"' + attrs[m.end():]
    return attrs + f' class="{cls}"'


def register_ui_style(app, login_required):
    """Wire the switcher into the Flask app (routes + response hook)."""

    @app.route('/ui/<path:filename>')
    def ui_style_asset(filename):
        resp = send_from_directory(ASSET_DIR, filename)
        resp.headers['Cache-Control'] = 'public, max-age=3600'
        return resp

    # Server and Settings open as pages inside the dashboard (Refined look).
    @app.route('/server')
    @login_required
    def ui_style_server_page():
        return redirect('/#server')

    @app.route('/settings')
    @login_required
    def ui_style_settings_page():
        return redirect('/#settings')

    @app.route('/about')
    @login_required
    def ui_style_about_page():
        return redirect('/#about')

    @app.route('/add-camera')
    @login_required
    def ui_style_add_camera_page():
        return redirect('/#add-camera')

    @app.route('/camera/<cam_id>')
    @login_required
    def ui_style_edit_camera_page(cam_id):
        return redirect('/#edit-' + quote(str(cam_id), safe=''))

    @app.route('/api/ui/server-details')
    @login_required
    def ui_style_server_details():
        try:
            limit = max(1, min(int(request.args.get('limit', 10)), 50))
        except ValueError:
            limit = 10
        return jsonify(server_details(limit))

    @app.route('/api/ui-style', methods=['GET'])
    def ui_style_get():
        return jsonify({'style': get_ui_style(), 'styles': list(STYLES)})

    @app.after_request
    def ui_style_inject(response):
        try:
            if (response.status_code != 200 or response.direct_passthrough
                    or response.is_streamed or response.mimetype != 'text/html'):
                return response
            if request.path.startswith(_SKIP_PREFIXES):
                return response
            html = response.get_data(as_text=True)
            new_html = inject_ui_style(html, get_ui_style())
            if new_html is not html:
                response.set_data(new_html)
        except Exception as e:
            logger.error(f"Interface style injection failed (page served unchanged): {e}")
        return response


# --- Server page details (memory + top processes) ---------------------------
_proc_cache = {}
_CRED_RE = re.compile(r'(://)[^/\s]*@')


def _mask(cmd):
    # Camera URLs on ffmpeg command lines carry passwords; never show them.
    return _CRED_RE.sub(r'\1***@', cmd)[:200]


def _meminfo_proc():
    """Fallback for Linux hosts without psutil."""
    info = {}
    with open('/proc/meminfo') as f:
        for line in f:
            k, v = line.split(':', 1)
            info[k] = int(v.strip().split()[0]) * 1024
    total = info.get('MemTotal', 0)
    avail = info.get('MemAvailable', info.get('MemFree', 0))
    cached = info.get('Cached', 0) + info.get('Buffers', 0) + info.get('SReclaimable', 0)
    return {
        'total': total, 'available': avail, 'used': total - avail,
        'cached': cached, 'free': info.get('MemFree', 0),
        'percent': round((total - avail) * 100.0 / total, 1) if total else 0,
        'swap_total': info.get('SwapTotal', 0),
        'swap_used': info.get('SwapTotal', 0) - info.get('SwapFree', 0),
    }


def _procs_proc(limit, total):
    page = os.sysconf('SC_PAGE_SIZE') if hasattr(os, 'sysconf') else 4096
    rows = []
    for pid in os.listdir('/proc'):
        if not pid.isdigit():
            continue
        try:
            with open(f'/proc/{pid}/statm') as f:
                rss = int(f.read().split()[1]) * page
            with open(f'/proc/{pid}/comm') as f:
                name = f.read().strip()
            try:
                with open(f'/proc/{pid}/cmdline', 'rb') as f:
                    cmd = _mask(f.read().replace(b'\0', b' ').decode('utf-8', 'replace').strip())
            except Exception:
                cmd = ''
            rows.append({'pid': int(pid), 'name': name, 'cmd': cmd, 'rss': rss,
                         'mem_percent': round(rss * 100.0 / total, 1) if total else 0, 'cpu_percent': None})
        except Exception:
            continue
    rows.sort(key=lambda r: r['rss'], reverse=True)
    return rows[:limit], len(rows)


def server_details(limit=10):
    try:
        import psutil
    except ImportError:
        psutil = None
    out = {'source': 'psutil' if psutil else 'proc'}
    try:
        if psutil:
            vm = psutil.virtual_memory()
            sw = psutil.swap_memory()
            out['memory'] = {
                'total': vm.total, 'available': vm.available, 'used': vm.total - vm.available,
                'cached': getattr(vm, 'cached', 0) + getattr(vm, 'buffers', 0), 'free': vm.free,
                'percent': vm.percent, 'swap_total': sw.total, 'swap_used': sw.used,
            }
            rows, seen = [], set()
            for p in psutil.process_iter(['pid', 'name', 'memory_info', 'cmdline']):
                try:
                    pid = p.info['pid']
                    seen.add(pid)
                    mi = p.info.get('memory_info')
                    if not mi:
                        continue
                    proc = _proc_cache.get(pid)
                    if proc is None or proc.pid != pid:
                        proc = _proc_cache[pid] = p
                    cpu = proc.cpu_percent(None)
                    cmd = _mask(' '.join(p.info.get('cmdline') or []))
                    rows.append({'pid': pid, 'name': p.info.get('name') or '?', 'cmd': cmd, 'rss': mi.rss,
                                 'mem_percent': round(mi.rss * 100.0 / vm.total, 1) if vm.total else 0,
                                 'cpu_percent': round(cpu, 1)})
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            for pid in list(_proc_cache):
                if pid not in seen:
                    _proc_cache.pop(pid, None)
            rows.sort(key=lambda r: r['rss'], reverse=True)
            out['process_count'] = len(rows)
            out['processes'] = rows[:limit]
        else:
            out['memory'] = _meminfo_proc()
            out['processes'], out['process_count'] = _procs_proc(limit, out['memory']['total'])
    except Exception as e:
        logger.error(f"Server details failed: {e}")
        out['error'] = str(e)
    return out
