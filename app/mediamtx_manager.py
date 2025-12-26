import os
import time
import platform
import subprocess
import requests
import yaml
import zipfile
import tarfile
import shlex
import shutil
from pathlib import Path
from .config import MEDIAMTX_PORT, MEDIAMTX_API_PORT
from .logging_config import get_logger

logger = get_logger(__name__)


def _is_safe_path(base_path, member_path):
    """
    Check if a path is safe for extraction (no path traversal).
    Returns True if the path is safe, False otherwise.
    """
    # Normalize paths
    base_path = os.path.abspath(base_path)
    # Join and normalize the target path
    target_path = os.path.normpath(os.path.join(base_path, member_path))
    # Check if the target is under the base path
    return target_path.startswith(base_path + os.sep) or target_path == base_path


def _safe_extract_zip(zip_ref, extract_dir):
    """
    Safely extract a zip file, checking for path traversal attacks.
    """
    extract_dir = os.path.abspath(extract_dir)
    for member in zip_ref.namelist():
        # Check for absolute paths or path traversal
        if os.path.isabs(member) or '..' in member:
            if not _is_safe_path(extract_dir, member):
                raise ValueError(f"Unsafe path detected in archive: {member}")
        # Additional check for the resolved path
        target_path = os.path.normpath(os.path.join(extract_dir, member))
        if not target_path.startswith(extract_dir):
            raise ValueError(f"Path traversal detected in archive: {member}")
    # All paths are safe, extract
    zip_ref.extractall(extract_dir)


def _safe_extract_tar(tar_ref, extract_dir):
    """
    Safely extract a tar file, checking for path traversal attacks.
    """
    extract_dir = os.path.abspath(extract_dir)
    for member in tar_ref.getmembers():
        member_path = member.name
        # Check for absolute paths or path traversal
        if os.path.isabs(member_path) or '..' in member_path:
            if not _is_safe_path(extract_dir, member_path):
                raise ValueError(f"Unsafe path detected in archive: {member_path}")
        # Additional check for the resolved path
        target_path = os.path.normpath(os.path.join(extract_dir, member_path))
        if not target_path.startswith(extract_dir):
            raise ValueError(f"Path traversal detected in archive: {member_path}")
    # All paths are safe, extract
    tar_ref.extractall(extract_dir)


