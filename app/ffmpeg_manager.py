import os
import platform
import subprocess
import zipfile
import shutil
import requests
import re

class FFmpegManager:
    """Manages FFmpeg/FFprobe installation"""
    
    # Minimum recommended version for full feature support
    MIN_RECOMMENDED_VERSION = (4, 0, 0)  # FFmpeg 4.0.0
    
    def __init__(self):
        self.ffprobe_executable = self._get_ffprobe_name()
        self.ffmpeg_executable = "ffmpeg.exe" if platform.system().lower() == "windows" else "ffmpeg"
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
        print("  Downloading FFmpeg...")
        
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        # Determine download URL based on platform
        if system == "windows":
            if "64" in machine or "amd64" in machine or "x86_64" in machine:
                # Use gyan.dev builds for Windows (essentials build)
                url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
                archive_name = "ffmpeg-release-essentials.zip"
            else:
                print("  Unsupported Windows architecture:", machine)
                return False
                
        elif system == "darwin":  # macOS
            print("  For macOS, please install FFmpeg using Homebrew:")
            print("    brew install ffmpeg")
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
                print("  Unsupported Linux architecture:", machine)
                return False
        else:
            print(f"  Unsupported operating system: {system}")
            return False
        
        print(f"  Platform: {system} {machine}")
        print(f"  Note: These are the official recommended static builds linked from ffmpeg.org")
        print(f"  Downloading from: {url}")
        
        # Ask for confirmation
        try:
            confirm = input(f"\n  Would you like to download and install FFmpeg from this source? (y/n): ")
            if confirm.lower() not in ['y', 'yes']:
                print("  Installation cancelled by user.")
                return False
        except EOFError:
            # Handle non-interactive environments
            print("  Non-interactive environment detected, proceeding with download...")
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
            
            print("\n  Downloaded FFmpeg")
            
            # Extract
            print("  Extracting...")
            if archive_name.endswith('.zip'):
                with zipfile.ZipFile(archive_name, 'r') as zip_ref:
                    # Extract to temporary directory
                    zip_ref.extractall('ffmpeg_temp')
                
                # Find the bin directory and move executables
                os.makedirs(self.ffmpeg_dir, exist_ok=True)
                
                for root, dirs, files in os.walk('ffmpeg_temp'):
                    if 'bin' in root:
                        for file in files:
                            if file.startswith('ffprobe') or file.startswith('ffmpeg'):
                                src = os.path.join(root, file)
                                dst = os.path.join(self.ffmpeg_dir, file)
                                shutil.copy2(src, dst)
                                print(f"  Extracted {file}")
                
                # Cleanup
                shutil.rmtree('ffmpeg_temp')
            elif archive_name.endswith('.tar.xz'):
                import tarfile
                with tarfile.open(archive_name, 'r:xz') as tar_ref:
                    tar_ref.extractall('ffmpeg_temp')
                
                os.makedirs(self.ffmpeg_dir, exist_ok=True)
                for root, dirs, files in os.walk('ffmpeg_temp'):
                    for file in files:
                        if file == 'ffprobe' or file == 'ffmpeg':
                            src = os.path.join(root, file)
                            dst = os.path.join(self.ffmpeg_dir, file)
                            shutil.copy2(src, dst)
                            # Make executable
                            os.chmod(dst, 0o755)
                            print(f"  Extracted {file}")
                
                shutil.rmtree('ffmpeg_temp')
            
            print("  Extracted FFmpeg")
            
            # Cleanup archive
            os.remove(archive_name)
            
            # Verify extraction
            ffprobe_path = os.path.join(self.ffmpeg_dir, self.ffprobe_executable)
            if not os.path.exists(ffprobe_path):
                print(f"  FFprobe not found after extraction: {ffprobe_path}")
                return False
            
            print(f"  FFmpeg ready: {self.ffmpeg_dir}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"  Download failed: {e}")
            return False
        except Exception as e:
            print(f"  Installation failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def install_system_ffmpeg(self):
        """Install FFmpeg using system package manager (Linux only)"""
        if platform.system().lower() != "linux":
            return False
            
        print("  Attempting to install FFmpeg via system package manager...")
        
        # Package managers: (name, update_cmd, install_cmd)
        managers = [
            ("apt-get", ["apt-get", "update"], ["apt-get", "install", "-y", "ffmpeg"]),
            ("dnf", None, ["dnf", "install", "-y", "ffmpeg"]),
            ("pacman", None, ["pacman", "-S", "--noconfirm", "ffmpeg"]),
            ("yum", None, ["yum", "install", "-y", "ffmpeg"]),
            ("apk", None, ["apk", "add", "--no-cache", "ffmpeg"]),
            ("zypper", None, ["zypper", "install", "-y", "ffmpeg"])
        ]
        
        for mgr, update_cmd, install_cmd in managers:
            if shutil.which(mgr):
                print(f"  Found package manager: {mgr}")
                
                # Ask for confirmation
                try:
                    print(f"  System FFmpeg is missing.")
                    confirm = input(f"  Would you like to install it using {mgr}? (y/n): ")
                    if confirm.lower() not in ['y', 'yes']:
                        print("  Installation cancelled by user.")
                        return False
                except EOFError:
                    # Handle non-interactive environments
                    print("  Non-interactive environment detected, proceeding with installation...")
                    pass
                
                try:
                    # Check if likely running as root or need sudo
                    # os.geteuid() is available on Unix
                    is_root = os.geteuid() == 0
                    prefix = [] if is_root else ["sudo"]
                    
                    if update_cmd:
                        print(f"  Running system update...")
                        try:
                            subprocess.run(prefix + update_cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        except Exception:
                            pass # Update failure shouldn't necessarily block install
                        
                    print(f"  Installing...")
                    subprocess.check_call(prefix + install_cmd)
                    print("  FFmpeg installed successfully")
                    return True
                except subprocess.CalledProcessError as e:
                    print(f"  Failed to install using {mgr}: {e}")
                    # Continue to next manager? Unlikely to have multiple valid ones but possible.
                except Exception as e:
                    print(f"  Error: {e}")
                    
        print("  No supported package manager found or installation failed.")
        return False

    def get_ffmpeg_version(self, ffmpeg_path="ffmpeg"):
        """
        Get FFmpeg version as a tuple (major, minor, patch)
        Returns None if FFmpeg is not installed or version cannot be determined
        """
        try:
            result = subprocess.run(
                [ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return None
            
            # Parse version from output like "ffmpeg version 4.4.2-0ubuntu0.22.04.1"
            # or "ffmpeg version 7.1.3-0+deb13u1+rpt1"
            version_line = result.stdout.split('\n')[0]
            
            # Extract version number using regex
            match = re.search(r'ffmpeg version (\d+)\.(\d+)\.?(\d*)', version_line)
            if match:
                major = int(match.group(1))
                minor = int(match.group(2))
                patch = int(match.group(3)) if match.group(3) else 0
                return (major, minor, patch)
            
            return None
            
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return None
    
    def is_version_sufficient(self, version):
        """Check if version meets minimum requirements"""
        if version is None:
            return False
        return version >= self.MIN_RECOMMENDED_VERSION
    
    def get_active_version(self):
        """Get the version of the ffmpeg binary that would actually be used"""
        path = self.get_ffmpeg_path()
        return self.get_ffmpeg_version(path)
    
    def check_and_prompt_upgrade(self):
        """
        Check FFmpeg version and prompt user to upgrade if needed.
        Returns True if FFmpeg is sufficient, False otherwise.
        """
        print("\nChecking FFmpeg installation...")
        
        # Try to find ffmpeg
        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            # Try local directory
            local_ffmpeg = os.path.join(self.ffmpeg_dir, self.ffmpeg_executable)
            if os.path.exists(local_ffmpeg):
                ffmpeg_path = local_ffmpeg
        
        version = self.get_ffmpeg_version(ffmpeg_path) if ffmpeg_path else None
        
        if version is None:
            print("=" * 60)
            print("WARNING: FFmpeg not found or version cannot be determined!")
            print("=" * 60)
            print("FFmpeg is required for transcoding features.")
            print("Please install FFmpeg manually:")
            print("")
            
            system = platform.system().lower()
            if system == "linux":
                print("  sudo apt update && sudo apt install -y ffmpeg")
            elif system == "darwin":
                print("  brew install ffmpeg")
            elif system == "windows":
                print("  Download from: https://ffmpeg.org/download.html")
            
            print("=" * 60)
            return False
        
        version_str = f"{version[0]}.{version[1]}.{version[2]}"
        min_version_str = f"{self.MIN_RECOMMENDED_VERSION[0]}.{self.MIN_RECOMMENDED_VERSION[1]}.{self.MIN_RECOMMENDED_VERSION[2]}"
        
        if self.is_version_sufficient(version):
            print(f"FFmpeg version {version_str} detected (meets requirements)")
            return True
        
        # Version is too old
        print("=" * 60)
        print("WARNING: FFmpeg version is outdated!")
        print("=" * 60)
        print(f"Current version:  {version_str}")
        print(f"Recommended:      {min_version_str} or higher")
        print("")
        print("Older FFmpeg versions may not support all features:")
        print("  - Advanced timeout options (-timeout)")
        print("  - Reconnect functionality")
        print("  - Hardware encoding")
        print("")
        
        system = platform.system().lower()
        
        if system == "linux":
            print("Would you like to upgrade FFmpeg now?")
            print("This will run: sudo apt update && sudo apt install -y ffmpeg")
            print("")
            
            try:
                response = input("Upgrade FFmpeg? (y/n): ").strip().lower()
                if response in ['y', 'yes']:
                    print("\nUpgrading FFmpeg...")
                    print("-" * 60)
                    
                    # Check if running as root
                    try:
                        is_root = os.geteuid() == 0
                    except AttributeError:
                        is_root = False
                    
                    prefix = [] if is_root else ["sudo"]
                    
                    # Update package list
                    print("Updating package list...")
                    subprocess.run(prefix + ["apt", "update"], check=False)
                    
                    # Install/upgrade FFmpeg
                    print("\nInstalling/upgrading FFmpeg...")
                    result = subprocess.run(
                        prefix + ["apt", "install", "-y", "ffmpeg"],
                        check=False
                    )
                    
                    if result.returncode == 0:
                        # Check new version
                        new_version = self.get_ffmpeg_version("ffmpeg")
                        if new_version:
                            new_version_str = f"{new_version[0]}.{new_version[1]}.{new_version[2]}"
                            print(f"\nFFmpeg upgraded to version {new_version_str}")
                            print("=" * 60)
                            return self.is_version_sufficient(new_version)
                        else:
                            print("\nFFmpeg installed successfully")
                            print("=" * 60)
                            return True
                    else:
                        print("\nFFmpeg upgrade failed")
                        print("Please upgrade manually: sudo apt update && sudo apt install -y ffmpeg")
                        print("=" * 60)
                        return False
                else:
                    print("\nSkipping FFmpeg upgrade.")
                    print("You can upgrade later with: sudo apt update && sudo apt install -y ffmpeg")
                    print("=" * 60)
                    return False
                    
            except (EOFError, KeyboardInterrupt):
                print("\n\nSkipping FFmpeg upgrade.")
                print("=" * 60)
                return False
                
        else:
            # Windows or macOS
            print("Please upgrade FFmpeg manually:")
            print("")
            if system == "darwin":
                print("  brew upgrade ffmpeg")
            elif system == "windows":
                print("  Download latest version from: https://ffmpeg.org/download.html")
            
            print("=" * 60)
            return False

    def get_ffmpeg_path(self):
        """Get the path to ffmpeg"""
        system = platform.system().lower()
        
        # Linux: Prioritize system-wide FFmpeg
        if system == "linux":
            # 1. Check system path
            system_path = shutil.which("ffmpeg")
            if system_path:
                return os.path.abspath(system_path)
                
            # 2. Try to install
            if self.install_system_ffmpeg():
                # Check again
                system_path = shutil.which("ffmpeg")
                if system_path:
                    return os.path.abspath(system_path)
            
            # 3. Fallback to local check (optional, but good for backward compat if user manually placed it)
            executable = "ffmpeg"
            local_path = os.path.join(self.ffmpeg_dir, executable)
            if os.path.exists(local_path):
                return local_path
                
            print("  FFmpeg not found locally or in system path.")
            return "ffmpeg" # Return default and let it fail
            
        # Windows/macOS: Check system PATH first, then local directory
        executable = "ffmpeg.exe" if system == "windows" else "ffmpeg"
        
        # 1. Check system PATH first
        system_path = shutil.which("ffmpeg")
        if system_path:
            return os.path.abspath(system_path)
        
        # 2. Check local directory
        local_path = os.path.join(self.ffmpeg_dir, executable)
        if os.path.exists(local_path):
            return local_path
            
        # 3. Try to download if missing (Windows only)
        if system == "windows":
            print(f"\n  Local FFmpeg not found. Attempting to download for {system}...")
            if self.download_ffmpeg():
                return os.path.join(self.ffmpeg_dir, executable)
        
        return local_path # Return the expected local path even if missing

    def get_ffprobe_path(self):
        """Get the path to ffprobe"""
        system = platform.system().lower()
        
        # Linux: Check system path
        if system == "linux":
            # 1. Check system path
            system_path = shutil.which("ffprobe")
            if system_path:
                return os.path.abspath(system_path)
            # Attempt install if missing (although ffmpeg install usually covers it)
            if self.install_system_ffmpeg():
                 system_path = shutil.which("ffprobe")
                 if system_path:
                     return os.path.abspath(system_path)
            return "ffprobe"

        # Windows/macOS: Check system PATH first, then local directory
        # 1. Check system PATH first
        system_path = shutil.which("ffprobe")
        if system_path:
            return os.path.abspath(system_path)
        
        # 2. Check local directory
        ffprobe_path = self.is_ffprobe_available()
        if ffprobe_path:
            return ffprobe_path
        
        # 3. Try to download (Windows only)
        if system == "windows":
            print(f"\n  FFprobe not found. Attempting to download for {system}...")
            if self.download_ffmpeg():
                return os.path.join(self.ffmpeg_dir, self.ffprobe_executable)
        
        return self.ffprobe_executable # Fallback
