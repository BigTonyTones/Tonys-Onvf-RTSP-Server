import json
import os
import sys
import threading
import tempfile
import re
from pathlib import Path
from urllib.parse import quote
from .config import CONFIG_FILE, MEDIAMTX_PORT
from .camera import VirtualONVIFCamera
from .onvif_service import ONVIFService
from .mediamtx_manager import MediaMTXManager
from .linux_service import LinuxServiceManager
from .logging_config import get_logger

logger = get_logger(__name__)


# Input validation patterns for security-sensitive fields
# MAC address: XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX
MAC_ADDRESS_PATTERN = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')

# Interface name: alphanumeric and underscore, 1-15 chars (Linux IFNAMSIZ limit)
INTERFACE_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{1,15}$')

# IPv4 address: standard dotted decimal notation
IPV4_ADDRESS_PATTERN = re.compile(
    r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
    r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
)

# Netmask: either CIDR notation (0-32) or dotted decimal
NETMASK_PATTERN = re.compile(
    r'^(?:[0-9]|[1-2][0-9]|3[0-2])$|'  # CIDR: 0-32
    r'^(?:(?:255|254|252|248|240|224|192|128|0)\.){3}'
    r'(?:255|254|252|248|240|224|192|128|0)$'  # Dotted decimal
)


def validate_mac_address(mac):
    """Validate MAC address format. Returns True if valid."""
    if not mac:
        return True  # Empty is allowed (optional field)
    return bool(MAC_ADDRESS_PATTERN.match(mac))


def validate_interface_name(name):
    """Validate network interface name. Returns True if valid."""
    if not name:
        return True  # Empty is allowed (optional field)
    return bool(INTERFACE_NAME_PATTERN.match(name))


def validate_ipv4_address(ip):
    """Validate IPv4 address format. Returns True if valid."""
    if not ip:
        return True  # Empty is allowed (optional field)
    return bool(IPV4_ADDRESS_PATTERN.match(ip))


def validate_netmask(netmask):
    """Validate netmask (CIDR or dotted decimal). Returns True if valid."""
    if not netmask:
        return True  # Empty is allowed (optional field)
    return bool(NETMASK_PATTERN.match(str(netmask)))


