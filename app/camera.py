
import threading
import socket
import time
import uuid
import hashlib
import queue
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import os
from concurrent.futures import ThreadPoolExecutor
from werkzeug.serving import make_server, ThreadedWSGIServer
from .config import MEDIAMTX_PORT
from .onvif_service import ONVIFService
from .linux_network import LinuxNetworkManager
from .utils import get_local_ip


class ThreadPoolWSGIServer(ThreadedWSGIServer):
    """Custom WSGI server with a fixed-size thread pool to prevent thread exhaustion"""
    
    def __init__(self, host, port, app, max_workers=20, **kwargs):
        super().__init__(host, port, app, **kwargs)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.max_workers = max_workers
    
    def process_request(self, request, client_address):
        """Process incoming request using thread pool instead of spawning new threads"""
        try:
            self.executor.submit(self.process_request_thread, request, client_address)
        except (RuntimeError, AttributeError):
            # Fall back to spawning a daemon thread if the thread pool or interpreter is shutting down
            try:
                t = threading.Thread(
                    target=self.process_request_thread,
                    args=(request, client_address),
                    daemon=True
                )
                t.start()
            except Exception:
                # Synchronous fallback as a last resort
                try:
                    self.process_request_thread(request, client_address)
                except Exception:
                    pass
    
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

class RTSPFrameGrabber:
    def __init__(self, rtsp_url):
        self.rtsp_url = rtsp_url
        self.cap = None
        self.latest_frame = None
        self.running = False
        self.thread = None
        self.cv2 = None
        
    def start(self, cv2):
        self.cv2 = cv2
        self.running = True
        self.thread = threading.Thread(target=self._grab_loop, daemon=True)
        self.thread.start()
        
    def _grab_loop(self):
        import time
        last_frame_time = time.time()
        
        while self.running:
            if self.cap and self.cap.isOpened():
                try:
                    ret, frame = self.cap.read()
                    if ret:
                        self.latest_frame = frame
                        last_frame_time = time.time()
                    else:
                        time.sleep(0.01)
                        if time.time() - last_frame_time > 5.0:
                            print(f"  [AI Camera Grabber] Stream read timeout. Reconnecting to {self.rtsp_url}...")
                            try:
                                self.cap.release()
                            except Exception:
                                pass
                            self.cap = self.cv2.VideoCapture(self.rtsp_url)
                            self.cap.set(self.cv2.CAP_PROP_BUFFERSIZE, 1)
                            last_frame_time = time.time()
                except Exception:
                    time.sleep(0.05)
            else:
                try:
                    if self.cap:
                        self.cap.release()
                except Exception:
                    pass
                try:
                    self.cap = self.cv2.VideoCapture(self.rtsp_url)
                    self.cap.set(self.cv2.CAP_PROP_BUFFERSIZE, 1)
                except Exception as e:
                    print(f"  [AI Camera Grabber] Error connecting to {self.rtsp_url}: {e}")
                last_frame_time = time.time()
                time.sleep(1.0)
                
    def stop(self):
        self.running = False
        if self.thread:
            try:
                self.thread.join(timeout=1.0)
            except Exception:
                pass
            self.thread = None
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

import threading
# Global AI state for memory management across all cameras
_AI_MODELS = {}
_AI_MODEL_LOCK = threading.Lock()
_AI_INFERENCE_LOCK = threading.Lock()

