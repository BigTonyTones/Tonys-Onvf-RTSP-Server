"""
Application Configuration

Configuration values are loaded in this priority order:
1. Environment variables (highest priority)
2. Default values (lowest priority)

Environment Variables:
    ONVIF_CONFIG_FILE    - Path to camera configuration file (default: camera_config.json)
    ONVIF_WEB_PORT       - Web UI port (default: 5552)
    ONVIF_RTSP_PORT      - RTSP/MediaMTX port (default: 8554)
    ONVIF_API_PORT       - MediaMTX API port (default: 9997)
    ONVIF_DEBUG          - Enable debug mode (default: false)
    ONVIF_NO_BROWSER     - Disable auto-opening browser (default: false)

Note: Command-line arguments override environment variables when using run.py
"""

import os


def _get_bool_env(name: str, default: bool = False) -> bool:
    """Get boolean from environment variable."""
    value = os.environ.get(name, '').lower()
    if value in ('true', '1', 'yes', 'on'):
        return True
    if value in ('false', '0', 'no', 'off'):
        return False
    return default


def _get_int_env(name: str, default: int) -> int:
    """Get integer from environment variable."""
    value = os.environ.get(name)
    if value is not None:
        try:
            return int(value)
        except ValueError:
            pass
    return default


# Configuration file path
CONFIG_FILE = os.environ.get('ONVIF_CONFIG_FILE', 'camera_config.json')

# Network ports
WEB_UI_PORT = _get_int_env('ONVIF_WEB_PORT', 5552)
MEDIAMTX_PORT = _get_int_env('ONVIF_RTSP_PORT', 8554)
MEDIAMTX_API_PORT = _get_int_env('ONVIF_API_PORT', 9997)

# Runtime options
DEBUG_MODE = _get_bool_env('ONVIF_DEBUG', False)
NO_BROWSER = _get_bool_env('ONVIF_NO_BROWSER', False)
