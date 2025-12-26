"""
Pytest configuration and fixtures for ONVIF-RTSP Server tests.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add the app directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.camera import VirtualONVIFCamera
from app.manager import CameraManager
from app.onvif_service import ONVIFService
from app.web import create_web_app


# =============================================================================
# Sample Camera Configuration Fixtures
# =============================================================================

@pytest.fixture
def sample_camera_config():
    """Provide a sample camera configuration dictionary."""
    return {
        'id': 1,
        'name': 'Test Camera',
        'mainStreamUrl': 'rtsp://admin:password@192.168.1.100:554/stream1',
        'subStreamUrl': 'rtsp://admin:password@192.168.1.100:554/stream2',
        'rtspPort': 8554,
        'onvifPort': 8001,
        'pathName': 'test_camera',
        'username': 'admin',
        'password': 'password',
        'autoStart': False,
        'mainWidth': 1920,
        'mainHeight': 1080,
        'subWidth': 640,
        'subHeight': 480,
        'mainFramerate': 30,
        'subFramerate': 15,
        'onvifUsername': 'admin',
        'onvifPassword': 'admin123',
        'transcodeSub': False,
        'transcodeMain': False,
        'useVirtualNic': False,
        'parentInterface': '',
        'nicMac': '',
        'ipMode': 'dhcp',
        'staticIp': '',
        'netmask': '24',
        'gateway': ''
    }


@pytest.fixture
def sample_camera_config_minimal():
    """Provide a minimal camera configuration dictionary."""
    return {
        'id': 2,
        'name': 'Minimal Camera',
        'mainStreamUrl': 'rtsp://192.168.1.101:554/main',
        'subStreamUrl': 'rtsp://192.168.1.101:554/sub'
    }


@pytest.fixture
def sample_camera_config_with_virtual_nic():
    """Provide a camera configuration with virtual NIC enabled."""
    return {
        'id': 3,
        'name': 'Virtual NIC Camera',
        'mainStreamUrl': 'rtsp://admin:pass@192.168.1.102:554/stream1',
        'subStreamUrl': 'rtsp://admin:pass@192.168.1.102:554/stream2',
        'rtspPort': 8554,
        'onvifPort': 8003,
        'pathName': 'vnic_camera',
        'username': 'admin',
        'password': 'pass',
        'autoStart': True,
        'mainWidth': 2560,
        'mainHeight': 1440,
        'subWidth': 854,
        'subHeight': 480,
        'mainFramerate': 25,
        'subFramerate': 10,
        'onvifUsername': 'onvif_user',
        'onvifPassword': 'onvif_pass',
        'transcodeSub': True,
        'transcodeMain': False,
        'useVirtualNic': True,
        'parentInterface': 'eth0',
        'nicMac': '02:00:00:00:00:03',
        'ipMode': 'static',
        'staticIp': '192.168.1.200',
        'netmask': '24',
        'gateway': '192.168.1.1'
    }


@pytest.fixture
def multiple_camera_configs(sample_camera_config):
    """Provide multiple camera configurations for testing."""
    configs = [sample_camera_config.copy()]

    # Add second camera
    config2 = sample_camera_config.copy()
    config2.update({
        'id': 2,
        'name': 'Camera 2',
        'mainStreamUrl': 'rtsp://192.168.1.102:554/stream1',
        'subStreamUrl': 'rtsp://192.168.1.102:554/stream2',
        'onvifPort': 8002,
        'pathName': 'camera_2'
    })
    configs.append(config2)

    # Add third camera
    config3 = sample_camera_config.copy()
    config3.update({
        'id': 3,
        'name': 'Camera 3',
        'mainStreamUrl': 'rtsp://192.168.1.103:554/stream1',
        'subStreamUrl': 'rtsp://192.168.1.103:554/stream2',
        'onvifPort': 8003,
        'pathName': 'camera_3'
    })
    configs.append(config3)

    return configs


# =============================================================================
# Temporary Directory and File Fixtures
# =============================================================================

@pytest.fixture
def temp_dir():
    """Provide a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_config_file(temp_dir):
    """Provide a temporary config file path."""
    return os.path.join(temp_dir, 'test_camera_config.json')


@pytest.fixture
def temp_config_file_with_data(temp_config_file, sample_camera_config):
    """Provide a temporary config file with sample data."""
    config_data = {
        'cameras': [sample_camera_config],
        'settings': {
            'serverIp': '192.168.1.50',
            'openBrowser': True,
            'theme': 'dracula',
            'gridColumns': 3,
            'rtspPort': 8554,
            'autoBoot': False
        }
    }
    with open(temp_config_file, 'w') as f:
        json.dump(config_data, f, indent=2)
    return temp_config_file


