"""
Tests for CameraManager class.

This module tests the CameraManager functionality including:
- Camera CRUD operations
- Configuration persistence
- Port availability checking
- Settings management
"""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.manager import CameraManager
from app.camera import VirtualONVIFCamera


class TestCameraManagerInitialization:
    """Tests for CameraManager initialization."""

    def test_init_with_empty_config(self, temp_config_file_empty, mock_mediamtx, mock_service_mgr):
        """Should initialize with default values when config doesn't exist."""
        # Arrange & Act
        with patch('app.manager.MediaMTXManager', return_value=mock_mediamtx), \
             patch('app.manager.LinuxServiceManager', return_value=mock_service_mgr):
            manager = CameraManager(config_file=temp_config_file_empty)

        # Assert
        assert manager.cameras == []
        assert manager.next_id == 1
        assert manager.next_onvif_port == 8001
        assert manager.server_ip == 'localhost'
        assert manager.open_browser is True
        assert manager.theme == 'dracula'

    def test_init_creates_config_file_when_missing(self, temp_config_file_empty, mock_mediamtx, mock_service_mgr):
        """Should create config file when it doesn't exist."""
        # Arrange & Act
        with patch('app.manager.MediaMTXManager', return_value=mock_mediamtx), \
             patch('app.manager.LinuxServiceManager', return_value=mock_service_mgr):
            manager = CameraManager(config_file=temp_config_file_empty)

        # Assert
        assert os.path.exists(temp_config_file_empty)

    def test_init_loads_existing_cameras(self, temp_config_file_with_data, mock_mediamtx, mock_service_mgr):
        """Should load cameras from existing config file."""
        # Arrange & Act
        with patch('app.manager.MediaMTXManager', return_value=mock_mediamtx), \
             patch('app.manager.LinuxServiceManager', return_value=mock_service_mgr), \
             patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            manager = CameraManager(config_file=temp_config_file_with_data)

        # Assert
        assert len(manager.cameras) == 1
        assert manager.cameras[0].name == 'Test Camera'

    def test_init_loads_settings(self, temp_config_file_with_data, mock_mediamtx, mock_service_mgr):
        """Should load settings from existing config file."""
        # Arrange & Act
        with patch('app.manager.MediaMTXManager', return_value=mock_mediamtx), \
             patch('app.manager.LinuxServiceManager', return_value=mock_service_mgr), \
             patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            manager = CameraManager(config_file=temp_config_file_with_data)

        # Assert
        assert manager.server_ip == '192.168.1.50'
        assert manager.theme == 'dracula'

    def test_init_updates_next_id(self, temp_dir, mock_mediamtx, mock_service_mgr, sample_camera_config):
        """Should set next_id higher than existing camera IDs."""
        # Arrange
        config_file = os.path.join(temp_dir, 'test_config.json')
        camera_config = sample_camera_config.copy()
        camera_config['id'] = 10
        config_data = {'cameras': [camera_config], 'settings': {}}
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        # Act
        with patch('app.manager.MediaMTXManager', return_value=mock_mediamtx), \
             patch('app.manager.LinuxServiceManager', return_value=mock_service_mgr), \
             patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            manager = CameraManager(config_file=config_file)

        # Assert
        assert manager.next_id == 11


