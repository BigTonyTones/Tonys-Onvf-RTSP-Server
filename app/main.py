import sys
import time
import threading
import webbrowser
from .utils import cleanup_stale_processes
from .manager import CameraManager
from .linux_network import LinuxNetworkManager
from .config import WEB_UI_PORT, MEDIAMTX_PORT
from .web import create_web_app

def main():
    """Main application entry point"""
    # Clean up before starting
    cleanup_stale_processes()
    
    # Clean up virtual network interfaces (Linux)
    if LinuxNetworkManager.is_linux():
        net_mgr = LinuxNetworkManager()
        net_mgr.cleanup_all_vnics()

    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║          Tonys Onvif-RTSP Server v4.1            ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    manager = CameraManager()
    
    # Auto-start cameras that have autoStart enabled
    # Note: We check auto_start setting, NOT the saved status
    # This ensures cameras start fresh based on their auto-start preference
    auto_start_cameras = [cam for cam in manager.cameras if cam.auto_start]
    if auto_start_cameras:
        print(f"\n🚀 Auto-starting {len(auto_start_cameras)} camera(s)...")
        for camera in auto_start_cameras:
            camera.start()
            print(f"  ✓ Started: {camera.name}")
            print("-" * 40)
        print("\n" + "=" * 60)
    else:
        print("\n  ℹ️  No cameras configured for auto-start")
        print("=" * 60)
    
    # Load settings to get RTSP port
    settings = manager.load_settings()
    rtsp_port = settings.get('rtspPort', MEDIAMTX_PORT)
    
    # Start MediaMTX
    # Pass manager.cameras so it can generate config
    print("\n📦 Initializing MediaMTX RTSP Server...")
    if not manager.mediamtx.start(manager.cameras, rtsp_port=rtsp_port):
        print("\n❌ Failed to start MediaMTX. Exiting...")
        sys.exit(1)
    
    web_app = create_web_app(manager)
    
    print(f"\n🌐 Starting Web UI on http://localhost:{WEB_UI_PORT}")
    web_thread = threading.Thread(
        target=lambda: web_app.run(
            host='0.0.0.0', 
            port=WEB_UI_PORT, 
            debug=False, 
            use_reloader=False,
            threaded=True  # Enable threading for better concurrency
        ),
        daemon=True
    )
    web_thread.start()
    
    time.sleep(2)
    
    print(f"✓ Web UI started!")
    
    # Check settings to see if we should open the browser
    settings = manager.load_settings()
    if settings.get('openBrowser', True) is not False:
        print(f"✓ Opening browser...\n")
        try:
            webbrowser.open(f'http://localhost:{WEB_UI_PORT}')
        except:
            pass
    
    print("="*60)
    print("SERVER RUNNING")
    print("="*60)
    print(f"Web Interface: http://localhost:{WEB_UI_PORT}")
    print(f"RTSP Server: rtsp://localhost:{rtsp_port}")
    print("Press Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    try:
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nShutdown requested...")
        manager.mediamtx.stop()
        print("Server stopped successfully. Goodbye!")
        sys.exit(0)