@pytest.fixture
def temp_config_file_empty(temp_config_file):
    """Provide an empty temporary config file (doesn't exist yet)."""
    # Just return the path, don't create the file
    return temp_config_file


# =============================================================================
# VirtualONVIFCamera Fixtures
# =============================================================================

@pytest.fixture
def virtual_camera(sample_camera_config):
    """Provide a VirtualONVIFCamera instance with mocked network manager."""
    with patch('app.camera.LinuxNetworkManager') as mock_network:
        mock_network.is_linux.return_value = False
        camera = VirtualONVIFCamera(sample_camera_config)
        yield camera


@pytest.fixture
def virtual_camera_stopped(virtual_camera):
    """Provide a stopped VirtualONVIFCamera instance."""
    virtual_camera.status = 'stopped'
    return virtual_camera


@pytest.fixture
def virtual_camera_running(virtual_camera):
    """Provide a running VirtualONVIFCamera instance (mocked)."""
    virtual_camera.status = 'running'
    return virtual_camera


# =============================================================================
# CameraManager Fixtures
# =============================================================================

@pytest.fixture
def mock_mediamtx():
    """Provide a mocked MediaMTX manager."""
    mock = MagicMock()
    mock.start.return_value = True
    mock.stop.return_value = True
    mock.restart.return_value = True
    return mock


@pytest.fixture
def mock_service_mgr():
    """Provide a mocked Linux service manager."""
    mock = MagicMock()
    mock.is_linux.return_value = False
    mock.install_service.return_value = (True, 'Service installed')
    mock.uninstall_service.return_value = (True, 'Service uninstalled')
    return mock


@pytest.fixture
def camera_manager(temp_config_file_empty, mock_mediamtx, mock_service_mgr):
    """Provide a CameraManager instance with mocked dependencies."""
    with patch('app.manager.MediaMTXManager', return_value=mock_mediamtx), \
         patch('app.manager.LinuxServiceManager', return_value=mock_service_mgr):
        manager = CameraManager(config_file=temp_config_file_empty)
        yield manager


@pytest.fixture
def camera_manager_with_cameras(temp_config_file_with_data, mock_mediamtx, mock_service_mgr):
    """Provide a CameraManager with pre-loaded cameras."""
    with patch('app.manager.MediaMTXManager', return_value=mock_mediamtx), \
         patch('app.manager.LinuxServiceManager', return_value=mock_service_mgr), \
         patch('app.camera.LinuxNetworkManager') as mock_network:
        mock_network.is_linux.return_value = False
        manager = CameraManager(config_file=temp_config_file_with_data)
        yield manager


# =============================================================================
# Flask Test Client Fixtures
# =============================================================================

@pytest.fixture
def mock_camera_manager(mock_mediamtx, mock_service_mgr):
    """Provide a mocked CameraManager for Flask app testing."""
    manager = MagicMock(spec=CameraManager)
    manager.cameras = []
    manager.mediamtx = mock_mediamtx
    manager.service_mgr = mock_service_mgr
    manager.server_ip = 'localhost'
    manager.open_browser = True
    manager.theme = 'dracula'
    manager.grid_columns = 3
    manager.rtsp_port = 8554
    manager.auto_boot = False

    # Mock load_settings to return proper settings
    manager.load_settings.return_value = {
        'serverIp': 'localhost',
        'openBrowser': True,
        'theme': 'dracula',
        'gridColumns': 3,
        'rtspPort': 8554,
        'autoBoot': False
    }

    return manager


@pytest.fixture
def app(mock_camera_manager):
    """Provide a Flask application instance for testing."""
    flask_app = create_web_app(mock_camera_manager)
    flask_app.config['TESTING'] = True
    flask_app.config['DEBUG'] = False
    return flask_app


@pytest.fixture
def client(app):
    """Provide a Flask test client."""
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture
def app_with_cameras(camera_manager_with_cameras):
    """Provide a Flask application with pre-loaded cameras."""
    flask_app = create_web_app(camera_manager_with_cameras)
    flask_app.config['TESTING'] = True
    flask_app.config['DEBUG'] = False
    return flask_app


@pytest.fixture
def client_with_cameras(app_with_cameras):
    """Provide a Flask test client with pre-loaded cameras."""
    with app_with_cameras.test_client() as test_client:
        yield test_client


# =============================================================================
# ONVIF Service Fixtures
# =============================================================================

@pytest.fixture
def onvif_service(virtual_camera):
    """Provide an ONVIFService instance."""
    return ONVIFService(virtual_camera)


