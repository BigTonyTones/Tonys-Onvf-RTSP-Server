import sys
import subprocess
import importlib.util
import platform
import collections
import threading

class Logger:
    def __init__(self, max_lines=2000):
        self._buffer = collections.deque(maxlen=max_lines)
        self._lock = threading.Lock()
        self._stdout = sys.stdout
        self._stderr = sys.stderr

    def write(self, message):
        if not message:
            return
            
        # Handle cases where message might be bytes (e.g. from Flask/Click in some environments)
        if isinstance(message, bytes):
            try:
                message = message.decode('utf-8', errors='replace')
            except:
                message = str(message)
                
        with self._lock:
            self._buffer.append(message)
        self._stdout.write(message)

    def flush(self):
        self._stdout.flush()

    def get_logs(self):
        with self._lock:
            return "".join(self._buffer)

_logger_instance = None

def init_logger():
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Logger()
        sys.stdout = _logger_instance
        sys.stderr = _logger_instance
    return _logger_instance

def get_captured_logs():
    if _logger_instance:
        return _logger_instance.get_logs()
    return ""

# Auto-install requirements
def check_and_install_requirements():
    """Check and install required packages automatically"""
    required_packages = {
        'flask': 'flask',
        'flask_cors': 'flask-cors',
        'requests': 'requests',
        'yaml': 'pyyaml',
        'psutil': 'psutil'
    }
    
    # Check if we need tzdata for timezone support
    if sys.version_info >= (3, 9):
        try:
            import zoneinfo
        except ImportError:
            required_packages['zoneinfo'] = 'tzdata'
    else:
        # For Python < 3.9, use backport
        required_packages['zoneinfo'] = 'backports.zoneinfo'
        required_packages['tzdata'] = 'tzdata'
    
    print("Checking dependencies...")
    missing_packages = []
    
    for module_name, package_name in required_packages.items():
        if importlib.util.find_spec(module_name) is None:
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\nInstalling missing packages: {', '.join(missing_packages)}")
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"Installed {package}")
            except subprocess.CalledProcessError as e:
                print(f"Failed to install {package}: {e}")
                sys.exit(1)
        print("\nAll dependencies installed successfully!\n")
    else:
        print("All dependencies are already installed.\n")

def check_and_install_system_dependencies():
    """Check and install required system packages (Linux only)"""
    if platform.system().lower() != "linux":
        return

    # Check for dhclient
    try:
        subprocess.run(['dhclient', '--version'], capture_output=True, check=False)
        return # Already installed
    except FileNotFoundError:
        pass

    print("Checking system dependencies (Linux)...")
    print("'dhclient' is missing. It's required for Virtual NIC DHCP support.")
    
    # Try to install based on package manager
    managers = [
        (['apt-get', '--version'], ['sudo', 'apt-get', 'update'], ['sudo', 'apt-get', 'install', '-y', 'isc-dhcp-client']),
        (['dnf', '--version'], None, ['sudo', 'dnf', 'install', '-y', 'dhcp-client']),
        (['pacman', '--version'], None, ['sudo', 'pacman', '-S', '--noconfirm', 'dhclient'])
    ]

    for check_cmd, update_cmd, install_cmd in managers:
        try:
            subprocess.run(check_cmd, capture_output=True, check=False)
            print(f"  Attempting to install 'isc-dhcp-client' via {check_cmd[0]}...")
            
            if update_cmd:
                subprocess.run(update_cmd, check=False)
            
            subprocess.run(install_cmd, check=True)
            print("  System dependency installed successfully!")
            return
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue

    print("  Could not automatically install 'dhclient'.")
    print("     Please install it manually: sudo apt-get install isc-dhcp-client")

def cleanup_stale_processes():
    """Kill any existing MediaMTX instances to prevent port conflicts"""
    print("Checking for stale processes...")
    try:
        if platform.system() == "Windows":
            # Check if mediamtx.exe is running
            output = subprocess.check_output("tasklist /FI \"IMAGENAME eq mediamtx.exe\"", shell=True, text=True)
            if "mediamtx.exe" in output:
                print("  Found stale mediamtx.exe, terminating...")
                subprocess.run("taskkill /F /IM mediamtx.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print("  Stale mediamtx.exe terminated")
        else:
            # Linux/Mac
            try:
                # Check if running first to provide feedback
                subprocess.check_call(["pgrep", "mediamtx"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print("  Found stale mediamtx, terminating...")
                subprocess.run(["pkill", "-9", "mediamtx"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print("  Stale mediamtx terminated")
            except subprocess.CalledProcessError:
                pass  # Not running
            
    except Exception as e:
        print(f"  Warning: Could not check/clean stale processes: {e}")
