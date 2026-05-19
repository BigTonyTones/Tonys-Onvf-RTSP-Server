
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
            self.start_event_forwarding()
        
    def stop(self):
        """Mark camera as stopped, shutdown ONVIF service, and cleanup networking"""
        self.status = "stopped"
        if self.enable_event_forwarding:
            self.stop_event_forwarding()
        
        # Stop the ONVIF WSGI server safely
        if hasattr(self, 'server') and self.server:
            try:
                import threading
                # shutdown() tells the serve_forever() loop to exit
                threading.Thread(target=self.server.shutdown, daemon=True).start()
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
            'onvifForwardingPassword': self.onvif_forwarding_password
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
            'onvifForwardingPassword': self.onvif_forwarding_password
        }

    def start_event_forwarding(self):
        """Start ONVIF Event Forwarder background thread"""
        self._event_forwarding_running = True
        self._event_forwarding_thread = threading.Thread(target=self._event_forwarding_loop, daemon=True)
        self._event_forwarding_thread.start()
        print(f"  [Camera {self.id}] ONVIF event forwarder thread started.")

    def stop_event_forwarding(self):
        """Stop ONVIF Event Forwarder background thread"""
        self._event_forwarding_running = False
        print(f"  [Camera {self.id}] ONVIF event forwarder thread stopped.")

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
                print(f"  [ONVIF Event Forwarder {self.id}] Error parsing stream URL: {e}")
                time.sleep(10)
                continue
                
            print(f"  [ONVIF Event Forwarder {self.id}] Connecting to camera events at {host}:{port}...")
            
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
                        print(f"  [ONVIF Event Forwarder {self.id}] Camera '{self.name}' is at its max concurrent ONVIF subscription limit. Another client is using the slot. Waiting 30s for a slot to free up...")
                        time.sleep(30)
                        continue
                    raise Exception(f"Subscription creation failed across all auth modes. Last error: {last_err}")
                
                print(f"  [ONVIF Event Forwarder {self.id}] Subscription created using auth mode '{self.current_auth_mode}'. PullPoint address: {pullpoint_addr}")
                
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
                                        print(f"  [ONVIF Event {self.id}] {evt['topic']} = {evt['value']}")
                            else:
                                print(f"  [ONVIF Event Forwarder {self.id}] PullMessages returned status {resp.status_code}. Reconnecting...")
                                break
                        except Exception as poll_err:
                            print(f"  [ONVIF Event Forwarder {self.id}] PullMessages connection error: {poll_err}. Reconnecting...")
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
                            print(f"  [ONVIF Event Forwarder {self.id}] Sent Unsubscribe to camera '{self.name}' to release subscription slot.")
                        except Exception as unsub_err:
                            print(f"  [ONVIF Event Forwarder {self.id}] Failed to unsubscribe from camera '{self.name}': {unsub_err}")
                            
            except Exception as conn_err:
                print(f"  [ONVIF Event Forwarder {self.id}] ONVIF events connection failed: {conn_err}. Retrying in 10s...")
                time.sleep(10)




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
