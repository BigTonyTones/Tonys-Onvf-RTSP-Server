"""
Tests for VirtualONVIFCamera class.

This module tests the VirtualONVIFCamera functionality including:
- Camera initialization
- to_dict and to_config_dict methods
- MAC address generation
- Start/stop operations
"""

from unittest.mock import MagicMock, patch

import pytest

from app.camera import VirtualONVIFCamera


class TestCameraInitialization:
    """Tests for VirtualONVIFCamera initialization."""

    def test_init_with_full_config(self, sample_camera_config):
        """Should initialize with all config values."""
        # Arrange & Act
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(sample_camera_config)

        # Assert
        assert camera.id == 1
        assert camera.name == 'Test Camera'
        assert camera.main_stream_url == 'rtsp://admin:password@192.168.1.100:554/stream1'
        assert camera.sub_stream_url == 'rtsp://admin:password@192.168.1.100:554/stream2'
        assert camera.rtsp_port == 8554
        assert camera.onvif_port == 8001
        assert camera.status == 'stopped'

    def test_init_with_minimal_config(self, sample_camera_config_minimal):
        """Should initialize with minimal config using defaults."""
        # Arrange & Act
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(sample_camera_config_minimal)

        # Assert
        assert camera.id == 2
        assert camera.name == 'Minimal Camera'
        assert camera.username == 'admin'  # Default
        assert camera.password == ''  # Default
        assert camera.auto_start is False  # Default
        assert camera.main_width == 1920  # Default
        assert camera.main_height == 1080  # Default

    def test_init_resolution_settings(self, sample_camera_config):
        """Should correctly set resolution settings."""
        # Arrange & Act
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(sample_camera_config)

        # Assert
        assert camera.main_width == 1920
        assert camera.main_height == 1080
        assert camera.sub_width == 640
        assert camera.sub_height == 480

    def test_init_framerate_settings(self, sample_camera_config):
        """Should correctly set framerate settings."""
        # Arrange & Act
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(sample_camera_config)

        # Assert
        assert camera.main_framerate == 30
        assert camera.sub_framerate == 15

    def test_init_onvif_credentials(self, sample_camera_config):
        """Should correctly set ONVIF credentials."""
        # Arrange & Act
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(sample_camera_config)

        # Assert
        assert camera.onvif_username == 'admin'
        assert camera.onvif_password == 'admin123'

    def test_init_transcoding_settings(self, sample_camera_config):
        """Should correctly set transcoding settings."""
        # Arrange & Act
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(sample_camera_config)

        # Assert
        assert camera.transcode_sub is False
        assert camera.transcode_main is False

    def test_init_virtual_nic_settings(self, sample_camera_config_with_virtual_nic):
        """Should correctly set virtual NIC settings."""
        # Arrange & Act
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(sample_camera_config_with_virtual_nic)

        # Assert
        assert camera.use_virtual_nic is True
        assert camera.parent_interface == 'eth0'
        assert camera.nic_mac == '02:00:00:00:00:03'
        assert camera.ip_mode == 'static'
        assert camera.static_ip == '192.168.1.200'
        assert camera.netmask == '24'
        assert camera.gateway == '192.168.1.1'

    def test_init_sets_stopped_status(self, sample_camera_config):
        """Should initialize with stopped status."""
        # Arrange & Act
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(sample_camera_config)

        # Assert
        assert camera.status == 'stopped'

    def test_init_no_network_manager_non_linux(self, sample_camera_config):
        """Should not create network manager on non-Linux systems."""
        # Arrange & Act
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(sample_camera_config)

        # Assert
        assert camera.network_mgr is None


class TestMacAddress:
    """Tests for MAC address property."""

    def test_mac_address_from_config(self, sample_camera_config_with_virtual_nic):
        """Should return MAC address from config when provided."""
        # Arrange & Act
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(sample_camera_config_with_virtual_nic)

        # Assert
        assert camera.mac_address == '02:00:00:00:00:03'

    def test_mac_address_generated_when_not_provided(self, sample_camera_config):
        """Should generate MAC address when not provided in config."""
        # Arrange
        config = sample_camera_config.copy()
        config['nicMac'] = ''

        # Act
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(config)

        # Assert
        assert camera.mac_address == '02:00:00:00:00:01'  # Based on ID=1

    def test_mac_address_is_lowercase(self, sample_camera_config_with_virtual_nic):
        """Should return MAC address in lowercase."""
        # Arrange
        config = sample_camera_config_with_virtual_nic.copy()
        config['nicMac'] = 'AA:BB:CC:DD:EE:FF'

        # Act
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(config)

        # Assert
        assert camera.mac_address == 'aa:bb:cc:dd:ee:ff'

    @pytest.mark.parametrize("camera_id,expected_mac", [
        (1, "02:00:00:00:00:01"),
        (2, "02:00:00:00:00:02"),
        (15, "02:00:00:00:00:0f"),
        (16, "02:00:00:00:00:10"),
        (255, "02:00:00:00:00:ff"),
    ])
    def test_generated_mac_address_format(self, sample_camera_config, camera_id, expected_mac):
        """Should generate proper MAC addresses for different camera IDs."""
        # Arrange
        config = sample_camera_config.copy()
        config['id'] = camera_id
        config['nicMac'] = ''

        # Act
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(config)

        # Assert
        assert camera.mac_address == expected_mac


