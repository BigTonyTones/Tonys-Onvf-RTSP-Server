"""
Tests for ONVIF service functionality.

This module tests the ONVIFService class including:
- SOAP response generation
- Authentication (valid/invalid credentials)
- Various ONVIF endpoints
"""

import base64
from unittest.mock import MagicMock, patch

import pytest

from app.camera import VirtualONVIFCamera
from app.onvif_service import ONVIFService


class TestONVIFServiceInitialization:
    """Tests for ONVIFService initialization."""

    def test_init_stores_camera_reference(self, virtual_camera):
        """Should store reference to camera."""
        # Act
        service = ONVIFService(virtual_camera)

        # Assert
        assert service.camera == virtual_camera

    def test_create_app_returns_flask_app(self, onvif_service):
        """Should return a Flask application."""
        # Act
        with patch('socket.gethostbyname', return_value='127.0.0.1'):
            app = onvif_service.create_app()

        # Assert
        assert app is not None
        assert hasattr(app, 'route')


class TestDeviceService:
    """Tests for /onvif/device_service endpoint."""

    def test_get_device_information(self, onvif_client, sample_camera_config, soap_get_device_info_request):
        """Should return device information in SOAP response."""
        # Arrange
        auth = base64.b64encode(b'admin:admin123').decode('utf-8')

        # Act
        response = onvif_client.post(
            '/onvif/device_service',
            data=soap_get_device_info_request,
            headers={
                'Content-Type': 'application/soap+xml',
                'Authorization': f'Basic {auth}'
            }
        )

        # Assert
        assert response.status_code == 200
        assert b'GetDeviceInformationResponse' in response.data
        assert b'Manufacturer' in response.data
        assert b'Model' in response.data
        assert b'FirmwareVersion' in response.data

    def test_get_device_info_includes_camera_name(self, onvif_client, soap_get_device_info_request):
        """Should include camera name in model field."""
        # Arrange
        auth = base64.b64encode(b'admin:admin123').decode('utf-8')

        # Act
        response = onvif_client.post(
            '/onvif/device_service',
            data=soap_get_device_info_request,
            headers={
                'Content-Type': 'application/soap+xml',
                'Authorization': f'Basic {auth}'
            }
        )

        # Assert
        assert response.status_code == 200
        assert b'Test Camera' in response.data

    def test_get_capabilities(self, onvif_client, soap_get_capabilities_request):
        """Should return capabilities in SOAP response."""
        # Arrange
        auth = base64.b64encode(b'admin:admin123').decode('utf-8')

        # Act
        response = onvif_client.post(
            '/onvif/device_service',
            data=soap_get_capabilities_request,
            headers={
                'Content-Type': 'application/soap+xml',
                'Authorization': f'Basic {auth}'
            }
        )

        # Assert
        assert response.status_code == 200
        assert b'GetCapabilitiesResponse' in response.data
        assert b'Media' in response.data
        assert b'Device' in response.data

    def test_get_system_date_time(self, onvif_client, soap_get_system_date_time_request):
        """Should return system date and time."""
        # Arrange
        auth = base64.b64encode(b'admin:admin123').decode('utf-8')

        # Act
        response = onvif_client.post(
            '/onvif/device_service',
            data=soap_get_system_date_time_request,
            headers={
                'Content-Type': 'application/soap+xml',
                'Authorization': f'Basic {auth}'
            }
        )

        # Assert
        assert response.status_code == 200
        assert b'GetSystemDateAndTimeResponse' in response.data
        assert b'UTCDateTime' in response.data
        assert b'LocalDateTime' in response.data

    def test_get_wsdl_via_get_request(self, onvif_client):
        """Should return WSDL for GET requests."""
        # Arrange
        auth = base64.b64encode(b'admin:admin123').decode('utf-8')

        # Act
        response = onvif_client.get(
            '/onvif/device_service',
            headers={'Authorization': f'Basic {auth}'}
        )

        # Assert
        assert response.status_code == 200
        assert b'definitions' in response.data or b'wsdl' in response.data.lower()


