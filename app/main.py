import sys
import time
import threading
import webbrowser
from .utils import cleanup_stale_processes
from .manager import CameraManager
from .linux_network import LinuxNetworkManager
from .config import WEB_UI_PORT, MEDIAMTX_PORT
from .web import create_web_app
from .logging_config import get_logger

logger = get_logger(__name__)


def run_server(options=None):
    """
    Main application entry point with configurable options.

    Args:
        options (dict): Configuration options from command line
            - port (int): Web UI port (default: 5552)
            - rtsp_port (int): RTSP server port (default: 8554)
            - open_browser (bool): Whether to open browser (default: True)
            - config_file (str): Path to config file (default: None)
            - debug (bool): Enable debug mode (default: False)
    """
    if options is None:
        options = {}

    # Extract options with defaults
    web_port = options.get('port') or WEB_UI_PORT
    rtsp_port = options.get('rtsp_port') or MEDIAMTX_PORT
    open_browser = options.get('open_browser', True)
    config_file = options.get('config_file')
    debug = options.get('debug', False)

    # Clean up before starting
    cleanup_stale_processes()

    # Clean up virtual network interfaces (Linux)
    if LinuxNetworkManager.is_linux():
        net_mgr = LinuxNetworkManager()
        net_mgr.cleanup_all_vnics()

    print("""
    ============================================================
              Tonys Onvif-RTSP Server v4.0
    ============================================================
    """)

    if debug:
        logger.debug("Running in debug mode")
        logger.debug("Web UI Port: %d", web_port)
        logger.debug("RTSP Port: %d", rtsp_port)
        logger.debug("Open Browser: %s", open_browser)
        logger.debug("Config File: %s", config_file or 'default')

    # Create manager with optional custom config file
    if config_file:
        manager = CameraManager(config_file=config_file)
    else:
        manager = CameraManager()

    # Auto-start cameras that have autoStart enabled
    # Note: We check auto_start setting, NOT the saved status
    # This ensures cameras start fresh based on their auto-start preference
    auto_start_cameras = [cam for cam in manager.cameras if cam.auto_start]
    if auto_start_cameras:
        logger.info("Auto-starting %d camera(s)...", len(auto_start_cameras))
        for camera in auto_start_cameras:
            camera.start()
            logger.info("Started: %s", camera.name)
        print("-" * 40)
    else:
        logger.info("No cameras configured for auto-start")
    print("=" * 60)

    # Load settings to get RTSP port (command line overrides saved settings)
    settings = manager.load_settings()
    if options.get('rtsp_port') is None:
        rtsp_port = settings.get('rtspPort', MEDIAMTX_PORT)

    # Start MediaMTX
    # Pass manager.cameras so it can generate config
    logger.info("Initializing MediaMTX RTSP Server...")
    if not manager.mediamtx.start(manager.cameras, rtsp_port=rtsp_port):
        logger.error("Failed to start MediaMTX. Exiting...")
        sys.exit(1)

    web_app = create_web_app(manager)

    # Configure Flask debug mode
    flask_debug = debug

    logger.info("Starting Web UI on http://localhost:%d", web_port)
    web_thread = threading.Thread(
        target=lambda: web_app.run(
            host='0.0.0.0',
            port=web_port,
            debug=flask_debug,
            use_reloader=False,
            threaded=True  # Enable threading for better concurrency
        ),
        daemon=True
    )
    web_thread.start()

    time.sleep(2)

    logger.info("Web UI started!")

    # Check settings to see if we should open the browser
    # Command line --no-browser takes precedence
    if open_browser:
        settings = manager.load_settings()
        if settings.get('openBrowser', True) is not False:
            logger.info("Opening browser...")
            try:
                webbrowser.open(f'http://localhost:{web_port}')
            except Exception:
                pass
    else:
        if debug:
            logger.debug("Browser opening disabled via command line")

    print("=" * 60)
    print("SERVER RUNNING")
    print("=" * 60)
    print(f"Web Interface: http://localhost:{web_port}")
    print(f"RTSP Server: rtsp://localhost:{rtsp_port}")
    print("Press Ctrl+C to stop the server")
    print("=" * 60 + "\n")

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutdown requested...")
        manager.mediamtx.stop()
        logger.info("Server stopped successfully. Goodbye!")
        sys.exit(0)


def main():
    """
    Legacy entry point for backwards compatibility.
    Calls run_server with default options.
    """
    run_server()
