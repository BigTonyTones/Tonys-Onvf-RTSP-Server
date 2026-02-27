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