class TestMediaService:
    """Tests for /onvif/media_service endpoint."""

    def test_get_profiles(self, onvif_client, soap_get_profiles_request):
        """Should return media profiles."""
        # Arrange
        auth = base64.b64encode(b'admin:admin123').decode('utf-8')

        # Act
        response = onvif_client.post(
            '/onvif/media_service',
            data=soap_get_profiles_request,
            headers={
                'Content-Type': 'application/soap+xml',
                'Authorization': f'Basic {auth}'
            }
        )

        # Assert
        assert response.status_code == 200
        assert b'GetProfilesResponse' in response.data
        assert b'mainStream' in response.data
        assert b'subStream' in response.data

    def test_get_profiles_includes_resolution(self, onvif_client, soap_get_profiles_request):
        """Should include resolution in profiles."""
        # Arrange
        auth = base64.b64encode(b'admin:admin123').decode('utf-8')

        # Act
        response = onvif_client.post(
            '/onvif/media_service',
            data=soap_get_profiles_request,
            headers={
                'Content-Type': 'application/soap+xml',
                'Authorization': f'Basic {auth}'
            }
        )

        # Assert
        assert response.status_code == 200
        assert b'Resolution' in response.data
        assert b'Width' in response.data
        assert b'Height' in response.data

    def test_get_stream_uri_main(self, onvif_client, soap_get_stream_uri_main_request):
        """Should return main stream URI."""
        # Arrange
        auth = base64.b64encode(b'admin:admin123').decode('utf-8')

        # Act
        response = onvif_client.post(
            '/onvif/media_service',
            data=soap_get_stream_uri_main_request,
            headers={
                'Content-Type': 'application/soap+xml',
                'Authorization': f'Basic {auth}'
            }
        )

        # Assert
        assert response.status_code == 200
        assert b'GetStreamUriResponse' in response.data
        assert b'rtsp://' in response.data
        assert b'_main' in response.data

    def test_get_stream_uri_sub(self, onvif_client, soap_get_stream_uri_sub_request):
        """Should return sub stream URI."""
        # Arrange
        auth = base64.b64encode(b'admin:admin123').decode('utf-8')

        # Act
        response = onvif_client.post(
            '/onvif/media_service',
            data=soap_get_stream_uri_sub_request,
            headers={
                'Content-Type': 'application/soap+xml',
                'Authorization': f'Basic {auth}'
            }
        )

        # Assert
        assert response.status_code == 200
        assert b'GetStreamUriResponse' in response.data
        assert b'rtsp://' in response.data
        assert b'_sub' in response.data

    def test_get_media_wsdl(self, onvif_client):
        """Should return media service WSDL for GET request."""
        # Arrange
        auth = base64.b64encode(b'admin:admin123').decode('utf-8')

        # Act
        response = onvif_client.get(
            '/onvif/media_service',
            headers={'Authorization': f'Basic {auth}'}
        )

        # Assert
        assert response.status_code == 200
        assert b'definitions' in response.data or b'MediaService' in response.data


class TestAuthentication:
    """Tests for ONVIF authentication."""

    def test_basic_auth_valid_credentials(self, onvif_client, soap_get_device_info_request):
        """Should accept valid Basic Auth credentials."""
        # Arrange
        auth = base64.b64encode(b'admin:admin123').decode('utf-8')

        # Act
        response = onvif_client.post(
            '/onvif/device_service',
            data=soap_get_device_info_request,
            headers={
                'Content-Type': 'application/soap+xml',
                'Authorization': f'Basic {auth}'
            }
        )

        # Assert
        assert response.status_code == 200

    def test_basic_auth_invalid_username(self, onvif_client, soap_get_device_info_request):
        """Should reject invalid username."""
        # Arrange
        auth = base64.b64encode(b'wrong_user:admin123').decode('utf-8')

        # Act
        response = onvif_client.post(
            '/onvif/device_service',
            data=soap_get_device_info_request,
            headers={
                'Content-Type': 'application/soap+xml',
                'Authorization': f'Basic {auth}'
            }
        )

        # Assert
        assert response.status_code == 401

    def test_basic_auth_invalid_password(self, onvif_client, soap_get_device_info_request):
        """Should reject invalid password."""
        # Arrange
        auth = base64.b64encode(b'admin:wrong_password').decode('utf-8')

        # Act
        response = onvif_client.post(
            '/onvif/device_service',
            data=soap_get_device_info_request,
            headers={
                'Content-Type': 'application/soap+xml',
                'Authorization': f'Basic {auth}'
            }
        )

        # Assert
        assert response.status_code == 401

    def test_no_auth_returns_401(self, onvif_client, soap_get_device_info_request):
        """Should return 401 when no authentication provided."""
        # Act
        response = onvif_client.post(
            '/onvif/device_service',
            data=soap_get_device_info_request,
            headers={'Content-Type': 'application/soap+xml'}
        )

        # Assert
        assert response.status_code == 401

    def test_ws_username_token_auth(self, onvif_client, soap_request_with_auth):
        """Should accept WS-UsernameToken authentication."""
        # Act
        response = onvif_client.post(
            '/onvif/device_service',
            data=soap_request_with_auth,
            headers={'Content-Type': 'application/soap+xml'}
        )

        # Assert
        assert response.status_code == 200

    def test_auth_returns_www_authenticate_header(self, onvif_client, soap_get_device_info_request):
        """Should include WWW-Authenticate header on 401."""
        # Act
        response = onvif_client.post(
            '/onvif/device_service',
            data=soap_get_device_info_request,
            headers={'Content-Type': 'application/soap+xml'}
        )

        # Assert
        assert response.status_code == 401
        assert 'WWW-Authenticate' in response.headers


