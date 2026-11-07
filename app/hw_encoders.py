"""
Hardware video encoder selection for GridFusion (issue #73).

The old detection only looked at `ffmpeg -encoders`, which lists every encoder
FFmpeg was *built* with (Debian's FFmpeg lists QSV/NVENC even on machines with
no such GPU or drivers), so it often picked an encoder that could not run.

This module:
  * reads the user's choice (auto / software / vaapi / qsv / nvenc / amf /
    videotoolbox) from advanced_settings['ffmpeg'],
  * runs a short real test encode before using any hardware encoder,
  * returns everything the GridFusion command builder needs (encoder args,
    global args, per-input decode args and the GPU upload filter).
"""
import glob
import os
import platform
import subprocess
import threading

DEFAULT_VAAPI_DEVICE = '/dev/dri/renderD128'

# Encoder definitions. 'params' is appended after '-c:v <encoder>'.
ENCODERS = {
    'videotoolbox': {
        'name': 'Apple VideoToolbox', 'encoder': 'h264_videotoolbox',
        'params': '-realtime 1',
    },
    'nvenc': {
        'name': 'NVIDIA NVENC', 'encoder': 'h264_nvenc',
        'params': '-preset p4 -tune ll -rc vbr',
    },
    'vaapi': {
        'name': 'VAAPI (Intel / AMD on Linux)', 'encoder': 'h264_vaapi',
        # B-frames off for low latency; CBR keeps the -b:v/-maxrate budget.
        'params': '-rc_mode CBR -bf 0',
    },
    'qsv': {
        'name': 'Intel QSV', 'encoder': 'h264_qsv',
        'params': '-preset veryfast -look_ahead 0 -bf 0',
    },
    'amf': {
        'name': 'AMD AMF', 'encoder': 'h264_amf',
        'params': '-usage ultra_low_latency -quality speed',
    },
}

VALID_CHOICES = ('auto', 'software') + tuple(ENCODERS.keys())

_cache = {}
_cache_lock = threading.Lock()


def get_choice(ff_advanced):
    """User's encoder choice. Older configs only had the hardwareEncoding checkbox."""
    ff_advanced = ff_advanced or {}
    choice = str(ff_advanced.get('hardwareEncoder') or '').strip().lower()
    if choice in VALID_CHOICES:
        return choice
    return 'auto' if ff_advanced.get('hardwareEncoding') else 'software'


def find_vaapi_device(preferred=None):
    """Configured render node if it exists, else the first /dev/dri/renderD* found."""
    if platform.system().lower() != 'linux':
        return None
    if preferred and os.path.exists(preferred):
        return preferred
    nodes = sorted(glob.glob('/dev/dri/renderD*'))
    if nodes:
        return nodes[0]
    return None


def _listed_encoders(ffmpeg_exe):
    try:
        out = subprocess.run([ffmpeg_exe, '-hide_banner', '-encoders'],
                             capture_output=True, text=True, timeout=15).stdout
        return out or ''
    except Exception:
        return ''


def _explain(stderr, code):
    """Pick the line that names the real cause (FFmpeg's last line is usually a
    generic 'nothing was written' follow-on error) and add a plain hint."""
    lines = [l.strip() for l in (stderr or '').splitlines() if l.strip()]
    generic = ('Nothing was written', 'Error initializing output', 'Conversion failed',
               'Error while opening encoder', 'Error parsing global options',
               'Terminating thread', 'Could not open encoder before EOF',
               'Error sending frames', 'Task finished with error')
    specific = [l for l in lines if not any(g in l for g in generic)]
    msg = (specific[0] if specific else (lines[-1] if lines else f'exit code {code}'))[:200]
    low = (stderr or '').lower()
    if 'libcuda' in low or 'cuda' in low and 'cannot load' in low:
        hint = 'no NVIDIA GPU/driver on this machine'
    elif 'libmfx' in low or 'mfx' in low or 'libvpl' in low or 'qsv' in low and 'init' in low:
        hint = 'Intel QSV runtime/driver not installed'
    elif 'vaapi' in low or 'va_' in low or 'libva' in low or 'input/output error' in low:
        hint = 'render device found but no working VA driver for it (try `vainfo`)'
    else:
        hint = ''
    return f'{hint}: {msg}' if hint else msg


