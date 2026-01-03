import json
import os
import sys
import threading
import tempfile
import secrets
import string
from pathlib import Path
from urllib.parse import quote
from werkzeug.security import generate_password_hash, check_password_hash
from .config import CONFIG_FILE, MEDIAMTX_PORT
from .camera import VirtualONVIFCamera
from .onvif_service import ONVIFService
from .mediamtx_manager import MediaMTXManager
from .linux_service import LinuxServiceManager

class CameraManager:
    """Manages multiple virtual ONVIF cameras"""
    
    def __init__(self, config_file=CONFIG_FILE):
        self.config_file = config_file
        self.cameras = []
        self.next_id = 1
        self.next_onvif_port = 8001
        self.mediamtx = MediaMTXManager()
        self.service_mgr = LinuxServiceManager()
        self.service_mgr = LinuxServiceManager()
        self._lock = threading.Lock()
        
        # GridFusion Layouts
        self.grid_fusion_layouts = []

        
        # Auth settings
        self.auth_enabled = False
        self.username = None
        self.password_hash = None
        self.session_token = None
        
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
            self.global_username = config.get('settings', {}).get('globalUsername', 'admin')
            self.global_password = config.get('settings', {}).get('globalPassword', 'admin')
            self.rtsp_auth_enabled = config.get('settings', {}).get('rtspAuthEnabled', False)
            self.debug_mode = config.get('settings', {}).get('debugMode', False)
            
            # Load GridFusion settings (Support multiple layouts)
            grid_fusion = config.get('gridFusion', {})
            
            # Check for new 'layouts' structure
            if 'layouts' in grid_fusion:
                self.grid_fusion_layouts = grid_fusion.get('layouts', [])
            else:
                # Migrate legacy single layout to new structure
                if grid_fusion.get('cameras') or grid_fusion.get('enabled'):
                    print("  Migrating GridFusion config to multi-layout structure...")
                    self.grid_fusion_layouts = [{
                        'id': 'matrix',
                        'name': 'Default Layout',
                        'enabled': grid_fusion.get('enabled', False),
                        'resolution': grid_fusion.get('resolution', '1920x1080'),
                        'cameras': grid_fusion.get('cameras', []),
                        'snapToGrid': grid_fusion.get('snapToGrid', True),
                        'showGrid': grid_fusion.get('showGrid', True),
                        'showSnapshots': grid_fusion.get('showSnapshots', True)
                    }]
                else:
                     # Default empty layout
                     self.grid_fusion_layouts = [{
                        'id': 'matrix',
                        'name': 'Default Layout',
                        'enabled': False,
                        'resolution': '1920x1080',
                        'cameras': [],
                        'snapToGrid': True,
                        'showGrid': True,
                        'showSnapshots': True
                    }]
            
            # Load auth settings
            auth = config.get('auth', {})
            self.auth_enabled = auth.get('enabled', False)
            self.username = auth.get('username')
            self.password_hash = auth.get('password_hash')
        else:
            self.server_ip = 'localhost'
            self.open_browser = True
            self.theme = 'dracula'
            self.grid_columns = 3
            self.rtsp_port = 8554
            self.auto_boot = False
            self.global_username = 'admin'
            self.global_password = 'admin'
            self.rtsp_auth_enabled = False
            self.debug_mode = False
            # Default layouts if config missing
            self.grid_fusion_layouts = [{
                'id': 'matrix',
                'name': 'Default Layout',
                'enabled': False,
                'resolution': '1920x1080',
                'cameras': [],
                'snapToGrid': True,
                'showGrid': True,
                'showSnapshots': True
            }]
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
                'autoBoot': getattr(self, 'auto_boot', False),
                'globalUsername': getattr(self, 'global_username', 'admin'),
                'globalPassword': getattr(self, 'global_password', 'admin'),
                'rtspAuthEnabled': getattr(self, 'rtsp_auth_enabled', False),
                'debugMode': getattr(self, 'debug_mode', False)
            },
            'auth': {
                'enabled': getattr(self, 'auth_enabled', False),
                'username': getattr(self, 'username', None),
                'password_hash': getattr(self, 'password_hash', None)
            },
            'gridFusion': {
                'layouts': getattr(self, 'grid_fusion_layouts', [])
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
                print(f"Error saving config: {e}")
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
                        self.global_username = settings.get('globalUsername', 'admin')
                        self.global_password = settings.get('globalPassword', 'admin')
                        self.rtsp_auth_enabled = settings.get('rtspAuthEnabled', False)
                        self.debug_mode = settings.get('debugMode', False)
                except Exception as e:
                    # If reading fails (e.g. file busy), we just fall back to the last known 
                    # value stored in self.server_ip, which is much safer.
                    print(f"Warning: Could not read config file for settings: {e}")
        
        return {
            'serverIp': self.server_ip, 
            'openBrowser': self.open_browser, 
            'theme': self.theme, 
            'gridColumns': self.grid_columns,
            'rtspPort': self.rtsp_port,
            'autoBoot': self.auto_boot,
            'globalUsername': getattr(self, 'global_username', 'admin'),
            'globalPassword': getattr(self, 'global_password', 'admin'),
            'rtspAuthEnabled': getattr(self, 'rtsp_auth_enabled', False),
            'debugMode': getattr(self, 'debug_mode', False),
            'authEnabled': self.auth_enabled,
            'username': self.username
        }
    
    def save_settings(self, settings):
        """Save settings to config"""
        self.server_ip = settings.get('serverIp', 'localhost')
        self.open_browser = settings.get('openBrowser', True)
        self.theme = settings.get('theme', self.theme)
        self.grid_columns = int(settings.get('gridColumns', self.grid_columns))
        old_rtsp_port = self.rtsp_port
        old_global_username = getattr(self, 'global_username', 'admin')
        old_global_password = getattr(self, 'global_password', 'admin')
        old_rtsp_auth_enabled = getattr(self, 'rtsp_auth_enabled', False)
        old_debug_mode = getattr(self, 'debug_mode', False)
        
        # Update values
        self.rtsp_port = int(settings.get('rtspPort', self.rtsp_port))
        self.global_username = settings.get('globalUsername', 'admin')
        self.global_password = settings.get('globalPassword', 'admin')
        self.rtsp_auth_enabled = settings.get('rtspAuthEnabled', False)
        self.debug_mode = settings.get('debugMode', False)
        
        # Check for changes that require MediaMTX restart
        rtsp_needs_restart = (
            old_rtsp_port != self.rtsp_port or
            old_global_username != self.global_username or
            old_global_password != self.global_password or
            old_rtsp_auth_enabled != self.rtsp_auth_enabled or
            old_debug_mode != self.debug_mode
        )
        
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

        # Handle Auth toggle
        new_auth_enabled = settings.get('authEnabled', False)
        new_username = settings.get('username')
        new_password = settings.get('password')
        
        if new_auth_enabled:
            if new_username:
                self.username = new_username
            if new_password:
                self.password_hash = generate_password_hash(new_password)
            
            # If still no username/password after potential update, can't enable
            if not self.username or not self.password_hash:
                 new_auth_enabled = False
        
        self.auth_enabled = new_auth_enabled
        
        self.save_config()
        
        # Restart MediaMTX if needed
        if rtsp_needs_restart:
            print("RTSP settings changed, restarting MediaMTX...")
            # Pass credentials only if auth is enabled
            rtsp_user = self.global_username if self.rtsp_auth_enabled else ''
            rtsp_pass = self.global_password if self.rtsp_auth_enabled else ''
            self.mediamtx.restart(self.cameras, self.rtsp_port, rtsp_user, rtsp_pass, self.get_grid_fusion(), debug_mode=self.debug_mode)
            
        return {
            'serverIp': self.server_ip, 
            'openBrowser': self.open_browser, 
            'theme': self.theme, 
            'gridColumns': self.grid_columns, 
            'rtspPort': self.rtsp_port,
            'autoBoot': self.auto_boot,
            'globalUsername': self.global_username,
            'globalPassword': self.global_password,
            'rtspAuthEnabled': self.rtsp_auth_enabled,
            'debugMode': self.debug_mode,
            'authEnabled': self.auth_enabled,
            'username': self.username
        }

    def get_grid_fusion(self):
        """Get GridFusion configuration (updated for multi-layout)"""
        return {
            'layouts': getattr(self, 'grid_fusion_layouts', [])
        }

    def save_grid_fusion(self, data):
        """Save GridFusion configuration (multi-layout)"""
        old_layouts = getattr(self, 'grid_fusion_layouts', [])
        
        # Expecting data to contain 'layouts' list
        # If receiving legacy single-layout update, wrap it (backward compat, though UI should be updated)
        if 'layouts' in data:
            self.grid_fusion_layouts = data['layouts']
        else:
             # This might happen if old UI sends data
             # Update the first layout or create one
             if not self.grid_fusion_layouts:
                 self.grid_fusion_layouts = [{
                     'id': 'matrix',
                     'name': 'Default Layout',
                     'enabled': data.get('enabled', False),
                     'resolution': data.get('resolution', '1920x1080'),
                     'cameras': data.get('cameras', []),
                     'snapToGrid': data.get('snapToGrid', True),
                     'showGrid': data.get('showGrid', True),
                     'showSnapshots': data.get('showSnapshots', True)
                 }]
             else:
                 # Update index 0
                 l = self.grid_fusion_layouts[0]
                 l['enabled'] = data.get('enabled', False)
                 l['resolution'] = data.get('resolution', '1920x1080')
                 l['cameras'] = data.get('cameras', [])
                 l['snapToGrid'] = data.get('snapToGrid', True)
                 l['showGrid'] = data.get('showGrid', True)
                 l['showSnapshots'] = data.get('showSnapshots', True)
        
        self.save_config()

        # Restart MediaMTX if crucial settings changed
        # Simple check: if layouts changed in a way that affects streams (enabled, resolution, cameras, id)
        # We'll just define that ANY change to the layout structure warrants a check
        # For simplicity, we compare the JSON representation of relevant fields
        
        def extract_stream_config(layouts):
            return [{k: v for k, v in l.items() if k in ['id', 'enabled', 'resolution', 'cameras']} for l in layouts]
            
        if extract_stream_config(old_layouts) != extract_stream_config(self.grid_fusion_layouts):
            print("GridFusion layouts changed, restarting MediaMTX...")
            rtsp_user = self.global_username if self.rtsp_auth_enabled else ''
            rtsp_pass = self.global_password if self.rtsp_auth_enabled else ''
            self.mediamtx.restart(self.cameras, self.rtsp_port, rtsp_user, rtsp_pass, self.get_grid_fusion())

        return self.get_grid_fusion()
    
    def is_port_available(self, port, exclude_camera_id=None):
        """Check if an ONVIF port is available (not used by other cameras)"""
        for camera in self.cameras:
            if camera.id != exclude_camera_id and camera.onvif_port == port:
                return False
        return True
    
    def add_camera(self, name, host, rtsp_port, username, password, main_path, sub_path, auto_start=False,
                   main_width=1920, main_height=1080, sub_width=640, sub_height=480,
                   main_framerate=30, sub_framerate=15, onvif_port=None,
                   transcode_sub=False, transcode_main=False,
                   use_virtual_nic=False, parent_interface='', nic_mac='', ip_mode='dhcp', 
                   static_ip='', netmask='24', gateway=''):
        """Add a new camera"""
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
        
        print(f"\nAdding camera: {name}")
        
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
            'onvifUsername': self.global_username,
            'onvifPassword': self.global_password,
            'transcodeSub': transcode_sub,
            'transcodeMain': transcode_main,
            'useVirtualNic': use_virtual_nic,
            'parentInterface': parent_interface,
            'nicMac': nic_mac,
            'ipMode': ip_mode,
            'staticIp': static_ip,
            'netmask': netmask,
            'gateway': gateway,
            'debugMode': getattr(self, 'debug_mode', False)
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
                      transcode_sub=False, transcode_main=False,
                      use_virtual_nic=False, parent_interface='', nic_mac='', ip_mode='dhcp', 
                      static_ip='', netmask='24', gateway=''):
        """Update an existing camera"""
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
        camera.onvif_username = self.global_username
        camera.onvif_password = self.global_password
        camera.transcode_sub = transcode_sub
        camera.transcode_main = transcode_main
        camera.use_virtual_nic = use_virtual_nic
        camera.parent_interface = parent_interface
        camera.nic_mac = nic_mac
        camera.ip_mode = ip_mode
        camera.static_ip = static_ip
        camera.netmask = netmask
        camera.gateway = gateway
        
        print(f"\nUpdated camera: {name}")
        
        # Save config
        self.save_config()
        
        # Restart camera if it was running
        if was_running:
            camera.start()
            rtsp_user = self.global_username if self.rtsp_auth_enabled else ''
            rtsp_pass = self.global_password if self.rtsp_auth_enabled else ''
            self.mediamtx.restart(self.cameras, self.rtsp_port, rtsp_user, rtsp_pass, self.get_grid_fusion())
        
        return camera
    
    def delete_camera(self, camera_id):
        """Delete a camera"""
        camera = self.get_camera(camera_id)
        if camera:
            camera.stop()
            self.cameras = [c for c in self.cameras if c.id != camera_id]
            self.save_config()
            rtsp_user = self.global_username if self.rtsp_auth_enabled else ''
            rtsp_pass = self.global_password if self.rtsp_auth_enabled else ''
            self.mediamtx.restart(self.cameras, self.rtsp_port, rtsp_user, rtsp_pass, self.get_grid_fusion())
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
        rtsp_user = self.global_username if self.rtsp_auth_enabled else ''
        rtsp_pass = self.global_password if self.rtsp_auth_enabled else ''
        self.mediamtx.restart(self.cameras, self.rtsp_port, rtsp_user, rtsp_pass, self.get_grid_fusion())
    
    def stop_all(self):
        """Stop all cameras"""
        for camera in self.cameras:
            camera.stop()
        rtsp_user = self.global_username if self.rtsp_auth_enabled else ''
        rtsp_pass = self.global_password if self.rtsp_auth_enabled else ''
        self.mediamtx.restart(self.cameras, self.rtsp_port, rtsp_user, rtsp_pass, self.get_grid_fusion())

    # --- Authentication Methods ---
    
    def is_setup_required(self):
        """Returns True if no preference is stored at all"""
        # We'll use a hidden setting to track if the user has ever seen the setup
        if hasattr(self, 'setup_shown'):
            return False
            
        settings_file = Path(self.config_file)
        if settings_file.exists():
            with open(settings_file, 'r') as f:
                config = json.load(f)
                if 'auth' in config:
                    return False
        return True

    def skip_setup(self):
        """Disable auth and mark setup as completed"""
        self.auth_enabled = False
        self.username = None
        self.password_hash = None
        self.save_config()
        return True

    def setup_user(self, username, password):
        """Initial setup of username and password"""
        self.username = username
        self.password_hash = generate_password_hash(password)
        self.auth_enabled = True
        self.save_config()
        return True

    def verify_login(self, username, password):
        """Verify login credentials"""
        if not self.auth_enabled:
            return True
            
        if username == self.username and check_password_hash(self.password_hash, password):
            return True
        return False

    def generate_session_token(self):
        """Generate a random session token"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(32))
