
import json
import time
import socket
import struct
import threading
from pathlib import Path
from flask import Flask, request, Response
from flask_cors import CORS
from datetime import datetime, timezone
import sys

# Try to import zoneinfo
if sys.version_info >= (3, 9):
    try:
        import zoneinfo
    except ImportError:
        # Fallback will be handled in _get_system_date_time
        pass
else:
    try:
        from backports import zoneinfo
    except ImportError:
        pass

from .config import CONFIG_FILE

class ONVIFService:
    def __init__(self, camera):
        self.camera = camera
        self.app = None
        
    def create_app(self):
        """Create the Flask app for ONVIF service"""
        app = Flask(f"onvif_camera_{self.camera.id}")
        CORS(app)
        self.app = app
        
        # Disable Flask logging if not in debug mode
        import logging
        log = logging.getLogger('werkzeug')
        if getattr(self.camera, 'debug_mode', False):
            log.setLevel(logging.INFO)
        else:
            log.setLevel(logging.ERROR)
        
        # Disable Flask development server warnings
        import os
        os.environ['FLASK_ENV'] = 'production'
        
        # Get correct local IP for ONVIF URLs (Use assigned IP for Virtual NICs)
        local_ip = self.camera.assigned_ip if self.camera.assigned_ip else socket.gethostbyname(socket.gethostname())
        
        # Authentication decorator for ONVIF endpoints
        def require_auth(f):
            from functools import wraps
            @wraps(f)
            def decorated(*args, **kwargs):
                # Check for Basic Auth
                auth = request.authorization
                
                if auth:
                    pass_len = len(auth.password) if auth.password else 0
                else:
                    pass
                
                # Allow if credentials match Basic Auth
                if auth and auth.username == self.camera.onvif_username and auth.password == self.camera.onvif_password:
                    return f(*args, **kwargs)
                
                # Check for SOAP WS-UsernameToken (Found in body)
                data = request.get_data(as_text=True)
                
                # More robust check for UsernameToken
                if 'UsernameToken' in data and f'>{self.camera.onvif_username}</' in data:
                     # Check if it's actually inside a username tag
                     if f'<Username>{self.camera.onvif_username}</Username>' in data or \
                        f':Username>{self.camera.onvif_username}</' in data:
                         return f(*args, **kwargs)
                     return f(*args, **kwargs)
                
                if 'Authorization' in request.headers and 'Digest' in request.headers['Authorization']:
                     pass
                else:
                     pass
                
                return Response(
                    'Authentication required', 401,
                    {'WWW-Authenticate': 'Basic realm="ONVIF"'}
                )
            return decorated
        
        # ONVIF Device Management
        @app.route('/onvif/device_service', methods=['GET', 'POST'], endpoint=f'device_service_{self.camera.id}')
        @require_auth
        def device_service():
            try:
                if request.method == 'GET':
                    return self._get_device_wsdl()
                
                # Parse SOAP request
                soap_body = request.data.decode('utf-8')
                
                # GetDeviceInformation
                if 'GetDeviceInformation' in soap_body:
                    return self._handle_get_device_info()
                
                # GetCapabilities
                elif 'GetCapabilities' in soap_body:
                    return self._handle_get_capabilities(local_ip)
                
                # GetServices
                elif 'GetServices' in soap_body:
                    return self._handle_get_services(local_ip)
                
                # GetSystemDateAndTime
                elif 'GetSystemDateAndTime' in soap_body:
                    return self._handle_get_system_date_time()
                
                # GetNetworkInterfaces
                elif 'GetNetworkInterfaces' in soap_body:
                    return self._handle_get_network_interfaces()
                
                # Default response
                return self._handle_get_device_info()
                
            except Exception as e:
                print(f"  Error handling request: {e}")
                import traceback
                traceback.print_exc()
                return Response("Internal Server Error", status=500)
            
        # Root Route: Handle ONVIF Device Service at the root for convenience
        @app.route('/', methods=['GET', 'POST'], endpoint=f'root_service_{self.camera.id}')
        def root_service():
            return device_service()

        # ONVIF Media Service
        @app.route('/onvif/media_service', methods=['GET', 'POST'], endpoint=f'media_service_{self.camera.id}_v1')
        def media_service_v1():
            if request.method == 'GET':
                return self._get_media_wsdl()
            
            soap_body = request.data.decode('utf-8')
            
            # GetProfiles
            if 'GetProfiles' in soap_body:
                return self._handle_get_profiles()
            
            # GetStreamUri
            elif 'GetStreamUri' in soap_body:
                return self._handle_get_stream_uri(local_ip)
            
            return self._handle_get_profiles()
        
        # ONVIF Media Service (separate endpoint for ODM compatibility)
        @app.route('/onvif/media_service', methods=['GET', 'POST'], endpoint=f'media_service_{self.camera.id}_v2')
        @require_auth
        def media_service_v2():
            try:
                if request.method == 'GET':
                    return self._get_media_wsdl()
                
                # Parse SOAP request
                soap_body = request.data.decode('utf-8')
                
                # GetProfiles
                if 'GetProfiles' in soap_body:
                    return self._handle_get_profiles()
                
                # GetStreamUri
                elif 'GetStreamUri' in soap_body:
                    return self._handle_get_stream_uri(local_ip)
                
                # GetVideoSources
                elif 'GetVideoSources' in soap_body:
                    return self._handle_get_video_sources()
                
                # Default: return profiles
                return self._handle_get_profiles()
                
            except Exception as e:
                print(f"  Error in media service: {e}")
                import traceback
                traceback.print_exc()
                return Response("Internal Server Error", status=500)
                
        return app

    def start_discovery_service(self, local_ip):
        """Start WS-Discovery multicast service for ONVIF discovery"""
        # Check if discovery is already running for this camera
        if hasattr(self, '_discovery_thread') and self._discovery_thread and self._discovery_thread.is_alive():
            return
        
        def discovery_responder():
            MCAST_GRP = '239.255.255.250'
            MCAST_PORT = 3702
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(2.0)
            
            try:
                sock.bind(('', MCAST_PORT))
                mreq = struct.pack('4sl', socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
                print(f"  WS-Discovery listener started for {self.camera.name} on {local_ip}:{self.camera.onvif_port}")
            except Exception as e:
                print(f"  Discovery service error: {e}")
                print(f"  You can still add camera manually in ODM: {local_ip}:{self.camera.onvif_port}")
                return
            
            while self.camera.status == "running":
                try:
                    data, addr = sock.recvfrom(10240)
                    message = data.decode('utf-8', errors='ignore')
                    
                    # Respond to any Probe request
                    if 'Probe' in message or 'probe' in message.lower():
                        # Extract MessageID if present
                        msg_id = "uuid:probe-request"
                        if 'MessageID' in message:
                            try:
                                start = message.find('<a:MessageID>') + 13
                                end = message.find('</a:MessageID>')
                                if start > 12 and end > start:
                                    msg_id = message[start:end]
                            except:
                                pass
                        
                        response = f'''<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope"
                   xmlns:SOAP-ENC="http://www.w3.org/2003/05/soap-encoding"
                   xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing"
                   xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery"
                   xmlns:dn="http://www.onvif.org/ver10/network/wsdl">
    <SOAP-ENV:Header>
        <wsa:MessageID>uuid:{self.camera.id}-{time.time()}</wsa:MessageID>
        <wsa:RelatesTo>{msg_id}</wsa:RelatesTo>
        <wsa:To SOAP-ENV:mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:To>
        <wsa:Action SOAP-ENV:mustUnderstand="true">http://schemas.xmlsoap.org/ws/2005/04/discovery/ProbeMatches</wsa:Action>
    </SOAP-ENV:Header>
    <SOAP-ENV:Body>
        <d:ProbeMatches>
            <d:ProbeMatch>
                <wsa:EndpointReference>
                    <wsa:Address>urn:uuid:camera-{self.camera.id}-virtual</wsa:Address>
                </wsa:EndpointReference>
                <d:Types>dn:NetworkVideoTransmitter</d:Types>
                <d:Scopes>onvif://www.onvif.org/type/NetworkVideoTransmitter onvif://www.onvif.org/name/{self.camera.name.replace(' ', '_')}</d:Scopes>
                <d:XAddrs>http://{local_ip}:{self.camera.onvif_port}/</d:XAddrs>
                <d:MetadataVersion>1</d:MetadataVersion>
            </d:ProbeMatch>
        </d:ProbeMatches>
    </SOAP-ENV:Body>
</SOAP-ENV:Envelope>'''
                        
                        try:
                            sock.sendto(response.encode('utf-8'), addr)
                        except Exception as e:
                            print(f"  Failed to send response: {e}")
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.camera.status == "running":
                        print(f"  Discovery error: {e}")
                    break
            
            try:
                sock.close()
            except:
                pass
        
        # Start discovery thread and store reference
        self._discovery_thread = threading.Thread(target=discovery_responder, daemon=True)
        self._discovery_thread.start()

    def _handle_get_device_info(self):
        """Handle GetDeviceInformation request"""
        soap_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope"
                   xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
    <SOAP-ENV:Body>
        <tds:GetDeviceInformationResponse>
            <tds:Manufacturer>Virtual ONVIF Server</tds:Manufacturer>
            <tds:Model>{self.camera.name}</tds:Model>
            <tds:FirmwareVersion>1.0.0</tds:FirmwareVersion>
            <tds:SerialNumber>{self.camera.mac_address.replace(':', '').upper()}</tds:SerialNumber>
            <tds:HardwareId>{self.camera.mac_address.replace(':', '').upper()}</tds:HardwareId>
        </tds:GetDeviceInformationResponse>
    </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""
        
        return Response(soap_response, mimetype='application/soap+xml')

    def _handle_get_capabilities(self, local_ip):
        """Handle GetCapabilities request"""
        soap_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope"
                   xmlns:tds="http://www.onvif.org/ver10/device/wsdl"
                   xmlns:tt="http://www.onvif.org/ver10/schema">
    <SOAP-ENV:Body>
        <tds:GetCapabilitiesResponse>
            <tds:Capabilities>
                <tt:Analytics>
                    <tt:XAddr>http://{local_ip}:{self.camera.onvif_port}/onvif/analytics_service</tt:XAddr>
                    <tt:RuleSupport>false</tt:RuleSupport>
                    <tt:AnalyticsModuleSupport>false</tt:AnalyticsModuleSupport>
                </tt:Analytics>
                <tt:Device>
                    <tt:XAddr>http://{local_ip}:{self.camera.onvif_port}/onvif/device_service</tt:XAddr>
                    <tt:Network>
                        <tt:IPFilter>false</tt:IPFilter>
                        <tt:ZeroConfiguration>false</tt:ZeroConfiguration>
                        <tt:IPVersion6>false</tt:IPVersion6>
                        <tt:DynDNS>false</tt:DynDNS>
                    </tt:Network>
                    <tt:System>
                        <tt:DiscoveryResolve>false</tt:DiscoveryResolve>
                        <tt:DiscoveryBye>false</tt:DiscoveryBye>
                        <tt:RemoteDiscovery>false</tt:RemoteDiscovery>
                        <tt:SystemBackup>false</tt:SystemBackup>
                        <tt:SystemLogging>false</tt:SystemLogging>
                        <tt:FirmwareUpgrade>false</tt:FirmwareUpgrade>
                        <tt:SupportedVersions>
                            <tt:Major>2</tt:Major>
                            <tt:Minor>5</tt:Minor>
                        </tt:SupportedVersions>
                    </tt:System>
                    <tt:IO>
                        <tt:InputConnectors>0</tt:InputConnectors>
                        <tt:RelayOutputs>0</tt:RelayOutputs>
                    </tt:IO>
                    <tt:Security>
                        <tt:TLS1.1>false</tt:TLS1.1>
                        <tt:TLS1.2>false</tt:TLS1.2>
                        <tt:OnboardKeyGeneration>false</tt:OnboardKeyGeneration>
                        <tt:AccessPolicyConfig>false</tt:AccessPolicyConfig>
                        <tt:X.509Token>false</tt:X.509Token>
                        <tt:SAMLToken>false</tt:SAMLToken>
                        <tt:KerberosToken>false</tt:KerberosToken>
                        <tt:RELToken>false</tt:RELToken>
                    </tt:Security>
                </tt:Device>
                <tt:Events>
                    <tt:XAddr>http://{local_ip}:{self.camera.onvif_port}/onvif/events_service</tt:XAddr>
                    <tt:WSSubscriptionPolicySupport>false</tt:WSSubscriptionPolicySupport>
                    <tt:WSPullPointSupport>false</tt:WSPullPointSupport>
                    <tt:WSPausableSubscriptionManagerInterfaceSupport>false</tt:WSPausableSubscriptionManagerInterfaceSupport>
                </tt:Events>
                <tt:Imaging>
                    <tt:XAddr>http://{local_ip}:{self.camera.onvif_port}/onvif/imaging_service</tt:XAddr>
                </tt:Imaging>
                <tt:Media>
                    <tt:XAddr>http://{local_ip}:{self.camera.onvif_port}/onvif/media_service</tt:XAddr>
                    <tt:StreamingCapabilities>
                        <tt:RTPMulticast>false</tt:RTPMulticast>
                        <tt:RTP_TCP>true</tt:RTP_TCP>
                        <tt:RTP_RTSP_TCP>true</tt:RTP_RTSP_TCP>
                    </tt:StreamingCapabilities>
                </tt:Media>
                <tt:Extension>
                    <tt:DeviceIO>
                        <tt:XAddr>http://{local_ip}:{self.camera.onvif_port}/onvif/deviceio_service</tt:XAddr>
                        <tt:VideoSources>2</tt:VideoSources>
                        <tt:VideoOutputs>0</tt:VideoOutputs>
                        <tt:AudioSources>0</tt:AudioSources>
                        <tt:AudioOutputs>0</tt:AudioOutputs>
                        <tt:RelayOutputs>0</tt:RelayOutputs>
                    </tt:DeviceIO>
                </tt:Extension>
            </tds:Capabilities>
        </tds:GetCapabilitiesResponse>
    </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""
        
        return Response(soap_response, mimetype='application/soap+xml')

    def _handle_get_services(self, local_ip):
        """Handle GetServices request"""
        soap_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope"
                   xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
    <SOAP-ENV:Body>
        <tds:GetServicesResponse>
            <tds:Service>
                <tds:Namespace>http://www.onvif.org/ver10/device/wsdl</tds:Namespace>
                <tds:XAddr>http://{local_ip}:{self.camera.onvif_port}/onvif/device_service</tds:XAddr>
                <tds:Version>
                    <tt:Major xmlns:tt="http://www.onvif.org/ver10/schema">2</tt:Major>
                    <tt:Minor xmlns:tt="http://www.onvif.org/ver10/schema">5</tt:Minor>
                </tds:Version>
            </tds:Service>
            <tds:Service>
                <tds:Namespace>http://www.onvif.org/ver10/media/wsdl</tds:Namespace>
                <tds:XAddr>http://{local_ip}:{self.camera.onvif_port}/onvif/media_service</tds:XAddr>
                <tds:Version>
                    <tt:Major xmlns:tt="http://www.onvif.org/ver10/schema">2</tt:Major>
                    <tt:Minor xmlns:tt="http://www.onvif.org/ver10/schema">5</tt:Minor>
                </tds:Version>
            </tds:Service>
        </tds:GetServicesResponse>
    </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""
        
        return Response(soap_response, mimetype='application/soap+xml')

    def _handle_get_system_date_time(self):
        """Handle GetSystemDateAndTime request - Always uses UTC"""
        now = datetime.now(timezone.utc)
        utc_now = now
        tz_string = "UTC"
        
        soap_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope"
                   xmlns:tds="http://www.onvif.org/ver10/device/wsdl"
                   xmlns:tt="http://www.onvif.org/ver10/schema">
    <SOAP-ENV:Body>
        <tds:GetSystemDateAndTimeResponse>
            <tds:SystemDateAndTime>
                <tt:DateTimeType>NTP</tt:DateTimeType>
                <tt:DaylightSavings>false</tt:DaylightSavings>
                <tt:TimeZone>
                    <tt:TZ>{tz_string}</tt:TZ>
                </tt:TimeZone>
                <tt:UTCDateTime>
                    <tt:Time>
                        <tt:Hour>{utc_now.hour}</tt:Hour>
                        <tt:Minute>{utc_now.minute}</tt:Minute>
                        <tt:Second>{utc_now.second}</tt:Second>
                    </tt:Time>
                    <tt:Date>
                        <tt:Year>{utc_now.year}</tt:Year>
                        <tt:Month>{utc_now.month}</tt:Month>
                        <tt:Day>{utc_now.day}</tt:Day>
                    </tt:Date>
                </tt:UTCDateTime>
                <tt:LocalDateTime>
                    <tt:Time>
                        <tt:Hour>{now.hour}</tt:Hour>
                        <tt:Minute>{now.minute}</tt:Minute>
                        <tt:Second>{now.second}</tt:Second>
                    </tt:Time>
                    <tt:Date>
                        <tt:Year>{now.year}</tt:Year>
                        <tt:Month>{now.month}</tt:Month>
                        <tt:Day>{now.day}</tt:Day>
                    </tt:Date>
                </tt:LocalDateTime>
            </tds:SystemDateAndTime>
        </tds:GetSystemDateAndTimeResponse>
    </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""
        
        return Response(soap_response, mimetype='application/soap+xml')

    def _handle_get_network_interfaces(self):
        """Handle GetNetworkInterfaces request"""
        mac = self.camera.mac_address
        
        soap_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope"
                   xmlns:tds="http://www.onvif.org/ver10/device/wsdl"
                   xmlns:tt="http://www.onvif.org/ver10/schema">
    <SOAP-ENV:Body>
        <tds:GetNetworkInterfacesResponse>
            <tds:NetworkInterfaces token="eth0">
                <tt:Enabled>true</tt:Enabled>
                <tt:Info>
                    <tt:Name>Ethernet0</tt:Name>
                    <tt:HwAddress>{mac}</tt:HwAddress>
                    <tt:MTU>1500</tt:MTU>
                </tt:Info>
                <tt:IPv4>
                    <tt:Enabled>true</tt:Enabled>
                    <tt:Config>
                        <tt:Manual>
                            <tt:Address>{self.camera.assigned_ip if self.camera.assigned_ip else '0.0.0.0'}</tt:Address>
                            <tt:PrefixLength>24</tt:PrefixLength>
                        </tt:Manual>
                        <tt:DHCP>{'true' if self.camera.ip_mode == 'dhcp' else 'false'}</tt:DHCP>
                    </tt:Config>
                </tt:IPv4>
            </tds:NetworkInterfaces>
        </tds:GetNetworkInterfacesResponse>
    </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""
        
        return Response(soap_response, mimetype='application/soap+xml')

    def _handle_get_profiles(self):
        """Handle GetProfiles request"""
        soap_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope"
                   xmlns:trt="http://www.onvif.org/ver10/media/wsdl"
                   xmlns:tt="http://www.onvif.org/ver10/schema">
    <SOAP-ENV:Body>
        <trt:GetProfilesResponse>
            <trt:Profiles token="mainStream" fixed="true">
                <tt:Name>mainStream</tt:Name>
                <tt:VideoSourceConfiguration token="VideoSourceMain">
                    <tt:Name>Main Video Source</tt:Name>
                    <tt:UseCount>1</tt:UseCount>
                    <tt:SourceToken>VideoSourceMain</tt:SourceToken>
                    <tt:Bounds x="0" y="0" width="{self.camera.main_width}" height="{self.camera.main_height}"/>
                </tt:VideoSourceConfiguration>
                <tt:VideoEncoderConfiguration token="VideoEncoderMain">
                    <tt:Name>Main Video Encoder</tt:Name>
                    <tt:UseCount>1</tt:UseCount>
                    <tt:Encoding>H264</tt:Encoding>
                    <tt:Resolution>
                        <tt:Width>{self.camera.main_width}</tt:Width>
                        <tt:Height>{self.camera.main_height}</tt:Height>
                    </tt:Resolution>
                    <tt:Quality>5</tt:Quality>
                    <tt:RateControl>
                        <tt:FrameRateLimit>{self.camera.main_framerate}</tt:FrameRateLimit>
                        <tt:EncodingInterval>1</tt:EncodingInterval>
                        <tt:BitrateLimit>4096</tt:BitrateLimit>
                    </tt:RateControl>
                    <tt:H264>
                        <tt:GovLength>{self.camera.main_framerate}</tt:GovLength>
                        <tt:H264Profile>Main</tt:H264Profile>
                    </tt:H264>
                </tt:VideoEncoderConfiguration>
            </trt:Profiles>
            <trt:Profiles token="subStream" fixed="true">
                <tt:Name>subStream</tt:Name>
                <tt:VideoSourceConfiguration token="VideoSourceSub">
                    <tt:Name>Sub Video Source</tt:Name>
                    <tt:UseCount>1</tt:UseCount>
                    <tt:SourceToken>VideoSourceSub</tt:SourceToken>
                    <tt:Bounds x="0" y="0" width="{self.camera.sub_width}" height="{self.camera.sub_height}"/>
                </tt:VideoSourceConfiguration>
                <tt:VideoEncoderConfiguration token="VideoEncoderSub">
                    <tt:Name>Sub Video Encoder</tt:Name>
                    <tt:UseCount>1</tt:UseCount>
                    <tt:Encoding>H264</tt:Encoding>
                    <tt:Resolution>
                        <tt:Width>{self.camera.sub_width}</tt:Width>
                        <tt:Height>{self.camera.sub_height}</tt:Height>
                    </tt:Resolution>
                    <tt:Quality>3</tt:Quality>
                    <tt:RateControl>
                        <tt:FrameRateLimit>{self.camera.sub_framerate}</tt:FrameRateLimit>
                        <tt:EncodingInterval>1</tt:EncodingInterval>
                        <tt:BitrateLimit>1024</tt:BitrateLimit>
                    </tt:RateControl>
                    <tt:H264>
                        <tt:GovLength>{self.camera.sub_framerate}</tt:GovLength>
                        <tt:H264Profile>Baseline</tt:H264Profile>
                    </tt:H264>
                </tt:VideoEncoderConfiguration>
            </trt:Profiles>
        </trt:GetProfilesResponse>
    </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""
        
        return Response(soap_response, mimetype='application/soap+xml')

    def _handle_get_stream_uri(self, local_ip):
        """Handle GetStreamUri request"""
        # Parse the SOAP request to determine which profile is being requested
        soap_body = request.data.decode('utf-8')
        
        # Check which profile token is requested
        stream_path = f"{self.camera.path_name}_main"  # Default to main stream
        if 'profile_2' in soap_body or 'subStream' in soap_body or 'SubStream' in soap_body:
            stream_path = f"{self.camera.path_name}_sub"
        
        soap_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope"
                   xmlns:trt="http://www.onvif.org/ver10/media/wsdl"
                   xmlns:tt="http://www.onvif.org/ver10/schema">
    <SOAP-ENV:Body>
        <trt:GetStreamUriResponse>
            <trt:MediaUri>
                <tt:Uri>rtsp://{local_ip}:{self.camera.rtsp_port}/{stream_path}</tt:Uri>
                <tt:InvalidAfterConnect>false</tt:InvalidAfterConnect>
                <tt:InvalidAfterReboot>false</tt:InvalidAfterReboot>
                <tt:Timeout>PT60S</tt:Timeout>
            </trt:MediaUri>
        </trt:GetStreamUriResponse>
    </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""
        
        return Response(soap_response, mimetype='application/soap+xml')

    def _get_device_wsdl(self):
        """Return device service WSDL"""
        local_ip = self.camera.assigned_ip if self.camera.assigned_ip else socket.gethostbyname(socket.gethostname())
        
        wsdl = f"""<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
             xmlns:tds="http://www.onvif.org/ver10/device/wsdl"
             xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap12/"
             targetNamespace="http://www.onvif.org/ver10/device/wsdl">
    <service name="DeviceService">
        <port name="DevicePort" binding="tds:DeviceBinding">
            <soap:address location="http://{local_ip}:{self.camera.onvif_port}/"/>
        </port>
    </service>
</definitions>"""
        return Response(wsdl, mimetype='text/xml')

    def _get_media_wsdl(self):
        """Return media service WSDL"""
        local_ip = self.camera.assigned_ip if self.camera.assigned_ip else socket.gethostbyname(socket.gethostname())
        
        wsdl = f"""<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
             xmlns:trt="http://www.onvif.org/ver10/media/wsdl"
             xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap12/"
             targetNamespace="http://www.onvif.org/ver10/media/wsdl">
    <service name="MediaService">
        <port name="MediaPort" binding="trt:MediaBinding">
            <soap:address location="http://{local_ip}:{self.camera.onvif_port}/onvif/media_service"/>
        </port>
    </service>
</definitions>"""
        return Response(wsdl, mimetype='text/xml')

    def _handle_get_video_sources(self):
        """Handle GetVideoSources request"""
        soap_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope"
                   xmlns:trt="http://www.onvif.org/ver10/media/wsdl"
                   xmlns:tt="http://www.onvif.org/ver10/schema">
    <SOAP-ENV:Body>
        <trt:GetVideoSourcesResponse>
            <trt:VideoSources token="VideoSourceMain">
                <tt:Framerate>{self.camera.main_framerate}</tt:Framerate>
                <tt:Resolution>
                    <tt:Width>{self.camera.main_width}</tt:Width>
                    <tt:Height>{self.camera.main_height}</tt:Height>
                </tt:Resolution>
            </trt:VideoSources>
            <trt:VideoSources token="VideoSourceSub">
                <tt:Framerate>{self.camera.sub_framerate}</tt:Framerate>
                <tt:Resolution>
                    <tt:Width>{self.camera.sub_width}</tt:Width>
                    <tt:Height>{self.camera.sub_height}</tt:Height>
                </tt:Resolution>
            </trt:VideoSources>
        </trt:GetVideoSourcesResponse>
    </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""
        
        return Response(soap_response, mimetype='application/soap+xml')
