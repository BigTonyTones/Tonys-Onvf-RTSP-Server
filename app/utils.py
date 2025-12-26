import sys
import subprocess
import importlib.util
import platform

from .logging_config import get_logger

logger = get_logger(__name__)


# Auto-install requirements
def check_and_install_requirements():
    """Check and install required packages automatically"""
    required_packages = {
        'flask': 'flask',
        'flask_cors': 'flask-cors',
        'flask_limiter': 'flask-limiter',
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

    logger.info("Checking dependencies...")
    missing_packages = []

    for module_name, package_name in required_packages.items():
        if importlib.util.find_spec(module_name) is None:
            missing_packages.append(package_name)

    if missing_packages:
        logger.info("Installing missing packages: %s", ', '.join(missing_packages))
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                logger.info("Installed %s", package)
            except subprocess.CalledProcessError as e:
                logger.error("Failed to install %s: %s", package, e)
                sys.exit(1)
        logger.info("All dependencies installed successfully!")
    else:
        logger.info("All dependencies are already installed.")


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

    logger.info("Checking system dependencies (Linux)...")
    logger.warning("'dhclient' is missing. It's required for Virtual NIC DHCP support.")

    # Try to install based on package manager
    managers = [
        (['apt-get', '--version'], ['sudo', 'apt-get', 'update'], ['sudo', 'apt-get', 'install', '-y', 'isc-dhcp-client']),
        (['dnf', '--version'], None, ['sudo', 'dnf', 'install', '-y', 'dhcp-client']),
        (['pacman', '--version'], None, ['sudo', 'pacman', '-S', '--noconfirm', 'dhclient'])
    ]

    for check_cmd, update_cmd, install_cmd in managers:
        try:
            subprocess.run(check_cmd, capture_output=True, check=False)
            logger.info("Attempting to install 'isc-dhcp-client' via %s...", check_cmd[0])

            if update_cmd:
                subprocess.run(update_cmd, check=False)

            subprocess.run(install_cmd, check=True)
            logger.info("System dependency installed successfully!")
            return
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue

    logger.error("Could not automatically install 'dhclient'.")
    logger.info("Please install it manually: sudo apt-get install isc-dhcp-client")


def cleanup_stale_processes():
    """Kill any existing MediaMTX instances to prevent port conflicts"""
    logger.info("Checking for stale processes...")
    try:
        if platform.system() == "Windows":
            # Check if mediamtx.exe is running
            output = subprocess.check_output(
                ["tasklist", "/FI", "IMAGENAME eq mediamtx.exe"],
                text=True
            )
            if "mediamtx.exe" in output:
                logger.info("Found stale mediamtx.exe, terminating...")
                subprocess.run(
                    ["taskkill", "/F", "/IM", "mediamtx.exe"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                logger.info("Stale mediamtx.exe terminated")
        else:
            # Linux/Mac
            try:
                # Check if running first to provide feedback
                subprocess.check_call(["pgrep", "mediamtx"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.info("Found stale mediamtx, terminating...")
                subprocess.run(["pkill", "-9", "mediamtx"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.info("Stale mediamtx terminated")
            except subprocess.CalledProcessError:
                pass  # Not running

    except Exception as e:
        logger.warning("Could not check/clean stale processes: %s", e)
