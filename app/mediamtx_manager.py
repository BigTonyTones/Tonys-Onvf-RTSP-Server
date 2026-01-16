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
from pathlib import Path
from .config import MEDIAMTX_PORT, MEDIAMTX_API_PORT

class MediaMTXManager:
    """Manages MediaMTX RTSP server"""
    
    def __init__(self):
        self.process = None
        self.config_file = "mediamtx.yml"
        self.executable = self._get_executable_name()
        self.log_buffer = [] # Store last 100 lines for debug
        self._log_lock = threading.Lock()
        self.debug_mode = False
        
    def _get_executable_name(self):
        """Get the correct executable name for the platform"""
        system = platform.system().lower()
        if system == "windows":
            return "mediamtx.exe"
        return "mediamtx"
    
    def _get_latest_version(self):
        """Locked to version v1.15.6 as requested"""
        return "v1.15.6"

    def _parse_version(self, version_str):
        """Parse version string like 'v1.15.6' into a list of integers [1, 15, 6]"""
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
                # Use absolute path for reliability
                exe_path = os.path.abspath(self.executable)
                result = subprocess.run([exe_path, "--version"], 
                                      capture_output=True, text=True, check=False)
                # Version output is often just "vX.Y.Z"
                current_version = result.stdout.strip()
                if current_version and not current_version.startswith('v'):
                    current_version = 'v' + current_version
                
                if current_version == latest_version:
                    print(f"MediaMTX is up to date ({current_version})")
                    return True
                elif self._version_is_newer(current_version, latest_version):
                    print(f"Newer MediaMTX version available: {current_version} -> {latest_version}")
                    print("Preparing to update...")
                else:
                    # Current version is actually newer or equal
                    print(f"MediaMTX is up to date ({current_version})")
                    return True
            except Exception as e:
                print(f"Could not check MediaMTX version: {e}")
                return True
        else:
            print(f"MediaMTX not found. Downloading latest version: {latest_version}")
        
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
        
        # Ask for confirmation
        try:
            confirm = input(f"\nWould you like to download and install MediaMTX {version}? (y/n): ")
            if confirm.lower() not in ['y', 'yes']:
                print("Installation cancelled by user.")
                return False
        except EOFError:
            # Handle non-interactive environments
            print("Non-interactive environment detected, proceeding with download...")
            pass
        
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
    
    def create_config(self, cameras, rtsp_port=None, rtsp_username=None, rtsp_password=None, grid_fusion=None, debug_mode=False, advanced_settings=None):
        """Create MediaMTX configuration optimized for multiple cameras and viewers"""
        if rtsp_port is None:
            rtsp_port = MEDIAMTX_PORT
        
        print(f"DEBUG: create_config called with user='{rtsp_username}', pass={'*' * len(rtsp_password) if rtsp_password else 'None'}")
            
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
            
            # ===== PROTOCOL SETTINGS =====
            'rtspTransports': ['tcp'],  # TCP only for reliability
            
            # ===== PERFORMANCE TUNING =====
            # Timeout settings - prevent premature disconnects
            'readTimeout': advanced_settings.get('mediamtx', {}).get('readTimeout', '30s') if advanced_settings else '30s',
            'writeTimeout': advanced_settings.get('mediamtx', {}).get('writeTimeout', '30s') if advanced_settings else '30s',
            
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
        }
        
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
        ff_input = ff_advanced.get('inputArgs', '-rtsp_transport tcp -timeout 10000000')
        ff_process = ff_advanced.get('processArgs', '-c:v libx264 -preset ultrafast -tune zerolatency -g 30')
        
        
        # Check if GLOBAL authentication is enabled
        enable_global_auth = bool(rtsp_username and rtsp_password)
        
        auth_users_map = {} # (user, pass) -> list of permissions
        sys_user = "internal_publisher"
        sys_pass = secrets.token_hex(16)
        
        # Ensure strings
        rtsp_username = str(rtsp_username) if rtsp_username else ""
        rtsp_password = str(rtsp_password) if rtsp_password else ""
        
        if enable_global_auth:
            print(f"    Global Authentication Enabled (User: {rtsp_username})")
            # Add system publisher with full rights (publish and read everywhere)
            # Use ~^.*$ for regex matching all paths
            auth_users_map[(sys_user, sys_pass)] = [
                {'action': 'publish', 'path': '~^.*$'}, 
                {'action': 'read', 'path': '~^.*$'},
                {'action': 'api', 'path': '~^.*$'},
                {'action': 'metrics', 'path': '~^.*$'},
                {'action': 'pprof', 'path': '~^.*$'}
            ]
            
            # Add the user defined global listener
            auth_users_map[(rtsp_username, rtsp_password)] = [
                {'action': 'read', 'path': '~^.*$'}
            ]

        # Only add paths for RUNNING cameras
        running_count = 0
        for camera in cameras:
            if camera.status == "running":
                running_count += 1
                
                # ===== MAIN STREAM - High Quality =====
                
                # Check for transcoding preference
                transcode_main = getattr(camera, 'transcode_main', False)
                main_source = camera.main_stream_url
                if transcode_main:
                    print(f"    Transcoding enabled for {camera.name} main-stream")
                    tgt_w = getattr(camera, 'main_width', 1920)
                    tgt_h = getattr(camera, 'main_height', 1080)
                    tgt_fps = getattr(camera, 'main_framerate', 30)
                    
                    # Inject credentials if global auth is on
                    if enable_global_auth:
                        dest_url = f"rtsp://{sys_user}:{sys_pass}@127.0.0.1:{rtsp_port}/{camera.path_name}_main"
                    else:
                        dest_url = f"rtsp://127.0.0.1:{rtsp_port}/{camera.path_name}_main"
                    
                    # Command for main stream (Baseline profile, strict GOP, NAL-HRD)
                    if system == "windows":
                        safe_source = f'"{main_source}"'
                        safe_dest = f'"{dest_url}"'
                    else:
                        safe_source = shlex.quote(main_source)
                        safe_dest = shlex.quote(dest_url)
                    
                    # Build FFmpeg command - Optimized for RAM and CPU usage
                    # -threads 2 limits memory footprint per process
                    # -rc-lookahead 0 prevents frame pre-buffering
                    cmd = (
                        f'"{ffmpeg_exe}" {ff_global} -nostdin '
                        f'{ff_input} '
                        f'-i {safe_source} '
                        f'-vf "scale={tgt_w}:{tgt_h}:force_original_aspect_ratio=decrease,pad={tgt_w}:{tgt_h}:(ow-iw)/2:(oh-ih)/2,format=yuv420p" '
                        f'{ff_process} '
                        f'-profile:v high -level 4.2 '
                        f'-threads 2 -g {tgt_fps} -sc_threshold 0 '
                        f'-b:v 2500k -maxrate 2500k -bufsize 5000k '
                        f'-r {tgt_fps} -c:a aac -ar 44100 -b:a 128k -f rtsp -rtsp_transport tcp {safe_dest}'
                    )
                    
                    main_path_cfg = {
                        'source': 'publisher',
                        'runOnInit': cmd,
                        'runOnInitRestart': False,  # Disable auto-restart to prevent zombie processes
                        'rtspTransport': 'tcp',
                        'overridePublisher': True,
                    }
                else:
                    main_path_cfg = {
                        'source': main_source,
                        'rtspTransport': 'tcp',
                        'sourceOnDemand': True,
                        'sourceOnDemandStartTimeout': '10s',
                        'sourceOnDemandCloseAfter': '10s',
                        'record': False,
                        'overridePublisher': True,
                        'fallback': '',
                    }
                

                
                config['paths'][f'{camera.path_name}_main'] = main_path_cfg
                
                # ===== SUB STREAM - Lower Quality, Optimized for Viewing =====
                
                # Check for transcoding preference
                transcode_sub = getattr(camera, 'transcode_sub', False)
                sub_source = camera.sub_stream_url
                
                if transcode_sub:
                    print(f"    Transcoding enabled for {camera.name} sub-stream")
                    
                    # Target resolution and frame rate
                    # Target resolution and frame rate
                    tgt_w = getattr(camera, 'sub_width', 640)
                    tgt_h = getattr(camera, 'sub_height', 480)
                    tgt_fps = getattr(camera, 'sub_framerate', 15)
                    
                    # Destination URL (Local MediaMTX)
                    if enable_global_auth:
                        dest_url = f"rtsp://{sys_user}:{sys_pass}@127.0.0.1:{rtsp_port}/{camera.path_name}_sub"
                    else:
                        dest_url = f"rtsp://127.0.0.1:{rtsp_port}/{camera.path_name}_sub"
                    
                    # Build FFmpeg command (Baseline profile, strict GOP, NAL-HRD)
                    if system == "windows":
                        safe_source = f'"{sub_source}"'
                        safe_dest = f'"{dest_url}"'
                    else:
                        safe_source = shlex.quote(sub_source)
                        safe_dest = shlex.quote(dest_url)
                    
                    cmd = (
                        f'"{ffmpeg_exe}" {ff_global} -nostdin '
                        f'{ff_input} '
                        f'-i {safe_source} '
                        f'-vf "scale={tgt_w}:{tgt_h}:force_original_aspect_ratio=decrease,pad={tgt_w}:{tgt_h}:(ow-iw)/2:(oh-ih)/2,format=yuv420p" '
                        f'{ff_process} '
                        f'-profile:v baseline -level 4.1 '
                        f'-threads 2 -g {tgt_fps} -sc_threshold 0 '
                        f'-b:v 800k -maxrate 800k -bufsize 1600k '
                        f'-r {tgt_fps} -c:a aac -ar 44100 -b:a 64k -f rtsp -rtsp_transport tcp {safe_dest}'
                    )
                    
                    
                    sub_path_cfg = {
                        'source': 'publisher',
                        'runOnInit': cmd,
                        'runOnInitRestart': False,  # Disable auto-restart to prevent zombie processes
                        'rtspTransport': 'tcp',
                        'sourceOnDemand': False,
                        'overridePublisher': True,
                    }
                else:
                    # Standard Proxy Mode
                    sub_path_cfg = {
                        'source': sub_source,
                        'rtspTransport': 'tcp',
                        
                        # On-demand disabled for multiple simultaneous viewers
                        'sourceOnDemand': True,
                        'sourceOnDemandStartTimeout': '10s',
                        'sourceOnDemandCloseAfter': '10s',
                        
                        # Recording settings
                        'record': False,
                        
                        # Republishing settings
                        'disablePublisherOverride': False,
                        'fallback': '',
                    }
                
                config['paths'][f'{camera.path_name}_sub'] = sub_path_cfg
                
                print(f"  Added {camera.name}: {camera.path_name}_main and {camera.path_name}_sub")
        
        print("-" * 40)
        print(f"  Total running cameras: {running_count}")
        print(f"  Total streams: {running_count * 2} (main + sub)")
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
                        
                        # Optimized for low-latency local ingestion with wallclock sync
                        inputs.append(f'-fflags nobuffer -flags low_delay -rtsp_transport tcp -probesize 1M -analyzeduration 1M -thread_queue_size 4096 -use_wallclock_as_timestamps 1 -i {safe_src}')
                        
                        # Scale and normalize timestamps to prevent sync-induced jumping
                        w = int(gf_cam.get('w', 640))
                        h = int(gf_cam.get('h', 480))
                        filters.append(f'[{input_idx}:v]scale={w}:{h},setpts=PTS-STARTPTS[v{input_idx}]')
                        active_gf_cams.append(gf_cam)
                        input_idx += 1
                    
                    if inputs:
                        # Construct overlay chain
                        # Force a constant baseline framerate
                        overlay_chain = f'color=black:s={res_w}x{res_h}:r={fps}[base];'
                        last_label = '[base]'
                        for i in range(len(active_gf_cams)):
                            gf_cam = active_gf_cams[i]
                            x = int(gf_cam.get('x', 0))
                            y = int(gf_cam.get('y', 0))
                            
                            next_label = f'[tmp{i}]' if i < len(active_gf_cams) - 1 else '[outv]'
                            # repeatlast=1 is critical: if one input stops, the others keep flowing
                            overlay_chain += f'{last_label}[v{i}]overlay={x}:{y}:eof_action=pass:repeatlast=1{next_label};'
                            last_label = next_label
                        
                        filter_complex = ";".join(filters) + ";" + overlay_chain
                        
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
                             encoder_args = '-c:v libx264 -preset veryfast -tune zerolatency'

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
                            'runOnInitRestart': False,  # Disable auto-restart to prevent zombie processes
                        }
                        print(f"      {layout_name} stream added at /{layout_id} ({res})")

        
        # Populate authInternalUsers if enabled
        if enable_global_auth and auth_users_map:
            config['authMethod'] = 'internal'
            config['authInternalUsers'] = []
            for (user, passwd), perms in auth_users_map.items():
                config['authInternalUsers'].append({
                    'user': user,
                    'pass': passwd,
                    'permissions': perms
                })
        
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
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

    def start(self, cameras, rtsp_port=None, rtsp_username=None, rtsp_password=None, grid_fusion=None, debug_mode=False, advanced_settings=None):
        """Start MediaMTX server"""
        self.debug_mode = debug_mode
        if not self.download_mediamtx():
            return False
        
        self.create_config(cameras, rtsp_port=rtsp_port, rtsp_username=rtsp_username, rtsp_password=rtsp_password, grid_fusion=grid_fusion, debug_mode=debug_mode, advanced_settings=advanced_settings)
        
        print("\nStarting MediaMTX RTSP Server...")
        
        try:
            # Use absolute path for executable
            exe_path = os.path.abspath(self.executable)
            config_path = os.path.abspath(self.config_file)
            
            print(f"   Executable: {exe_path}")
            print(f"   Config: {config_path}")
            
            self.process = subprocess.Popen(
                [exe_path, config_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1  # Line buffered
            )
            
            # Start thread to capture output and send to our Logger
            def capture_output(process):
                for line in process.stdout:
                    if line:
                        # Update buffer
                        with self._log_lock:
                            self.log_buffer.append(line.strip())
                            if len(self.log_buffer) > 100:
                                self.log_buffer.pop(0)
                        
                        # Only write to console if debug mode is ON OR it's not a spammy ffmpeg status line
                        # ffmpeg status lines contain "frame=" and "fps="
                        is_ffmpeg_status = "frame=" in line and "fps=" in line
                        
                        if self.debug_mode or not is_ffmpeg_status:
                            # Write to sys.stdout so our Logger captures it
                            sys.stdout.write(line)
                            sys.stdout.flush()
            
            output_thread = threading.Thread(target=capture_output, args=(self.process,), daemon=True)
            output_thread.start()
            
            time.sleep(3)
            
            if self.process.poll() is None:
                print(f"MediaMTX running on RTSP port {MEDIAMTX_PORT}")
                return True
            else:
                print("MediaMTX failed to start. Check console output above.")
                return False
                
        except Exception as e:
            print(f"Error starting MediaMTX: {e}")
            import traceback
            traceback.print_exc()
            return False

    def stop(self):
        """Stop MediaMTX server"""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except:
                self.process.kill()
            self.process = None
            print("MediaMTX stopped")
    
    def restart(self, cameras, rtsp_port=None, rtsp_username=None, rtsp_password=None, grid_fusion=None, debug_mode=False, advanced_settings=None):
        """Restart MediaMTX with new configuration"""
        print("\nRestarting MediaMTX...")
        self.stop()
        time.sleep(3)
        return self.start(cameras, rtsp_port=rtsp_port, rtsp_username=rtsp_username, rtsp_password=rtsp_password, grid_fusion=grid_fusion, debug_mode=debug_mode, advanced_settings=advanced_settings)