class MediaMTXManager:
    """Manages MediaMTX RTSP server"""

    def __init__(self):
        self.process = None
        self.config_file = "mediamtx.yml"
        self.executable = self._get_executable_name()
        # Check environment variable to disable auto-downloads (security best practice)
        self._allow_downloads = os.environ.get('ONVIF_ALLOW_BINARY_DOWNLOADS', 'false').lower() in ('true', '1', 'yes')

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

    def _get_executable_path(self):
        """Get the path to mediamtx (system PATH first, then local)"""
        # 1. Check system PATH first (preferred - for Docker/system installs)
        system_path = shutil.which('mediamtx')
        if system_path:
            logger.debug("Found mediamtx in system PATH: %s", system_path)
            return system_path

        # 2. Fall back to local directory
        if Path(self.executable).exists():
            logger.debug("Found mediamtx in local directory: %s", self.executable)
            return os.path.abspath(self.executable)

        return None

    def download_mediamtx(self):
        """Download MediaMTX if not present or update if newer version available"""
        latest_version = self._get_latest_version()

        # Check system PATH first (preferred for Docker/system installs)
        system_path = shutil.which('mediamtx')
        if system_path:
            logger.info("Using system-installed mediamtx: %s", system_path)
            # Update executable to use system path
            self.executable = system_path
            return True

        # Check if already installed locally
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
                    logger.info("MediaMTX is up to date (%s)", current_version)
                    return True
                elif self._version_is_newer(current_version, latest_version):
                    logger.info("Newer MediaMTX version available: %s -> %s", current_version, latest_version)
                    logger.info("Preparing to update...")
                else:
                    # Current version is actually newer or equal
                    logger.info("MediaMTX is up to date (%s)", current_version)
                    return True
            except Exception as e:
                logger.warning("Could not check MediaMTX version: %s", e)
                return True
        else:
            logger.info("MediaMTX not found.")
            # Security: Auto-downloads are disabled by default
            if not self._allow_downloads:
                logger.error("MediaMTX auto-download is disabled (security). Set ONVIF_ALLOW_BINARY_DOWNLOADS=true to enable.")
                logger.info("Or manually download MediaMTX from: https://github.com/bluenviron/mediamtx/releases")
                return False
            logger.info("Downloading latest version: %s", latest_version)

        # Security check for updates too
        if not self._allow_downloads:
            logger.warning("MediaMTX update available but auto-downloads disabled. Current version will be used.")
            return True

        version = latest_version
        logger.info("Installing MediaMTX %s...", version)

        system = platform.system().lower()
        machine = platform.machine().lower()

        # Determine download URL based on platform
        base_url = f"https://github.com/bluenviron/mediamtx/releases/download/{version}/"

        if system == "windows":
            if "64" in machine or "amd64" in machine or "x86_64" in machine:
                url = base_url + f"mediamtx_{version}_windows_amd64.zip"
                archive_name = f"mediamtx_{version}_windows_amd64.zip"
            else:
                logger.error("Unsupported Windows architecture: %s", machine)
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
            logger.error("Unsupported operating system: %s", system)
            return False

        logger.info("Platform: %s %s", system, machine)
        logger.info("Downloading from: %s", url)

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

            print()  # Newline after progress
            logger.info("Downloaded MediaMTX")

            # Extract safely (with path traversal protection)
            logger.info("Extracting...")
            extract_dir = os.path.abspath('.')
            if archive_name.endswith('.zip'):
                with zipfile.ZipFile(archive_name, 'r') as zip_ref:
                    _safe_extract_zip(zip_ref, extract_dir)
            else:
                with tarfile.open(archive_name, 'r:gz') as tar_ref:
                    _safe_extract_tar(tar_ref, extract_dir)

            logger.info("Extracted MediaMTX")

            # Make executable on Unix-like systems
            if system in ["darwin", "linux"]:
                os.chmod(self.executable, 0o755)
                logger.info("Set executable permissions")

            # Cleanup archive
            os.remove(archive_name)

            # Verify extraction
            if not Path(self.executable).exists():
                logger.error("Executable not found after extraction: %s", self.executable)
                return False

            logger.info("MediaMTX ready: %s", self.executable)
            return True

        except requests.exceptions.RequestException as e:
            logger.error("Download failed: %s", e)
            return False
        except Exception as e:
            logger.error("Installation failed: %s", e)
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

        logger.info("Using FFmpeg: %s", ffmpeg_exe)

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
                    logger.info("Transcoding enabled for %s main-stream", camera.name)
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

                    config['paths'][f'{camera.path_name}_main'] = {
                        'source': 'publisher',
                        'runOnInit': cmd,
                        'runOnInitRestart': True,
                        'rtspTransport': 'tcp',
                        'sourceOnDemand': False,
                        'disablePublisherOverride': False,
                    }
                else:
                    config['paths'][f'{camera.path_name}_main'] = {
                        'source': main_source,
                        'rtspTransport': 'tcp',
                        'sourceOnDemand': False,
                        'sourceOnDemandStartTimeout': '10s',
                        'sourceOnDemandCloseAfter': '10s',
                        'record': False,
                        'disablePublisherOverride': False,
                        'fallback': '',
                    }

                # ===== SUB STREAM - Lower Quality, Optimized for Viewing =====

                # Check for transcoding preference
                transcode_sub = getattr(camera, 'transcode_sub', False)
                sub_source = camera.sub_stream_url

                if transcode_sub:
                    logger.info("Transcoding enabled for %s sub-stream", camera.name)

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

                    config['paths'][f'{camera.path_name}_sub'] = {
                        'source': 'publisher',
                        'runOnInit': cmd,
                        'runOnInitRestart': True,
                        'rtspTransport': 'tcp',
                        'sourceOnDemand': False,
                        'disablePublisherOverride': False,
                    }
                else:
                    # Standard Proxy Mode
                    config['paths'][f'{camera.path_name}_sub'] = {
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

                logger.info("Added %s: %s_main and %s_sub", camera.name, camera.path_name, camera.path_name)

        logger.info("-" * 40)
        logger.info("Total running cameras: %d", running_count)
        logger.info("Total streams: %d (main + sub)", running_count * 2)

        with open(self.config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    def start(self, cameras, rtsp_port=None):
        """Start MediaMTX server"""
        if not self.download_mediamtx():
            return False

        self.create_config(cameras, rtsp_port=rtsp_port)

        logger.info("Starting MediaMTX RTSP Server...")

        try:
            # Use absolute path for executable
            exe_path = os.path.abspath(self.executable)
            config_path = os.path.abspath(self.config_file)

            logger.debug("Executable: %s", exe_path)
            logger.debug("Config: %s", config_path)

            self.process = subprocess.Popen(
                [exe_path, config_path],
                stdout=None,
                stderr=None,
                text=True
            )

            time.sleep(3)

            if self.process.poll() is None:
                logger.info("MediaMTX running on RTSP port %d", MEDIAMTX_PORT)
                return True
            else:
                logger.error("MediaMTX failed to start. Check console output above.")
                return False

        except Exception as e:
            logger.error("Error starting MediaMTX: %s", e)
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
            logger.info("MediaMTX stopped")

    def restart(self, cameras):
        """Restart MediaMTX with new configuration"""
        logger.info("Restarting MediaMTX...")
        self.stop()
        time.sleep(3)
        return self.start(cameras)