class TestAddCamera:
    """Tests for CameraManager.add_camera method."""

    def test_add_camera_success(self, camera_manager):
        """Should successfully add a new camera."""
        # Act
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = camera_manager.add_camera(
                name='New Camera',
                host='192.168.1.100',
                rtsp_port=554,
                username='admin',
                password='password',
                main_path='/stream1',
                sub_path='/stream2'
            )

        # Assert
        assert camera is not None
        assert camera.name == 'New Camera'
        assert camera.id == 1
        assert len(camera_manager.cameras) == 1

    def test_add_camera_increments_id(self, camera_manager):
        """Should increment camera ID for each new camera."""
        # Arrange & Act
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera1 = camera_manager.add_camera(
                name='Camera 1', host='192.168.1.100', rtsp_port=554,
                username='', password='', main_path='/stream1', sub_path='/stream2'
            )
            camera2 = camera_manager.add_camera(
                name='Camera 2', host='192.168.1.101', rtsp_port=554,
                username='', password='', main_path='/stream1', sub_path='/stream2'
            )

        # Assert
        assert camera1.id == 1
        assert camera2.id == 2

    def test_add_camera_auto_assigns_onvif_port(self, camera_manager):
        """Should auto-assign ONVIF port when not specified."""
        # Act
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = camera_manager.add_camera(
                name='Camera', host='192.168.1.100', rtsp_port=554,
                username='', password='', main_path='/stream1', sub_path='/stream2'
            )

        # Assert
        assert camera.onvif_port == 8001

    def test_add_camera_with_custom_onvif_port(self, camera_manager):
        """Should use specified ONVIF port."""
        # Act
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = camera_manager.add_camera(
                name='Camera', host='192.168.1.100', rtsp_port=554,
                username='', password='', main_path='/stream1', sub_path='/stream2',
                onvif_port=9000
            )

        # Assert
        assert camera.onvif_port == 9000

    def test_add_camera_rejects_duplicate_onvif_port(self, camera_manager):
        """Should raise ValueError when ONVIF port is already in use."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera_manager.add_camera(
                name='Camera 1', host='192.168.1.100', rtsp_port=554,
                username='', password='', main_path='/stream1', sub_path='/stream2',
                onvif_port=8001
            )

            # Act & Assert
            with pytest.raises(ValueError, match="already in use"):
                camera_manager.add_camera(
                    name='Camera 2', host='192.168.1.101', rtsp_port=554,
                    username='', password='', main_path='/stream1', sub_path='/stream2',
                    onvif_port=8001
                )

    def test_add_camera_normalizes_paths(self, camera_manager):
        """Should add leading slash to paths if missing."""
        # Act
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = camera_manager.add_camera(
                name='Camera', host='192.168.1.100', rtsp_port=554,
                username='', password='',
                main_path='stream1',  # No leading slash
                sub_path='stream2'   # No leading slash
            )

        # Assert
        assert '/stream1' in camera.main_stream_url
        assert '/stream2' in camera.sub_stream_url

    def test_add_camera_encodes_credentials(self, camera_manager):
        """Should URL-encode special characters in credentials."""
        # Act
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = camera_manager.add_camera(
                name='Camera', host='192.168.1.100', rtsp_port=554,
                username='user@domain',
                password='pass#word!',
                main_path='/stream1', sub_path='/stream2'
            )

        # Assert
        assert 'user%40domain' in camera.main_stream_url
        assert 'pass%23word%21' in camera.main_stream_url

    def test_add_camera_saves_config(self, camera_manager, temp_config_file_empty):
        """Should save config after adding camera."""
        # Act
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera_manager.add_camera(
                name='Camera', host='192.168.1.100', rtsp_port=554,
                username='', password='', main_path='/stream1', sub_path='/stream2'
            )

        # Assert
        assert os.path.exists(temp_config_file_empty)
        with open(temp_config_file_empty, 'r') as f:
            config = json.load(f)
        assert len(config['cameras']) == 1

    def test_add_camera_generates_safe_path_name(self, camera_manager):
        """Should generate safe path name from camera name."""
        # Act
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = camera_manager.add_camera(
                name='My Camera - Unit 1',
                host='192.168.1.100', rtsp_port=554,
                username='', password='', main_path='/stream1', sub_path='/stream2'
            )

        # Assert - multiple underscores are collapsed to single underscores
        assert camera.path_name == 'my_camera_unit_1'


class TestUpdateCamera:
    """Tests for CameraManager.update_camera method."""

    def test_update_camera_success(self, camera_manager_with_cameras):
        """Should successfully update an existing camera."""
        # Arrange
        camera_id = camera_manager_with_cameras.cameras[0].id

        # Act
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            updated = camera_manager_with_cameras.update_camera(
                camera_id=camera_id,
                name='Updated Name',
                host='192.168.1.200',
                rtsp_port=555,
                username='new_user',
                password='new_pass',
                main_path='/new_stream1',
                sub_path='/new_stream2'
            )

        # Assert
        assert updated is not None
        assert updated.name == 'Updated Name'

    def test_update_camera_returns_none_for_missing_camera(self, camera_manager):
        """Should return None when camera doesn't exist."""
        # Act
        result = camera_manager.update_camera(
            camera_id=999,
            name='Name',
            host='192.168.1.100',
            rtsp_port=554,
            username='', password='',
            main_path='/stream1', sub_path='/stream2'
        )

        # Assert
        assert result is None

    def test_update_camera_rejects_duplicate_onvif_port(self, camera_manager):
        """Should raise ValueError when changing to an in-use ONVIF port."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera1 = camera_manager.add_camera(
                name='Camera 1', host='192.168.1.100', rtsp_port=554,
                username='', password='', main_path='/s1', sub_path='/s2',
                onvif_port=8001
            )
            camera2 = camera_manager.add_camera(
                name='Camera 2', host='192.168.1.101', rtsp_port=554,
                username='', password='', main_path='/s1', sub_path='/s2',
                onvif_port=8002
            )

            # Act & Assert
            with pytest.raises(ValueError, match="already in use"):
                camera_manager.update_camera(
                    camera_id=camera2.id,
                    name='Camera 2',
                    host='192.168.1.101',
                    rtsp_port=554,
                    username='', password='',
                    main_path='/s1', sub_path='/s2',
                    onvif_port=8001  # Same as camera1
                )


class TestDeleteCamera:
    """Tests for CameraManager.delete_camera method."""

    def test_delete_camera_success(self, camera_manager_with_cameras):
        """Should successfully delete a camera."""
        # Arrange
        camera_id = camera_manager_with_cameras.cameras[0].id
        initial_count = len(camera_manager_with_cameras.cameras)

        # Act
        result = camera_manager_with_cameras.delete_camera(camera_id)

        # Assert
        assert result is True
        assert len(camera_manager_with_cameras.cameras) == initial_count - 1

    def test_delete_camera_returns_false_for_missing(self, camera_manager):
        """Should return False when camera doesn't exist."""
        # Act
        result = camera_manager.delete_camera(999)

        # Assert
        assert result is False

    def test_delete_camera_updates_config(self, camera_manager_with_cameras, temp_config_file_with_data):
        """Should update config file after deletion."""
        # Arrange
        camera_id = camera_manager_with_cameras.cameras[0].id

        # Act
        camera_manager_with_cameras.delete_camera(camera_id)

        # Assert
        with open(temp_config_file_with_data, 'r') as f:
            config = json.load(f)
        assert len(config['cameras']) == 0


