import os
import platform
import subprocess
import zipfile
import shutil
import requests

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
            
        # Windows/Other: Strict local management (Existing logic)
        executable = "ffmpeg.exe" if system == "windows" else "ffmpeg"
        
        # 1. Check local directory ONLY
        local_path = os.path.join(self.ffmpeg_dir, executable)
        if os.path.exists(local_path):
            return local_path
            
        # 2. Try to download if missing
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

        # Windows/Existing logic
        ffprobe_path = self.is_ffprobe_available()
        if ffprobe_path:
            return ffprobe_path
        
        # Try to download
        if system == "windows":
            print(f"\n  FFprobe not found. Attempting to download for {system}...")
            if self.download_ffmpeg():
                return os.path.join(self.ffmpeg_dir, self.ffprobe_executable)
        
        return self.ffprobe_executable # Fallback
