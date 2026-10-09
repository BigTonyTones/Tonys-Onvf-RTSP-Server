import os
import sys
import time
import platform
import subprocess
import requests
import yaml
import zipfile
import tarfile
import shlex
import secrets
import threading
import re
from pathlib import Path
from urllib.parse import quote
from .config import MEDIAMTX_PORT, MEDIAMTX_API_PORT, WEB_UI_PORT, DATA_DIR
from . import stream_source
from .ffmpeg_manager import insecure_tls_input_args

class MediaMTXManager:
    """Manages MediaMTX RTSP server"""
    
    def __init__(self):
        self.process = None
        self.config_file = os.path.join(DATA_DIR, "mediamtx.yml")
        self.executable = self._get_executable_name()
        self.log_buffer = [] # Store last 100 lines for debug
        self._log_lock = threading.Lock()
        self.debug_mode = False
        # Cache of probed source video codecs, keyed by stream URL -> (codec, expiry_ts).
        # Used to auto-transcode H.265/HEVC substreams to H.264 for browser playback.
        self._codec_cache = {}
        self._codec_cache_lock = threading.Lock()
        # Serialises start/stop/restart so only one MediaMTX instance exists.
        self._lifecycle_lock = threading.RLock()
        self.path_events = {}
        self.last_start_error = None
        
    def _get_executable_name(self):
        """Get the correct executable name for the platform"""
        system = platform.system().lower()
        if system == "windows":
            return "mediamtx.exe"
        return "mediamtx"
    
    def _get_latest_version(self):
        """Required minimum version of MediaMTX"""
        return "v1.18.2"

    REQUIRED_VERSION = "v1.18.2"

    def _parse_version(self, version_str):
        """Parse version string like 'v1.18.1' into a list of integers [1, 18, 1]"""
        try:
            # Remove 'v' prefix and split by '.'
            parts = version_str.lstrip('v').split('.')
            return [int(p) for p in parts]
        except:
            return [0, 0, 0]

    def _version_is_newer(self, current, latest):
        """Returns True if latest version is actually newer than current"""
        curr_parts = self._parse_version(current)
        late_parts = self._parse_version(latest)
        
        for i in range(max(len(curr_parts), len(late_parts))):
            curr = curr_parts[i] if i < len(curr_parts) else 0
            late = late_parts[i] if i < len(late_parts) else 0
            if late > curr: return True
            if late < curr: return False
        return False

    def download_mediamtx(self):
        """Download MediaMTX if not present or update if newer version available"""
        latest_version = self._get_latest_version()
        
        if Path(self.executable).exists():
            # Check current version
            try:
                exe_path = os.path.abspath(self.executable)
                import errno
                # Retry loop in case the text file is temporarily busy
                for attempt in range(5):
                    try:
                        result = subprocess.run([exe_path, "--version"],
                                               capture_output=True, text=True, check=False)
                        break
                    except OSError as e:
                        if e.errno == getattr(errno, 'ETXTBSY', 26) and attempt < 4:
                            time.sleep(0.2)
                            continue
                        raise
                
                current_version = result.stdout.strip()
                if current_version and not current_version.startswith('v'):
                    current_version = 'v' + current_version

                if current_version == latest_version:
                    print(f"MediaMTX is up to date ({current_version})")
                    return True
                elif self._version_is_newer(current_version, latest_version):
                    print(f"MediaMTX {current_version} is outdated. v1.18.2 is required for compatibility.")
                    print("Automatically upgrading MediaMTX...")
                    # Fall through to download
                else:
                    # Current version is newer than required — that's fine
                    print(f"MediaMTX {current_version} meets the v1.18.2 requirement.")
                    return True
            except Exception as e:
                print(f"Could not check MediaMTX version: {e}")
                return True
        else:
            print(f"MediaMTX not found. Downloading required version: {latest_version}")
        
        version = latest_version
        print(f"Installing MediaMTX {version}...")
        
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        # Determine download URL based on platform
        base_url = f"https://github.com/bluenviron/mediamtx/releases/download/{version}/"
        
        if system == "windows":
            if "64" in machine or "amd64" in machine or "x86_64" in machine:
                url = base_url + f"mediamtx_{version}_windows_amd64.zip"
                archive_name = f"mediamtx_{version}_windows_amd64.zip"
            else:
                print("Unsupported Windows architecture:", machine)
                return False
                
        elif system == "darwin":  # macOS
            if "arm" in machine or "aarch64" in machine:
                url = base_url + f"mediamtx_{version}_darwin_arm64.tar.gz"
                archive_name = f"mediamtx_{version}_darwin_arm64.tar.gz"
            else:
                url = base_url + f"mediamtx_{version}_darwin_amd64.tar.gz"
                archive_name = f"mediamtx_{version}_darwin_amd64.tar.gz"
                
        elif system == "linux" or True:  # Defaulting to linux logic for other unix
            if "aarch64" in machine or "arm64" in machine:
                url = base_url + f"mediamtx_{version}_linux_arm64.tar.gz"
                archive_name = f"mediamtx_{version}_linux_arm64.tar.gz"
            elif "arm" in machine:
                url = base_url + f"mediamtx_{version}_linux_armv7.tar.gz"
                archive_name = f"mediamtx_{version}_linux_armv7.tar.gz"
            elif "64" in machine or "x86_64" in machine or "amd64" in machine:
                url = base_url + f"mediamtx_{version}_linux_amd64.tar.gz"
                archive_name = f"mediamtx_{version}_linux_amd64.tar.gz"
            else:
                url = base_url + f"mediamtx_{version}_linux_386.tar.gz"
                archive_name = f"mediamtx_{version}_linux_386.tar.gz"
        else:
            print(f"Unsupported operating system: {system}")
            return False
        
        print(f"  Platform: {system} {machine}")
        print(f"  Downloading from: {url}")
        # Auto-download without prompting — v1.18.1 is a required dependency
        
        try:
            # Download with progress
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            downloaded = 0
            
            with open(archive_name, 'wb') as f:
                for chunk in response.iter_content(chunk_size=block_size):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r  Progress: {percent:.1f}%", end='', flush=True)
            
            print("\nDownloaded MediaMTX")
            
            # Extract
            print("  Extracting...")
            if archive_name.endswith('.zip'):
                with zipfile.ZipFile(archive_name, 'r') as zip_ref:
                    zip_ref.extractall('.')
            else:
                with tarfile.open(archive_name, 'r:gz') as tar_ref:
                    tar_ref.extractall('.')
            
            print("Extracted MediaMTX")
            
            # Make executable on Unix-like systems
            if system in ["darwin", "linux"]:
                os.chmod(self.executable, 0o755)
                print("Set executable permissions")
            
            # Cleanup archive
            os.remove(archive_name)
            
            # Verify extraction
            if not Path(self.executable).exists():
                print(f"Executable not found after extraction: {self.executable}")
                return False
            
            print(f"MediaMTX ready: {self.executable}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"Download failed: {e}")
            return False
        except Exception as e:
            print(f"Installation failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _get_source_codec(self, stream_url):
        """Return the source video codec (e.g. 'h264', 'hevc') for a stream URL,
        caching results so repeated config rebuilds don't re-probe every camera.

        Returns the lowercased codec string, or None if it could not be probed.
        Successful probes are cached for 10 minutes; failures for 30 seconds so a
        camera that comes online later is re-checked soon.
        """
        if not stream_url:
            return None
        now = time.time()
        with self._codec_cache_lock:
            cached = self._codec_cache.get(stream_url)
            if cached and cached[1] > now:
                return cached[0]
        try:
            from .ffmpeg_manager import FFmpegManager
            info = FFmpegManager().probe_stream(stream_url, timeout=8)
            codec = (info or {}).get('codec') or None
        except Exception:
            codec = None
        ttl = 600 if codec else 30
        with self._codec_cache_lock:
            self._codec_cache[stream_url] = (codec, now + ttl)
        return codec

    def create_config(self, cameras, rtsp_port=None, rtsp_username=None, rtsp_password=None, grid_fusion=None, debug_mode=False, advanced_settings=None, web_port=None):
        """Create MediaMTX configuration optimized for multiple cameras and viewers"""
        if rtsp_port is None:
            rtsp_port = MEDIAMTX_PORT
        if web_port is None:
            web_port = WEB_UI_PORT
        
        if debug_mode:
            print(f"DEBUG: create_config called (RTSP auth {'enabled' if rtsp_username and rtsp_password else 'disabled'})")
            
        system = platform.system().lower()

        config = {

            # ===== NETWORK SETTINGS =====
            'rtspAddress': f':{rtsp_port}',
            'rtpAddress': ':18000',
            'rtcpAddress': ':18001',
            'webrtcAddress': ':8889',
            'hlsAddress': ':8888',
            
            # ===== HLS SETTINGS - Optimized for multiple viewers =====
            'hlsAlwaysRemux': True,
            'hlsVariant': 'fmp4',  # LL-HLS (fMP4) handles multi-track/Opus better than mpegts
            'hlsSegmentCount': advanced_settings.get('mediamtx', {}).get('hlsSegmentCount', 10) if advanced_settings else 10,
            'hlsSegmentDuration': advanced_settings.get('mediamtx', {}).get('hlsSegmentDuration', '1s') if advanced_settings else '1s',
            'hlsPartDuration': advanced_settings.get('mediamtx', {}).get('hlsPartDuration', '200ms') if advanced_settings else '200ms',
            'hlsSegmentMaxSize': '50M',  # Max 50MB per segment
            'hlsAllowOrigins': ['*'],       # Allow CORS for web players
            'hlsEncryption': False,      # Clear text for local streaming
            
            # ===== API SETTINGS =====
            'api': True,
            'apiAddress': f':{MEDIAMTX_API_PORT}',
            
            # ===== AUTHENTICATION =====
            'authMethod': 'http',
            'authHTTPAddress': f'http://localhost:{web_port}/api/auth',
            
            # ===== PROTOCOL SETTINGS =====
            'rtspTransports': ['tcp'],  # TCP only for reliability
            
            # ===== PERFORMANCE TUNING =====
            # Timeout settings - prevent premature disconnects
            'readTimeout': advanced_settings.get('mediamtx', {}).get('readTimeout', '30s') if advanced_settings else '30s',
            'writeTimeout': advanced_settings.get('mediamtx', {}).get('writeTimeout', '30s') if advanced_settings else '30s',
            
            # Ensure timeouts are valid and not empty or zero
            # MediaMTX will crash if these are "0", "0s", or empty
        }
        
        # Sanitize timeouts
        for key in ['readTimeout', 'writeTimeout']:
            val = config.get(key)
            if not val or str(val).strip() in ['0', '0s', '']:
                config[key] = '30s'
            elif isinstance(val, (int, float)):
                # If it's a number, convert to string with 's' suffix
                config[key] = f"{int(val)}s"
            elif isinstance(val, str) and val.isdigit():
                 # If it's a digits-only string, add 's'
                 config[key] = f"{val}s"

        # Continue with other settings
        config.update({
            # Buffer and queue settings
            'writeQueueSize': advanced_settings.get('mediamtx', {}).get('writeQueueSize', 32768) if advanced_settings else 32768,
            'udpMaxPayloadSize': advanced_settings.get('mediamtx', {}).get('udpMaxPayloadSize', 1472) if advanced_settings else 1472,
            
            # ===== MEMORY MANAGEMENT =====
            # Reduce log verbosity to save CPU
            'logLevel': 'info' if debug_mode else 'error',  # Show more info if debug mode is on
            
            # ===== CONNECTION HANDLING =====
            'runOnConnect': '',
            'runOnConnectRestart': False,
            'runOnDisconnect': '',
            
            # ===== PATHS (CAMERAS) =====
            'paths': {}
        })
        
        # Find FFmpeg using the manager
        from .ffmpeg_manager import FFmpegManager
        ffmpeg_mgr = FFmpegManager()
        ffmpeg_exe = ffmpeg_mgr.get_ffmpeg_path()
        
        # Use absolute path for ffmpeg to ensure mediamtx finds it
        if os.path.exists(ffmpeg_exe):
            ffmpeg_exe = os.path.abspath(ffmpeg_exe)
            
            # Ensure execution permissions on Unix-like systems
            if system in ["linux", "darwin"]:
                try:
                    if not os.access(ffmpeg_exe, os.X_OK):
                        print(f"   Fixing permissions for FFmpeg: {ffmpeg_exe}")
                except Exception as e:
                    print(f"   Could not set execution permissions on FFmpeg: {e}")
            
        print(f"   Using FFmpeg: {ffmpeg_exe}")
        
        # Get advanced ffmpeg args
        ff_advanced = advanced_settings.get('ffmpeg', {}) if advanced_settings else {}
        ff_global = ff_advanced.get('globalArgs', '-hide_banner -loglevel error')
        # Optimized for stability: using -timeout (correct option name, not -stimeout)
        # Timeout is in microseconds: 10000000 = 10 seconds
        ff_input = ff_advanced.get('inputArgs', '-rtsp_transport tcp -timeout 10000000 -fflags +genpts')
        ff_process = ff_advanced.get('processArgs', '-c:v libx264 -preset ultrafast -tune zerolatency -g 30')
        
        
        # Auth handling is now external via the Python web app
        enable_global_auth = bool(rtsp_username and rtsp_password)
        sys_user = rtsp_username
        sys_pass = rtsp_password

        # Only add paths for RUNNING cameras
        running_count = 0
        stream_count = 0
        loopback = lambda path: f"rtsp://127.0.0.1:{rtsp_port}/{path}"
        for camera in cameras:
            if camera.status != "running":
                continue
            running_count += 1
            added = self._add_camera_paths(
                config, camera, rtsp_port=rtsp_port, ffmpeg_exe=ffmpeg_exe, system=system,
                ff_global=ff_global, ff_input=ff_input, ff_process=ff_process,
                enable_global_auth=enable_global_auth, sys_user=sys_user, sys_pass=sys_pass,
                loopback=loopback)
            stream_count += added
            
        print("-" * 40)
        print(f"  Total running cameras: {running_count}")
        print(f"  Total streams: {stream_count}")
        print("-" * 40)

        # ===== GRIDFUSION COMPOSITE STREAM =====
        # ===== GRIDFUSION COMPOSITE STREAM (Multi-Layout Support) =====
        grid_fusion_layouts = []
        if grid_fusion:
            if 'layouts' in grid_fusion:
                grid_fusion_layouts = grid_fusion.get('layouts', [])
            elif grid_fusion.get('enabled'):
                # Legacy single layout (backward compat)
                grid_fusion['id'] = 'matrix'
                grid_fusion_layouts = [grid_fusion]

        if grid_fusion_layouts:
            print(f"    Configuring GridFusion Composite Streams ({len(grid_fusion_layouts)} layouts)...")
            
            for layout in grid_fusion_layouts:
                if not layout.get('enabled'):
                    continue
                    
                layout_id = layout.get('id', 'matrix')
                layout_name = layout.get('name', 'Matrix')
                res = layout.get('resolution', '1920x1080')
                fps = int(layout.get('outputFramerate', 5))
                
                try:
                    res_w, res_h = map(int, res.split('x'))
                except:
                    res_w, res_h = 1920, 1080
                
                gf_cams = layout.get('cameras', [])
                if gf_cams:
                    # Build FFmpeg command for composition
                    inputs = []
                    filters = []
                    active_gf_cams_data = []
                    for gf_cam in gf_cams:
                        cam_id = gf_cam.get('id')
                        cam = next((c for c in cameras if c.id == cam_id), None)
                        if cam and cam.status == "running":
                            # Store both for easier access
                            active_gf_cams_data.append((gf_cam, cam))
                    
                    # Sort: False < True, so True (always on top) comes last in the list
                    # and thus last in the overlay chain (appearing on top)
                    active_gf_cams_data.sort(key=lambda x: bool(x[0].get('always_on_top', False)))

                    active_gf_cams = []
                    input_idx = 0
                    for gf_cam, cam in active_gf_cams_data:
                        # Determine stream type (default to sub if not specified)
                        stream_type = gf_cam.get('stream_type', 'sub')
                        suffix = "_main" if stream_type == "main" else "_sub"
                        
                        # Source is the local MediaMTX stream
                        if enable_global_auth:
                            src_url = f"rtsp://{sys_user}:{sys_pass}@127.0.0.1:{rtsp_port}/{cam.path_name}{suffix}"
                        else:
                            src_url = f"rtsp://127.0.0.1:{rtsp_port}/{cam.path_name}{suffix}"
                        
                        if system == "windows":
                            safe_src = f'"{src_url}"'
                        else:
                            safe_src = shlex.quote(src_url)
                        
                        # Low-latency startup: analyzeduration 0 drops the time-based
                        # probe wait so FFmpeg opens the stream as soon as it sees data.
                        # probesize 500k keeps enough byte budget to reliably find the
                        # H.264 SPS/PPS headers (going lower, e.g. 32, causes intermittent
                        # "could not find codec parameters" failures on RTSP substreams).
                        inputs.append(f'-fflags nobuffer+genpts+discardcorrupt -flags low_delay -rtsp_transport tcp -timeout 5000000 -analyzeduration 0 -probesize 500k -thread_queue_size 16 -use_wallclock_as_timestamps 1 -i {safe_src}')
                        
                        # Scale and normalize timestamps only. 
                        # Removing the per-input 'fps' filter as it adds unnecessary CPU overhead and latency.
                        w = int(round(float(gf_cam.get('w', 640))))
                        h = int(round(float(gf_cam.get('h', 480))))
                        filters.append(f'[{input_idx}:v]scale={w}:{h},setpts=PTS-STARTPTS[v{input_idx}]')
                        active_gf_cams.append(gf_cam)
                        input_idx += 1
                    
                    if inputs:
                        # ===== Hybrid compositor =====
                        # Base (grid) cameras are composited in a single parallel xstack
                        # pass — lower CPU and tighter frame sync than a long overlay chain.
                        # Cameras flagged always_on_top (PiP), and any base cameras that
                        # overlap each other, fall back to sequential overlay so that
                        # arbitrary / overlapping layouts still render correctly (xstack
                        # cannot represent overlapping or z-ordered tiles).
                        # The [base] color source provides the master clock for the matrix.
                        def _rect(gc):
                            return (
                                int(round(float(gc.get('x', 0)))), int(round(float(gc.get('y', 0)))),
                                int(round(float(gc.get('w', 640)))), int(round(float(gc.get('h', 480)))),
                            )

                        base_idxs = [i for i, gc in enumerate(active_gf_cams)
                                     if not bool(gc.get('always_on_top', False))]
                        top_idxs = [i for i, gc in enumerate(active_gf_cams)
                                    if bool(gc.get('always_on_top', False))]

                        # Detect overlap among base cameras; if present, xstack can't be
                        # used for them (it has no z-order), so fall back to overlay.
                        base_overlap = False
                        for a in range(len(base_idxs)):
                            ax, ay, aw, ah = _rect(active_gf_cams[base_idxs[a]])
                            for b in range(a + 1, len(base_idxs)):
                                bx, by, bw, bh = _rect(active_gf_cams[base_idxs[b]])
                                if ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah:
                                    base_overlap = True
                                    break
                            if base_overlap:
                                break

                        # xstack requires at least 2 inputs.
                        use_xstack = len(base_idxs) >= 2 and not base_overlap

                        chain_parts = [f'color=black:s={res_w}x{res_h}:r={fps}[base]']
                        last_label = '[base]'

                        if use_xstack:
                            xs_inputs = ''.join(f'[v{i}]' for i in base_idxs)
                            # Absolute pixel coordinates per tile; fill=black so any gaps
                            # match the canvas. Composited in one parallel pass.
                            layout = '|'.join(
                                f'{int(round(float(active_gf_cams[i].get("x", 0))))}_'
                                f'{int(round(float(active_gf_cams[i].get("y", 0))))}'
                                for i in base_idxs
                            )
                            chain_parts.append(
                                f'{xs_inputs}xstack=inputs={len(base_idxs)}:layout={layout}:fill=black[grid]'
                            )
                            # Overlay the composited grid onto the full-size canvas at origin.
                            grid_label = '[tmp_base]' if top_idxs else '[outv]'
                            chain_parts.append(
                                f'[base][grid]overlay=0:0:eof_action=pass:repeatlast=1{grid_label}'
                            )
                            last_label = grid_label
                        else:
                            # 0/1 base camera, or overlapping base tiles: sequential overlay.
                            for n, i in enumerate(base_idxs):
                                x, y, _, _ = _rect(active_gf_cams[i])
                                is_last = (n == len(base_idxs) - 1) and not top_idxs
                                nxt = '[outv]' if is_last else f'[b{n}]'
                                # eof_action=pass + repeatlast=1: keep the matrix running
                                # if an input dies/EOFs.
                                chain_parts.append(
                                    f'{last_label}[v{i}]overlay={x}:{y}:eof_action=pass:repeatlast=1{nxt}'
                                )
                                last_label = nxt

                        # Always-on-top PiP cameras, layered last so they sit on top.
                        for n, i in enumerate(top_idxs):
                            x, y, _, _ = _rect(active_gf_cams[i])
                            is_last = (n == len(top_idxs) - 1)
                            nxt = '[outv]' if is_last else f'[t{n}]'
                            chain_parts.append(
                                f'{last_label}[v{i}]overlay={x}:{y}:eof_action=pass:repeatlast=1{nxt}'
                            )
                            last_label = nxt

                        filter_complex = ";".join(filters) + ";" + ";".join(chain_parts)
                        
                        if enable_global_auth:
                            dest_url = f"rtsp://{sys_user}:{sys_pass}@127.0.0.1:{rtsp_port}/{layout_id}"
                        else:
                            dest_url = f"rtsp://127.0.0.1:{rtsp_port}/{layout_id}"
                            
                        if system == "windows":
                            safe_dest = f'"{dest_url}"'
                        else:
                            safe_dest = shlex.quote(dest_url)
                            
                        # Check for hardware acceleration setting
                        ff_advanced = advanced_settings.get('ffmpeg', {}) if advanced_settings else {}
                        use_hw_accel = False
                        hw_accel_info = None
                        
                        if ff_advanced.get('hardwareEncoding', False):
                            hw_accel_info = self._detect_hardware_acceleration(ffmpeg_exe)
                            if hw_accel_info:
                                use_hw_accel = True
                                print(f"      Hardware acceleration enabled and detected: {hw_accel_info['name']}")
                            else:
                                print(f"      Hardware acceleration enabled but not detected. Falling back to software.")
                        
                        # Determine encoder arguments
                        if use_hw_accel and hw_accel_info:
                             encoder_args = f'-c:v {hw_accel_info["encoder"]} {hw_accel_info["params"]}'
                        else:
                             # Software encoding with optimized preset
                             # 'ultrafast' is used to minimize latency at the cost of bitrate efficiency
                             encoder_args = '-c:v libx264 -preset ultrafast -tune zerolatency'

                        # Final command - optimized for multi-core CPU utilization and stability
                        # -threads 0: Auto-detect and use all available CPU cores
                        # -filter_complex_threads 0: Parallelize filter graph processing across cores
                        gf_cmd = (
                            f'"{ffmpeg_exe}" {ff_global} -nostdin -stats '
                            f'{" ".join(inputs)} '
                            f'-filter_complex "{filter_complex}" '
                            f'-filter_complex_threads 0 '
                            f'-map "[outv]" '
                            f'{encoder_args} '
                            f'-profile:v high -level 4.2 '
                            f'-threads 0 '
                            f'-b:v 2500k -maxrate 2500k -bufsize 5000k -g {fps} '
                            f'-r {fps} -vsync cfr -max_delay 500000 -f rtsp -rtsp_transport tcp {safe_dest}'
                        )
                        
                        config['paths'][layout_id] = {
                            'source': 'publisher',
                            'runOnInit': gf_cmd,
                            'runOnInitRestart': True,  # Auto-restart enabled to recover from initial connection failures
                        }
                        print(f"      {layout_name} stream added at /{layout_id} ({res})")

        
        # External auth handled via hook
        
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    # ------------------------------------------------------------------
    # Per-camera path generation
    # ------------------------------------------------------------------

    _AUDIO_CODEC_MAP = {
        'aac': 'aac',
        'g711ulaw': 'pcm_mulaw',
        'g711alaw': 'pcm_alaw',
        'mp2l2': 'mp2',
        'g726': 'g726',
        'pcm': 'pcm_s16le',
        'mp3': 'libmp3lame',
        'g722.1': 'g722'
    }

    def _audio_args(self, camera, which):
        """FFmpeg audio arguments for a transcode/relay command."""
        if not getattr(camera, 'enable_audio', False):
            return '-an'
        if not getattr(camera, f'transcode_{which}_audio', False):
            return '-c:a copy'
        enc = str(getattr(camera, f'audio_encoding_{which}', 'aac')).lower()
        ff_codec = self._AUDIO_CODEC_MAP.get(enc, 'aac')
        sr = str(getattr(camera, f'audio_sample_rate_{which}', '44100')).lower().replace('khz', '000')
        br = str(getattr(camera, f'audio_bitrate_{which}', '64k'))
        if br.isdigit(): br = f"{br}k"
        elif 'kbps' in br.lower(): br = br.lower().replace('kbps', 'k')
        return f'-c:a {ff_codec} -ar {sr} -ac 1 -b:a {br} -af "aresample=async=1"'

    @staticmethod
    def _quote(value, system):
        return f'"{value}"' if system == "windows" else shlex.quote(value)

    def _pull_path_cfg(self, camera, source_url, on_demand=True):
        """MediaMTX path that pulls a source URL directly (codec passthrough).

        For RTSPS the TLS policy is enforced here by MediaMTX: full CA +
        hostname verification by default, or the pinned SHA-256 fingerprint."""
        cfg = {
            'source': source_url,
            'rtspTransport': 'tcp',
            'sourceOnDemand': on_demand,
            'sourceOnDemandStartTimeout': '10s',
            'sourceOnDemandCloseAfter': '10s',
            'record': False,
        }
        if source_url.lower().startswith('rtsps://'):
            cfg.update(camera.mediamtx_source_fields())
        return cfg

    def _insecure_relay_cfg(self, camera, source_url, dest_url, ffmpeg_exe, system, ff_global, which):
        """Explicitly-insecure RTSPS: MediaMTX can't skip certificate checks
        for a pulled source, so FFmpeg relays the camera (still over TLS, codec
        passthrough) into MediaMTX on demand."""
        audio = '-c:a copy' if getattr(camera, 'enable_audio', False) else '-an'
        tls = ' '.join(insecure_tls_input_args(ffmpeg_exe))
        cmd = (
            f'"{ffmpeg_exe}" {ff_global} -nostdin '
            f'-rtsp_transport tcp {tls + " " if tls else ""}-timeout 10000000 -fflags +genpts '
            f'-i {self._quote(source_url, system)} '
            f'-c:v copy {audio} -f rtsp -rtsp_transport tcp {self._quote(dest_url, system)}'
        )
        return {
            'source': 'publisher',
            'runOnDemand': cmd,
            'runOnDemandRestart': True,
            'runOnDemandStartTimeout': '15s',
            'runOnDemandCloseAfter': '10s',
            'overridePublisher': True,
        }

    def _transcode_input(self, camera, which, source_url, config, loopback, ffmpeg_exe=None):
        """Return (input_url, extra_input_args) for a transcode command.

        RTSPS cameras in a verified TLS mode are never read by FFmpeg directly
        (FFmpeg's certificate checks vary by build); a hidden '<cam>_<which>_src'
        path lets MediaMTX enforce the policy and FFmpeg reads it on loopback."""
        if camera.ffmpeg_requires_relay():
            src_path = f'{camera.path_name}_{which}_src'
            config['paths'][src_path] = self._pull_path_cfg(camera, source_url)
            return loopback(src_path), ''
        if source_url.lower().startswith('rtsps://'):
            tls = ' '.join(insecure_tls_input_args(ffmpeg_exe))
            return source_url, f'{tls} ' if tls else ''
        return source_url, ''

    def _sub_codec(self, camera, sub_source):
        """Source codec of the sub stream, for automatic HEVC->H.264."""
        probe = getattr(camera, 'stream_probe', {}) or {}
        cached = probe.get('sub') if isinstance(probe.get('sub'), dict) else None
        if cached and cached.get('codec'):
            return cached['codec']
        if camera.ffmpeg_requires_relay():
            # Can't probe safely before MediaMTX is serving the camera; the
            # health monitor records the codec and the next restart uses it.
            return None
        return self._get_source_codec(sub_source)

    def _add_camera_paths(self, config, camera, rtsp_port, ffmpeg_exe, system, ff_global,
                          ff_input, ff_process, enable_global_auth, sys_user, sys_pass, loopback):
        """Add the MediaMTX paths for one running camera. Returns the number of
        served (non-hidden) streams."""
        enable_audio = getattr(camera, 'enable_audio', False)
        insecure_rtsps = camera.is_rtsps and camera.tls_mode == stream_source.TLS_INSECURE
        if insecure_rtsps:
            print(f"    WARNING: {camera.name}: RTSPS certificate verification is DISABLED "
                  f"(insecure diagnostic mode)")

        def dest(suffix):
            if enable_global_auth:
                return (f"rtsp://{quote(sys_user, safe='')}:{quote(sys_pass, safe='')}"
                        f"@127.0.0.1:{rtsp_port}/{camera.path_name}{suffix}")
            return f"rtsp://127.0.0.1:{rtsp_port}/{camera.path_name}{suffix}"

        # ===== MAIN STREAM - High Quality =====
        transcode_main = getattr(camera, 'transcode_main', False)
        transcode_main_audio = getattr(camera, 'transcode_main_audio', False)
        main_source = camera.main_stream_url

        if transcode_main or (enable_audio and transcode_main_audio):
            print(f"    Transcoding enabled for {camera.name} main-stream")
            tgt_w = getattr(camera, 'main_width', 1920)
            tgt_h = getattr(camera, 'main_height', 1080)
            tgt_fps = getattr(camera, 'main_framerate', 30)
            in_url, in_extra = self._transcode_input(camera, 'main', main_source, config, loopback, ffmpeg_exe)

            if transcode_main:
                video_args = (
                    f'-vf "scale={tgt_w}:{tgt_h}:force_original_aspect_ratio=decrease,pad={tgt_w}:{tgt_h}:(ow-iw)/2:(oh-ih)/2,format=yuv420p" '
                    f'{ff_process} '
                    f'-profile:v high -level 4.2 '
                    f'-b:v 2500k -maxrate 2500k -bufsize 5000k '
                    f'-threads 2 -g {tgt_fps} -sc_threshold 0 '
                    f'-r {tgt_fps} '
                )
            else:
                video_args = '-c:v copy'

            cmd = (
                f'"{ffmpeg_exe}" {ff_global} -nostdin '
                f'{ff_input} {in_extra}-use_wallclock_as_timestamps 1 '
                f'-i {self._quote(in_url, system)} '
                f'{video_args} '
                f'{self._audio_args(camera, "main")} -f rtsp -rtsp_transport tcp {self._quote(dest("_main"), system)}'
            )
            main_path_cfg = {
                'source': 'publisher',
                'runOnInit': cmd,
                'runOnInitRestart': True,  # Auto-restart enabled to recover from connection failures
                'rtspTransport': 'tcp',
                'overridePublisher': True,
            }
        elif insecure_rtsps:
            main_path_cfg = self._insecure_relay_cfg(camera, main_source, dest('_main'),
                                                     ffmpeg_exe, system, ff_global, 'main')
        else:
            main_path_cfg = self._pull_path_cfg(camera, main_source)
            main_path_cfg['overridePublisher'] = True

        config['paths'][f'{camera.path_name}_main'] = main_path_cfg

        # ===== SUB STREAM - Lower Quality, Optimized for Viewing =====
        if getattr(camera, 'disable_substream', False):
            print(f"    Sub-stream disabled for {camera.name}")
            return 1

        transcode_sub = getattr(camera, 'transcode_sub', False)
        transcode_sub_audio = getattr(camera, 'transcode_sub_audio', False)
        use_main_as_sub = camera.effective_use_main_as_substream
        if getattr(camera, 'substream_fallback_active', False):
            print(f"    {camera.name}: sub stream unavailable, serving main stream on the sub path")

        # RTSPS cameras (and runtime fallback) take "main as sub" from our own
        # main path on loopback, so the camera sees one connection and the TLS
        # policy is applied once.
        sub_from_loopback = use_main_as_sub and (camera.is_rtsps or getattr(camera, 'substream_fallback_active', False))
        sub_source = camera.main_stream_url if use_main_as_sub else camera.sub_stream_url

        # Auto-transcode H.265/HEVC substreams to H.264 so the web dashboard
        # (WebRTC and HLS) can play them — browsers can't decode HEVC. The main
        # stream is left untouched so the NVR keeps the original H.265 feed.
        auto_h264_sub = False
        if not transcode_sub:
            src_codec = self._sub_codec(camera, sub_source)
            if src_codec in ('hevc', 'h265'):
                auto_h264_sub = True
                print(f"    Auto-transcoding {camera.name} sub-stream H.265 -> H.264 for browser playback")
        transcode_sub_video = transcode_sub or auto_h264_sub

        if transcode_sub_video or (enable_audio and transcode_sub_audio):
            print(f"    Transcoding enabled for {camera.name} sub-stream")
            tgt_w = getattr(camera, 'sub_width', 640)
            tgt_h = getattr(camera, 'sub_height', 480)
            tgt_fps = getattr(camera, 'sub_framerate', 15)
            if sub_from_loopback:
                in_url, in_extra = loopback(f'{camera.path_name}_main'), ''
            else:
                in_url, in_extra = self._transcode_input(camera, 'sub', sub_source, config, loopback, ffmpeg_exe)

            if transcode_sub_video:
                video_args = (
                    f'-vf "scale={tgt_w}:{tgt_h}:force_original_aspect_ratio=decrease,pad={tgt_w}:{tgt_h}:(ow-iw)/2:(oh-ih)/2,format=yuv420p" '
                    f'{ff_process} '
                    f'-profile:v baseline -level 4.1 '
                    f'-b:v 800k -maxrate 800k -bufsize 1600k '
                    f'-threads 2 -g {tgt_fps} -sc_threshold 0 '
                    f'-r {tgt_fps} '
                )
            else:
                video_args = '-c:v copy'

            cmd = (
                f'"{ffmpeg_exe}" {ff_global} -nostdin '
                f'{ff_input} {in_extra}-use_wallclock_as_timestamps 1 '
                f'-i {self._quote(in_url, system)} '
                f'{video_args} '
                f'{self._audio_args(camera, "sub")} -f rtsp -rtsp_transport tcp {self._quote(dest("_sub"), system)}'
            )
            sub_path_cfg = {
                'source': 'publisher',
                'runOnInit': cmd,
                'runOnInitRestart': True,  # Auto-restart enabled to recover from connection failures
                'rtspTransport': 'tcp',
                'sourceOnDemand': False,
                'overridePublisher': True,
            }
        elif sub_from_loopback:
            sub_path_cfg = self._pull_path_cfg(camera, loopback(f'{camera.path_name}_main'))
        elif insecure_rtsps:
            sub_path_cfg = self._insecure_relay_cfg(camera, sub_source, dest('_sub'),
                                                    ffmpeg_exe, system, ff_global, 'sub')
        else:
            # Standard Proxy Mode
            sub_path_cfg = self._pull_path_cfg(camera, sub_source)
            sub_path_cfg['disablePublisherOverride'] = False

        config['paths'][f'{camera.path_name}_sub'] = sub_path_cfg
        print(f"  Added {camera.name}: {camera.path_name}_main and {camera.path_name}_sub")
        return 2

    def _detect_hardware_acceleration(self, ffmpeg_exe):
        """
        Detects available hardware acceleration methods supported by the FFmpeg binary.
        Returns the best available encoder configuration or None.
        """
        try:
            # Run ffmpeg -encoders to get list of supported encoders
            process = subprocess.Popen(
                [ffmpeg_exe, "-encoders"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, _ = process.communicate()
            
            # Check for Apple Silicon VideoToolbox (macOS)
            if "h264_videotoolbox" in stdout:
                return {
                    "name": "Apple VideoToolbox",
                    "type": "videotoolbox",
                    "encoder": "h264_videotoolbox",
                    "params": "-realtime 1"
                }
                
            # Check for NVIDIA NVENC
            if "h264_nvenc" in stdout:
                return {
                    "name": "NVIDIA NVENC",
                    "type": "nvenc",
                    "encoder": "h264_nvenc",
                    "params": "-preset p4 -tune ll -rc vbr"
                }
            
            # Check for Intel QSV (Quick Sync Video)
            if "h264_qsv" in stdout:
                return {
                    "name": "Intel QSV",
                    "type": "qsv",
                    "encoder": "h264_qsv",
                    "params": "-preset veryfast -global_quality 25 -look_ahead 0"
                }
                
            # Check for AMD AMF
            if "h264_amf" in stdout:
                return {
                    "name": "AMD AMF",
                    "type": "amf",
                    "encoder": "h264_amf",
                    "params": "-usage ultra_low_latency -quality speed -rc cqp"
                }
                
            return None
            
        except Exception as e:
            print(f"Error detecting hardware acceleration: {e}")
            import traceback
            traceback.print_exc()
            return None

    # ------------------------------------------------------------------
    # Process lifecycle
    #
    # Only one MediaMTX instance may own the RTSP/API ports. Every start,
    # stop and restart runs under one lock, so overlapping requests from the
    # web UI, the watchdog and camera start/stop can no longer spawn a second
    # process (the old cause of "bind: address already in use"). Instances
    # left behind by a previous run are identified by our PID file or by an
    # exact command line match (our binary + our config file) and nothing
    # else is ever killed.
    # ------------------------------------------------------------------

    _PATH_LOG_RE = re.compile(r'\b(ERR|WAR|INF)\b \[path ([^\]]+)\] (?:\[[^\]]+\] )?(.*)$')

    @property
    def pid_file(self):
        return os.path.join(os.path.dirname(os.path.abspath(self.config_file)), "mediamtx.pid")

    def _owned_cmdline(self):
        return [os.path.abspath(self.executable), os.path.abspath(self.config_file)]

    def _is_owned_process(self, proc):
        """True if a psutil.Process is a MediaMTX started by this app with our config."""
        try:
            cmd = proc.cmdline()
        except Exception:
            return False
        exe, cfg = self._owned_cmdline()
        # "<our mediamtx binary> <our config file>" as consecutive arguments
        # (cmd[0] normally; later if launched through an interpreter/wrapper).
        for i in range(len(cmd) - 1):
            try:
                if os.path.abspath(cmd[i]) == exe and os.path.abspath(cmd[i + 1]) == cfg:
                    return True
            except Exception:
                continue
        return False

    def find_owned_processes(self):
        """Running MediaMTX processes that belong to this app (excluding self.process)."""
        try:
            import psutil
        except ImportError:
            return []
        current = self.process.pid if self.process and self.process.poll() is None else None
        owned = {}
        # 1. PID recorded by a previous run
        try:
            with open(self.pid_file) as f:
                pid = int(f.read().strip() or 0)
            if pid and pid != current and psutil.pid_exists(pid):
                p = psutil.Process(pid)
                if self._is_owned_process(p):
                    owned[pid] = p
        except (OSError, ValueError):
            pass
        except Exception:
            pass
        # 2. Exact command-line match (covers runs before the PID file existed)
        try:
            for p in psutil.process_iter():
                if p.pid in owned or p.pid == current or p.pid == os.getpid():
                    continue
                if self._is_owned_process(p):
                    owned[p.pid] = p
        except Exception:
            pass
        return list(owned.values())

    def cleanup_stale_instances(self):
        """Terminate stale MediaMTX processes we own. Returns how many were stopped."""
        stale = self.find_owned_processes()
        for p in stale:
            try:
                print(f"  Stopping stale MediaMTX instance from a previous run (PID {p.pid})")
                p.terminate()
                p.wait(timeout=5)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        if stale:
            self._remove_pid_file()
        return len(stale)

    def port_holder(self, port):
        """(pid, name) of the process listening on TCP port, (None, None) if free,
        or ('unknown', None) if something listens but can't be identified."""
        import socket
        try:
            import psutil
            for conn in psutil.net_connections(kind='tcp'):
                if conn.laddr and conn.laddr.port == int(port) and conn.status == 'LISTEN':
                    if conn.pid:
                        try:
                            return conn.pid, psutil.Process(conn.pid).name()
                        except Exception:
                            return conn.pid, None
                    return 'unknown', None
            return None, None
        except Exception:
            pass
        # psutil unavailable or not permitted: fall back to a bind test
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(('0.0.0.0', int(port)))
            return None, None
        except OSError:
            return 'unknown', None
        finally:
            s.close()

    def _wait_port_free(self, port, timeout=6.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            holder, _ = self.port_holder(port)
            if holder is None:
                return True
            time.sleep(0.25)
        return False

    def _write_pid_file(self):
        try:
            with open(self.pid_file, 'w') as f:
                f.write(str(self.process.pid))
        except OSError:
            pass

    def _remove_pid_file(self):
        try:
            os.remove(self.pid_file)
        except OSError:
            pass

    def _process_env(self):
        """Environment for MediaMTX. Custom CA certificates in data/tls/ca are
        added to Go's trust store (used for RTSPS sources in 'verify' mode)."""
        env = os.environ.copy()
        if stream_source.list_custom_cas(DATA_DIR):
            dirs = [d for d in ('/etc/ssl/certs', '/etc/pki/tls/certs') if os.path.isdir(d)]
            dirs.append(stream_source.custom_ca_dir(DATA_DIR))
            env['SSL_CERT_DIR'] = ':'.join(dirs)
        return env

    def is_running(self):
        return bool(self.process and self.process.poll() is None)

    # Per-path source events parsed from MediaMTX output, used by the health monitor.
    def get_path_event(self, path):
        with self._log_lock:
            return dict(self.path_events.get(path, {}))

    def clear_path_events(self):
        with self._log_lock:
            self.path_events = {}

    def _handle_output_line(self, raw_line):
        line = stream_source.redact_text(raw_line.rstrip('\n'))
        if not line:
            return
        with self._log_lock:
            self.log_buffer.append(line.strip())
            if len(self.log_buffer) > 100:
                self.log_buffer.pop(0)

        m = self._PATH_LOG_RE.search(line)
        suppress = False
        if m:
            level, path, msg = m.group(1), m.group(2), m.group(3)
            now = time.time()
            with self._log_lock:
                ev = self.path_events.setdefault(path, {})
                if level == 'ERR':
                    # Errors repeat every few seconds while a source is down;
                    # print each distinct error at most once a minute.
                    suppress = (ev.get('error') == msg and now - ev.get('printedAt', 0) < 60)
                    ev['error'] = msg
                    ev['errorAt'] = now
                    if not suppress:
                        ev['printedAt'] = now
                elif 'is available and online' in msg or ' is ready' in msg:
                    ev['onlineAt'] = now
                    ev.pop('error', None)

        # ffmpeg status lines contain "frame=" and "fps="
        is_ffmpeg_status = "frame=" in line and "fps=" in line
        if suppress and not self.debug_mode:
            return
        if self.debug_mode or not is_ffmpeg_status:
            sys.stdout.write(line + "\n")
            sys.stdout.flush()

    def start(self, cameras, rtsp_port=None, rtsp_username=None, rtsp_password=None, grid_fusion=None, debug_mode=False, advanced_settings=None, web_port=None):
        """Start MediaMTX server (never starts a second instance)."""
        with self._lifecycle_lock:
            return self._start_locked(cameras, rtsp_port=rtsp_port, rtsp_username=rtsp_username,
                                      rtsp_password=rtsp_password, grid_fusion=grid_fusion,
                                      debug_mode=debug_mode, advanced_settings=advanced_settings,
                                      web_port=web_port)

    def _start_locked(self, cameras, rtsp_port=None, rtsp_username=None, rtsp_password=None, grid_fusion=None, debug_mode=False, advanced_settings=None, web_port=None):
        self.debug_mode = debug_mode
        rtsp_port = rtsp_port or MEDIAMTX_PORT

        if self.is_running():
            print(f"MediaMTX is already running (PID {self.process.pid}); restarting it instead of starting a second instance.")
            self._stop_locked()

        if not self.download_mediamtx():
            return False

        # Stop leftovers we own (e.g. from a crashed previous run). Never touch others.
        self.cleanup_stale_instances()

        for port, label in ((rtsp_port, 'RTSP'), (MEDIAMTX_API_PORT, 'MediaMTX API')):
            if not self._wait_port_free(port, timeout=6.0):
                pid, name = self.port_holder(port)
                who = f"PID {pid}" + (f" ({name})" if name else "") if pid not in (None, 'unknown') else "another process"
                print(f"ERROR: {label} port {port} is already in use by {who}, which is not managed by this server.")
                print(f"       Not starting MediaMTX. Stop that process or change the RTSP port in Settings.")
                self.last_start_error = f"{label} port {port} is in use by {who}"
                return False

        self.create_config(cameras, rtsp_port=rtsp_port, rtsp_username=rtsp_username, rtsp_password=rtsp_password, grid_fusion=grid_fusion, debug_mode=debug_mode, advanced_settings=advanced_settings, web_port=web_port)
        self.clear_path_events()

        print("\nStarting MediaMTX RTSP Server...")

        try:
            exe_path, config_path = self._owned_cmdline()
            print(f"   Executable: {exe_path}")
            print(f"   Config: {config_path}")

            import errno
            for attempt in range(5):
                try:
                    self.process = subprocess.Popen(
                        [exe_path, config_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,  # Line buffered
                        env=self._process_env(),
                    )
                    break
                except OSError as e:
                    if e.errno == getattr(errno, 'ETXTBSY', 26) and attempt < 4:
                        print(f"   MediaMTX binary busy (ETXTBSY), retrying in 0.2s... (attempt {attempt+1}/5)")
                        time.sleep(0.2)
                        continue
                    raise
            self._write_pid_file()

            def capture_output(process):
                for line in process.stdout:
                    if line:
                        try:
                            self._handle_output_line(line)
                        except Exception:
                            pass

            output_thread = threading.Thread(target=capture_output, args=(self.process,), daemon=True)
            output_thread.start()

            time.sleep(3)

            if self.process.poll() is None:
                self.last_start_error = None
                print(f"MediaMTX running on RTSP port {rtsp_port} (PID {self.process.pid})")
                return True
            else:
                self.last_start_error = "MediaMTX exited during startup"
                print("MediaMTX failed to start or was stopped. Check console output above.")
                self._remove_pid_file()
                return False

        except Exception as e:
            self.last_start_error = str(e)
            print(f"Error starting MediaMTX: {e}")
            import traceback
            traceback.print_exc()
            return False

    def stop(self):
        """Stop MediaMTX server"""
        with self._lifecycle_lock:
            self._stop_locked()

    def _stop_locked(self):
        if self.process:
            proc = self.process
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except Exception:
                    proc.kill()
                    try:
                        proc.wait(timeout=3)
                    except Exception:
                        pass
            self.process = None
            self._remove_pid_file()
            print("MediaMTX stopped")

    def restart(self, cameras, rtsp_port=None, rtsp_username=None, rtsp_password=None, grid_fusion=None, debug_mode=False, advanced_settings=None, web_port=None):
        """Restart MediaMTX with new configuration"""
        with self._lifecycle_lock:
            print("\nRestarting MediaMTX...")
            self._stop_locked()
            self._wait_port_free(rtsp_port or MEDIAMTX_PORT, timeout=6.0)
            return self._start_locked(cameras, rtsp_port=rtsp_port, rtsp_username=rtsp_username, rtsp_password=rtsp_password, grid_fusion=grid_fusion, debug_mode=debug_mode, advanced_settings=advanced_settings, web_port=web_port)

    # ------------------------------------------------------------------
    # Policy-respecting source probe
    # ------------------------------------------------------------------

    def probe_source(self, camera, which, rtsp_port=None, timeout=20):
        """Probe a camera's main/sub source and return (info, error).

        RTSPS sources in a verified TLS mode are never probed by FFprobe
        directly: a temporary MediaMTX path (added through the API, not the
        config file) pulls the camera with the camera's TLS policy and FFprobe
        reads it on loopback. Plain RTSP and explicit insecure RTSPS are probed
        directly as before."""
        from .ffmpeg_manager import FFmpegManager
        ffm = FFmpegManager()
        rtsp_port = rtsp_port or MEDIAMTX_PORT
        errors = []

        url, extra = camera.ffmpeg_direct_input(which)
        if url:
            info = ffm.probe_stream(url, timeout=timeout, input_args=extra, errors=errors)
            return info, (errors[0] if errors else '')

        source_url = camera.source_url(which)
        if not source_url:
            return None, "No source URL configured"
        if not self.is_running():
            return None, "The MediaMTX stream server is not running"

        name = f"probe_{secrets.token_hex(4)}"
        api = f"http://127.0.0.1:{MEDIAMTX_API_PORT}/v3/config/paths"
        cfg = self._pull_path_cfg(camera, source_url, on_demand=True)
        try:
            r = requests.post(f"{api}/add/{name}", json=cfg, timeout=5)
            if r.status_code >= 300:
                return None, f"Could not create a temporary MediaMTX path (HTTP {r.status_code})"
            info = ffm.probe_stream(f"rtsp://127.0.0.1:{rtsp_port}/{name}", timeout=timeout,
                                    errors=errors)
            if info:
                return info, ''
            time.sleep(0.5)
            err = self.get_path_event(name).get('error') or (errors[0] if errors else '')
            return None, err or "No video received from the source"
        except Exception as e:
            return None, stream_source.redact_text(str(e))
        finally:
            try:
                requests.delete(f"{api}/delete/{name}", timeout=5)
            except Exception:
                pass
            with self._log_lock:
                self.path_events.pop(name, None)