class TestToDict:
    """Tests for to_dict method."""

    def test_to_dict_includes_all_fields(self, sample_camera_config):
        """Should include all required fields in output."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(sample_camera_config)

        # Act
        result = camera.to_dict()

        # Assert
        expected_fields = [
            'id', 'name', 'mainStreamUrl', 'subStreamUrl', 'rtspPort',
            'onvifPort', 'pathName', 'username', 'password', 'autoStart',
            'status', 'mainWidth', 'mainHeight', 'subWidth', 'subHeight',
            'mainFramerate', 'subFramerate', 'onvifUsername', 'onvifPassword',
            'transcodeSub', 'transcodeMain', 'useVirtualNic', 'parentInterface',
            'nicMac', 'ipMode', 'staticIp', 'netmask', 'gateway',
            'assignedIp', 'macAddress'
        ]
        for field in expected_fields:
            assert field in result, f"Missing field: {field}"

    def test_to_dict_includes_status(self, sample_camera_config):
        """Should include runtime status."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(sample_camera_config)
            camera.status = 'running'

        # Act
        result = camera.to_dict()

        # Assert
        assert result['status'] == 'running'

    def test_to_dict_includes_assigned_ip(self, sample_camera_config):
        """Should include assigned IP when set."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(sample_camera_config)
            camera.assigned_ip = '192.168.1.100'

        # Act
        result = camera.to_dict()

        # Assert
        assert result['assignedIp'] == '192.168.1.100'

    def test_to_dict_includes_mac_address(self, sample_camera_config):
        """Should include MAC address."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(sample_camera_config)

        # Act
        result = camera.to_dict()

        # Assert
        assert 'macAddress' in result
        assert result['macAddress'] == camera.mac_address