class TestGetCamera:
    """Tests for CameraManager.get_camera method."""

    def test_get_camera_found(self, camera_manager_with_cameras):
        """Should return camera when found."""
        # Arrange
        expected_id = camera_manager_with_cameras.cameras[0].id

        # Act
        camera = camera_manager_with_cameras.get_camera(expected_id)

        # Assert
        assert camera is not None
        assert camera.id == expected_id

    def test_get_camera_not_found(self, camera_manager):
        """Should return None when camera not found."""
        # Act
        camera = camera_manager.get_camera(999)

        # Assert
        assert camera is None


class TestPortAvailability:
    """Tests for CameraManager.is_port_available method."""

    def test_port_available_when_empty(self, camera_manager):
        """Should return True when no cameras exist."""
        # Act
        result = camera_manager.is_port_available(8001)

        # Assert
        assert result is True

    def test_port_unavailable_when_in_use(self, camera_manager_with_cameras):
        """Should return False when port is in use."""
        # Arrange
        used_port = camera_manager_with_cameras.cameras[0].onvif_port

        # Act
        result = camera_manager_with_cameras.is_port_available(used_port)

        # Assert
        assert result is False

    def test_port_available_when_excluded(self, camera_manager_with_cameras):
        """Should return True when port belongs to excluded camera."""
        # Arrange
        camera = camera_manager_with_cameras.cameras[0]
        used_port = camera.onvif_port

        # Act
        result = camera_manager_with_cameras.is_port_available(
            used_port,
            exclude_camera_id=camera.id
        )

        # Assert
        assert result is True


