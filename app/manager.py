import json
import os
import time
import sys
import threading
import tempfile
import secrets
import string
from pathlib import Path
from urllib.parse import quote
from werkzeug.security import generate_password_hash, check_password_hash
import ipaddress
from .config import CONFIG_FILE, MEDIAMTX_PORT, MEDIAMTX_API_PORT
from .camera import VirtualONVIFCamera
from .onvif_service import ONVIFService
from .mediamtx_manager import MediaMTXManager
from .linux_service import LinuxServiceManager
from .analytics import AnalyticsManager
import requests

class CameraManager:
    """Manages multiple virtual ONVIF cameras"""
    
    def __init__(self, config_file=CONFIG_FILE):
        self.config_file = config_file
        self.cameras = []
        self.next_id = 1
        self.next_onvif_port = 8001
        self.mediamtx = MediaMTXManager()
        self.service_mgr = LinuxServiceManager()
        self.analytics = AnalyticsManager()
        self._lock = threading.Lock()
        
        # Start analytics polling
        self.analytics.start()
        
        # Initialize basic attributes
        self.ip_whitelist = []
        self.debug_mode = False
        self.server_ip = 'localhost'
        
        # GridFusion Layouts
        self.grid_fusion_layouts = []

        # Stream Watchdog tracking
        self.stale_path_times = {} # path_name -> first_stale_timestamp
        self._watchdog_running = False
        self._watchdog_thread = None

        
        # Auth settings
        self.auth_enabled = False
        self.username = None
        self.password_hash = None
        self.session_token = None

        # Advanced Settings
        self.advanced_settings = {
            'mediamtx': {
                'writeQueueSize': 32768,
                'readTimeout': '30s',
                'writeTimeout': '30s',
                'udpMaxPayloadSize': 1472,
                'hlsSegmentCount': 3,
                'hlsSegmentDuration': '1s',
                'hlsPartDuration': '200ms',
            },
            'ffmpeg': {
                'globalArgs': '-hide_banner -loglevel error',
                'inputArgs': '-rtsp_transport tcp -reconnect 1 -reconnect_at_eof 1 -reconnect_streamed 1 -reconnect_delay_max 2',
                'processArgs': '-c:v libx264 -preset ultrafast -tune zerolatency -g 30',
            }
        }
        
        self.ip_whitelist = []
        self.load_config()
        
        # Start watchdog
        self.start_watchdog()
        
    def load_config(self):
        """Load camera configuration"""
        if Path(self.config_file).exists():
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Clear existing cameras before loading to prevent duplicates
            self.cameras.clear()
            self.next_id = 1
            self.next_onvif_port = 8001
                
            for cam_config in config.get('cameras', []):
                camera = VirtualONVIFCamera(cam_config, self)
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
            self.ip_whitelist = config.get('settings', {}).get('ipWhitelist', [])
            
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
                        'showSnapshots': grid_fusion.get('showSnapshots', True),
                        'outputFramerate': grid_fusion.get('outputFramerate', 5)
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
                        'showSnapshots': True,
                        'outputFramerate': 5
                    }]
            
            # Load advanced settings
            self.advanced_settings = config.get('advancedSettings', self.advanced_settings)
            
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
            self.ip_whitelist = []
            # Default layouts if config missing
            self.grid_fusion_layouts = [{
                'id': 'matrix',
                'name': 'Default Layout',
                'enabled': False,
                'resolution': '1920x1080',
                'cameras': [],
                'snapToGrid': True,
                'showGrid': True,
                'showSnapshots': True,
                'outputFramerate': 5
            }]
            self.save_config()
        
        # Migrate old FFmpeg options if needed
        self._migrate_ffmpeg_options()
    
    def _migrate_ffmpeg_options(self):
        """Migrate old FFmpeg options to new format (v5.8+)"""
        import re
        
        # Check if advanced settings have old reconnect options
        if 'ffmpeg' in self.advanced_settings:
            input_args = self.advanced_settings['ffmpeg'].get('inputArgs', '')
            
            # Check if it contains old -reconnect options
            if '-reconnect' in input_args or '-stimeout' in input_args:
                print("  Migrating FFmpeg options to v5.8 format...")
                
                # Remove all reconnect options and fix stimeout -> timeout
                new_input_args = input_args
                
                # Remove reconnect options
                new_input_args = re.sub(r'-reconnect\s+\d+', '', new_input_args)
                new_input_args = re.sub(r'-reconnect_at_eof\s+\d+', '', new_input_args)
                new_input_args = re.sub(r'-reconnect_streamed\s+\d+', '', new_input_args)
                new_input_args = re.sub(r'-reconnect_delay_max\s+\d+', '', new_input_args)
                
                # Fix stimeout -> timeout
                new_input_args = re.sub(r'-stimeout\s+(\d+)', r'-timeout \1', new_input_args)
                
                # Clean up extra spaces
                new_input_args = ' '.join(new_input_args.split())
                
                # Ensure we have timeout option
                if '-timeout' not in new_input_args:
                    new_input_args += ' -timeout 10000000'
                
                # Update the settings
                self.advanced_settings['ffmpeg']['inputArgs'] = new_input_args
                
                print(f"  Old: {input_args}")
                print(f"  New: {new_input_args}")
                
                # Save the migrated config
                self.save_config()
                print("  ✓ FFmpeg options migrated successfully")
            
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
                'debugMode': getattr(self, 'debug_mode', False),
                'ipWhitelist': getattr(self, 'ip_whitelist', [])
            },
            'auth': {
                'enabled': getattr(self, 'auth_enabled', False),
                'username': getattr(self, 'username', None),
                'password_hash': getattr(self, 'password_hash', None)
            },
            'advancedSettings': getattr(self, 'advanced_settings', {}),
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
        try:
            if not os.path.exists(self.config_file):
                return {}
            
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                settings = config.get('settings', {})
                
                # Update attributes from settings
                self.server_ip = settings.get('serverIp', 'localhost')
                self.open_browser = settings.get('openBrowser', True)
                self.theme = settings.get('theme', 'dracula')
                self.grid_columns = settings.get('gridColumns', 3)
                self.rtsp_port = settings.get('rtspPort', 8554)
                self.auto_boot = settings.get('autoBoot', False)
                self.global_username = settings.get('globalUsername', 'admin')
                self.global_password = settings.get('globalPassword', 'admin')
                self.rtsp_auth_enabled = settings.get('rtspAuthEnabled', False)
                self.debug_mode = settings.get('debugMode', False)
                
                # Ensure whitelist exists
                self.ip_whitelist = settings.get('ipWhitelist', [])
                settings['ipWhitelist'] = self.ip_whitelist
                
                return settings
        except Exception as e:
            print(f"Error loading settings: {e}")
            return {}

    def save_settings(self, settings):
        """Save settings to config"""
        old_settings = self.load_settings()
        
        # Check for changes that require MediaMTX restart
        restart_keys = [
            'rtspPort', 'globalUsername', 'globalPassword', 
            'rtspAuthEnabled', 'debugMode', 'advancedSettings'
        ]
        restart_needed = False
        for key in restart_keys:
            if settings.get(key) != old_settings.get(key):
                restart_needed = True
                break

        # Update attributes
        self.server_ip = settings.get('serverIp', self.server_ip)
        self.open_browser = settings.get('openBrowser', self.open_browser)
        self.theme = settings.get('theme', self.theme)
        self.grid_columns = int(settings.get('gridColumns', self.grid_columns))
        self.rtsp_port = int(settings.get('rtspPort', self.rtsp_port))
        self.auto_boot = settings.get('autoBoot', self.auto_boot)
        self.global_username = settings.get('globalUsername', self.global_username)
        self.global_password = settings.get('globalPassword', self.global_password)
        self.rtsp_auth_enabled = settings.get('rtspAuthEnabled', self.rtsp_auth_enabled)
        self.debug_mode = settings.get('debugMode', self.debug_mode)
        self.ip_whitelist = settings.get('ipWhitelist', self.ip_whitelist)
        
        if 'advancedSettings' in settings:
            self.advanced_settings = settings['advancedSettings']

        # Handle auto-boot setting (Linux only)
        if settings.get('autoBoot') != old_settings.get('autoBoot'):
            if self.service_mgr.is_linux():
                if settings.get('autoBoot'):
                    self.service_mgr.install_service()
                else:
                    self.service_mgr.uninstall_service()

        # Handle Web UI Auth
        if 'authEnabled' in settings:
            self.auth_enabled = settings['authEnabled']
            if settings.get('username'):
                self.username = settings['username']
            if settings.get('password'):
                self.password_hash = generate_password_hash(settings['password'])

        self.save_config()

        if restart_needed:
            print("Settings changed, restarting MediaMTX...")
            rtsp_user = self.global_username if self.rtsp_auth_enabled else ''
            rtsp_pass = self.global_password if self.rtsp_auth_enabled else ''
            self.mediamtx.restart(self.cameras, self.rtsp_port, rtsp_user, rtsp_pass, self.get_grid_fusion(), 
                                  debug_mode=self.debug_mode, advanced_settings=self.advanced_settings)
        
        return self.load_settings()

    def get_ip_whitelist(self):
        """Get the current IP whitelist"""
        settings = self.load_settings()
        return settings.get('ipWhitelist', [])

    def save_ip_whitelist(self, whitelist):
        """Save the IP whitelist"""
        self.ip_whitelist = whitelist
        
        # Save the entire config
        self.save_config()
        return self.load_settings()

    def is_ip_whitelisted(self, ip_address):
        """Check if an IP address or range is whitelisted"""
        if not ip_address or ip_address == 'Unknown':
            return False
            
        # Clean IP if it has brackets (IPv6) or a port
        if ip_address.startswith('['):
            ip_address = ip_address.split(']')[0][1:]
        
        if ':' in ip_address:
            # IPv4 with port (e.g. 1.2.3.4:5678)
            if '.' in ip_address:
                ip_address = ip_address.rsplit(':', 1)[0]
            # IPv6 with port is already handled by brackets check

        # Normalize local addresses
        if ip_address in ['::1', 'localhost']:
            ip_address = '127.0.0.1'

        whitelist = self.ip_whitelist
        if not whitelist:
            return False

        try:
            client_ip = ipaddress.ip_address(ip_address)
            for entry in whitelist:
                try:
                    if '/' in entry:
                        if client_ip in ipaddress.ip_network(entry, strict=False):
                            return True
                    elif client_ip == ipaddress.ip_address(entry):
                        return True
                except ValueError:
                    continue
        except ValueError:
            pass
            
        return False

    def get_active_sessions(self):
        """Get ALL active sessions (RTSP, HLS, WebRTC) from MediaMTX API"""
        all_formatted = []
        # MediaMTX separates these into different endpoints
        endpoints = [
            ('sessions', None),      # RTSP, RTMP, etc.
            ('hlssessions', 'HLS'),
            ('webrtcsessions', 'WebRTC')
        ]
        
        for ep_name, proto_override in endpoints:
            try:
                # Use 127.0.0.1 for consistency
                url = f"http://127.0.0.1:{MEDIAMTX_API_PORT}/v3/{ep_name}/list"
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('items', []) if isinstance(data, dict) else []
                    
                    for s in items:
                        remote_addr = s.get('remoteAddr', 'Unknown')
                        
                        # Robust IP extraction from "IP:PORT" or "[IPv6]:PORT"
                        clean_ip = remote_addr
                        if remote_addr.startswith('['):
                            clean_ip = remote_addr.split(']')[0][1:]
                        elif ':' in remote_addr:
                             # For IPv4 (and IPv6 without brackets), rsplit the last colon (the port)
                             if remote_addr.count(':') == 1 or '.' in remote_addr:
                                 clean_ip = remote_addr.rsplit(':', 1)[0]
                        
                        all_formatted.append({
                            'id': s.get('id'),
                            'remoteAddr': remote_addr,
                            'cleanIp': clean_ip,
                            'path': s.get('path'),
                            'protocol': proto_override or s.get('protocol', 'Unknown'),
                            'created': s.get('created'),
                            'whitelisted': self.is_ip_whitelisted(clean_ip)
                        })
            except Exception as e:
                if getattr(self, 'debug_mode', False):
                    print(f"  [Session API] Warning fetching {ep_name}: {e}")
                continue
                
        # Sort by creation time (most recent first)
        try:
            all_formatted.sort(key=lambda x: x.get('created') or '', reverse=True)
        except:
            pass
            
        return all_formatted
            
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
                     'showSnapshots': data.get('showSnapshots', True),
                     'outputFramerate': data.get('outputFramerate', 5)
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
                 l['outputFramerate'] = data.get('outputFramerate', 5)
        
        self.save_config()

        # Restart MediaMTX if crucial settings changed
        # Simple check: if layouts changed in a way that affects streams (enabled, resolution, cameras, id)
        # We'll just define that ANY change to the layout structure warrants a check
        # For simplicity, we compare the JSON representation of relevant fields
        
        def extract_stream_config(layouts):
            return [{k: v for k, v in l.items() if k in ['id', 'enabled', 'resolution', 'cameras', 'outputFramerate']} for l in layouts]
            
        if extract_stream_config(old_layouts) != extract_stream_config(self.grid_fusion_layouts):
            print("GridFusion layouts changed, restarting MediaMTX...")
            rtsp_user = self.global_username if self.rtsp_auth_enabled else ''
            rtsp_pass = self.global_password if self.rtsp_auth_enabled else ''
            self.mediamtx.restart(self.cameras, self.rtsp_port, rtsp_user, rtsp_pass, self.get_grid_fusion(), debug_mode=self.debug_mode, advanced_settings=self.advanced_settings)

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
                   static_ip='', netmask='24', gateway='', uuid=None):
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
            'uuid': uuid,
            'debugMode': getattr(self, 'debug_mode', False)
        }
        
        camera = VirtualONVIFCamera(config, self)
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
                      static_ip='', netmask='24', gateway='', uuid=None):
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
        
        if uuid:
            camera.uuid = uuid
        
        print(f"\nUpdated camera: {name}")
        
        # Save config
        self.save_config()
        
        # Restart camera if it was running
        if was_running:
            camera.start()
            rtsp_user = self.global_username if self.rtsp_auth_enabled else ''
            rtsp_pass = self.global_password if self.rtsp_auth_enabled else ''
            self.mediamtx.restart(self.cameras, self.rtsp_port, rtsp_user, rtsp_pass, self.get_grid_fusion(), debug_mode=self.debug_mode, advanced_settings=self.advanced_settings)
        
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
            self.mediamtx.restart(self.cameras, self.rtsp_port, rtsp_user, rtsp_pass, self.get_grid_fusion(), debug_mode=self.debug_mode, advanced_settings=self.advanced_settings)
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
        self.mediamtx.restart(self.cameras, self.rtsp_port, rtsp_user, rtsp_pass, self.get_grid_fusion(), debug_mode=self.debug_mode, advanced_settings=self.advanced_settings)
    
    def stop_all(self):
        """Stop all cameras"""
        for camera in self.cameras:
            camera.stop()
        rtsp_user = self.global_username if self.rtsp_auth_enabled else ''
        rtsp_pass = self.global_password if self.rtsp_auth_enabled else ''
        self.mediamtx.restart(self.cameras, self.rtsp_port, rtsp_user, rtsp_pass, self.get_grid_fusion(), debug_mode=self.debug_mode, advanced_settings=self.advanced_settings)

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

    # --- Watchdog System ---

    def start_watchdog(self):
        """Start the background watchdog thread"""
        if self._watchdog_running:
            return
        self._watchdog_running = True
        self._watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self._watchdog_thread.start()
        print("Stream Health Watchdog started.")

    def _watchdog_loop(self):
        """Monitor stream health and restart if necessary"""
        # Wait for system to stabilize
        time.sleep(30)
        
        while self._watchdog_running:
            try:
                self._check_stream_health()
            except Exception as e:
                print(f"Watchdog error: {e}")
            
            time.sleep(15) # Check every 15 seconds

    def _check_stream_health(self):
        """Check for hung streams and perform recovery"""
        analytics = self.analytics.get_analytics()
        now = time.time()
        restart_needed = False
        stale_paths = []

        for path_name, stats in analytics.items():
            # We care about publishers that are 'ready' but sending 0 bytes
            is_publisher = stats.get('source') == 'publisher'
            is_ready = stats.get('ready', False)
            is_stale = stats.get('stale', False)
            
            if is_ready and is_stale and is_publisher:
                if path_name not in self.stale_path_times:
                    self.stale_path_times[path_name] = now
                
                stale_duration = now - self.stale_path_times[path_name]
                if stale_duration > 120: # 2 minutes of zero-bitrate "zombie" state
                    print(f"Watchdog Alert: Path '{path_name}' has been dead for {stale_duration:.0f}s. Recovery needed.")
                    restart_needed = True
                    stale_paths.append(path_name)
            else:
                # Path is healthy or not active, clear stale marker
                if path_name in self.stale_path_times:
                    del self.stale_path_times[path_name]

        if restart_needed:
            print(f"Watchdog: Restarting MediaMTX to recover {len(stale_paths)} stalled streams...")
            rtsp_user = self.global_username if getattr(self, 'rtsp_auth_enabled', False) else ''
            rtsp_pass = self.global_password if getattr(self, 'rtsp_auth_enabled', False) else ''
            self.mediamtx.restart(
                self.cameras, 
                self.rtsp_port, 
                rtsp_user, 
                rtsp_pass, 
                self.get_grid_fusion(), 
                debug_mode=self.debug_mode, 
                advanced_settings=self.advanced_settings
            )
            # Clear all stale trackers after restart to give them time to come back
            self.stale_path_times.clear()
            time.sleep(30) # Grace period after restart