class TestToConfigDict:
    """Tests for to_config_dict method."""

    def test_to_config_dict_excludes_status(self, sample_camera_config):
        """Should NOT include runtime status."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(sample_camera_config)
            camera.status = 'running'

        # Act
        result = camera.to_config_dict()

        # Assert
        assert 'status' not in result

    def test_to_config_dict_excludes_assigned_ip(self, sample_camera_config):
        """Should NOT include assigned IP (runtime value)."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(sample_camera_config)
            camera.assigned_ip = '192.168.1.100'

        # Act
        result = camera.to_config_dict()

        # Assert
        assert 'assignedIp' not in result

    def test_to_config_dict_excludes_mac_address_property(self, sample_camera_config):
        """Should NOT include computed macAddress property."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(sample_camera_config)

        # Act
        result = camera.to_config_dict()

        # Assert
        assert 'macAddress' not in result  # The property, not nicMac

    def test_to_config_dict_includes_nic_mac(self, sample_camera_config):
        """Should include nicMac configuration value."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(sample_camera_config)

        # Act
        result = camera.to_config_dict()

        # Assert
        assert 'nicMac' in result

    def test_to_config_dict_preserves_auto_start(self, sample_camera_config):
        """Should include autoStart setting."""
        # Arrange
        config = sample_camera_config.copy()
        config['autoStart'] = True

        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(config)

        # Act
        result = camera.to_config_dict()

        # Assert
        assert result['autoStart'] is True

    def test_to_config_dict_includes_all_config_fields(self, sample_camera_config):
        """Should include all configuration fields."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(sample_camera_config)

        # Act
        result = camera.to_config_dict()

        # Assert
        expected_fields = [
            'id', 'name', 'mainStreamUrl', 'subStreamUrl', 'rtspPort',
            'onvifPort', 'pathName', 'username', 'password', 'autoStart',
            'mainWidth', 'mainHeight', 'subWidth', 'subHeight',
            'mainFramerate', 'subFramerate', 'onvifUsername', 'onvifPassword',
            'transcodeSub', 'transcodeMain', 'useVirtualNic', 'parentInterface',
            'nicMac', 'ipMode', 'staticIp', 'netmask', 'gateway'
        ]
        for field in expected_fields:
            assert field in result, f"Missing field: {field}"


class TestStartStop:
    """Tests for start and stop methods."""

    def test_start_sets_running_status(self, sample_camera_config):
        """Should set status to running when started."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(sample_camera_config)
            camera._start_onvif_service = MagicMock()

        # Act
        camera.start()

        # Assert
        assert camera.status == 'running'

    def test_stop_sets_stopped_status(self, sample_camera_config):
        """Should set status to stopped when stopped."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(sample_camera_config)
            camera.status = 'running'

        # Act
        camera.stop()

        # Assert
        assert camera.status == 'stopped'

    def test_start_calls_onvif_service(self, sample_camera_config):
        """Should start ONVIF service when camera starts."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(sample_camera_config)
            camera._start_onvif_service = MagicMock()

        # Act
        camera.start()

        # Assert
        camera._start_onvif_service.assert_called_once()

    def test_stop_clears_assigned_ip(self, sample_camera_config):
        """Should clear assigned IP when stopped."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(sample_camera_config)
            camera.assigned_ip = '192.168.1.100'

        # Act
        camera.stop()

        # Assert
        assert camera.assigned_ip is None


class TestVirtualNicOperations:
    """Tests for virtual NIC-related operations."""

    def test_start_with_virtual_nic_linux(self, sample_camera_config_with_virtual_nic):
        """Should create virtual NIC on Linux when enabled."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as MockNetwork:
            MockNetwork.is_linux.return_value = True
            mock_mgr = MagicMock()
            mock_mgr.create_macvlan.return_value = True
            mock_mgr.setup_ip.return_value = '192.168.1.200'
            MockNetwork.return_value = mock_mgr

            camera = VirtualONVIFCamera(sample_camera_config_with_virtual_nic)
            camera._start_onvif_service = MagicMock()

            # Act
            camera.start()

            # Assert
            mock_mgr.create_macvlan.assert_called_once()
            mock_mgr.setup_ip.assert_called_once()

    def test_stop_with_virtual_nic_linux(self, sample_camera_config_with_virtual_nic):
        """Should remove virtual NIC on Linux when stopping."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as MockNetwork:
            MockNetwork.is_linux.return_value = True
            mock_mgr = MagicMock()
            MockNetwork.return_value = mock_mgr

            camera = VirtualONVIFCamera(sample_camera_config_with_virtual_nic)
            camera.status = 'running'

            # Act
            camera.stop()

            # Assert
            mock_mgr.remove_interface.assert_called_once()

    def test_no_virtual_nic_operations_when_disabled(self, sample_camera_config):
        """Should not perform virtual NIC operations when disabled."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as MockNetwork:
            MockNetwork.is_linux.return_value = True
            mock_mgr = MagicMock()
            MockNetwork.return_value = mock_mgr

            camera = VirtualONVIFCamera(sample_camera_config)
            camera._start_onvif_service = MagicMock()

            # Act
            camera.start()
            camera.stop()

            # Assert
            mock_mgr.create_macvlan.assert_not_called()
            mock_mgr.remove_interface.assert_not_called()


class TestOnvifServiceStart:
    """Tests for _start_onvif_service method."""

    def test_onvif_service_not_started_twice(self, sample_camera_config):
        """Should not start ONVIF service if already running."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(sample_camera_config)

            # Mock an already running thread
            mock_thread = MagicMock()
            mock_thread.is_alive.return_value = True
            camera.flask_thread = mock_thread

            # Act
            with patch('app.camera.ONVIFService') as mock_onvif:
                camera._start_onvif_service()

                # Assert
                mock_onvif.assert_not_called()

    def test_onvif_service_creates_flask_app(self, sample_camera_config):
        """Should create Flask app when starting ONVIF service."""
        # Arrange
        with patch('app.camera.LinuxNetworkManager') as mock_network:
            mock_network.is_linux.return_value = False
            camera = VirtualONVIFCamera(sample_camera_config)

            # Act
            with patch('app.camera.ONVIFService') as MockONVIFService, \
                 patch('socket.gethostbyname', return_value='127.0.0.1'):
                mock_service = MagicMock()
                mock_app = MagicMock()
                mock_service.create_app.return_value = mock_app
                MockONVIFService.return_value = mock_service

                camera._start_onvif_service()

                # Assert
                MockONVIFService.assert_called_once_with(camera)
                mock_service.create_app.assert_called_once()
