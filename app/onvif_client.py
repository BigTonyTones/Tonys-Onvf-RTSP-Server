import sys
import os
import logging
from urllib.parse import urlparse

# Suppress zeep logging
logging.getLogger('zeep').setLevel(logging.ERROR)

class ONVIFProber:
    def __init__(self):
        self.wsdl_dir = None
        # Try to locate WSDL files if needed, but onvif-zeep usually finds them
        
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
            # Determine WSDL directory
            wsdl_dir = os.path.join(os.path.dirname(onvif.__file__), 'wsdl')
            if not os.path.exists(os.path.join(wsdl_dir, 'devicemgmt.wsdl')):
                # Search for WSDLs in common separated locations
                possible_paths = [
                    r"C:\Users\Tony\AppData\Roaming\Python\Lib\site-packages\wsdl",
                    os.path.join(os.path.dirname(os.path.dirname(onvif.__file__)), 'wsdl'),
                    # Try three levels up + Lib/site-packages/wsdl (common in some user installs)
                    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(onvif.__file__))), 'Lib', 'site-packages', 'wsdl'),
                ]
                for p in possible_paths:
                    if os.path.exists(os.path.join(p, 'devicemgmt.wsdl')):
                        wsdl_dir = p
                        print(f"Found WSDLs at: {wsdl_dir}")
                        break
            
            # Connect to Camera with explicit wsdl_dir
            mycam = ONVIFCamera(host, port, username, password, wsdl_dir=wsdl_dir)
            
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

    def reboot_camera(self, host, port, username, password):
        """
        Send a SystemReboot command to an ONVIF camera.
        """
        try:
            from onvif import ONVIFCamera
            import onvif
        except ImportError:
            return {
                'success': False, 
                'error': 'onvif-zeep library not installed.'
            }

        try:
            # Determine WSDL directory (same logic as probe)
            wsdl_dir = os.path.join(os.path.dirname(onvif.__file__), 'wsdl')
            if not os.path.exists(os.path.join(wsdl_dir, 'devicemgmt.wsdl')):
                possible_paths = [
                    r"C:\Users\Tony\AppData\Roaming\Python\Lib\site-packages\wsdl",
                    os.path.join(os.path.dirname(os.path.dirname(onvif.__file__)), 'wsdl'),
                    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(onvif.__file__))), 'Lib', 'site-packages', 'wsdl'),
                ]
                for p in possible_paths:
                    if os.path.exists(os.path.join(p, 'devicemgmt.wsdl')):
                        wsdl_dir = p
                        break
            
            # Connect to Camera
            mycam = ONVIFCamera(host, port, username, password, wsdl_dir=wsdl_dir)
            
            # Create device management service
            devicemgmt = mycam.create_devicemgmt_service()
            
            # Send Reboot command
            # SystemReboot returns a message (often "Rebooting")
            response = devicemgmt.SystemReboot()
            
            return {
                'success': True,
                'message': str(response)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
