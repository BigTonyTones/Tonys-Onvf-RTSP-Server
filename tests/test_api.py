"""
Tests for REST API endpoints.

This module tests all the Flask API endpoints for camera management,
settings, and server control.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.camera import VirtualONVIFCamera


class TestGetCameras:
    """Tests for GET /api/cameras endpoint."""

    def test_get_cameras_returns_empty_list_when_no_cameras(self, client, mock_camera_manager):
        """Should return empty list when no cameras are configured."""
        # Arrange
        mock_camera_manager.cameras = []

        # Act
        response = client.get('/api/cameras')

        # Assert
        assert response.status_code == 200
        assert response.json == []

    def test_get_cameras_returns_camera_list(self, client, mock_camera_manager, sample_camera_config):
        """Should return list of cameras when cameras exist."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(sample_camera_config)
            mock_camera_manager.cameras = [camera]

            # Act
            response = client.get('/api/cameras')

            # Assert
            assert response.status_code == 200
            assert len(response.json) == 1
            assert response.json[0]['name'] == 'Test Camera'
            assert response.json[0]['id'] == 1

    def test_get_cameras_returns_all_camera_fields(self, client, mock_camera_manager, sample_camera_config):
        """Should return all expected fields for each camera."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(sample_camera_config)
            mock_camera_manager.cameras = [camera]

            # Act
            response = client.get('/api/cameras')

            # Assert
            assert response.status_code == 200
            camera_data = response.json[0]
            expected_fields = [
                'id', 'name', 'mainStreamUrl', 'subStreamUrl', 'rtspPort',
                'onvifPort', 'pathName', 'username', 'password', 'autoStart',
                'status', 'mainWidth', 'mainHeight', 'subWidth', 'subHeight',
                'mainFramerate', 'subFramerate', 'onvifUsername', 'onvifPassword',
                'transcodeSub', 'transcodeMain', 'useVirtualNic', 'macAddress'
            ]
            for field in expected_fields:
                assert field in camera_data, f"Missing field: {field}"


class TestAddCamera:
    """Tests for POST /api/cameras endpoint."""

    def test_add_camera_success(self, client, mock_camera_manager, new_camera_request_data, sample_camera_config):
        """Should successfully add a new camera."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            mock_camera = VirtualONVIFCamera(sample_camera_config)
            mock_camera_manager.add_camera.return_value = mock_camera

            # Act
            response = client.post(
                '/api/cameras',
                data=json.dumps(new_camera_request_data),
                content_type='application/json'
            )

            # Assert
            assert response.status_code == 201
            mock_camera_manager.add_camera.assert_called_once()

    def test_add_camera_returns_camera_data(self, client, mock_camera_manager, new_camera_request_data, sample_camera_config):
        """Should return the created camera data."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            mock_camera = VirtualONVIFCamera(sample_camera_config)
            mock_camera_manager.add_camera.return_value = mock_camera

            # Act
            response = client.post(
                '/api/cameras',
                data=json.dumps(new_camera_request_data),
                content_type='application/json'
            )

            # Assert
            assert response.status_code == 201
            assert 'id' in response.json
            assert 'name' in response.json

    def test_add_camera_with_minimal_data(self, client, mock_camera_manager, sample_camera_config):
        """Should add camera with only required fields."""
        # Arrange
        minimal_data = {
            'name': 'Minimal Camera',
            'host': '192.168.1.100',
            'rtspPort': 554,
            'mainPath': '/stream1',
            'subPath': '/stream2'
        }
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            mock_camera = VirtualONVIFCamera(sample_camera_config)
            mock_camera_manager.add_camera.return_value = mock_camera

            # Act
            response = client.post(
                '/api/cameras',
                data=json.dumps(minimal_data),
                content_type='application/json'
            )

            # Assert
            assert response.status_code == 201

    def test_add_camera_value_error_returns_400(self, client, mock_camera_manager, new_camera_request_data):
        """Should return 400 when ValueError is raised."""
        # Arrange
        mock_camera_manager.add_camera.side_effect = ValueError("Port already in use")

        # Act
        response = client.post(
            '/api/cameras',
            data=json.dumps(new_camera_request_data),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 400
        assert 'error' in response.json
        assert 'Port already in use' in response.json['error']

    def test_add_camera_exception_returns_400(self, client, mock_camera_manager, new_camera_request_data):
        """Should return 400 when generic exception is raised."""
        # Arrange
        mock_camera_manager.add_camera.side_effect = Exception("Unexpected error")

        # Act
        response = client.post(
            '/api/cameras',
            data=json.dumps(new_camera_request_data),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 400
        assert 'error' in response.json


class TestUpdateCamera:
    """Tests for PUT /api/cameras/<camera_id> endpoint."""

    def test_update_camera_success(self, client, mock_camera_manager, update_camera_request_data, sample_camera_config):
        """Should successfully update an existing camera."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            mock_camera = VirtualONVIFCamera(sample_camera_config)
            mock_camera_manager.update_camera.return_value = mock_camera

            # Act
            response = client.put(
                '/api/cameras/1',
                data=json.dumps(update_camera_request_data),
                content_type='application/json'
            )

            # Assert
            assert response.status_code == 200
            mock_camera_manager.update_camera.assert_called_once()

    def test_update_camera_not_found_returns_404(self, client, mock_camera_manager, update_camera_request_data):
        """Should return 404 when camera is not found."""
        # Arrange
        mock_camera_manager.update_camera.return_value = None

        # Act
        response = client.put(
            '/api/cameras/999',
            data=json.dumps(update_camera_request_data),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 404
        assert 'error' in response.json
        assert 'not found' in response.json['error'].lower()

    def test_update_camera_value_error_returns_400(self, client, mock_camera_manager, update_camera_request_data):
        """Should return 400 when ValueError is raised."""
        # Arrange
        mock_camera_manager.update_camera.side_effect = ValueError("Invalid configuration")

        # Act
        response = client.put(
            '/api/cameras/1',
            data=json.dumps(update_camera_request_data),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 400
        assert 'error' in response.json


class TestDeleteCamera:
    """Tests for DELETE /api/cameras/<camera_id> endpoint."""

    def test_delete_camera_success(self, client, mock_camera_manager):
        """Should successfully delete a camera."""
        # Arrange
        mock_camera_manager.delete_camera.return_value = True

        # Act
        response = client.delete('/api/cameras/1')

        # Assert
        assert response.status_code == 204
        mock_camera_manager.delete_camera.assert_called_once_with(1)

    def test_delete_camera_not_found_returns_404(self, client, mock_camera_manager):
        """Should return 404 when camera is not found."""
        # Arrange
        mock_camera_manager.delete_camera.return_value = False

        # Act
        response = client.delete('/api/cameras/999')

        # Assert
        assert response.status_code == 404
        assert 'error' in response.json


class TestStartCamera:
    """Tests for POST /api/cameras/<camera_id>/start endpoint."""

    def test_start_camera_success(self, client, mock_camera_manager, sample_camera_config):
        """Should successfully start a camera."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            mock_camera = VirtualONVIFCamera(sample_camera_config)
            mock_camera.status = 'stopped'
            mock_camera.start = MagicMock()
            mock_camera_manager.get_camera.return_value = mock_camera

            # Act
            response = client.post('/api/cameras/1/start')

            # Assert
            assert response.status_code == 200
            mock_camera.start.assert_called_once()

    def test_start_camera_not_found_returns_404(self, client, mock_camera_manager):
        """Should return 404 when camera is not found."""
        # Arrange
        mock_camera_manager.get_camera.return_value = None

        # Act
        response = client.post('/api/cameras/999/start')

        # Assert
        assert response.status_code == 404
        assert 'error' in response.json

    def test_start_camera_restarts_mediamtx_when_not_running(self, client, mock_camera_manager, sample_camera_config):
        """Should restart MediaMTX when camera was not already running."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            mock_camera = VirtualONVIFCamera(sample_camera_config)
            mock_camera.status = 'stopped'
            mock_camera.start = MagicMock()
            mock_camera_manager.get_camera.return_value = mock_camera

            # Act
            response = client.post('/api/cameras/1/start')

            # Assert
            assert response.status_code == 200
            mock_camera_manager.mediamtx.restart.assert_called_once()


class TestStopCamera:
    """Tests for POST /api/cameras/<camera_id>/stop endpoint."""

    def test_stop_camera_success(self, client, mock_camera_manager, sample_camera_config):
        """Should successfully stop a camera."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            mock_camera = VirtualONVIFCamera(sample_camera_config)
            mock_camera.status = 'running'
            mock_camera.stop = MagicMock()
            mock_camera_manager.get_camera.return_value = mock_camera

            # Act
            response = client.post('/api/cameras/1/stop')

            # Assert
            assert response.status_code == 200
            mock_camera.stop.assert_called_once()

    def test_stop_camera_not_found_returns_404(self, client, mock_camera_manager):
        """Should return 404 when camera is not found."""
        # Arrange
        mock_camera_manager.get_camera.return_value = None

        # Act
        response = client.post('/api/cameras/999/stop')

        # Assert
        assert response.status_code == 404
        assert 'error' in response.json


class TestStartAllCameras:
    """Tests for POST /api/cameras/start-all endpoint."""

    def test_start_all_cameras(self, client, mock_camera_manager, sample_camera_config):
        """Should start all cameras."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            cameras = [
                VirtualONVIFCamera(sample_camera_config),
                VirtualONVIFCamera({**sample_camera_config, 'id': 2, 'name': 'Camera 2'})
            ]
            mock_camera_manager.cameras = cameras
            mock_camera_manager.start_all = MagicMock()

            # Act
            response = client.post('/api/cameras/start-all')

            # Assert
            assert response.status_code == 200
            mock_camera_manager.start_all.assert_called_once()


class TestStopAllCameras:
    """Tests for POST /api/cameras/stop-all endpoint."""

    def test_stop_all_cameras(self, client, mock_camera_manager, sample_camera_config):
        """Should stop all cameras."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            cameras = [
                VirtualONVIFCamera(sample_camera_config),
                VirtualONVIFCamera({**sample_camera_config, 'id': 2, 'name': 'Camera 2'})
            ]
            mock_camera_manager.cameras = cameras
            mock_camera_manager.stop_all = MagicMock()

            # Act
            response = client.post('/api/cameras/stop-all')

            # Assert
            assert response.status_code == 200
            mock_camera_manager.stop_all.assert_called_once()


class TestGetSettings:
    """Tests for GET /api/settings endpoint."""

    def test_get_settings_returns_settings(self, client, mock_camera_manager):
        """Should return current settings."""
        # Act
        response = client.get('/api/settings')

        # Assert
        assert response.status_code == 200
        assert 'serverIp' in response.json
        assert 'openBrowser' in response.json
        assert 'theme' in response.json
        assert 'gridColumns' in response.json
        assert 'rtspPort' in response.json

    def test_get_settings_returns_expected_values(self, client, mock_camera_manager):
        """Should return expected default values."""
        # Act
        response = client.get('/api/settings')

        # Assert
        assert response.json['serverIp'] == 'localhost'
        assert response.json['theme'] == 'dracula'
        assert response.json['gridColumns'] == 3


class TestSaveSettings:
    """Tests for POST /api/settings endpoint."""

    def test_save_settings_success(self, client, mock_camera_manager, settings_request_data):
        """Should successfully save settings."""
        # Arrange
        mock_camera_manager.save_settings.return_value = settings_request_data

        # Act
        response = client.post(
            '/api/settings',
            data=json.dumps(settings_request_data),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 200
        mock_camera_manager.save_settings.assert_called_once()

    def test_save_settings_returns_updated_settings(self, client, mock_camera_manager, settings_request_data):
        """Should return the updated settings."""
        # Arrange
        mock_camera_manager.save_settings.return_value = settings_request_data

        # Act
        response = client.post(
            '/api/settings',
            data=json.dumps(settings_request_data),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 200
        assert response.json['serverIp'] == '192.168.1.100'
        assert response.json['theme'] == 'light'

    def test_save_settings_error_returns_400(self, client, mock_camera_manager, settings_request_data):
        """Should return 400 when save fails."""
        # Arrange
        mock_camera_manager.save_settings.side_effect = Exception("Failed to save")

        # Act
        response = client.post(
            '/api/settings',
            data=json.dumps(settings_request_data),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 400
        assert 'error' in response.json


class TestAutoStartToggle:
    """Tests for POST /api/cameras/<camera_id>/auto-start endpoint."""

    def test_toggle_auto_start_on(self, client, mock_camera_manager, sample_camera_config):
        """Should enable auto-start for a camera."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            mock_camera = VirtualONVIFCamera(sample_camera_config)
            mock_camera_manager.get_camera.return_value = mock_camera

            # Act
            response = client.post(
                '/api/cameras/1/auto-start',
                data=json.dumps({'autoStart': True}),
                content_type='application/json'
            )

            # Assert
            assert response.status_code == 200
            assert mock_camera.auto_start is True

    def test_toggle_auto_start_off(self, client, mock_camera_manager, sample_camera_config):
        """Should disable auto-start for a camera."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            mock_camera = VirtualONVIFCamera(sample_camera_config)
            mock_camera.auto_start = True
            mock_camera_manager.get_camera.return_value = mock_camera

            # Act
            response = client.post(
                '/api/cameras/1/auto-start',
                data=json.dumps({'autoStart': False}),
                content_type='application/json'
            )

            # Assert
            assert response.status_code == 200
            assert mock_camera.auto_start is False

    def test_toggle_auto_start_camera_not_found(self, client, mock_camera_manager):
        """Should return 404 when camera is not found."""
        # Arrange
        mock_camera_manager.get_camera.return_value = None

        # Act
        response = client.post(
            '/api/cameras/999/auto-start',
            data=json.dumps({'autoStart': True}),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 404


class TestStats:
    """Tests for GET /api/stats endpoint."""

    def test_get_stats_returns_cpu_and_memory(self, client, mock_camera_manager):
        """Should return CPU and memory statistics."""
        # Arrange
        with patch('psutil.Process') as mock_process, \
             patch('psutil.cpu_count', return_value=4):
            mock_proc = MagicMock()
            mock_proc.memory_info.return_value.rss = 100 * 1024 * 1024
            mock_proc.cpu_times.return_value.user = 1.0
            mock_proc.cpu_times.return_value.system = 0.5
            mock_proc.children.return_value = []
            mock_process.return_value = mock_proc

            # Act
            response = client.get('/api/stats')

            # Assert
            assert response.status_code == 200
            assert 'cpu_percent' in response.json
            assert 'memory_mb' in response.json

    def test_get_stats_handles_errors(self, client, mock_camera_manager):
        """Should return 500 on error."""
        # Arrange
        with patch('psutil.Process', side_effect=Exception("Process error")):
            # Act
            response = client.get('/api/stats')

            # Assert
            assert response.status_code == 500
            assert 'error' in response.json


class TestNetworkInterfaces:
    """Tests for GET /api/network/interfaces endpoint."""

    def test_get_network_interfaces_non_linux(self, client, mock_camera_manager):
        """Should return empty list on non-Linux systems."""
        # Arrange
        with patch('app.web.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False

            # Act
            response = client.get('/api/network/interfaces')

            # Assert
            assert response.status_code == 200
            assert response.json == []

    def test_get_network_interfaces_linux(self, client, mock_camera_manager):
        """Should return list of interfaces on Linux."""
        # Arrange
        with patch('app.web.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = True
            mock_network.get_physical_interfaces.return_value = ['eth0', 'eth1', 'wlan0']

            # Act
            response = client.get('/api/network/interfaces')

            # Assert
            assert response.status_code == 200
            assert response.json == ['eth0', 'eth1', 'wlan0']


class TestIndexRoute:
    """Tests for GET / endpoint."""

    def test_index_returns_html(self, client, mock_camera_manager):
        """Should return HTML content."""
        # Act
        response = client.get('/')

        # Assert
        assert response.status_code == 200
        assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data

    def test_index_has_no_cache_headers(self, client, mock_camera_manager):
        """Should have no-cache headers."""
        # Act
        response = client.get('/')

        # Assert
        assert response.status_code == 200
        assert 'no-cache' in response.headers.get('Cache-Control', '')


class TestServerControl:
    """Tests for server restart/stop endpoints."""

    def test_restart_server(self, client, mock_camera_manager):
        """Should initiate server restart."""
        # Act
        response = client.post('/api/server/restart')

        # Assert
        assert response.status_code == 200
        assert 'message' in response.json

    def test_stop_server(self, client, mock_camera_manager):
        """Should initiate server stop."""
        # Act
        response = client.post('/api/server/stop')

        # Assert
        assert response.status_code == 200
        assert 'message' in response.json


class TestOnvifProbe:
    """Tests for POST /api/onvif/probe endpoint."""

    def test_probe_missing_host(self, client, mock_camera_manager):
        """Should return 400 when host is missing."""
        # Arrange
        data = {'username': 'admin', 'password': 'pass'}

        # Act
        response = client.post(
            '/api/onvif/probe',
            data=json.dumps(data),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 400
        assert 'error' in response.json

    def test_probe_missing_credentials(self, client, mock_camera_manager):
        """Should return 400 when credentials are missing."""
        # Arrange
        data = {'host': '192.168.1.100'}

        # Act
        response = client.post(
            '/api/onvif/probe',
            data=json.dumps(data),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 400
        assert 'error' in response.json

    def test_probe_success(self, client, mock_camera_manager):
        """Should return probe results on success."""
        # Arrange
        data = {
            'host': '192.168.1.100',
            'port': 80,
            'username': 'admin',
            'password': 'pass'
        }
        with patch('app.web.ONVIFProber') as mock_prober:
            mock_instance = MagicMock()
            mock_instance.probe.return_value = {'success': True, 'profiles': []}
            mock_prober.return_value = mock_instance

            # Act
            response = client.post(
                '/api/onvif/probe',
                data=json.dumps(data),
                content_type='application/json'
            )

            # Assert
            assert response.status_code == 200

    def test_probe_failure(self, client, mock_camera_manager):
        """Should return 400 on probe failure."""
        # Arrange
        data = {
            'host': '192.168.1.100',
            'username': 'admin',
            'password': 'wrong'
        }
        with patch('app.web.ONVIFProber') as mock_prober:
            mock_instance = MagicMock()
            mock_instance.probe.return_value = {'success': False, 'error': 'Connection failed'}
            mock_prober.return_value = mock_instance

            # Act
            response = client.post(
                '/api/onvif/probe',
                data=json.dumps(data),
                content_type='application/json'
            )

            # Assert
            assert response.status_code == 400


class TestFetchStreamInfo:
    """Tests for POST /api/cameras/<camera_id>/fetch-stream-info endpoint."""

    def test_fetch_stream_info_camera_not_found(self, client, mock_camera_manager):
        """Should return 404 when camera is not found."""
        # Arrange
        mock_camera_manager.get_camera.return_value = None

        # Act
        response = client.post(
            '/api/cameras/999/fetch-stream-info',
            data=json.dumps({'streamType': 'main'}),
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 404
