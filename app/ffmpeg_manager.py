import os
import platform
import subprocess
import zipfile
import shutil
import requests

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


class FFmpegManager:
    """Manages FFmpeg/FFprobe installation"""

    def __init__(self):
        self.ffprobe_executable = self._get_ffprobe_name()
        self.ffmpeg_dir = "ffmpeg"

    def _get_ffprobe_name(self):
        """Get the correct ffprobe executable name for the platform"""
        system = platform.system().lower()
        if system == "windows":
            return "ffprobe.exe"
        return "ffprobe"

    def is_ffprobe_available(self):
        """Check if ffprobe is available ONLY in local directory"""
        local_path = os.path.join(self.ffmpeg_dir, self.ffprobe_executable)
        if os.path.exists(local_path):
            return local_path
        return None

    def download_ffmpeg(self):
        """Download FFmpeg if not present"""
        logger.info("Downloading FFmpeg...")

        system = platform.system().lower()
        machine = platform.machine().lower()

        # Determine download URL based on platform
        if system == "windows":
            if "64" in machine or "amd64" in machine or "x86_64" in machine:
                # Use gyan.dev builds for Windows (essentials build)
                url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
                archive_name = "ffmpeg-release-essentials.zip"
            else:
                logger.error("Unsupported Windows architecture: %s", machine)
                return False

        elif system == "darwin":  # macOS
            logger.info("For macOS, please install FFmpeg using Homebrew:")
            logger.info("    brew install ffmpeg")
            return False

        elif system == "linux":
            if "aarch64" in machine or "arm64" in machine:
                # John Van Sickle's static builds for ARM64
                url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz"
                archive_name = "ffmpeg-release-arm64-static.tar.xz"
            elif "64" in machine or "x86_64" in machine or "amd64" in machine:
                # John Van Sickle's static builds for AMD64
                url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
                archive_name = "ffmpeg-release-amd64-static.tar.xz"
            else:
                logger.error("Unsupported Linux architecture: %s", machine)
                return False
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
            logger.info("Downloaded FFmpeg")

            # Extract safely (with path traversal protection)
            logger.info("Extracting...")
            if archive_name.endswith('.zip'):
                with zipfile.ZipFile(archive_name, 'r') as zip_ref:
                    # Extract to temporary directory with path traversal protection
                    temp_extract_dir = os.path.abspath('ffmpeg_temp')
                    os.makedirs(temp_extract_dir, exist_ok=True)
                    _safe_extract_zip(zip_ref, temp_extract_dir)

                # Find the bin directory and move executables
                os.makedirs(self.ffmpeg_dir, exist_ok=True)

                for root, dirs, files in os.walk('ffmpeg_temp'):
                    if 'bin' in root:
                        for file in files:
                            if file.startswith('ffprobe') or file.startswith('ffmpeg'):
                                src = os.path.join(root, file)
                                dst = os.path.join(self.ffmpeg_dir, file)
                                shutil.copy2(src, dst)
                                logger.info("Extracted %s", file)

                # Cleanup
                shutil.rmtree('ffmpeg_temp')
            elif archive_name.endswith('.tar.xz'):
                import tarfile
                with tarfile.open(archive_name, 'r:xz') as tar_ref:
                    temp_extract_dir = os.path.abspath('ffmpeg_temp')
                    os.makedirs(temp_extract_dir, exist_ok=True)
                    _safe_extract_tar(tar_ref, temp_extract_dir)

                os.makedirs(self.ffmpeg_dir, exist_ok=True)
                for root, dirs, files in os.walk('ffmpeg_temp'):
                    for file in files:
                        if file == 'ffprobe' or file == 'ffmpeg':
                            src = os.path.join(root, file)
                            dst = os.path.join(self.ffmpeg_dir, file)
                            shutil.copy2(src, dst)
                            # Make executable
                            os.chmod(dst, 0o755)
                            logger.info("Extracted %s", file)

                shutil.rmtree('ffmpeg_temp')

            logger.info("Extracted FFmpeg")

            # Cleanup archive
            os.remove(archive_name)

            # Verify extraction
            ffprobe_path = os.path.join(self.ffmpeg_dir, self.ffprobe_executable)
            if not os.path.exists(ffprobe_path):
                logger.error("FFprobe not found after extraction: %s", ffprobe_path)
                return False

            logger.info("FFmpeg ready: %s", self.ffmpeg_dir)
            return True

        except requests.exceptions.RequestException as e:
            logger.error("Download failed: %s", e)
            return False
        except Exception as e:
            logger.error("Installation failed: %s", e)
            import traceback
            traceback.print_exc()
            return False

    def get_ffmpeg_path(self):
        """Get the path to ffmpeg, strictly using local directory"""
        system = platform.system().lower()
        executable = "ffmpeg.exe" if system == "windows" else "ffmpeg"

        # 1. Check local directory ONLY
        local_path = os.path.join(self.ffmpeg_dir, executable)
        if os.path.exists(local_path):
            return local_path

        # 2. Try to download if missing (Windows and Linux)
        if system in ["windows", "linux"]:
            logger.warning("Local FFmpeg not found. Attempting to download for %s...", system)
            if self.download_ffmpeg():
                return os.path.join(self.ffmpeg_dir, executable)

        return local_path # Return the expected local path even if missing

    def get_ffprobe_path(self):
        """Get the path to ffprobe, downloading if necessary"""
        ffprobe_path = self.is_ffprobe_available()

        if ffprobe_path:
            return ffprobe_path

        # Try to download
        system = platform.system().lower()
        if system in ["windows", "linux"]:
            logger.warning("FFprobe not found. Attempting to download for %s...", system)
            if self.download_ffmpeg():
                return os.path.join(self.ffmpeg_dir, self.ffprobe_executable)

        return self.ffprobe_executable # Fallback