def _test_cmd(ffmpeg_exe, kind, vaapi_device):
    enc = ENCODERS[kind]['encoder']
    cmd = [ffmpeg_exe, '-hide_banner', '-loglevel', 'error', '-nostdin']
    if kind == 'vaapi':
        cmd += ['-vaapi_device', vaapi_device]
    cmd += ['-f', 'lavfi', '-i', 'testsrc2=size=640x360:rate=15', '-frames:v', '15']
    if kind == 'vaapi':
        cmd += ['-vf', 'format=nv12,hwupload']
    elif kind == 'qsv':
        cmd += ['-vf', 'format=nv12']
    cmd += ['-c:v', enc, '-f', 'null', '-']
    return cmd


def test_encoder(ffmpeg_exe, kind, vaapi_device=None, use_cache=True):
    """Run a 1-second test encode. Returns (ok, message)."""
    if kind not in ENCODERS:
        return False, 'unknown encoder'
    if kind == 'vaapi':
        vaapi_device = find_vaapi_device(vaapi_device or DEFAULT_VAAPI_DEVICE)
        if not vaapi_device:
            return False, 'no /dev/dri render device (pass /dev/dri into the container)'
    key = (ffmpeg_exe, kind, vaapi_device)
    if use_cache:
        with _cache_lock:
            if key in _cache:
                return _cache[key]
    if ENCODERS[kind]['encoder'] not in _listed_encoders(ffmpeg_exe):
        result = (False, 'this FFmpeg build has no ' + ENCODERS[kind]['encoder'])
    else:
        try:
            p = subprocess.run(_test_cmd(ffmpeg_exe, kind, vaapi_device),
                               capture_output=True, text=True, timeout=20)
            if p.returncode == 0:
                result = (True, 'OK' + (f' ({vaapi_device})' if kind == 'vaapi' else ''))
            else:
                result = (False, _explain(p.stderr, p.returncode))
        except subprocess.TimeoutExpired:
            result = (False, 'test encode timed out')
        except Exception as e:
            result = (False, str(e)[:200])
    with _cache_lock:
        _cache[key] = result
    return result


def auto_order():
    system = platform.system().lower()
    if system == 'darwin':
        return ['videotoolbox']
    if system == 'windows':
        return ['nvenc', 'qsv', 'amf']
    return ['nvenc', 'vaapi', 'qsv']


def probe_all(ffmpeg_exe, vaapi_device=None):
    """Fresh test of every encoder relevant to this OS (for the Settings 'Test' button)."""
    kinds = auto_order()
    results = []
    for kind in kinds:
        ok, msg = test_encoder(ffmpeg_exe, kind, vaapi_device, use_cache=False)
        results.append({'id': kind, 'name': ENCODERS[kind]['name'], 'ok': ok, 'message': msg})
    return results