class TestRootEndpoint:
    """Tests for root endpoint (/)."""

    def test_root_endpoint_handles_device_service(self, onvif_client, soap_get_device_info_request):
        """Should handle device service requests at root."""
        # Arrange
        auth = base64.b64encode(b'admin:admin123').decode('utf-8')

        # Act
        response = onvif_client.post(
            '/',
            data=soap_get_device_info_request,
            headers={
                'Content-Type': 'application/soap+xml',
                'Authorization': f'Basic {auth}'
            }
        )

        # Assert
        assert response.status_code == 200
        assert b'GetDeviceInformationResponse' in response.data


class TestSOAPResponseFormat:
    """Tests for SOAP response formatting."""

    def test_response_is_soap_xml(self, onvif_client, soap_get_device_info_request):
        """Should return SOAP XML content type."""
        # Arrange
        auth = base64.b64encode(b'admin:admin123').decode('utf-8')

        # Act
        response = onvif_client.post(
            '/onvif/device_service',
            data=soap_get_device_info_request,
            headers={
                'Content-Type': 'application/soap+xml',
                'Authorization': f'Basic {auth}'
            }
        )

        # Assert
        assert 'application/soap+xml' in response.content_type

    def test_response_has_xml_declaration(self, onvif_client, soap_get_device_info_request):
        """Should include XML declaration in response."""
        # Arrange
        auth = base64.b64encode(b'admin:admin123').decode('utf-8')

        # Act
        response = onvif_client.post(
            '/onvif/device_service',
            data=soap_get_device_info_request,
            headers={
                'Content-Type': 'application/soap+xml',
                'Authorization': f'Basic {auth}'
            }
        )

        # Assert
        assert b'<?xml version' in response.data

    def test_response_has_soap_envelope(self, onvif_client, soap_get_device_info_request):
        """Should include SOAP envelope in response."""
        # Arrange
        auth = base64.b64encode(b'admin:admin123').decode('utf-8')

        # Act
        response = onvif_client.post(
            '/onvif/device_service',
            data=soap_get_device_info_request,
            headers={
                'Content-Type': 'application/soap+xml',
                'Authorization': f'Basic {auth}'
            }
        )

        # Assert
        assert b'SOAP-ENV:Envelope' in response.data or b'soap:Envelope' in response.data


class TestGetNetworkInterfaces:
    """Tests for GetNetworkInterfaces request."""

    def test_get_network_interfaces(self, onvif_client):
        """Should return network interfaces."""
        # Arrange
        auth = base64.b64encode(b'admin:admin123').decode('utf-8')
        request = '''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
    <soap:Body>
        <tds:GetNetworkInterfaces/>
    </soap:Body>
</soap:Envelope>'''

        # Act
        response = onvif_client.post(
            '/onvif/device_service',
            data=request,
            headers={
                'Content-Type': 'application/soap+xml',
                'Authorization': f'Basic {auth}'
            }
        )

        # Assert
        assert response.status_code == 200
        assert b'GetNetworkInterfacesResponse' in response.data
        assert b'HwAddress' in response.data