class CameraManager:
    """Manages multiple virtual ONVIF cameras"""

    def __init__(self, config_file=CONFIG_FILE):
        self.config_file = config_file
        self.cameras = []
        self.next_id = 1
        self.next_onvif_port = 8001
        self.mediamtx = MediaMTXManager()
        self.service_mgr = LinuxServiceManager()
        self._lock = threading.Lock()
        self.load_config()

    def load_config(self):
        """Load camera configuration"""
        if Path(self.config_file).exists():
            with open(self.config_file, 'r') as f:
                config = json.load(f)

            for cam_config in config.get('cameras', []):
                camera = VirtualONVIFCamera(cam_config)
                self.cameras.append(camera)

                if cam_config['id'] >= self.next_id:
                    self.next_id = cam_config['id'] + 1
                if cam_config.get('onvifPort', 0) >= self.next_onvif_port:
                    self.next_onvif_port = cam_config['onvifPort'] + 1

            # Load settings
            self.server_ip = config.get('settings', {}).get('serverIp', 'localhost')
            self.open_browser = config.get('settings', {}).get('openBrowser', True)
            self.theme = config.get('settings', {}).get('theme', 'dracula')
            self.grid_columns = config.get('settings', {}).get('gridColumns', 3)
            self.rtsp_port = config.get('settings', {}).get('rtspPort', 8554)
            self.auto_boot = config.get('settings', {}).get('autoBoot', False)
        else:
            self.server_ip = 'localhost'
            self.open_browser = True
            self.theme = 'dracula'
            self.grid_columns = 3
            self.rtsp_port = 8554
            self.auto_boot = False
            self.save_config()

    def save_config(self):
        """Save configuration to file atomically"""
        config = {
            'cameras': [cam.to_config_dict() for cam in self.cameras],  # Use to_config_dict() to exclude status
            'settings': {
                'serverIp': getattr(self, 'server_ip', 'localhost'),
                'openBrowser': getattr(self, 'open_browser', True),
                'theme': getattr(self, 'theme', 'dracula'),
                'gridColumns': getattr(self, 'grid_columns', 3),
                'rtspPort': getattr(self, 'rtsp_port', 8554),
                'autoBoot': getattr(self, 'auto_boot', False)
            }
        }

        with self._lock:
            try:
                # Use a temporary file for atomic write
                fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(self.config_file)), text=True)
                with os.fdopen(fd, 'w') as f:
                    json.dump(config, f, indent=2)

                # Atomic rename
                os.replace(temp_path, self.config_file)
            except Exception as e:
                logger.error("Error saving config: %s", e)
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    os.remove(temp_path)

    def load_settings(self):
        """Load settings from config with error safety"""
        if Path(self.config_file).exists():
            with self._lock:
                try:
                    with open(self.config_file, 'r') as f:
                        config = json.load(f)
                        settings = config.get('settings', {})
                        new_ip = settings.get('serverIp')
                        if new_ip:
                            self.server_ip = new_ip
                        self.open_browser = settings.get('openBrowser', True)
                        self.theme = settings.get('theme', 'dracula')
                        self.grid_columns = settings.get('gridColumns', 3)
                        self.rtsp_port = settings.get('rtspPort', 8554)
                        self.auto_boot = settings.get('autoBoot', False)
                except Exception as e:
                    # If reading fails (e.g. file busy), we just fall back to the last known
                    # value stored in self.server_ip, which is much safer.
                    logger.warning("Could not read config file for settings: %s", e)

        return {
            'serverIp': self.server_ip,
            'openBrowser': self.open_browser,
            'theme': self.theme,
            'gridColumns': self.grid_columns,
            'rtspPort': self.rtsp_port,
            'autoBoot': self.auto_boot
        }

    def save_settings(self, settings):
        """Save settings to config"""
        self.server_ip = settings.get('serverIp', 'localhost')
        self.open_browser = settings.get('openBrowser', True)
        self.theme = settings.get('theme', self.theme)
        self.grid_columns = int(settings.get('gridColumns', self.grid_columns))
        self.rtsp_port = int(settings.get('rtspPort', self.rtsp_port))

        # Handle auto-boot setting (Linux only)
        new_auto_boot = settings.get('autoBoot', False)
        if new_auto_boot != self.auto_boot:
            if self.service_mgr.is_linux():
                if new_auto_boot:
                    success, msg = self.service_mgr.install_service()
                    if not success:
                        raise Exception(f"Failed to enable auto-boot: {msg}")
                else:
                    success, msg = self.service_mgr.uninstall_service()
                    if not success:
                        raise Exception(f"Failed to disable auto-boot: {msg}")
            self.auto_boot = new_auto_boot

        self.save_config()
        return {
            'serverIp': self.server_ip,
            'openBrowser': self.open_browser,
            'theme': self.theme,
            'gridColumns': self.grid_columns,
            'rtspPort': self.rtsp_port,
            'autoBoot': self.auto_boot
        }

    def is_port_available(self, port, exclude_camera_id=None):
        """Check if an ONVIF port is available (not used by other cameras)"""
        for camera in self.cameras:
            if camera.id != exclude_camera_id and camera.onvif_port == port:
                return False
        return True

    def add_camera(self, name, host, rtsp_port, username, password, main_path, sub_path, auto_start=False,
                   main_width=1920, main_height=1080, sub_width=640, sub_height=480,
                   main_framerate=30, sub_framerate=15, onvif_port=None,
                   onvif_username='admin', onvif_password='admin', transcode_sub=False, transcode_main=False,
                   use_virtual_nic=False, parent_interface='', nic_mac='', ip_mode='dhcp',
                   static_ip='', netmask='24', gateway=''):
        """Add a new camera"""
        # Validate security-sensitive fields to prevent command injection
        if not validate_mac_address(nic_mac):
            raise ValueError(f"Invalid MAC address format: {nic_mac}")
        if not validate_interface_name(parent_interface):
            raise ValueError(f"Invalid interface name format: {parent_interface}")
        if not validate_ipv4_address(static_ip):
            raise ValueError(f"Invalid static IP address format: {static_ip}")
        if not validate_ipv4_address(gateway):
            raise ValueError(f"Invalid gateway IP address format: {gateway}")
        if not validate_ipv4_address(host):
            # Host can be either IP or hostname - validate if it looks like an IP
            if re.match(r'^\d+\.\d+\.\d+\.\d+$', host) and not validate_ipv4_address(host):
                raise ValueError(f"Invalid host IP address format: {host}")
        if not validate_netmask(netmask):
            raise ValueError(f"Invalid netmask format: {netmask}")

        if not main_path.startswith('/'):
            main_path = '/' + main_path
        if not sub_path.startswith('/'):
            sub_path = '/' + sub_path

        rtsp_port = str(rtsp_port)

        # Handle ONVIF port assignment
        if onvif_port is not None:
            onvif_port = int(onvif_port)
            if not self.is_port_available(onvif_port):
                raise ValueError(f"ONVIF port {onvif_port} is already in use by another camera")
        else:
            # Auto-assign port
            onvif_port = self.next_onvif_port

        # URL-encode credentials
        username_encoded = quote(username, safe='') if username else ''
        password_encoded = quote(password, safe='') if password else ''

        # Build RTSP URLs
        if username_encoded and password_encoded:
            main_url = f"rtsp://{username_encoded}:{password_encoded}@{host}:{rtsp_port}{main_path}"
            sub_url = f"rtsp://{username_encoded}:{password_encoded}@{host}:{rtsp_port}{sub_path}"
        elif username_encoded:
            main_url = f"rtsp://{username_encoded}@{host}:{rtsp_port}{main_path}"
            sub_url = f"rtsp://{username_encoded}@{host}:{rtsp_port}{sub_path}"
        else:
            main_url = f"rtsp://{host}:{rtsp_port}{main_path}"
            sub_url = f"rtsp://{host}:{rtsp_port}{sub_path}"

        # Create safe path name
        path_name = name.lower().replace(' ', '_').replace('-', '_')
        path_name = ''.join(c for c in path_name if c.isalnum() or c == '_')
        # Collapse multiple consecutive underscores
        path_name = re.sub(r'_+', '_', path_name)

        logger.info("Adding camera: %s", name)

        config = {
            'id': self.next_id,
            'name': name,
            'mainStreamUrl': main_url,
            'subStreamUrl': sub_url,
            'rtspPort': MEDIAMTX_PORT,
            'onvifPort': onvif_port,
            'pathName': path_name,
            'username': username,
            'password': password,
            'autoStart': auto_start,
            'mainWidth': main_width,
            'mainHeight': main_height,
            'subWidth': sub_width,
            'subHeight': sub_height,
            'mainFramerate': main_framerate,
            'subFramerate': sub_framerate,
            'onvifUsername': onvif_username,
            'onvifPassword': onvif_password,
            'transcodeSub': transcode_sub,
            'transcodeMain': transcode_main,
            'useVirtualNic': use_virtual_nic,
            'parentInterface': parent_interface,
            'nicMac': nic_mac,
            'ipMode': ip_mode,
            'staticIp': static_ip,
            'netmask': netmask,
            'gateway': gateway
        }

        camera = VirtualONVIFCamera(config)
        self.cameras.append(camera)

        self.next_id += 1
        # Update next_onvif_port to be higher than any used port
        if onvif_port >= self.next_onvif_port:
            self.next_onvif_port = onvif_port + 1

        self.save_config()
        return camera

    def update_camera(self, camera_id, name, host, rtsp_port, username, password, main_path, sub_path, auto_start=False,
                      main_width=1920, main_height=1080, sub_width=640, sub_height=480,
                      main_framerate=30, sub_framerate=15, onvif_port=None,
                      onvif_username='admin', onvif_password='admin', transcode_sub=False, transcode_main=False,
                      use_virtual_nic=False, parent_interface='', nic_mac='', ip_mode='dhcp',
                      static_ip='', netmask='24', gateway=''):
        """Update an existing camera"""
        # Validate security-sensitive fields to prevent command injection
        if not validate_mac_address(nic_mac):
            raise ValueError(f"Invalid MAC address format: {nic_mac}")
        if not validate_interface_name(parent_interface):
            raise ValueError(f"Invalid interface name format: {parent_interface}")
        if not validate_ipv4_address(static_ip):
            raise ValueError(f"Invalid static IP address format: {static_ip}")
        if not validate_ipv4_address(gateway):
            raise ValueError(f"Invalid gateway IP address format: {gateway}")
        if not validate_ipv4_address(host):
            # Host can be either IP or hostname - validate if it looks like an IP
            if re.match(r'^\d+\.\d+\.\d+\.\d+$', host) and not validate_ipv4_address(host):
                raise ValueError(f"Invalid host IP address format: {host}")
        if not validate_netmask(netmask):
            raise ValueError(f"Invalid netmask format: {netmask}")

        camera = self.get_camera(camera_id)
        if not camera:
            return None

        # Check if camera is running
        was_running = camera.status == "running"

        # Stop camera if running
        if was_running:
            camera.stop()

        # Validate ONVIF port if provided
        if onvif_port is not None:
            onvif_port = int(onvif_port)
            if not self.is_port_available(onvif_port, exclude_camera_id=camera_id):
                raise ValueError(f"ONVIF port {onvif_port} is already in use by another camera")
        else:
            # Keep existing port if not specified
            onvif_port = camera.onvif_port

        # Ensure paths start with /
        if not main_path.startswith('/'):
            main_path = '/' + main_path
        if not sub_path.startswith('/'):
            sub_path = '/' + sub_path

        rtsp_port = str(rtsp_port)

        # URL-encode credentials
        username_encoded = quote(username, safe='') if username else ''
        password_encoded = quote(password, safe='') if password else ''

        # Build RTSP URLs
        if username_encoded and password_encoded:
            main_url = f"rtsp://{username_encoded}:{password_encoded}@{host}:{rtsp_port}{main_path}"
            sub_url = f"rtsp://{username_encoded}:{password_encoded}@{host}:{rtsp_port}{sub_path}"
        elif username_encoded:
            main_url = f"rtsp://{username_encoded}@{host}:{rtsp_port}{main_path}"
            sub_url = f"rtsp://{username_encoded}@{host}:{rtsp_port}{sub_path}"
        else:
            main_url = f"rtsp://{host}:{rtsp_port}{main_path}"
            sub_url = f"rtsp://{host}:{rtsp_port}{sub_path}"

        # Create safe path name
        path_name = name.lower().replace(' ', '_').replace('-', '_')
        path_name = ''.join(c for c in path_name if c.isalnum() or c == '_')
        # Collapse multiple consecutive underscores
        path_name = re.sub(r'_+', '_', path_name)

        # Update camera properties
        camera.name = name
        camera.main_stream_url = main_url
        camera.sub_stream_url = sub_url
        camera.path_name = path_name
        camera.username = username
        camera.password = password
        camera.auto_start = auto_start
        camera.onvif_port = onvif_port
        camera.main_width = main_width
        camera.main_height = main_height
        camera.sub_width = sub_width
        camera.sub_height = sub_height
        camera.main_framerate = main_framerate
        camera.sub_framerate = sub_framerate
        camera.onvif_username = onvif_username
        camera.onvif_password = onvif_password
        camera.transcode_sub = transcode_sub
        camera.transcode_main = transcode_main
        camera.use_virtual_nic = use_virtual_nic
        camera.parent_interface = parent_interface
        camera.nic_mac = nic_mac
        camera.ip_mode = ip_mode
        camera.static_ip = static_ip
        camera.netmask = netmask
        camera.gateway = gateway

        logger.info("Updated camera: %s", name)

        # Save config
        self.save_config()

        # Restart camera if it was running
        if was_running:
            camera.start()
            self.mediamtx.restart(self.cameras)

        return camera

    def delete_camera(self, camera_id):
        """Delete a camera"""
        camera = self.get_camera(camera_id)
        if camera:
            camera.stop()
            self.cameras = [c for c in self.cameras if c.id != camera_id]
            self.save_config()
            self.mediamtx.restart(self.cameras)
            return True
        return False

    def get_camera(self, camera_id):
        """Get camera by ID"""
        for camera in self.cameras:
            if camera.id == camera_id:
                return camera
        return None

    def start_all(self):
        """Start all cameras"""
        for camera in self.cameras:
            camera.start()
        self.mediamtx.restart(self.cameras)

    def stop_all(self):
        """Stop all cameras"""
        for camera in self.cameras:
            camera.stop()
        self.mediamtx.restart(self.cameras)