@pytest.fixture
def onvif_app(onvif_service):
    """Provide an ONVIF Flask application for testing."""
    with patch('socket.gethostbyname', return_value='127.0.0.1'):
        flask_app = onvif_service.create_app()
        flask_app.config['TESTING'] = True
        flask_app.config['DEBUG'] = False
        return flask_app


@pytest.fixture
def onvif_client(onvif_app):
    """Provide an ONVIF Flask test client."""
    with onvif_app.test_client() as test_client:
        yield test_client


# =============================================================================
# API Request Data Fixtures
# =============================================================================

@pytest.fixture
def new_camera_request_data():
    """Provide sample data for creating a new camera via API."""
    return {
        'name': 'New Test Camera',
        'host': '192.168.1.200',
        'rtspPort': 554,
        'username': 'admin',
        'password': 'secret123',
        'mainPath': '/stream/main',
        'subPath': '/stream/sub',
        'autoStart': False,
        'mainWidth': 1920,
        'mainHeight': 1080,
        'subWidth': 640,
        'subHeight': 480,
        'mainFramerate': 30,
        'subFramerate': 15,
        'onvifPort': 8010,
        'onvifUsername': 'admin',
        'onvifPassword': 'admin',
        'transcodeSub': False,
        'transcodeMain': False,
        'useVirtualNic': False
    }


@pytest.fixture
def update_camera_request_data():
    """Provide sample data for updating a camera via API."""
    return {
        'name': 'Updated Camera Name',
        'host': '192.168.1.201',
        'rtspPort': 554,
        'username': 'new_admin',
        'password': 'new_secret',
        'mainPath': '/stream/main/updated',
        'subPath': '/stream/sub/updated',
        'autoStart': True,
        'mainWidth': 2560,
        'mainHeight': 1440,
        'subWidth': 854,
        'subHeight': 480,
        'mainFramerate': 25,
        'subFramerate': 10,
        'onvifPort': 8020,
        'onvifUsername': 'new_onvif',
        'onvifPassword': 'new_pass'
    }


@pytest.fixture
def settings_request_data():
    """Provide sample settings data for API testing."""
    return {
        'serverIp': '192.168.1.100',
        'openBrowser': False,
        'theme': 'light',
        'gridColumns': 4,
        'rtspPort': 8555,
        'autoBoot': False
    }


# =============================================================================
# SOAP Request Fixtures
# =============================================================================

@pytest.fixture
def soap_get_device_info_request():
    """Provide a SOAP GetDeviceInformation request."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
    <soap:Body>
        <tds:GetDeviceInformation/>
    </soap:Body>
</soap:Envelope>'''


@pytest.fixture
def soap_get_capabilities_request():
    """Provide a SOAP GetCapabilities request."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
    <soap:Body>
        <tds:GetCapabilities>
            <tds:Category>All</tds:Category>
        </tds:GetCapabilities>
    </soap:Body>
</soap:Envelope>'''


@pytest.fixture
def soap_get_profiles_request():
    """Provide a SOAP GetProfiles request."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
    <soap:Body>
        <trt:GetProfiles/>
    </soap:Body>
</soap:Envelope>'''


@pytest.fixture
def soap_get_stream_uri_main_request():
    """Provide a SOAP GetStreamUri request for main stream."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
    <soap:Body>
        <trt:GetStreamUri>
            <trt:StreamSetup>
                <tt:Stream xmlns:tt="http://www.onvif.org/ver10/schema">RTP-Unicast</tt:Stream>
                <tt:Transport xmlns:tt="http://www.onvif.org/ver10/schema">
                    <tt:Protocol>RTSP</tt:Protocol>
                </tt:Transport>
            </trt:StreamSetup>
            <trt:ProfileToken>mainStream</trt:ProfileToken>
        </trt:GetStreamUri>
    </soap:Body>
</soap:Envelope>'''


@pytest.fixture
def soap_get_stream_uri_sub_request():
    """Provide a SOAP GetStreamUri request for sub stream."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
    <soap:Body>
        <trt:GetStreamUri>
            <trt:StreamSetup>
                <tt:Stream xmlns:tt="http://www.onvif.org/ver10/schema">RTP-Unicast</tt:Stream>
                <tt:Transport xmlns:tt="http://www.onvif.org/ver10/schema">
                    <tt:Protocol>RTSP</tt:Protocol>
                </tt:Transport>
            </trt:StreamSetup>
            <trt:ProfileToken>subStream</trt:ProfileToken>
        </trt:GetStreamUri>
    </soap:Body>