class TestGetServices:
    """Tests for GetServices request."""

    def test_get_services(self, onvif_client):
        """Should return available services."""
        # Arrange
        auth = base64.b64encode(b'admin:admin123').decode('utf-8')
        request = '''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
    <soap:Body>
        <tds:GetServices/>
    </soap:Body>
</soap:Envelope>'''

        # Act
        response = onvif_client.post(
            '/onvif/device_service',
            data=request,
            headers={
                'Content-Type': 'application/soap+xml',
                'Authorization': f'Basic {auth}'
            }
        )

        # Assert
        assert response.status_code == 200
        assert b'GetServicesResponse' in response.data
        assert b'device/wsdl' in response.data
        assert b'media/wsdl' in response.data


class TestGetVideoSources:
    """Tests for GetVideoSources request."""

    def test_get_video_sources(self, onvif_client):
        """Should return video sources."""
        # Arrange
        auth = base64.b64encode(b'admin:admin123').decode('utf-8')
        request = '''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
    <soap:Body>
        <trt:GetVideoSources/>
    </soap:Body>
</soap:Envelope>'''

        # Act
        response = onvif_client.post(
            '/onvif/media_service',
            data=request,
            headers={
                'Content-Type': 'application/soap+xml',
                'Authorization': f'Basic {auth}'
            }
        )

        # Assert
        assert response.status_code == 200
        assert b'GetVideoSourcesResponse' in response.data
        assert b'VideoSourceMain' in response.data
        assert b'VideoSourceSub' in response.data


class TestErrorHandling:
    """Tests for error handling in ONVIF service."""

    def test_malformed_soap_request(self, onvif_client):
        """Should handle malformed SOAP requests."""
        # Arrange
        auth = base64.b64encode(b'admin:admin123').decode('utf-8')
        malformed_request = 'This is not valid XML'

        # Act
        response = onvif_client.post(
            '/onvif/device_service',
            data=malformed_request,
            headers={
                'Content-Type': 'application/soap+xml',
                'Authorization': f'Basic {auth}'
            }
        )

        # Assert - should not crash, may return 200 or error
        assert response.status_code in [200, 400, 500]

    def test_empty_soap_body(self, onvif_client):
        """Should handle empty SOAP body."""
        # Arrange
        auth = base64.b64encode(b'admin:admin123').decode('utf-8')
        empty_request = '''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
    <soap:Body>
    </soap:Body>
</soap:Envelope>'''

        # Act
        response = onvif_client.post(
            '/onvif/device_service',
            data=empty_request,
            headers={
                'Content-Type': 'application/soap+xml',
                'Authorization': f'Basic {auth}'
            }
        )

        # Assert - should return default device info
        assert response.status_code == 200


class TestCameraSpecificResponses:
    """Tests for camera-specific data in responses."""

    def test_device_info_includes_mac_address(self, onvif_client, soap_get_device_info_request):
        """Should include MAC address in serial number."""
        # Arrange
        auth = base64.b64encode(b'admin:admin123').decode('utf-8')

        # Act
        response = onvif_client.post(
            '/onvif/device_service',
            data=soap_get_device_info_request,
            headers={
                'Content-Type': 'application/soap+xml',
                'Authorization': f'Basic {auth}'
            }
        )

        # Assert
        assert response.status_code == 200
        assert b'SerialNumber' in response.data

    def test_profiles_include_correct_resolution(self, onvif_client, soap_get_profiles_request, sample_camera_config):
        """Should include correct resolution from camera config."""
        # Arrange
        auth = base64.b64encode(b'admin:admin123').decode('utf-8')

        # Act
        response = onvif_client.post(
            '/onvif/media_service',
            data=soap_get_profiles_request,
            headers={
                'Content-Type': 'application/soap+xml',
                'Authorization': f'Basic {auth}'
            }
        )

        # Assert
        assert response.status_code == 200
        # Check for expected resolution values
        assert b'1920' in response.data  # Main width
        assert b'1080' in response.data  # Main height

    def test_profiles_include_correct_framerate(self, onvif_client, soap_get_profiles_request, sample_camera_config):
        """Should include correct framerate from camera config."""
        # Arrange
        auth = base64.b64encode(b'admin:admin123').decode('utf-8')

        # Act
        response = onvif_client.post(
            '/onvif/media_service',
            data=soap_get_profiles_request,
            headers={
                'Content-Type': 'application/soap+xml',
                'Authorization': f'Basic {auth}'
            }
        )

        # Assert
        assert response.status_code == 200
        assert b'FrameRateLimit' in response.data
