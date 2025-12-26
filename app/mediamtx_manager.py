import os
import time
import platform
import subprocess
import requests
import yaml
import zipfile
import tarfile
import shlex
from pathlib import Path
from .config import MEDIAMTX_PORT, MEDIAMTX_API_PORT

class MediaMTXManager:
    """Manages MediaMTX RTSP server"""
    
    def __init__(self):
        self.process = None
        self.config_file = "mediamtx.yml"
        self.executable = self._get_executable_name()
        
    def _get_executable_name(self):
        """Get the correct executable name for the platform"""
        system = platform.system().lower()
        if system == "windows":
            return "mediamtx.exe"
        return "mediamtx"
    
    def _get_latest_version(self):
        """Locked to version v1.15.5 as requested"""
        return "v1.15.5"

    def _parse_version(self, version_str):
        """Parse version string like 'v1.15.5' into a list of integers [1, 15, 5]"""
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
                    print(f"✓ MediaMTX is up to date ({current_version})")
                    return True
                elif self._version_is_newer(current_version, latest_version):
                    print(f"🔄 Newer MediaMTX version available: {current_version} -> {latest_version}")
                    print("📥 Preparing to update...")
                else:
                    # Current version is actually newer or equal
                    print(f"✓ MediaMTX is up to date ({current_version})")
                    return True
            except Exception as e:
                print(f"⚠️ Could not check MediaMTX version: {e}")
                return True
        else:
            print(f"📥 MediaMTX not found. Downloading latest version: {latest_version}")
        
        version = latest_version
        print(f"🚀 Installing MediaMTX {version}...")
        
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        # Determine download URL based on platform
        base_url = f"https://github.com/bluenviron/mediamtx/releases/download/{version}/"
        
        if system == "windows":
            if "64" in machine or "amd64" in machine or "x86_64" in machine:
                url = base_url + f"mediamtx_{version}_windows_amd64.zip"
                archive_name = f"mediamtx_{version}_windows_amd64.zip"
            else:
                print("❌ Unsupported Windows architecture:", machine)
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
                url = base_url + f"mediamtx_{version}_linux_arm64v8.tar.gz"
                archive_name = f"mediamtx_{version}_linux_arm64v8.tar.gz"
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
            print(f"❌ Unsupported operating system: {system}")
            return False
        
        print(f"  Platform: {system} {machine}")
        print(f"  Downloading from: {url}")
        
        # Ask for confirmation
        try:
            confirm = input(f"\n❓ Would you like to download and install MediaMTX {version}? (y/n): ")
            if confirm.lower() not in ['y', 'yes']:
                print("❌ Installation cancelled by user.")
                return False
        except EOFError:
            # Handle non-interactive environments
            print("⚠️  Non-interactive environment detected, proceeding with download...")
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
            
            print("\n✓ Downloaded MediaMTX")
            
            # Extract
            print("  Extracting...")
            if archive_name.endswith('.zip'):
                with zipfile.ZipFile(archive_name, 'r') as zip_ref:
                    zip_ref.extractall('.')
            else:
                with tarfile.open(archive_name, 'r:gz') as tar_ref:
                    tar_ref.extractall('.')
            
            print("✓ Extracted MediaMTX")
            
            # Make executable on Unix-like systems
            if system in ["darwin", "linux"]:
                os.chmod(self.executable, 0o755)
                print("✓ Set executable permissions")
            
            # Cleanup archive
            os.remove(archive_name)
            
            # Verify extraction
            if not Path(self.executable).exists():
                print(f"❌ Executable not found after extraction: {self.executable}")
                return False
            
            print(f"✓ MediaMTX ready: {self.executable}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Download failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Installation failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def create_config(self, cameras, rtsp_port=None):
        """Create MediaMTX configuration optimized for multiple cameras and viewers"""
        if rtsp_port is None:
            rtsp_port = MEDIAMTX_PORT
            
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
            'hlsSegmentCount': 10, # Increased buffer for irregular cameras
            'hlsSegmentDuration': '1s',  # Set to minimum to trigger on every keyframe
            'hlsPartDuration': '200ms',  # LL-HLS part duration
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
            'readTimeout': '30s',  # How long to wait for data from source
            'writeTimeout': '30s',  # How long to wait when writing to clients
            
            # Buffer and queue settings
            'writeQueueSize': 2048,  # Increased from 1024 for multiple viewers
            'udpMaxPayloadSize': 1472,  # Standard MTU-safe size
            
            # ===== MEMORY MANAGEMENT =====
            # Reduce log verbosity to save CPU
            'logLevel': 'warn',  # Reduce log verbosity (info/warn/error)
            
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
            
        print(f"   Using FFmpeg: {ffmpeg_exe}")
        
        import platform
        system = platform.system().lower()

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
                    print(f"    ℹ️  Transcoding enabled for {camera.name} main-stream")
                    tgt_w = getattr(camera, 'main_width', 1920)
                    tgt_h = getattr(camera, 'main_height', 1080)
                    tgt_fps = getattr(camera, 'main_framerate', 30)
                    dest_url = f"rtsp://127.0.0.1:{rtsp_port}/{camera.path_name}_main"
                    
                    # Command for main stream (Baseline profile, strict GOP, NAL-HRD)
                    if system == "windows":
                        safe_source = f'"{main_source}"'
                        safe_dest = f'"{dest_url}"'
                    else:
                        import shlex
                        safe_source = shlex.quote(main_source)
                        safe_dest = shlex.quote(dest_url)
                    
                    # Build FFmpeg command - Optimized for RAM and CPU usage
                    # -threads 2 limits memory footprint per process
                    # -rc-lookahead 0 prevents frame pre-buffering
                    cmd = (
                        f'"{ffmpeg_exe}" -hide_banner -loglevel warning -nostdin '
                        f'-rtsp_transport tcp -use_wallclock_as_timestamps 1 '
                        f'-i {safe_source} '
                        f'-vf "scale={tgt_w}:{tgt_h}:force_original_aspect_ratio=decrease,pad={tgt_w}:{tgt_h}:(ow-iw)/2:(oh-ih)/2,format=yuv420p" '
                        f'-c:v libx264 -profile:v baseline -level:v 4.0 -preset ultrafast -tune zerolatency '
                        f'-threads 2 -g {tgt_fps * 4} -keyint_min {tgt_fps} -sc_threshold 0 '
                        f'-x264-params "force-cfr=1:nal-hrd=vbr:rc-lookahead=0" -bf 0 -b:v 2500k -maxrate 2500k -bufsize 2500k '
                        f'-r {tgt_fps} -c:a aac -ar 44100 -b:a 128k -f rtsp {safe_dest}'
                    )
                    
                    main_path_cfg = {
                        'source': 'publisher',
                        'runOnInit': cmd,
                        'runOnInitRestart': True,
                        'rtspTransport': 'tcp',
                        'sourceOnDemand': False,
                        'disablePublisherOverride': False,
                    }
                else:
                    main_path_cfg = {
                        'source': main_source,
                        'rtspTransport': 'tcp',
                        'sourceOnDemand': False,
                        'sourceOnDemandStartTimeout': '10s',
                        'sourceOnDemandCloseAfter': '10s',
                        'record': False,
                        'disablePublisherOverride': False,
                        'fallback': '',
                    }
                
                # Add authentication if set
                if getattr(camera, 'stream_username', '') and getattr(camera, 'stream_password', ''):
                    main_path_cfg['readUser'] = camera.stream_username
                    main_path_cfg['readPass'] = camera.stream_password
                
                config['paths'][f'{camera.path_name}_main'] = main_path_cfg
                
                # ===== SUB STREAM - Lower Quality, Optimized for Viewing =====
                
                # Check for transcoding preference
                transcode_sub = getattr(camera, 'transcode_sub', False)
                sub_source = camera.sub_stream_url
                
                if transcode_sub:
                    print(f"    ℹ️  Transcoding enabled for {camera.name} sub-stream")
                    
                    # Target resolution and frame rate
                    tgt_w = getattr(camera, 'sub_width', 640)
                    tgt_h = getattr(camera, 'sub_height', 480)
                    tgt_fps = getattr(camera, 'sub_framerate', 15)
                    
                    # Destination URL (Local MediaMTX)
                    dest_url = f"rtsp://127.0.0.1:{rtsp_port}/{camera.path_name}_sub"
                    
                    # Build FFmpeg command (Baseline profile, strict GOP, NAL-HRD)
                    if system == "windows":
                        safe_source = f'"{sub_source}"'
                        safe_dest = f'"{dest_url}"'
                    else:
                        import shlex
                        safe_source = shlex.quote(sub_source)
                        safe_dest = shlex.quote(dest_url)
                    
                    cmd = (
                        f'"{ffmpeg_exe}" -hide_banner -loglevel warning -nostdin '
                        f'-rtsp_transport tcp -use_wallclock_as_timestamps 1 '
                        f'-i {safe_source} '
                        f'-vf "scale={tgt_w}:{tgt_h}:force_original_aspect_ratio=decrease,pad={tgt_w}:{tgt_h}:(ow-iw)/2:(oh-ih)/2,format=yuv420p" '
                        f'-c:v libx264 -profile:v baseline -level:v 3.0 -preset ultrafast -tune zerolatency '
                        f'-threads 2 -g {tgt_fps} -keyint_min {tgt_fps} -sc_threshold 0 '
                        f'-x264-params "force-cfr=1:nal-hrd=vbr:rc-lookahead=0" -bf 0 -b:v 800k -maxrate 800k -bufsize 800k '
                        f'-r {tgt_fps} -c:a aac -ar 44100 -b:a 64k -f rtsp {safe_dest}'
                    )
                    
                    sub_path_cfg = {
                        'source': 'publisher',
                        'runOnInit': cmd,
                        'runOnInitRestart': True,
                        'rtspTransport': 'tcp',
                        'sourceOnDemand': False,
                        'disablePublisherOverride': False,
                    }
                else:
                    # Standard Proxy Mode
                    sub_path_cfg = {
                        'source': sub_source,
                        'rtspTransport': 'tcp',
                        
                        # On-demand disabled for multiple simultaneous viewers
                        'sourceOnDemand': False,
                        'sourceOnDemandStartTimeout': '10s',
                        'sourceOnDemandCloseAfter': '10s',
                        
                        # Recording settings
                        'record': False,
                        
                        # Republishing settings
                        'disablePublisherOverride': False,
                        'fallback': '',
                    }
                
                # Add authentication if set
                if getattr(camera, 'stream_username', '') and getattr(camera, 'stream_password', ''):
                    sub_path_cfg['readUser'] = camera.stream_username
                    sub_path_cfg['readPass'] = camera.stream_password
                
                config['paths'][f'{camera.path_name}_sub'] = sub_path_cfg
                
                print(f"  ✓ Added {camera.name}: {camera.path_name}_main and {camera.path_name}_sub")
        
        print("\n" + "-" * 40)
        print(f"  Total running cameras: {running_count}")
        print(f"  Total streams: {running_count * 2} (main + sub)")
        
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    def start(self, cameras, rtsp_port=None):
        """Start MediaMTX server"""
        if not self.download_mediamtx():
            return False
        
        self.create_config(cameras, rtsp_port=rtsp_port)
        
        print("\n🚀 Starting MediaMTX RTSP Server...")
        
        try:
            # Use absolute path for executable
            exe_path = os.path.abspath(self.executable)
            config_path = os.path.abspath(self.config_file)
            
            print(f"   Executable: {exe_path}")
            print(f"   Config: {config_path}")
            
            self.process = subprocess.Popen(
                [exe_path, config_path],
                stdout=None,
                stderr=None,
                text=True
            )
            
            time.sleep(3)
            
            if self.process.poll() is None:
                print(f"✓ MediaMTX running on RTSP port {MEDIAMTX_PORT}")
                return True
            else:
                print("❌ MediaMTX failed to start. Check console output above.")
                return False
                
        except Exception as e:
            print(f"❌ Error starting MediaMTX: {e}")
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
            print("✓ MediaMTX stopped")
    
    def restart(self, cameras):
        """Restart MediaMTX with new configuration"""
        print("\n🔄 Restarting MediaMTX...")
        self.stop()
        time.sleep(3)
        return self.start(cameras)