def resolve(ffmpeg_exe, ff_advanced, log=print):
    """
    Decide which encoder GridFusion uses. Returns a dict:
      kind, name, encoder_args, global_args, input_args, upload_filter
    kind == 'software' means libx264.
    """
    ff_advanced = ff_advanced or {}
    choice = get_choice(ff_advanced)
    vaapi_pref = (ff_advanced.get('vaapiDevice') or DEFAULT_VAAPI_DEVICE).strip()
    hw_decode = bool(ff_advanced.get('hwDecode', False))

    software = {
        'kind': 'software', 'name': 'Software (libx264)',
        'encoder_args': '-c:v libx264 -preset ultrafast -tune zerolatency',
        'global_args': '', 'input_args': '', 'upload_filter': '',
        'hw_decode': False,
    }
    if choice == 'software':
        return software

    candidates = auto_order() if choice == 'auto' else [choice]
    for kind in candidates:
        ok, msg = test_encoder(ffmpeg_exe, kind, vaapi_pref)
        if not ok:
            log(f"      Hardware encoder {ENCODERS[kind]['name']} not usable: {msg}")
            continue
        info = ENCODERS[kind]
        out = {
            'kind': kind, 'name': info['name'],
            'encoder_args': f"-c:v {info['encoder']} {info['params']}",
            'global_args': '', 'input_args': '', 'upload_filter': '',
            'hw_decode': False,
        }
        if kind == 'vaapi':
            dev = find_vaapi_device(vaapi_pref)
            out['name'] = f"{info['name']} on {dev}"
            out['global_args'] = f'-vaapi_device {dev}'
            # Frames are composited (crop/scale/xstack) in system memory, then
            # uploaded to the GPU for encoding.
            out['upload_filter'] = 'format=nv12,hwupload'
            if hw_decode:
                # Decode on the GPU; frames are downloaded automatically so the
                # existing CPU crop/scale/stack filters keep working.
                # -err_detect ignore_err + -skip_frame nokey_at_start tolerate
                # mid-GOP RTSP connections (missing POC reference frames before
                # the first IDR keyframe) that otherwise cause VAAPI HEVC
                # decoding to fail with VA_STATUS_ERROR_DECODING_ERROR (23) / EIO.
                out['input_args'] = f'-hwaccel vaapi -hwaccel_device {dev} -err_detect ignore_err'
                out['hw_decode'] = True
        elif kind == 'qsv':
            out['upload_filter'] = 'format=nv12'
            if hw_decode:
                out['input_args'] = '-hwaccel qsv -err_detect ignore_err'
                out['hw_decode'] = True
        elif kind == 'nvenc' and hw_decode:
            out['input_args'] = '-hwaccel cuda -err_detect ignore_err'
            out['hw_decode'] = True
        elif kind == 'videotoolbox' and hw_decode:
            out['input_args'] = '-hwaccel videotoolbox'
            out['hw_decode'] = True
        return out

    if choice != 'auto':
        log(f"      Selected hardware encoder '{choice}' failed its test. Falling back to software.")
    else:
        log("      No working hardware encoder found. Falling back to software.")
    return software


# ---------------------------------------------------------------------------
# Missing driver report + one-click install (Linux, apt-based systems only)
# ---------------------------------------------------------------------------
_GPU_VENDORS = {
    '0x8086': 'intel', '0x1002': 'amd', '0x1022': 'amd', '0x10de': 'nvidia',
    '0x1af4': 'virtual', '0x1234': 'virtual', '0x15ad': 'virtual', '0x1b36': 'virtual',
    '0x80ee': 'virtual', '0x1414': 'virtual',
}
_VENDOR_NAMES = {'intel': 'Intel', 'amd': 'AMD', 'nvidia': 'NVIDIA', 'virtual': 'virtual (VM)'}

# Only these packages can ever be installed from the web UI.
INSTALLABLE = {
    'vainfo', 'intel-media-va-driver', 'intel-media-va-driver-non-free',
    'i965-va-driver', 'i965-va-driver-shaders', 'mesa-va-drivers',
    'libvpl2', 'libmfx-gen1.2', 'libmfx-gen1',
}


def detect_gpus():
    """Vendors of the GPUs Linux sees, from /sys/class/drm (no lspci needed)."""
    found = []
    for path in sorted(glob.glob('/sys/class/drm/card[0-9]*/device/vendor')):
        try:
            vid = open(path).read().strip().lower()
        except Exception:
            continue
        v = _GPU_VENDORS.get(vid, 'other')
        if v not in found:
            found.append(v)
    return found


def _pkg_installed(pkg):
    try:
        p = subprocess.run(['dpkg-query', '-W', '-f=${Status}', pkg],
                           capture_output=True, text=True, timeout=10)
        return 'install ok installed' in (p.stdout or '')
    except Exception:
        return False


def _pkg_available(pkg):
    try:
        p = subprocess.run(['apt-cache', 'policy', pkg], capture_output=True, text=True, timeout=15)
        for line in (p.stdout or '').splitlines():
            if line.strip().startswith('Candidate:'):
                return '(none)' not in line
    except Exception:
        pass
    return False