def get_shared_ai_model(model_name):
    global _AI_MODELS
    with _AI_MODEL_LOCK:
        if model_name not in _AI_MODELS:
            from ultralytics import YOLO
            try:
                import torch
                # Limit threads so multiple cameras don't oversubscribe CPU cores and exhaust memory
                torch.set_num_threads(2)
            except Exception:
                pass
            _AI_MODELS[model_name] = YOLO(model_name)
        return _AI_MODELS[model_name]

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
        self.disable_substream = config.get('disableSubstream', False)
        self.use_main_as_substream = config.get('useMainAsSubstream', False)
        self.enable_audio = config.get('enableAudio', False)
        self.transcode_main_audio = config.get('transcodeMainAudio', False)
        self.transcode_sub_audio = config.get('transcodeSubAudio', False)
        
        # Audio transcoding settings
        self.audio_encoding_main = config.get('audioEncodingMain', 'aac')
        self.audio_sample_rate_main = config.get('audioSampleRateMain', '44100')
        self.audio_bitrate_main = config.get('audioBitrateMain', '128k')
        
        self.audio_encoding_sub = config.get('audioEncodingSub', 'aac')
        self.audio_sample_rate_sub = config.get('audioSampleRateSub', '44100')
        self.audio_bitrate_sub = config.get('audioBitrateSub', '64k')
        
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
        
        # Event forwarding settings
        self.enable_event_forwarding = config.get('enableEventForwarding', False)
        self.physical_onvif_port = config.get('physicalOnvifPort', 80)
        self.onvif_forwarding_username = config.get('onvifForwardingUsername', '')
        self.onvif_forwarding_password = config.get('onvifForwardingPassword', '')
        self._event_forwarding_thread = None
        self._event_forwarding_running = False
        self.event_logs = []
        
        # AI Event Detection settings
        self.event_source = config.get('eventSource', 'onvif')  # 'onvif' or 'ai'
        self.ai_targets = config.get('aiTargets', ['person', 'vehicle'])
        self.ai_model = config.get('aiModel', 'yolov8n.pt')
        self.ai_motion_detection_enabled = config.get('aiMotionDetectionEnabled', True)
        self.ai_motion_sensitivity = config.get('aiMotionSensitivity', 50)
        self.ai_zone = config.get('aiZone', [])
        self._ai_thread = None
        self._ai_running = False
        
        # AI statistics
        self.ai_inference_count = 0
        self.ai_last_inference_time = 0.0
        self.ai_last_inference_latency = 0.0
        self.ai_avg_inference_latency = 0.0
        self.ai_queue_time = 0.0
        self.ai_fps_measurement = 0.0
        self.ai_last_detection = []
        
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
        
    def get_effective_ip(self):
        """Determine the IP address that should be reported for this camera"""
        # 1. Use the specific IP assigned to a Virtual NIC if active
        if self.assigned_ip:
            return self.assigned_ip
            
        # 2. Use the host/IP set in the global server settings (if it's not 'localhost')
        if self.manager and hasattr(self.manager, 'server_ip') and \
           self.manager.server_ip and self.manager.server_ip != 'localhost':
            return self.manager.server_ip
            
        # 3. Fallback to automatic detection
        return get_local_ip()
        
    def start(self):
        """Mark camera as running and start ONVIF service"""
        self.status = "running"
        
        # Setup Virtual NIC if requested (Linux only)
        if self.use_virtual_nic and self.network_mgr:
            # VNIC name must be <= 15 chars on Linux.
            # Use UUID (stripped of hyphens) to ensure uniqueness regardless of camera name.
            vnic_name = f"vnic_{self.uuid.replace('-', '')[:10]}"
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
        if self.enable_event_forwarding:
            if self.event_source == 'ai':
                self.start_ai_detection()
            else:
                self.start_event_forwarding()
        
    def stop(self):
        """Mark camera as stopped, shutdown ONVIF service, and cleanup networking"""
        self.status = "stopped"
        if self.enable_event_forwarding:
            self.stop_event_forwarding()
            self.stop_ai_detection()
        
        # Stop the ONVIF WSGI server safely
        if hasattr(self, 'server') and self.server:
            try:
                import threading
                srv = self.server
                def _safe_shutdown():
                    try:
                        srv.shutdown()
                        srv.server_close()
                        if hasattr(srv, 'executor') and srv.executor:
                            srv.executor.shutdown(wait=False)
                    except Exception as shutdown_err:
                        print(f"  Error during background socket shutdown for {self.name}: {shutdown_err}")
                threading.Thread(target=_safe_shutdown, daemon=True).start()
                self.server = None
            except Exception as e:
                print(f"  Error shutting down ONVIF server for {self.name}: {e}")
        
        # Cleanup Virtual NIC
        if self.use_virtual_nic and self.network_mgr:
            vnic_name = f"vnic_{self.uuid.replace('-', '')[:10]}"
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
        
        # Create server with thread pool to prevent thread exhaustion (with retry for port release)
        server = None
        for attempt in range(10):
            try:
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
                break
            except OSError as e:
                if attempt < 9:
                    print(f"  [Camera ({self.name})] Port {self.onvif_port} busy, retrying in 0.3s... (attempt {attempt+1}/10)")
                    time.sleep(0.3)
                else:
                    raise e
        
        # Replace the server class with our thread-pooled version
        server.__class__ = ThreadPoolWSGIServer
        server.executor = ThreadPoolExecutor(max_workers=20)
        server.max_workers = 20
        
        self.server = server
        
        # Run server in a separate thread
        self.flask_thread = threading.Thread(
            target=self.server.serve_forever,
            daemon=True
        )
        self.flask_thread.start()
        
        # Start WS-Discovery
        # Use effective IP for discovery reporting
        local_ip = self.get_effective_ip()
        
        self.onvif_service.start_discovery_service(local_ip)
        
        print(f"  ONVIF service started on port {self.onvif_port}")
        print(f"  Add manually in ODM: {local_ip}:{self.onvif_port}\n")
        
    def to_dict(self):
        """Convert to dictionary for API"""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'name': self.name,
            'host': self.get_effective_ip(),
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
            'disableSubstream': self.disable_substream,
            'useMainAsSubstream': self.use_main_as_substream,
            'enableAudio': self.enable_audio,
            'transcodeMainAudio': self.transcode_main_audio,
            'transcodeSubAudio': self.transcode_sub_audio,
            'audioEncodingMain': self.audio_encoding_main,
            'audioSampleRateMain': self.audio_sample_rate_main,
            'audioBitrateMain': self.audio_bitrate_main,
            'audioEncodingSub': self.audio_encoding_sub,
            'audioSampleRateSub': self.audio_sample_rate_sub,
            'audioBitrateSub': self.audio_bitrate_sub,
            'useVirtualNic': self.use_virtual_nic,
            'parentInterface': self.parent_interface,
            'nicMac': self.nic_mac,
            'ipMode': self.ip_mode,
            'staticIp': self.static_ip,
            'netmask': self.netmask,
            'gateway': self.gateway,
            'assignedIp': self.assigned_ip,
            'macAddress': self.mac_address,
            'debugMode': self.debug_mode,
            'enableEventForwarding': self.enable_event_forwarding,
            'physicalOnvifPort': self.physical_onvif_port,
            'onvifForwardingUsername': self.onvif_forwarding_username,
            'onvifForwardingPassword': self.onvif_forwarding_password,
            'eventSource': self.event_source,
            'aiTargets': self.ai_targets,
            'aiModel': self.ai_model,
            'aiMotionDetectionEnabled': self.ai_motion_detection_enabled,
            'aiMotionSensitivity': self.ai_motion_sensitivity,
            'aiZone': self.ai_zone,
            'aiInferenceCount': self.ai_inference_count,
            'aiLastInferenceTime': self.ai_last_inference_time,
            'aiLastInferenceLatency': self.ai_last_inference_latency,
            'aiAvgInferenceLatency': self.ai_avg_inference_latency,
            'aiQueueTime': self.ai_queue_time,
            'aiFpsMeasurement': self.ai_fps_measurement,
            'aiLastDetection': self.ai_last_detection
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
            'disableSubstream': self.disable_substream,
            'useMainAsSubstream': self.use_main_as_substream,
            'enableAudio': self.enable_audio,
            'transcodeMainAudio': self.transcode_main_audio,
            'transcodeSubAudio': self.transcode_sub_audio,
            'useVirtualNic': self.use_virtual_nic,
            'parentInterface': self.parent_interface,
            'nicMac': self.nic_mac,
            'ipMode': self.ip_mode,
            'staticIp': self.static_ip,
            'netmask': self.netmask,
            'gateway': self.gateway,
            'debugMode': self.debug_mode,
            'enableEventForwarding': self.enable_event_forwarding,
            'physicalOnvifPort': self.physical_onvif_port,
            'onvifForwardingUsername': self.onvif_forwarding_username,
            'onvifForwardingPassword': self.onvif_forwarding_password,
            'eventSource': self.event_source,
            'aiTargets': self.ai_targets,
            'aiModel': self.ai_model,
            'aiMotionDetectionEnabled': self.ai_motion_detection_enabled,
            'aiMotionSensitivity': self.ai_motion_sensitivity,
            'aiZone': self.ai_zone
        }

    def start_event_forwarding(self):
        """Start ONVIF Event Forwarder background thread"""
        self._event_forwarding_running = True
        self._event_forwarding_thread = threading.Thread(target=self._event_forwarding_loop, daemon=True)
        self._event_forwarding_thread.start()
        print(f"  [Camera ({self.name})] ONVIF event forwarder thread started.")

    def stop_event_forwarding(self):
        """Stop ONVIF Event Forwarder background thread"""
        self._event_forwarding_running = False
        print(f"  [Camera ({self.name})] ONVIF event forwarder thread stopped.")

    def _event_forwarding_loop(self):
        """Background thread loop to pull event notifications from physical camera"""
        from urllib.parse import urlparse
        
        while self._event_forwarding_running:
            try:
                from urllib.parse import unquote
                parsed = urlparse(self.main_stream_url.replace('rtsp://', 'http://'))
                host = parsed.hostname
                # Use dedicated ONVIF forwarding credentials if set, otherwise fall back to stream creds
                if self.onvif_forwarding_username:
                    username = self.onvif_forwarding_username
                    password = self.onvif_forwarding_password
                else:
                    username = unquote(parsed.username) if parsed.username else (self.username or 'admin')
                    password = unquote(parsed.password) if parsed.password else (self.password or 'admin')
                port = getattr(self, 'physical_onvif_port', 80) or 80
            except Exception as e:
                print(f"  [ONVIF Event Forwarder ({self.name})] Error parsing stream URL: {e}")
                time.sleep(10)
                continue
                
            print(f"  [ONVIF Event Forwarder ({self.name})] Connecting to camera events at {host}:{port}...")
            
            # Locate WSDLs
            import onvif
            wsdl_dir = os.path.join(os.path.dirname(onvif.__file__), 'wsdl')
            if not os.path.exists(os.path.join(wsdl_dir, 'devicemgmt.wsdl')):
                local_wsdl = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wsdl')
                if os.path.exists(os.path.join(local_wsdl, 'devicemgmt.wsdl')):
                    wsdl_dir = local_wsdl
                else:
                    wsdl_dir = None
                    
            try:
                from onvif import ONVIFCamera
                if wsdl_dir:
                    mycam = ONVIFCamera(host, port, username, password, wsdl_dir=wsdl_dir)
                else:
                    mycam = ONVIFCamera(host, port, username, password)
                    
                # 2. Get events service XAddr
                events_xaddr = None
                try:
                    caps = mycam.devicemgmt.GetCapabilities(Category=['Events', 'All'])
                    events_xaddr = caps.Events.XAddr
                except Exception:
                    try:
                        services = mycam.devicemgmt.GetServices(IncludeCapability=False)
                        for s in services:
                            if 'events' in s.Namespace.lower():
                                events_xaddr = s.XAddr
                                break
                    except Exception:
                        pass
                
                if not events_xaddr:
                    events_xaddr = f"http://{host}:{port}/onvif/events_service"
                
                # 3. Create PullPoint subscription using raw SOAP POST (robust authentication handling)
                pullpoint_addr = None
                auth_modes = ['digest', 'text', 'none']
                last_err = None
                self.current_auth_mode = 'digest'
                subscription_limit_hit = False
                
                for mode in auth_modes:
                    try:
                        sec_header = get_ws_security_header(username, password, mode=mode)
                        sub_payload = f"""<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:wsa="http://www.w3.org/2005/08/addressing" xmlns:tet="http://www.onvif.org/ver10/events/wsdl">
                          <soap:Header>
                            <wsa:Action>http://www.onvif.org/ver10/events/wsdl/EventPortType/CreatePullPointSubscriptionRequest</wsa:Action>
                            <wsa:To>{events_xaddr}</wsa:To>
                            {sec_header}
                          </soap:Header>
                          <soap:Body>
                            <tet:CreatePullPointSubscription/>
                          </soap:Body>
                        </soap:Envelope>"""
                        
                        sub_headers = {
                            'Content-Type': 'application/soap+xml; charset=utf-8; action="http://www.onvif.org/ver10/events/wsdl/EventPortType/CreatePullPointSubscriptionRequest"',
                        }
                        
                        resp = requests.post(events_xaddr, data=sub_payload, headers=sub_headers, timeout=15)
                        if resp.status_code == 200:
                            sub_root = ET.fromstring(resp.text)
                            addr_node = sub_root.find('.//{*}SubscriptionReference/{*}Address')
                            if addr_node is None:
                                addr_node = sub_root.find('.//{*}Address')
                            
                            if addr_node is not None and addr_node.text:
                                pullpoint_addr = addr_node.text.strip()
                                self.current_auth_mode = mode
                                break
                            else:
                                raise Exception("SubscriptionReference Address node not found in XML response")
                        elif resp.status_code == 500 and 'SubscribeCreationFailedFault' in resp.text:
                            # Camera has hit its max concurrent subscription limit - no point
                            # trying other auth modes, this is a capacity issue not an auth issue
                            subscription_limit_hit = True
                            last_err = Exception(f"Camera at max concurrent ONVIF subscriptions (HTTP 500 SubscribeCreationFailedFault)")
                            break
                        else:
                            raise Exception(f"HTTP {resp.status_code}: {resp.text[:200]}")
                    except Exception as e:
                        last_err = e
                        continue
                
                if not pullpoint_addr:
                    if subscription_limit_hit:
                        print(f"  [ONVIF Event Forwarder ({self.name})] Camera '{self.name}' is at its max concurrent ONVIF subscription limit. Another client is using the slot. Waiting 30s for a slot to free up...")
                        time.sleep(30)
                        continue
                    raise Exception(f"Subscription creation failed across all auth modes. Last error: {last_err}")
                
                print(f"  [ONVIF Event Forwarder ({self.name})] Subscription created using auth mode '{self.current_auth_mode}'. PullPoint address: {pullpoint_addr}")
                
                # Poll loop
                try:
                    while self._event_forwarding_running:
                        payload = f"""<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:wsa="http://www.w3.org/2005/08/addressing" xmlns:tet="http://www.onvif.org/ver10/events/wsdl">
                          <soap:Header>
                            <wsa:Action>http://www.onvif.org/ver10/events/wsdl/PullPointSubscription/PullMessagesRequest</wsa:Action>
                            <wsa:To>{pullpoint_addr}</wsa:To>
                            {get_ws_security_header(username, password, mode=self.current_auth_mode)}
                          </soap:Header>
                          <soap:Body>
                            <tet:PullMessages>
                              <tet:Timeout>PT5S</tet:Timeout>
                              <tet:MessageLimit>10</tet:MessageLimit>
                            </tet:PullMessages>
                          </soap:Body>
                        </soap:Envelope>"""
                        
                        headers = {
                            'Content-Type': 'application/soap+xml; charset=utf-8; action="http://www.onvif.org/ver10/events/wsdl/PullPointSubscription/PullMessagesRequest"',
                        }
                        
                        try:
                            resp = requests.post(pullpoint_addr, data=payload, headers=headers, timeout=15)
                            if resp.status_code == 200:
                                events_list = parse_pull_messages_response(resp.text)
                                for evt in events_list:
                                    # Filter: only keep relevant motion, alarm, tamper, detector, input events
                                    topic_lower = evt['topic'].lower()
                                    is_relevant = any(k in topic_lower for k in ['motion', 'alarm', 'tamper', 'detector', 'input', 'logicalstate', 'digital', 'image'])
                                    if not is_relevant:
                                        continue
                                        
                                    evt['camera_id'] = self.id
                                    evt['camera_name'] = self.name
                                    evt['type'] = 'onvif'
                                    evt['timestamp'] = evt['timestamp'] or datetime.utcnow().isoformat() + 'Z'
                                    
                                    # Log locally (limit to 50)
                                    self.event_logs.append(evt)
                                    if len(self.event_logs) > 50:
                                        self.event_logs.pop(0)
                                        
                                    # Broadcast to virtual clients
                                    if self.onvif_service:
                                        for sub in list(self.onvif_service.subscriptions.values()):
                                            try:
                                                sub.queue.put_nowait(evt)
                                            except queue.Full:
                                                try:
                                                    sub.queue.get_nowait()
                                                    sub.queue.put_nowait(evt)
                                                except:
                                                    pass
                                                    
                                    # Log globally (limit to 200)
                                    if self.manager:
                                        if not hasattr(self.manager, 'onvif_events'):
                                            self.manager.onvif_events = []
                                        self.manager.onvif_events.append(evt)
                                        if len(self.manager.onvif_events) > 200:
                                            self.manager.onvif_events.pop(0)
                                            
                                    if getattr(self, 'debug_mode', False):
                                        print(f"  [ONVIF Event ({self.name})] {evt['topic']} = {evt['value']}")
                            else:
                                print(f"  [ONVIF Event Forwarder ({self.name})] PullMessages returned status {resp.status_code}. Reconnecting...")
                                break
                        except Exception as poll_err:
                            print(f"  [ONVIF Event Forwarder ({self.name})] PullMessages connection error: {poll_err}. Reconnecting...")
                            break
                finally:
                    # Always clean up the subscription to free the camera slot
                    if pullpoint_addr:
                        try:
                            unsub_payload = f"""<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:wsnt="http://docs.oasis-open.org/wsn/b-2">
                              <soap:Header>
                                {get_ws_security_header(username, password, mode=self.current_auth_mode)}
                              </soap:Header>
                              <soap:Body>
                                <wsnt:Unsubscribe/>
                              </soap:Body>
                            </soap:Envelope>"""
                            unsub_headers = {
                                'Content-Type': 'application/soap+xml; charset=utf-8; action="http://docs.oasis-open.org/wsn/bw-2/SubscriptionManager/UnsubscribeRequest"',
                            }
                            # Send unsubscribe to pullpoint_addr
                            requests.post(pullpoint_addr, data=unsub_payload, headers=unsub_headers, timeout=5)
                            print(f"  [ONVIF Event Forwarder ({self.name})] Sent Unsubscribe to camera '{self.name}' to release subscription slot.")
                        except Exception as unsub_err:
                            print(f"  [ONVIF Event Forwarder ({self.name})] Failed to unsubscribe from camera '{self.name}': {unsub_err}")
                            
            except Exception as conn_err:
                print(f"  [ONVIF Event Forwarder ({self.name})] ONVIF events connection failed: {conn_err}. Retrying in 10s...")
                time.sleep(10)

    def start_ai_detection(self):
        """Start local AI event detection background thread"""
        self._ai_running = True
        self._ai_thread = threading.Thread(target=self._ai_detection_loop, daemon=True)
        self._ai_thread.start()
        print(f"  [Camera ({self.name})] Local AI detection thread started.")

    def stop_ai_detection(self):
        """Stop local AI event detection background thread"""
        self._ai_running = False
        if hasattr(self, '_ai_thread') and self._ai_thread and self._ai_thread.is_alive():
            try:
                self._ai_thread.join(timeout=2.0)
            except Exception:
                pass
        print(f"  [Camera ({self.name})] Local AI detection thread stopped.")

    def _ai_detection_loop(self):
        # Lazy imports
        try:
            import cv2
            from ultralytics import YOLO
        except ImportError as e:
            print(f"  [AI Error] Failed to import cv2 or ultralytics. Make sure they are installed: {e}")
            from datetime import datetime
            self.event_logs.append({
                'topic': 'System/Error',
                'value': 'true',
                'data_name': 'AIImportError',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'camera_name': self.name,
                'error_message': 'Failed to import cv2 or ultralytics. Check installation.'
            })
            self._ai_running = False
            return

        # Determine stream URL
        stream_path = f"{self.path_name}_sub" if (self.sub_stream_url and not self.disable_substream) else self.path_name
        local_url = f"rtsp://127.0.0.1:{self.rtsp_port}/{stream_path}"
        
        print(f"  [AI Camera ({self.name})] Connecting to stream: {local_url}")
        grabber = RTSPFrameGrabber(local_url)
        grabber.start(cv2)
            
        try:
            model = get_shared_ai_model(self.ai_model)
        except Exception as e:
            print(f"  [AI Error] Failed to load YOLO model: {e}")
            from datetime import datetime
            self.event_logs.append({
                'topic': 'System/Error',
                'value': 'true',
                'data_name': 'AIModelLoadError',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'camera_name': self.name,
                'error_message': f'Failed to load YOLO model: {e}'
            })
            grabber.stop()
            self._ai_running = False
            return
            
        # COCO class mapping
        class_map = {
            'person': [0],
            'vehicle': [2, 3, 5, 7],
            'animal': [15, 16, 17, 18, 19]
        }
        
        monitored_classes = []
        for target in self.ai_targets:
            if target in class_map:
                monitored_classes.extend(class_map[target])
                
        if not monitored_classes:
            monitored_classes = [0, 2, 3, 5, 7]  # Default fallback
            
        print(f"  [AI Camera ({self.name})] Monitored class IDs: {monitored_classes}")
        
        # Map sensitivity (0-100) to motion change threshold
        # Higher sensitivity = lower threshold = triggers on less motion
        # sensitivity 10 -> threshold ~4.0% of pixels must change
        # sensitivity 50 -> threshold ~1.5% of pixels must change
        # sensitivity 95 -> threshold ~0.15% of pixels must change
        # motion_threshold = max(0.1, 5.0 - (self.ai_motion_sensitivity / 100.0) * 5.0)
        # conf_threshold = 0.40  # Fixed YOLO confidence
        motion_threshold = max(0.1, 5.0 - (self.ai_motion_sensitivity / 100.0) * 5.0)
        conf_threshold = 0.40  # Fixed YOLO confidence
        print(f"  [AI Camera ({self.name})] Motion change threshold: {motion_threshold:.2f}% (sensitivity: {self.ai_motion_sensitivity})")
        
        motion_state = False
        last_detected_time = 0
        cooldown_period = 5.0  # seconds
        prev_gray = None
        startup_frames = 0
        startup_grace = 5  # Skip first N frames to establish baseline
        last_loop_time = 0
        
        # Zone-aware motion masking: only detect motion inside the drawn zone
        import numpy as np
        zone_points = self.ai_zone if len(self.ai_zone) >= 3 else None
        zone_mask = None
        zone_pixel_count = 0
        
        while self._ai_running:
            loop_start = time.time()
            if last_loop_time > 0:
                self.ai_fps_measurement = round(1.0 / (loop_start - last_loop_time), 2)
            last_loop_time = loop_start
            
            raw_frame = grabber.latest_frame
            if raw_frame is not None:
                try:
                    # Optimize CPU usage by resizing frame to a max width of 640px before processing
                    h, w = raw_frame.shape[:2]
                    if w > 640:
                        scale = 640.0 / w
                        frame = cv2.resize(raw_frame, (640, int(h * scale)))
                    else:
                        frame = raw_frame
                        
                    # Update w and h to resized dimensions for zone calculation
                    h, w = frame.shape[:2]
                    
                    # Create zone mask on first valid frame (only once)
                    if zone_mask is None and zone_points:
                        zone_mask = np.zeros((h, w), dtype=np.uint8)
                        pts = np.array([[int(p.get('x', 0) * w), int(p.get('y', 0) * h)] for p in zone_points], dtype=np.int32)
                        cv2.fillPoly(zone_mask, [pts], 255)
                        zone_pixel_count = cv2.countNonZero(zone_mask)
                        print(f"  [AI Camera ({self.name})] Zone mask applied: {zone_pixel_count}/{h * w} pixels monitored ({round(zone_pixel_count / (h * w) * 100, 1)}% of frame)")
 
                    # Convert current frame to grayscale for motion comparison
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    gray = cv2.GaussianBlur(gray, (21, 21), 0)
                    
                    if prev_gray is None:
                        # First frame — establish baseline, no detection
                        prev_gray = gray
                        startup_frames += 1
                    elif startup_frames <= startup_grace:
                        # Still in grace period — update baseline but don't trigger
                        prev_gray = gray
                        startup_frames += 1
                    else:
                        startup_frames += 1
                        
                        # Frame differencing: detect pixel-level changes
                        frame_delta = cv2.absdiff(prev_gray, gray)
                        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
                        
                        # Apply zone mask: ignore all motion outside the drawn zone
                        if zone_mask is not None:
                            thresh = cv2.bitwise_and(thresh, zone_mask)
                            change_pct = (cv2.countNonZero(thresh) / zone_pixel_count) * 100.0 if zone_pixel_count > 0 else 0.0
                        else:
                            change_pct = (cv2.countNonZero(thresh) / thresh.size) * 100.0
                        
                        # Update baseline for next comparison
                        prev_gray = gray
                        
                        # Only run AI if enough motion detected
                        if change_pct < motion_threshold:
                            # No significant motion — check cooldown for clearing state
                            self.ai_last_detection = []
                            if motion_state and (time.time() - last_detected_time > cooldown_period):
                                motion_state = False
                                self._trigger_ai_motion(False, [])
                        else:
                            # Motion detected — run YOLO to identify what's moving
                            # Use a global lock to prevent multiple cameras from running inference at the exact same millisecond
                            t_queue_start = time.time()
                            with _AI_INFERENCE_LOCK:
                                t_inference_start = time.time()
                                results = model(frame, verbose=False, conf=conf_threshold, classes=monitored_classes)
                                t_inference_end = time.time()
                                
                            self.ai_queue_time = round(t_inference_start - t_queue_start, 3)
                            self.ai_last_inference_latency = round(t_inference_end - t_inference_start, 3)
                            self.ai_last_inference_time = t_inference_end
                            self.ai_inference_count += 1
                            if self.ai_avg_inference_latency == 0.0:
                                self.ai_avg_inference_latency = self.ai_last_inference_latency
                            else:
                                self.ai_avg_inference_latency = round(0.9 * self.ai_avg_inference_latency + 0.1 * self.ai_last_inference_latency, 3)
                            
                            detected_tags = set()
                            h, w = frame.shape[:2]
                            zone = self.ai_zone if len(self.ai_zone) >= 3 else None
                            
                            for result in results:
                                for box in result.boxes:
                                    cls_id = int(box.cls[0])
                                    
                                    # Zone filtering: check if box center is inside zone polygon
                                    if zone:
                                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                                        cx = ((x1 + x2) / 2) / w  # normalize to 0-1
                                        cy = ((y1 + y2) / 2) / h
                                        if not self._point_in_polygon(cx, cy, zone):
                                            continue
                                    
                                    if cls_id == 0:
                                        detected_tags.add('person')
                                    elif cls_id in [2, 3, 5, 7]:
                                        detected_tags.add('vehicle')
                                    elif cls_id in [15, 16, 17, 18, 19]:
                                        detected_tags.add('animal')
                                        
                            self.ai_last_detection = list(detected_tags)
                            if detected_tags:
                                last_detected_time = time.time()
                                if not motion_state:
                                    motion_state = True
                                    self._trigger_ai_motion(True, list(detected_tags))
                            else:
                                if motion_state and (time.time() - last_detected_time > cooldown_period):
                                    motion_state = False
                                    self._trigger_ai_motion(False, [])
                                    
                except Exception as ex:
                    print(f"  [AI Camera ({self.name})] Error in inference loop: {ex}")
                    
            # Target frame rate: ~2.0 FPS (1 frame every 500ms)
            elapsed = time.time() - loop_start
            sleep_time = max(0.01, 0.50 - elapsed)
            time.sleep(sleep_time)
            
        grabber.stop()
        print(f"  [AI Camera ({self.name})] AI detection thread finished.")

    def _point_in_polygon(self, px, py, polygon):
        """Ray casting algorithm to check if point is inside polygon"""
        n = len(polygon)
        inside = False
        j = n - 1
        for i in range(n):
            xi = polygon[i].get('x', 0)
            yi = polygon[i].get('y', 0)
            xj = polygon[j].get('x', 0)
            yj = polygon[j].get('y', 0)
            if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        return inside

    def trigger_test_event(self):
        """Trigger a test ONVIF event (motion detected, then clear after 3 seconds)"""
        print(f"  [AI Camera ({self.name})] User triggered test ONVIF event...")
        # Trigger motion detected
        self._trigger_ai_motion(is_active=True, tags=['test'])
        
        def _clear_after_delay():
            time.sleep(3)
            self._trigger_ai_motion(is_active=False, tags=['test'])
            
        import threading
        threading.Thread(target=_clear_after_delay, daemon=True).start()
        return True

    def _trigger_ai_motion(self, is_active, tags):
        """Broadcast motion state from local AI engine to subscribers"""
        val = 'true' if is_active else 'false'
        topic = 'RuleEngine/CellMotionDetector/Motion'
        data_name = 'IsMotion'
        
        from datetime import datetime
        evt = {
            'topic': topic,
            'value': val,
            'data_name': data_name,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'camera_id': self.id,
            'camera_name': self.name,
            'tags': tags,
            'type': 'ai'
        }
        
        # Log locally (limit to 50 logs)
        self.event_logs.append(evt)
        if len(self.event_logs) > 50:
            self.event_logs.pop(0)
            
        # Log globally (limit to 200)
        if self.manager:
            if not hasattr(self.manager, 'onvif_events'):
                self.manager.onvif_events = []
            self.manager.onvif_events.append(evt)
            if len(self.manager.onvif_events) > 200:
                self.manager.onvif_events.pop(0)
            
        print(f"  [AI Camera ({self.name})] AI Event: {topic} = {val} (Tags: {tags})")
        
        # Broadcast to virtual clients
        if self.onvif_service:
            import queue
            for sub in list(self.onvif_service.subscriptions.values()):
                try:
                    sub.queue.put_nowait(evt)
                except queue.Full:
                    try:
                        sub.queue.get_nowait()
                        sub.queue.put_nowait(evt)
                    except:
                        pass