</soap:Envelope>'''


@pytest.fixture
def soap_get_system_date_time_request():
    """Provide a SOAP GetSystemDateAndTime request."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
    <soap:Body>
        <tds:GetSystemDateAndTime/>
    </soap:Body>
</soap:Envelope>'''


@pytest.fixture
def soap_request_with_auth():
    """Provide a SOAP request with WS-UsernameToken authentication."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
               xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
    <soap:Header>
        <wsse:Security>
            <wsse:UsernameToken>
                <wsse:Username>admin</wsse:Username>
                <wsse:Password>admin123</wsse:Password>
            </wsse:UsernameToken>
        </wsse:Security>
    </soap:Header>
    <soap:Body>
        <tds:GetDeviceInformation/>
    </soap:Body>
</soap:Envelope>'''


# =============================================================================
# Utility Fixtures
# =============================================================================

@pytest.fixture
def mock_socket():
    """Provide a mocked socket for network tests."""
    with patch('socket.gethostbyname', return_value='127.0.0.1'):
        yield


@pytest.fixture
def mock_psutil():
    """Provide mocked psutil for stats tests."""
    with patch('psutil.Process') as mock_process:
        mock_process.return_value.memory_info.return_value.rss = 100 * 1024 * 1024  # 100 MB
        mock_process.return_value.cpu_times.return_value.user = 1.0
        mock_process.return_value.cpu_times.return_value.system = 0.5
        mock_process.return_value.children.return_value = []
        yield mock_process


# =============================================================================
# Validation Test Data Fixtures
# =============================================================================

@pytest.fixture
def valid_mac_addresses():
    """Provide a list of valid MAC addresses."""
    return [
        '00:11:22:33:44:55',
        'AA:BB:CC:DD:EE:FF',
        'aa:bb:cc:dd:ee:ff',
        '01:23:45:67:89:ab',
        '02:00:00:00:00:01',
    ]


@pytest.fixture
def invalid_mac_addresses():
    """Provide a list of invalid MAC addresses."""
    return [
        '',
        '00:11:22:33:44',  # Too short
        '00:11:22:33:44:55:66',  # Too long
        '00-11-22-33-44-55',  # Wrong separator
        'GG:HH:II:JJ:KK:LL',  # Invalid hex
        '001122334455',  # No separators
        '00:11:22:33:44:5G',  # Invalid character
    ]


@pytest.fixture
def valid_ip_addresses():
    """Provide a list of valid IP addresses."""
    return [
        '192.168.1.1',
        '10.0.0.1',
        '172.16.0.1',
        '255.255.255.255',
        '0.0.0.0',
        '127.0.0.1',
    ]


@pytest.fixture
def invalid_ip_addresses():
    """Provide a list of invalid IP addresses."""
    return [
        '',
        '256.1.1.1',  # Out of range
        '192.168.1',  # Incomplete
        '192.168.1.1.1',  # Too many octets
        'not.an.ip.address',
        '192.168.1.1/24',  # CIDR notation
        '192.168.1.-1',  # Negative
    ]


@pytest.fixture
def valid_interface_names():
    """Provide a list of valid network interface names."""
    return [
        'eth0',
        'eth1',
        'enp0s3',
        'wlan0',
        'br0',
        'docker0',
        'lo',
    ]


@pytest.fixture
def invalid_interface_names():
    """Provide a list of invalid network interface names."""
    return [
        '',
        'eth0; rm -rf /',  # Command injection attempt
        '../etc/passwd',  # Path traversal
        'interface with spaces',
        'a' * 256,  # Too long
    ]


# =============================================================================
# Malicious Input Fixtures (for security testing)
# =============================================================================

@pytest.fixture
def malicious_inputs():
    """Provide a list of potentially malicious inputs for security testing."""
    return [
        # SQL injection attempts
        "'; DROP TABLE cameras; --",
        "1' OR '1'='1",
        "admin'--",

        # XSS attempts
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
        "javascript:alert('xss')",

        # Command injection attempts
        "; rm -rf /",
        "| cat /etc/passwd",
        "`id`",
        "$(whoami)",

        # Path traversal attempts
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "/etc/passwd%00.jpg",

        # LDAP injection
        ")(cn=*)",
        "*)(uid=*))(|(uid=*",

        # XML/XXE injection
        "<!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]>",
        "&xxe;",

        # Unicode shenanigans
        "\u0000",  # Null byte
        "\u202E",  # Right-to-left override

        # Very long strings
        "A" * 10000,

        # Format string attacks
        "%s%s%s%s%s",
        "%x%x%x%x",
    ]
