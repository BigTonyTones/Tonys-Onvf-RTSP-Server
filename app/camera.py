
import threading
import socket
import time
import uuid
import hashlib
from concurrent.futures import ThreadPoolExecutor
from werkzeug.serving import make_server, ThreadedWSGIServer
from .config import MEDIAMTX_PORT
from .onvif_service import ONVIFService
from .linux_network import LinuxNetworkManager


class ThreadPoolWSGIServer(ThreadedWSGIServer):
    """Custom WSGI server with a fixed-size thread pool to prevent thread exhaustion"""
    
    def __init__(self, host, port, app, max_workers=20, **kwargs):
        super().__init__(host, port, app, **kwargs)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.max_workers = max_workers
    
    def process_request(self, request, client_address):
        """Process incoming request using thread pool instead of spawning new threads"""
        self.executor.submit(self.process_request_thread, request, client_address)
    
    def process_request_thread(self, request, client_address):
        """Handle one request in a thread from the pool"""
        try:
            self.finish_request(request, client_address)
        except Exception:
            self.handle_error(request, client_address)
        finally:
            self.shutdown_request(request)
    
    def shutdown(self):
        """Shutdown the server and thread pool"""
        self.executor.shutdown(wait=True)
        super().shutdown()

class VirtualONVIFCamera:
    """Represents a virtual ONVIF camera"""
    
    def __init__(self, config, manager=None):
        self.manager = manager
        self.id = config['id']
        self.uuid = config.get('uuid') or str(uuid.uuid4())
        self.name = config['name']
        self.main_stream_url = config['mainStreamUrl']
        self.sub_stream_url = config['subStreamUrl']
        self.rtsp_port = config.get('rtspPort', MEDIAMTX_PORT)
        self.onvif_port = config.get('onvifPort', 8000 + self.id)
        self.path_name = config.get('pathName', f'camera{self.id}')
        self.username = config.get('username', 'admin')
        self.password = config.get('password', '')
        self.auto_start = config.get('autoStart', False)
        # Resolution settings
        self.main_width = config.get('mainWidth', 1920)
        self.main_height = config.get('mainHeight', 1080)
        self.sub_width = config.get('subWidth', 640)
        self.sub_height = config.get('subHeight', 480)
        # Frame rate settings
        self.main_framerate = config.get('mainFramerate', 30)
        self.sub_framerate = config.get('subFramerate', 15)
        
        # ONVIF authentication credentials
        self.onvif_username = config.get('onvifUsername', 'admin')
        self.onvif_password = config.get('onvifPassword', 'admin')
        self.transcode_sub = config.get('transcodeSub', False)
        self.transcode_main = config.get('transcodeMain', False)
        
        # Network settings (Linux only)
        self.use_virtual_nic = config.get('useVirtualNic', False)
        self.parent_interface = config.get('parentInterface', '')
        self.nic_mac = config.get('nicMac', '')
        self.ip_mode = config.get('ipMode', 'dhcp') # 'dhcp' or 'static'
        self.static_ip = config.get('staticIp', '')
        self.netmask = config.get('netmask', '24')
        self.gateway = config.get('gateway', '')
        self.debug_mode = config.get('debugMode', False)
        self.assigned_ip = None
        self.network_mgr = LinuxNetworkManager() if LinuxNetworkManager.is_linux() else None
        
        self.status = "stopped"
        self.flask_app = None
        self.flask_thread = None
        self.onvif_service = None

    @property
    def mac_address(self):
        """Get the MAC address for this camera (Virtual NIC or generated)"""
        if self.nic_mac and ':' in self.nic_mac:
            return self.nic_mac.lower()
        
        # Generate a stable MAC based on camera UUID if none provided
        # Use hashlib to get a deterministic hash from the UUID
        h = hashlib.md5(self.uuid.encode()).hexdigest()
        # Take the first 10 characters for the MAC suffix (5 bytes)
        # Prefix with 02 to indicate locally administered
        mac = f"02:{h[0:2]}:{h[2:4]}:{h[4:6]}:{h[6:8]}:{h[8:10]}"
        return mac.lower()
        
    def start(self):
        """Mark camera as running and start ONVIF service"""
        self.status = "running"
        
        # Setup Virtual NIC if requested (Linux only)
        if self.use_virtual_nic and self.network_mgr:
            vnic_name = f"vnic_{self.path_name[:10]}"
            if self.network_mgr.create_macvlan(self.parent_interface, vnic_name, self.nic_mac):
                self.assigned_ip = self.network_mgr.setup_ip(
                    vnic_name, 
                    self.ip_mode, 
                    self.static_ip, 
                    self.netmask, 
                    self.gateway
                )
            # Give the system and router a moment to stabilize
            time.sleep(0.5)
        
        self._start_onvif_service()
        
    def stop(self):
        """Mark camera as stopped and cleanup networking"""
        self.status = "stopped"
        
        # Cleanup Virtual NIC
        if self.use_virtual_nic and self.network_mgr:
            vnic_name = f"vnic_{self.path_name[:10]}"
            self.network_mgr.remove_interface(vnic_name)
            self.assigned_ip = None
        
    def _start_onvif_service(self):
        """Start the ONVIF web service"""
        # Check if already running
        if self.flask_thread and self.flask_thread.is_alive():
            print(f"  ONVIF service already running on port {self.onvif_port}")
            return
            
        self.onvif_service = ONVIFService(self)
        app = self.onvif_service.create_app()
        self.flask_app = app
        
        # Use assigned IP if available, otherwise 0.0.0.0
        bind_ip = self.assigned_ip if self.assigned_ip else '0.0.0.0'
        
        # Create server with thread pool to prevent thread exhaustion
        server = make_server(
            bind_ip,
            self.onvif_port,
            app,
            threaded=False,  # Disable default threading
            request_handler=None,
            passthrough_errors=False,
            ssl_context=None,
            fd=None
        )
        
        # Replace the server class with our thread-pooled version
        server.__class__ = ThreadPoolWSGIServer
        server.executor = ThreadPoolExecutor(max_workers=20)
        server.max_workers = 20
        
        # Run server in a separate thread
        self.flask_thread = threading.Thread(
            target=server.serve_forever,
            daemon=True
        )
        self.flask_thread.start()
        
        # Start WS-Discovery
        # Use assigned IP for discovery if virtual NIC is active
        local_ip = self.assigned_ip if self.assigned_ip else socket.gethostbyname(socket.gethostname())
        
        self.onvif_service.start_discovery_service(local_ip)
        
        print(f"  ONVIF service started on port {self.onvif_port}")
        print(f"  Add manually in ODM: {local_ip}:{self.onvif_port}\n")
        
    def to_dict(self):
        """Convert to dictionary for API"""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'name': self.name,
            'mainStreamUrl': self.main_stream_url,
            'subStreamUrl': self.sub_stream_url,
            'rtspPort': self.rtsp_port,
            'onvifPort': self.onvif_port,
            'pathName': self.path_name,
            'username': self.username,
            'password': self.password,
            'autoStart': self.auto_start,
            'status': self.status,
            'mainWidth': self.main_width,
            'mainHeight': self.main_height,
            'subWidth': self.sub_width,
            'subHeight': self.sub_height,
            'mainFramerate': self.main_framerate,
            'subFramerate': self.sub_framerate,
            'onvifUsername': self.onvif_username,
            'onvifPassword': self.onvif_password,
            'transcodeSub': self.transcode_sub,
            'transcodeMain': self.transcode_main,
            'useVirtualNic': self.use_virtual_nic,
            'parentInterface': self.parent_interface,
            'nicMac': self.nic_mac,
            'ipMode': self.ip_mode,
            'staticIp': self.static_ip,
            'netmask': self.netmask,
            'gateway': self.gateway,
            'assignedIp': self.assigned_ip,
            'macAddress': self.mac_address,
            'debugMode': self.debug_mode
        }
    
    def to_config_dict(self):
        """Convert to dictionary for config file (excludes runtime status)"""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'name': self.name,
            'mainStreamUrl': self.main_stream_url,
            'subStreamUrl': self.sub_stream_url,
            'rtspPort': self.rtsp_port,
            'onvifPort': self.onvif_port,
            'pathName': self.path_name,
            'username': self.username,
            'password': self.password,
            'autoStart': self.auto_start,
            # NOTE: status is NOT saved - it's runtime only
            # This ensures autoStart setting is respected on server restart
            'mainWidth': self.main_width,
            'mainHeight': self.main_height,
            'subWidth': self.sub_width,
            'subHeight': self.sub_height,
            'mainFramerate': self.main_framerate,
            'subFramerate': self.sub_framerate,
            'onvifUsername': self.onvif_username,
            'onvifPassword': self.onvif_password,
            'transcodeSub': self.transcode_sub,
            'transcodeMain': self.transcode_main,
            'useVirtualNic': self.use_virtual_nic,
            'parentInterface': self.parent_interface,
            'nicMac': self.nic_mac,
            'ipMode': self.ip_mode,
            'staticIp': self.static_ip,
            'netmask': self.netmask,
            'gateway': self.gateway,
            'debugMode': self.debug_mode
        }