def get_ws_security_header(username, password, mode='digest'):
    if not username:
        return ""
    if mode == 'none':
        return ""
    if mode == 'text':
        return f"""
        <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd" xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
          <wsse:UsernameToken>
            <wsse:Username>{username}</wsse:Username>
            <wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">{password}</wsse:Password>
          </wsse:UsernameToken>
        </wsse:Security>
        """
    # Default to digest
    import base64
    import hashlib
    import secrets
    from datetime import datetime
    nonce_bytes = secrets.token_bytes(16)
    nonce_b64 = base64.b64encode(nonce_bytes).decode('utf-8')
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    hasher = hashlib.sha1()
    hasher.update(nonce_bytes)
    hasher.update(timestamp.encode('utf-8'))
    hasher.update(password.encode('utf-8'))
    digest_b64 = base64.b64encode(hasher.digest()).decode('utf-8')
    return f"""
    <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd" xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
      <wsse:UsernameToken>
        <wsse:Username>{username}</wsse:Username>
        <wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordDigest">{digest_b64}</wsse:Password>
        <wsse:Nonce EncodingType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary">{nonce_b64}</wsse:Nonce>
        <wsu:Created>{timestamp}</wsu:Created>
      </wsse:UsernameToken>
    </wsse:Security>
    """