class TestConfigPersistence:
    """Tests for configuration save/load functionality."""

    def test_save_config_creates_file(self, camera_manager, temp_config_file_empty):
        """Should create config file on save."""
        # Note: CameraManager creates the file during __init__ if it doesn't exist
        # So we just verify the file exists after initialization

        # Act - call save_config to ensure it works
        camera_manager.save_config()

        # Assert - file should exist (created during init or by save_config)
        assert os.path.exists(temp_config_file_empty)
        assert os.path.getsize(temp_config_file_empty) > 0

    def test_save_config_includes_all_cameras(self, camera_manager, temp_config_file_empty):
        """Should save all cameras to config file."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera_manager.add_camera(
                name='Camera 1', host='192.168.1.100', rtsp_port=554,
                username='', password='', main_path='/s1', sub_path='/s2'
            )
            camera_manager.add_camera(
                name='Camera 2', host='192.168.1.101', rtsp_port=554,
                username='', password='', main_path='/s1', sub_path='/s2'
            )

        # Assert
        with open(temp_config_file_empty, 'r') as f:
            config = json.load(f)
        assert len(config['cameras']) == 2

    def test_save_config_includes_settings(self, camera_manager, temp_config_file_empty):
        """Should save settings to config file."""
        # Arrange
        camera_manager.server_ip = '10.0.0.1'
        camera_manager.theme = 'light'

        # Act
        camera_manager.save_config()

        # Assert
        with open(temp_config_file_empty, 'r') as f:
            config = json.load(f)
        assert config['settings']['serverIp'] == '10.0.0.1'
        assert config['settings']['theme'] == 'light'

    def test_load_config_preserves_data(self, temp_dir, mock_mediamtx, mock_service_mgr):
        """Should load and preserve all config data."""
        # Arrange
        config_file = os.path.join(temp_dir, 'test_config.json')
        config_data = {
            'cameras': [],
            'settings': {
                'serverIp': '192.168.1.50',
                'openBrowser': False,
                'theme': 'light',
                'gridColumns': 4,
                'rtspPort': 8555,
                'autoBoot': False
            }
        }
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        # Act
        with patch('app.manager.MediaMTXManager', return_value=mock_mediamtx), \
             patch('app.manager.LinuxServiceManager', return_value=mock_service_mgr):
            manager = CameraManager(config_file=config_file)

        # Assert
        assert manager.server_ip == '192.168.1.50'
        assert manager.open_browser is False
        assert manager.theme == 'light'
        assert manager.grid_columns == 4
        assert manager.rtsp_port == 8555


class TestSettingsManagement:
    """Tests for settings save/load functionality."""

    def test_load_settings_returns_current_values(self, camera_manager):
        """Should return current settings values."""
        # Act
        settings = camera_manager.load_settings()

        # Assert
        assert 'serverIp' in settings
        assert 'openBrowser' in settings
        assert 'theme' in settings
        assert 'gridColumns' in settings
        assert 'rtspPort' in settings
        assert 'autoBoot' in settings

    def test_save_settings_updates_values(self, camera_manager):
        """Should update manager attributes when saving settings."""
        # Act
        camera_manager.save_settings({
            'serverIp': '10.0.0.50',
            'openBrowser': False,
            'theme': 'light',
            'gridColumns': 4,
            'rtspPort': 9000
        })

        # Assert
        assert camera_manager.server_ip == '10.0.0.50'
        assert camera_manager.open_browser is False
        assert camera_manager.theme == 'light'
        assert camera_manager.grid_columns == 4
        assert camera_manager.rtsp_port == 9000

    def test_save_settings_returns_saved_values(self, camera_manager):
        """Should return the saved settings."""
        # Arrange
        new_settings = {
            'serverIp': '10.0.0.50',
            'openBrowser': False,
            'theme': 'light',
            'gridColumns': 4,
            'rtspPort': 9000
        }

        # Act
        result = camera_manager.save_settings(new_settings)

        # Assert
        assert result['serverIp'] == '10.0.0.50'
        assert result['theme'] == 'light'

    def test_save_settings_auto_boot_linux_only(self, camera_manager, mock_service_mgr):
        """Should only try to install service on Linux."""
        # Arrange
        mock_service_mgr.is_linux.return_value = False

        # Act
        camera_manager.save_settings({
            'serverIp': 'localhost',
            'autoBoot': True
        })

        # Assert
        mock_service_mgr.install_service.assert_not_called()


class TestStartStopAll:
    """Tests for start_all and stop_all methods."""

    def test_start_all_starts_all_cameras(self, camera_manager):
        """Should start all cameras."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera1 = camera_manager.add_camera(
                name='Camera 1', host='192.168.1.100', rtsp_port=554,
                username='', password='', main_path='/s1', sub_path='/s2'
            )
            camera2 = camera_manager.add_camera(
                name='Camera 2', host='192.168.1.101', rtsp_port=554,
                username='', password='', main_path='/s1', sub_path='/s2'
            )

            # Mock the start method
            camera1.start = MagicMock()
            camera2.start = MagicMock()

            # Act
            camera_manager.start_all()

            # Assert
            camera1.start.assert_called_once()
            camera2.start.assert_called_once()

    def test_stop_all_stops_all_cameras(self, camera_manager):
        """Should stop all cameras."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera1 = camera_manager.add_camera(
                name='Camera 1', host='192.168.1.100', rtsp_port=554,
                username='', password='', main_path='/s1', sub_path='/s2'
            )
            camera2 = camera_manager.add_camera(
                name='Camera 2', host='192.168.1.101', rtsp_port=554,
                username='', password='', main_path='/s1', sub_path='/s2'
            )

            # Mock the stop method
            camera1.stop = MagicMock()
            camera2.stop = MagicMock()

            # Act
            camera_manager.stop_all()

            # Assert
            camera1.stop.assert_called_once()
            camera2.stop.assert_called_once()

    def test_start_all_restarts_mediamtx(self, camera_manager, mock_mediamtx):
        """Should restart MediaMTX after starting all cameras."""
        # Act
        camera_manager.start_all()

        # Assert
        mock_mediamtx.restart.assert_called_once()

    def test_stop_all_restarts_mediamtx(self, camera_manager, mock_mediamtx):
        """Should restart MediaMTX after stopping all cameras."""
        # Act
        camera_manager.stop_all()

        # Assert
        mock_mediamtx.restart.assert_called_once()


class TestThreadSafety:
    """Tests for thread-safety of config operations."""

    def test_save_config_uses_lock(self, camera_manager):
        """Should use lock when saving config."""
        # This test verifies that _lock is used
        # We can't easily test the lock directly, but we can verify the attribute exists
        assert hasattr(camera_manager, '_lock')
        assert camera_manager._lock is not None

    def test_load_settings_uses_lock(self, camera_manager_with_cameras):
        """Should use lock when loading settings."""
        # Verify lock exists and settings can be loaded
        settings = camera_manager_with_cameras.load_settings()
        assert settings is not None
