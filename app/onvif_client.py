import sys
import os
import logging
import socket
import struct
import uuid
import time
import re
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

# Suppress zeep logging
logging.getLogger('zeep').setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

class ONVIFProber:
    def __init__(self):
        self.wsdl_dir = None
        # Try to locate WSDL files if needed, but onvif-zeep usually finds them

    # ----------------------------------------------------------------
    #  WS-Discovery based ONVIF Network Scanner
    # ----------------------------------------------------------------
    WS_DISCOVERY_MULTICAST = '239.255.255.250'
    WS_DISCOVERY_PORT = 3702

    # SOAP probe template for WS-Discovery
    _PROBE_TEMPLATE = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"'
        ' xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing"'
        ' xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery"'
        ' xmlns:dn="http://www.onvif.org/ver10/network/wsdl">'
        '<s:Header>'
        '<a:Action s:mustUnderstand="1">'
        'http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe'
        '</a:Action>'
        '<a:MessageID>uuid:{msg_id}</a:MessageID>'
        '<a:ReplyTo><a:Address>'
        'http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous'
        '</a:Address></a:ReplyTo>'
        '<a:To s:mustUnderstand="1">'
        'urn:schemas-xmlsoap-org:ws:2005:04:discovery'
        '</a:To>'
        '</s:Header>'
        '<s:Body>'
        '<d:Probe>'
        '<d:Types>dn:NetworkVideoTransmitter</d:Types>'
        '</d:Probe>'
        '</s:Body>'
        '</s:Envelope>'
    )

    def network_scan(self, timeout=4):
        """
        Discover ONVIF cameras on the local network using WS-Discovery.
        Returns a list of discovered devices with their addresses and basic info.
        """
        msg_id = str(uuid.uuid4())
        probe_msg = self._PROBE_TEMPLATE.format(msg_id=msg_id).encode('utf-8')

        devices = {}  # keyed by XAddr to de-duplicate

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(0.5)

        # Set multicast TTL
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack('b', 4))

        try:
            # Send the probe multiple times for reliability
            for _ in range(3):
                sock.sendto(probe_msg, (self.WS_DISCOVERY_MULTICAST, self.WS_DISCOVERY_PORT))
                time.sleep(0.1)

            # Collect responses until timeout
            deadline = time.time() + timeout
            while time.time() < deadline:
                try:
                    data, addr = sock.recvfrom(65535)
                    sender_ip = addr[0]
                    device = self._parse_probe_match(data, sender_ip)
                    if device:
                        # Use first XAddr as key for de-duplication
                        key = device.get('xaddrs', [None])[0] or sender_ip
                        if key not in devices:
                            devices[key] = device
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.debug(f"Error receiving WS-Discovery response: {e}")
                    continue
        finally:
            sock.close()

        result = list(devices.values())

        # Try to get device info for each discovered camera using GetDeviceInformation
        for device in result:
            self._enrich_device_info(device)

        return result

    def _parse_probe_match(self, data, sender_ip):
        """Parse a WS-Discovery ProbeMatch XML response."""
        try:
            root = ET.fromstring(data)
        except ET.ParseError:
            return None

        # Define namespace map
        ns = {
            's': 'http://www.w3.org/2003/05/soap-envelope',
            'd': 'http://schemas.xmlsoap.org/ws/2005/04/discovery',
            'a': 'http://schemas.xmlsoap.org/ws/2004/08/addressing',
        }

        # Find ProbeMatch elements
        matches = root.findall('.//d:ProbeMatch', ns)
        if not matches:
            return None

        match = matches[0]

        # Extract endpoint reference (EPR)
        epr_el = match.find('.//a:Address', ns)
        epr = epr_el.text.strip() if epr_el is not None and epr_el.text else ''

        # Extract types
        types_el = match.find('d:Types', ns)
        types = types_el.text.strip() if types_el is not None and types_el.text else ''

        # Extract scopes  
        scopes_el = match.find('d:Scopes', ns)
        scopes_text = scopes_el.text.strip() if scopes_el is not None and scopes_el.text else ''
        scopes = scopes_text.split() if scopes_text else []

        # Extract XAddrs (service URLs)
        xaddrs_el = match.find('d:XAddrs', ns)
        xaddrs_text = xaddrs_el.text.strip() if xaddrs_el is not None and xaddrs_el.text else ''
        xaddrs = xaddrs_text.split() if xaddrs_text else []

        # Parse useful scope data
        hardware_name = ''
        scope_name = ''
        location = ''
        for scope in scopes:
            scope_lower = scope.lower()
            if '/name/' in scope_lower:
                scope_name = scope.split('/name/')[-1]
            elif '/hardware/' in scope_lower:
                hardware_name = scope.split('/hardware/')[-1]
            elif '/location/' in scope_lower:
                location = scope.split('/location/')[-1]

        # Extract host and port from XAddrs
        onvif_host = sender_ip
        onvif_port = 80
        if xaddrs:
            try:
                parsed = urlparse(xaddrs[0])
                onvif_host = parsed.hostname or sender_ip
                onvif_port = parsed.port or 80
            except Exception:
                pass

        return {
            'ip': sender_ip,
            'host': onvif_host,
            'port': onvif_port,
            'name': scope_name or hardware_name or f'ONVIF Device ({sender_ip})',
            'hardware': hardware_name,
            'location': location,
            'types': types,
            'xaddrs': xaddrs,
            'scopes': scopes,
            'epr': epr,
            'manufacturer': '',
            'model': '',
            'firmware': '',
        }

    def _enrich_device_info(self, device):
        """Try a quick unauthenticated GetDeviceInformation call to populate manufacturer/model."""
        if not device.get('xaddrs'):
            return

        xaddr = device['xaddrs'][0]
        soap_body = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"'
            ' xmlns:tds="http://www.onvif.org/ver10/device/wsdl">'
            '<s:Header/>'
            '<s:Body><tds:GetDeviceInformation/></s:Body>'
            '</s:Envelope>'
        )
        try:
            parsed = urlparse(xaddr)
            host = parsed.hostname
            port = parsed.port or 80
            path = parsed.path or '/onvif/device_service'

            conn = socket.create_connection((host, port), timeout=2)
            http_req = (
                f"POST {path} HTTP/1.1\r\n"
                f"Host: {host}:{port}\r\n"
                f"Content-Type: application/soap+xml; charset=utf-8\r\n"
                f"Content-Length: {len(soap_body)}\r\n"
                f"Connection: close\r\n"
                f"\r\n"
                f"{soap_body}"
            )
            conn.sendall(http_req.encode('utf-8'))

            response = b''
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                response += chunk
            conn.close()

            resp_text = response.decode('utf-8', errors='replace')

            # Parse manufacturer, model, firmware from response
            for tag, key in [('Manufacturer', 'manufacturer'), ('Model', 'model'),
                             ('FirmwareVersion', 'firmware')]:
                m = re.search(rf'<[^>]*{tag}[^>]*>([^<]+)</', resp_text)
                if m:
                    device[key] = m.group(1).strip()

        except Exception:
            # Silently ignore — many cameras require auth for GetDeviceInformation
            pass


        
    def probe(self, host, port, username, password):
        """
        Connect to an ONVIF camera and return available media profiles with RTSP URLs.
        Returns:
            {
                'success': True,
                'profiles': [
                    {
                        'name': 'Profile1',
                        'token': 'token1',
                        'streamUrl': 'rtsp://...',
                        'width': 1920,
                        'height': 1080,
                        'framerate': 30
                    }, ...
                ]
            }
        """
        try:
            # Import here to avoid issues if not installed
            from onvif import ONVIFCamera
            import onvif
        except ImportError:
            return {
                'success': False, 
                'error': 'onvif-zeep library not installed. Please install it with: pip install onvif-zeep'
            }

        try:
            print(f"Connecting to ONVIF camera at {host}:{port}...")
            
            # Connect to Camera
            # We assume the WSDLs are in the standard location
            # Match the library's internal WSDL directory
            wsdl_dir = os.path.join(os.path.dirname(onvif.__file__), 'wsdl')
            
            # Check if devicemgmt.wsdl exists in the primary wsdl_dir
            if not os.path.exists(os.path.join(wsdl_dir, 'devicemgmt.wsdl')):
                # Search for WSDLs in common locations
                possible_paths = [
                    # Linux venv (user-specific path logic)
                    os.path.join(os.path.dirname(os.path.dirname(onvif.__file__)), 'wsdl'),
                    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(onvif.__file__))), 'share', 'onvif', 'wsdl'),
                    # Windows paths
                    r"C:\Users\Tony\AppData\Roaming\Python\Lib\site-packages\onvif\wsdl",
                    # Default system paths
                    "/usr/local/lib/python3.11/dist-packages/onvif/wsdl",
                    "/usr/lib/python3/dist-packages/onvif/wsdl",
                ]
                
                found_valid = False
                for p in possible_paths:
                    if os.path.exists(os.path.join(p, 'devicemgmt.wsdl')):
                        wsdl_dir = p
                        print(f"  [ONVIF] Found WSDLs at alternative location: {wsdl_dir}")
                        found_valid = True
                        break
                
                if not found_valid:
                    print(f"  [ONVIF] Warning: devicemgmt.wsdl not found in standard paths.")
                    print(f"  [ONVIF] Checking if it's in the same directory as this file...")
                    local_wsdl = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wsdl')
                    if os.path.exists(os.path.join(local_wsdl, 'devicemgmt.wsdl')):
                        wsdl_dir = local_wsdl
                        print(f"  [ONVIF] Found local WSDLs: {wsdl_dir}")
                    else:
                        # Fallback: Let the library try its own defaults if we can't find it
                        # but if the devicemgmt.wsdl is truly missing from the package, this will still fail.
                        print(f"  [ONVIF] Final fallback: attempting to use library defaults")
                        wsdl_dir = None
            
            # Connect to Camera
            try:
                if wsdl_dir:
                    mycam = ONVIFCamera(host, port, username, password, wsdl_dir=wsdl_dir)
                else:
                    mycam = ONVIFCamera(host, port, username, password)
            except Exception as e:
                error_str = str(e)
                if "No such file" in error_str and "wsdl" in error_str:
                    return {
                        'success': False,
                        'error': f"ONVIF WSDL files are missing from your installation. "
                                 f"Please run: 'pip install --force-reinstall onvif-zeep' "
                                 f"or 'pip install onvif-zeep-foscam' to fix this. "
                                 f"(Original Error: {error_str})"
                    }
                raise e # Re-raise to catch in outer block
            
            # Create media service
            media = mycam.create_media_service()
            
            # Get Profiles
            profiles = media.GetProfiles()
            
            result_profiles = []
            
            for profile in profiles:
                try:
                    # Generic RTSP Stream
                    stream_setup = {
                        'Stream': 'RTP-Unicast',
                        'Transport': {
                            'Protocol': 'RTSP'
                        }
                    }
                    
                    # Get RTSP Stream URL
                    stream_uri_resp = media.GetStreamUri({
                        'StreamSetup': stream_setup,
                        'ProfileToken': profile.token
                    })
                    
                    rtsp_url = stream_uri_resp.Uri
                    
                    # Inject credentials into RTSP URL if missing
                    # (Many cameras return RTSP URL without credentials)
                    if username and password and '@' not in rtsp_url:
                        parsed = urlparse(rtsp_url)
                        if not parsed.username:
                            # Reconstruct URL with credentials
                            scheme = parsed.scheme
                            netloc = f"{username}:{password}@{parsed.netloc}"
                            path = parsed.path
                            params = parsed.params
                            query = parsed.query
                            fragment = parsed.fragment
                            
                            from urllib.parse import urlunparse
                            rtsp_url = urlunparse((scheme, netloc, path, params, query, fragment))
                    
                    # Extract Video Resolution if available
                    width = 0
                    height = 0
                    framerate = 0
                    
                    if hasattr(profile, 'VideoEncoderConfiguration') and profile.VideoEncoderConfiguration:
                        config = profile.VideoEncoderConfiguration
                        if hasattr(config, 'Resolution'):
                            width = config.Resolution.Width
                            height = config.Resolution.Height
                        if hasattr(config, 'RateControl') and hasattr(config.RateControl, 'FrameRateLimit'):
                            framerate = int(config.RateControl.FrameRateLimit)
                    
                    result_profiles.append({
                        'name': profile.Name,
                        'token': profile.token,
                        'streamUrl': rtsp_url,
                        'width': width,
                        'height': height,
                        'framerate': framerate
                    })
                    
                except Exception as e:
                    print(f"Error processing profile {profile.token}: {e}")
                    continue
            
            # Sort profiles by resolution (High to Low)
            result_profiles.sort(key=lambda x: x['width'] * x['height'], reverse=True)
            
            return {
                'success': True,
                'profiles': result_profiles,
                'device_info': {
                    'host': host,
                    'port': port
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_detailed_diagnostics(self, host, port, username, password):
        """
        Connect to an ONVIF camera and return detailed info + raw SOAP XML for troubleshooting.
        """
        try:
            from onvif import ONVIFCamera
            from zeep.plugins import HistoryPlugin
            from lxml import etree
        except ImportError:
            return {
                'success': False, 
                'error': 'onvif-zeep or lxml library not installed.'
            }

        history = HistoryPlugin()
        
        # Locate WSDLs (same logic as probe)
        import onvif
        wsdl_dir = os.path.join(os.path.dirname(onvif.__file__), 'wsdl')
        if not os.path.exists(os.path.join(wsdl_dir, 'devicemgmt.wsdl')):
            local_wsdl = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wsdl')
            if os.path.exists(os.path.join(local_wsdl, 'devicemgmt.wsdl')):
                wsdl_dir = local_wsdl
            else:
                wsdl_dir = None

        try:
            if wsdl_dir:
                mycam = ONVIFCamera(host, port, username, password, wsdl_dir=wsdl_dir)
            else:
                mycam = ONVIFCamera(host, port, username, password)
            
            # Attach history plugin to zeep clients
            def attach_history(service):
                if service and hasattr(service, 'zeep_client'):
                    if history not in service.zeep_client.plugins:
                        service.zeep_client.plugins.append(history)

            attach_history(mycam.devicemgmt)

            diag_results = []

            def record_call(name, func, *args, **kwargs):
                call_info = {'name': name, 'success': False}
                try:
                    res = func(*args, **kwargs)
                    call_info['success'] = True
                    # Result is often a zeep object, convert if possible or just store type
                    call_info['result_type'] = str(type(res))
                except Exception as e:
                    call_info['error'] = str(e)
                
                # Capture history for THIS call
                if history.last_sent:
                    # XML formatting
                    try:
                        req_xml = etree.tostring(history.last_sent['envelope'], encoding='unicode', pretty_print=True)
                        resp_xml = etree.tostring(history.last_received['envelope'], encoding='unicode', pretty_print=True)
                        call_info['request_xml'] = req_xml
                        call_info['response_xml'] = resp_xml
                    except:
                        call_info['request_xml'] = str(history.last_sent['envelope'])
                        call_info['response_xml'] = str(history.last_received['envelope'])
                
                diag_results.append(call_info)
                return res if call_info['success'] else None

            # 1. Device Information
            record_call("GetDeviceInformation", mycam.devicemgmt.GetDeviceInformation)
            
            # 2. Capabilities
            record_call("GetCapabilities", mycam.devicemgmt.GetCapabilities)
            
            # 3. Network Interfaces
            record_call("GetNetworkInterfaces", mycam.devicemgmt.GetNetworkInterfaces)

            # 4. Media Profiles
            media = mycam.create_media_service()
            attach_history(media)
            profiles = record_call("GetProfiles", media.GetProfiles)
            
            if profiles:
                # Get more details for the first profile if exists
                token = profiles[0].token
                record_call(f"GetStreamUri (Token: {token})", media.GetStreamUri, {
                    'StreamSetup': {'Stream': 'RTP-Unicast', 'Transport': {'Protocol': 'RTSP'}},
                    'ProfileToken': token
                })

            return {
                'success': True,
                'diagnostics': diag_results
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