def parse_pull_messages_response(xml_data):
    """Parse standard ONVIF XML response for PullMessages"""
    events = []
    try:
        root = ET.fromstring(xml_data)
        for message_node in root.findall('.//{*}NotificationMessage'):
            topic_node = message_node.find('.//{*}Topic')
            topic = topic_node.text.strip() if topic_node is not None else "unknown"
            
            # Remove namespace prefixes from topic name for cleaner display
            clean_topic = topic
            if '/' in topic:
                parts = []
                for p in topic.split('/'):
                    if ':' in p:
                        parts.append(p.split(':')[1])
                    else:
                        parts.append(p)
                clean_topic = '/'.join(parts)
            elif ':' in topic:
                clean_topic = topic.split(':')[1]
            
            msg_node = message_node.find('.//{*}Message')
            if msg_node is not None:
                data_node = msg_node.find('.//{*}Data')
                value = None
                data_name = 'IsMotion'
                if data_node is not None:
                    simple_items = data_node.findall('.//{*}SimpleItem')
                    for item in simple_items:
                        name = item.attrib.get('Name', '')
                        val = item.attrib.get('Value', '')
                        if name.lower() in ['ismotion', 'active', 'state', 'value', 'status']:
                            value = val
                            data_name = name
                            break
                    if value is None and len(simple_items) > 0:
                        value = simple_items[0].attrib.get('Value', None)
                        data_name = simple_items[0].attrib.get('Name', 'IsMotion')
                
                source_node = message_node.find('.//{*}Source')
                source = {}
                if source_node is not None:
                    for item in source_node.findall('.//{*}SimpleItem'):
                        name = item.attrib.get('Name', '')
                        val = item.attrib.get('Value', '')
                        if name:
                            source[name] = val
                
                timestamp = msg_node.attrib.get('UtcTime', None)
                if not timestamp:
                    child = msg_node.find('.//{*}Message')
                    if child is not None:
                        timestamp = child.attrib.get('UtcTime', None)
                
                # Scan for person / vehicle tags
                detection_tags = []
                def scan_str(s):
                    if not s:
                        return
                    s_lower = str(s).lower()
                    if any(x in s_lower for x in ['human', 'person', 'face', 'pedestrian', 'people']):
                        if 'person' not in detection_tags:
                            detection_tags.append('person')
                    if any(x in s_lower for x in ['vehicle', 'car', 'truck', 'bus', 'bike', 'motorcycle', 'nonmotor', 'plate']):
                        if 'vehicle' not in detection_tags:
                            detection_tags.append('vehicle')

                scan_str(clean_topic)
                if source:
                    for k, v in source.items():
                        scan_str(k)
                        scan_str(v)
                
                if msg_node is not None:
                    data_node = msg_node.find('.//{*}Data')
                    if data_node is not None:
                        for item in data_node.findall('.//{*}SimpleItem'):
                            for attr_name, attr_val in item.attrib.items():
                                scan_str(attr_name)
                                scan_str(attr_val)

                events.append({
                    'topic': clean_topic,
                    'value': value if value is not None else 'false',
                    'data_name': data_name,
                    'timestamp': timestamp,
                    'source': source,
                    'tags': detection_tags
                })
    except Exception as e:
        print(f"Error parsing PullMessages XML: {e}")
    return events