def diagnose(results):
    """
    Explain why hardware encoders failed and which packages would fix it.
    Returns {gpus, notes[], missing[], can_install, install_note}.
    """
    report = {'gpus': [], 'notes': [], 'missing': [], 'can_install': False, 'install_note': ''}
    if platform.system().lower() != 'linux':
        return report
    working = {r['id'] for r in results if r.get('ok')}
    gpus = detect_gpus()
    report['gpus'] = [_VENDOR_NAMES.get(g, 'unknown') for g in gpus]
    in_docker = os.path.exists('/.dockerenv')
    has_apt = bool(subprocess.run(['sh', '-c', 'command -v apt-get'], capture_output=True).stdout.strip())

    if not gpus:
        if in_docker:
            report['notes'].append('No GPU is visible inside the container. Add "devices: - /dev/dri:/dev/dri" to docker-compose.yml and recreate the container.')
        else:
            report['notes'].append('No GPU was found on this machine, so only software encoding is possible.')
        return report
    if gpus == ['virtual']:
        report['notes'].append('Only a virtual (VM) graphics adapter was found. It cannot encode video; pass the real GPU through to the VM to use hardware encoding.')
        return report
    if 'nvidia' in gpus and 'nvenc' not in working:
        report['notes'].append('An NVIDIA GPU was found but NVENC does not work. Install the NVIDIA driver on the host (and the NVIDIA container toolkit for Docker); this is not installed automatically.')

    want = []
    if ('intel' in gpus or 'amd' in gpus) and 'vaapi' not in working:
        want.append('vainfo')
        if 'intel' in gpus:
            want += ['intel-media-va-driver', 'i965-va-driver']
        if 'amd' in gpus:
            want.append('mesa-va-drivers')
    if 'intel' in gpus and 'qsv' not in working:
        want += ['intel-media-va-driver', 'libvpl2', 'libmfx-gen1.2']

    seen = []
    for pkg in want:
        if pkg not in seen:
            seen.append(pkg)
    missing = [p for p in seen if not _pkg_installed(p)] if has_apt else seen
    if has_apt:
        # Older/newer distros name the QSV runtime differently; skip ones apt doesn't have.
        missing = [p for p in missing if _pkg_available(p) or p not in ('libmfx-gen1.2', 'libvpl2')]
    report['missing'] = missing

    if missing:
        if not has_apt:
            report['install_note'] = 'Automatic install needs an apt-based system (Debian/Ubuntu). Install these with your package manager.'
        elif hasattr(os, 'geteuid') and os.geteuid() != 0:
            report['install_note'] = 'The server is not running as root, so it cannot install packages. Run: sudo apt install ' + ' '.join(missing)
        else:
            report['can_install'] = True
            if in_docker:
                report['install_note'] = 'Running in Docker: packages installed here are lost when the container is recreated. Rebuild the image to keep them.'
    elif ('intel' in gpus or 'amd' in gpus) and 'vaapi' not in working:
        report['notes'].append('The VA driver packages are installed but VAAPI still fails. The GPU may be too old for H.264 encoding, or the driver does not support it. Run "vainfo" to check.')
    return report


_install_state = {'running': False, 'done': False, 'ok': None, 'log': '', 'packages': []}
_install_lock = threading.Lock()


def install_status():
    with _install_lock:
        return dict(_install_state)


def start_install(packages):
    """Install whitelisted packages with apt-get in a background thread."""
    pkgs = [p for p in packages if p in INSTALLABLE]
    if not pkgs:
        return False, 'No installable packages requested'
    with _install_lock:
        if _install_state['running']:
            return False, 'An install is already running'
        _install_state.update(running=True, done=False, ok=None, log='', packages=pkgs)

    def _run():
        env = dict(os.environ, DEBIAN_FRONTEND='noninteractive')
        log = []
        ok = False
        try:
            for cmd in (['apt-get', 'update'],
                        ['apt-get', 'install', '-y', '--no-install-recommends'] + pkgs):
                log.append('$ ' + ' '.join(cmd))
                p = subprocess.run(cmd, capture_output=True, text=True, timeout=900, env=env)
                log.append(((p.stdout or '') + (p.stderr or '')).strip()[-3000:])
                if p.returncode != 0 and cmd[1] == 'install':
                    break
            else:
                ok = True
        except Exception as e:
            log.append(f'Install failed: {e}')
        with _cache_lock:
            _cache.clear()  # re-test encoders with the new drivers
        with _install_lock:
            _install_state.update(running=False, done=True, ok=ok, log='\n'.join(log)[-6000:])

    threading.Thread(target=_run, daemon=True).start()
    return True, 'started'
