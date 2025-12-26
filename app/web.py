
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import threading
import subprocess
import json
import os
import sys
import psutil
import time
import logging

from .ffmpeg_manager import FFmpegManager
from .onvif_client import ONVIFProber
from .linux_network import LinuxNetworkManager
from .logging_config import get_logger

logger = get_logger(__name__)

# Allowed CORS origins - can be configured via environment variable
ALLOWED_CORS_ORIGINS = os.environ.get(
    'WEB_CORS_ORIGINS',
    'http://localhost:5552,http://127.0.0.1:5552'
).split(',')

# Rate limit configuration - can be configured via environment variables
RATE_LIMIT_DEFAULT = os.environ.get('RATE_LIMIT_DEFAULT', '200 per minute')
RATE_LIMIT_PROBE = os.environ.get('RATE_LIMIT_PROBE', '10 per minute')
RATE_LIMIT_SETTINGS = os.environ.get('RATE_LIMIT_SETTINGS', '30 per minute')
RATE_LIMIT_CAMERA_CRUD = os.environ.get('RATE_LIMIT_CAMERA_CRUD', '30 per minute')


def create_web_app(manager):
    """Create Flask web application"""
    # Get the path to the static folder (relative to the project root)
    static_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    app = Flask(__name__, static_folder=static_folder, static_url_path='/static')
    CORS(app, origins=ALLOWED_CORS_ORIGINS)

    # Initialize rate limiter
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=[RATE_LIMIT_DEFAULT],
        storage_uri="memory://",
    )

    # Initialize stats tracking
    app.stats_last_time = time.time()
    app.stats_last_cpu = 0

    # Suppress Flask/Werkzeug logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    @app.route('/api/onvif/probe', methods=['POST'])
    @limiter.limit(RATE_LIMIT_PROBE)
    def probe_onvif():
        """Probe an ONVIF camera for profiles"""
        data = request.json
        host = data.get('host')
        port = int(data.get('port', 80))
        username = data.get('username')
        password = data.get('password')

        if not host or not username or not password:
            return jsonify({'error': 'Host, username, and password are required'}), 400

        prober = ONVIFProber()
        result = prober.probe(host, port, username, password)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400

    @app.route('/api/server/restart', methods=['POST'])
    def restart_server():
        """Restart the RTSP server"""
        def do_restart():
            import time
            time.sleep(2)  # Give time for response to be sent
            logger.info("Server restart requested from web UI...")
            logger.info("Stopping MediaMTX...")
            manager.mediamtx.stop()
            logger.info("Restarting MediaMTX...")
            manager.mediamtx.start(manager.cameras)
            logger.info("Server restarted successfully!")

        # Run restart in background thread
        restart_thread = threading.Thread(target=do_restart, daemon=True)
        restart_thread.start()

        return jsonify({'message': 'Server restart initiated'})

    @app.route('/api/stats')
    def get_stats():
        """Get CPU and memory usage for the app and its children using delta timings"""
        try:
            current_time = time.time()
            parent = psutil.Process(os.getpid())

            # Memory (snapshot)
            memory_info = parent.memory_info().rss
            # CPU Times (cumulative)
            total_cpu_time = parent.cpu_times().user + parent.cpu_times().system

            # Sum up all children recursively
            for child in parent.children(recursive=True):
                try:
                    memory_info += child.memory_info().rss
                    total_cpu_time += child.cpu_times().user + child.cpu_times().system
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Calculate delta since last request
            delta_time = current_time - app.stats_last_time
            delta_cpu = total_cpu_time - app.stats_last_cpu

            # Update baseline for next request
            app.stats_last_time = current_time
            app.stats_last_cpu = total_cpu_time

            # Normalization
            cpu_count = psutil.cpu_count() or 1
            if delta_time > 0:
                # percentage = (seconds_of_cpu / seconds_of_wallclock) * 100
                # Divided by cores to get 0-100% total system view
                cpu_percent = (delta_cpu / delta_time) * 100 / cpu_count
            else:
                cpu_percent = 0.0

            return jsonify({
                'cpu_percent': min(100.0, round(max(0.0, cpu_percent), 1)),
                'memory_mb': round(memory_info / (1024 * 1024), 1)
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/')
    def index():
        """Serve the main HTML page from static files"""
        response = send_from_directory(static_folder, 'index.html')
        # Add headers to prevent caching
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    @app.route('/api/cameras', methods=['GET'])
    def get_cameras():
        return jsonify([cam.to_dict() for cam in manager.cameras])

    @app.route('/api/cameras', methods=['POST'])
    @limiter.limit(RATE_LIMIT_CAMERA_CRUD)
    def add_camera():
        data = request.json
        try:
            camera = manager.add_camera(
                name=data['name'],
                host=data['host'],
                rtsp_port=data['rtspPort'],
                username=data.get('username', ''),
                password=data.get('password', ''),
                main_path=data['mainPath'],
                sub_path=data['subPath'],
                auto_start=data.get('autoStart', False),
                main_width=data.get('mainWidth', 1920),
                main_height=data.get('mainHeight', 1080),
                sub_width=data.get('subWidth', 640),
                sub_height=data.get('subHeight', 480),
                main_framerate=data.get('mainFramerate', 30),
                sub_framerate=data.get('subFramerate', 15),
                onvif_port=data.get('onvifPort'),
                onvif_username=data.get('onvifUsername', 'admin'),
                onvif_password=data.get('onvifPassword', 'admin'),
                transcode_sub=data.get('transcodeSub', False),
                transcode_main=data.get('transcodeMain', False),
                use_virtual_nic=data.get('useVirtualNic', False),
                parent_interface=data.get('parentInterface', ''),
                nic_mac=data.get('nicMac', ''),
                ip_mode=data.get('ipMode', 'dhcp'),
                static_ip=data.get('staticIp', ''),
                netmask=data.get('netmask', '24'),
                gateway=data.get('gateway', '')
            )
            return jsonify(camera.to_dict()), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/api/cameras/<int:camera_id>', methods=['PUT'])
    @limiter.limit(RATE_LIMIT_CAMERA_CRUD)
    def update_camera(camera_id):
        data = request.json
        try:
            camera = manager.update_camera(
                camera_id=camera_id,
                name=data['name'],
                host=data['host'],
                rtsp_port=data['rtspPort'],
                username=data.get('username', ''),
                password=data.get('password', ''),
                main_path=data['mainPath'],
                sub_path=data['subPath'],
                auto_start=data.get('autoStart', False),
                main_width=data.get('mainWidth', 1920),
                main_height=data.get('mainHeight', 1080),
                sub_width=data.get('subWidth', 640),
                sub_height=data.get('subHeight', 480),
                main_framerate=data.get('mainFramerate', 30),
                sub_framerate=data.get('subFramerate', 15),
                onvif_port=data.get('onvifPort'),
                onvif_username=data.get('onvifUsername', 'admin'),
                onvif_password=data.get('onvifPassword', 'admin'),
                transcode_sub=data.get('transcodeSub', False),
                transcode_main=data.get('transcodeMain', False),
                use_virtual_nic=data.get('useVirtualNic', False),
                parent_interface=data.get('parentInterface', ''),
                nic_mac=data.get('nicMac', ''),
                ip_mode=data.get('ipMode', 'dhcp'),
                static_ip=data.get('staticIp', ''),
                netmask=data.get('netmask', '24'),
                gateway=data.get('gateway', '')
            )
            if camera:
                return jsonify(camera.to_dict())
            return jsonify({'error': 'Camera not found'}), 404
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/api/cameras/<int:camera_id>', methods=['DELETE'])
    @limiter.limit(RATE_LIMIT_CAMERA_CRUD)
    def delete_camera(camera_id):
        if manager.delete_camera(camera_id):
            return '', 204
        return jsonify({'error': 'Camera not found'}), 404

    @app.route('/api/cameras/<int:camera_id>/start', methods=['POST'])
    def start_camera(camera_id):
        camera = manager.get_camera(camera_id)
        if camera:
            # Only restart MediaMTX if camera wasn't already running
            was_running = camera.status == "running"
            camera.start()
            manager.save_config()
            if not was_running:
                manager.mediamtx.restart(manager.cameras)
            return jsonify(camera.to_dict())
        return jsonify({'error': 'Camera not found'}), 404

    @app.route('/api/cameras/<int:camera_id>/stop', methods=['POST'])
    def stop_camera(camera_id):
        camera = manager.get_camera(camera_id)
        if camera:
            # Only restart MediaMTX if camera was actually running
            was_running = camera.status == "running"
            camera.stop()
            manager.save_config()
            if was_running:
                manager.mediamtx.restart(manager.cameras)
            return jsonify(camera.to_dict())
        return jsonify({'error': 'Camera not found'}), 404

    @app.route('/api/cameras/start-all', methods=['POST'])
    def start_all():
        manager.start_all()
        return jsonify([cam.to_dict() for cam in manager.cameras])

    @app.route('/api/cameras/stop-all', methods=['POST'])
    def stop_all():
        manager.stop_all()
        return jsonify([cam.to_dict() for cam in manager.cameras])

    @app.route('/api/cameras/<int:camera_id>/fetch-stream-info', methods=['POST'])
    def fetch_stream_info(camera_id):
        """Fetch stream information using FFprobe"""
        data = request.json
        stream_type = data.get('streamType', 'main')  # 'main' or 'sub'

        camera = manager.get_camera(camera_id)
        if not camera:
            return jsonify({'error': 'Camera not found'}), 404

        # Get the appropriate stream URL
        stream_url = camera.main_stream_url if stream_type == 'main' else camera.sub_stream_url

        try:
            # Use ffprobe to get stream information

            # Get ffprobe path (will download if needed)
            ffmpeg_manager = FFmpegManager()
            ffprobe_path = ffmpeg_manager.get_ffprobe_path()

            if not ffprobe_path:
                return jsonify({
                    'error': 'FFprobe not available and could not be downloaded automatically.',
                    'installUrl': 'https://ffmpeg.org/download.html'
                }), 400

            logger.debug("Using ffprobe: %s", ffprobe_path)
            logger.debug("Probing stream: %s", stream_url)

            # Run ffprobe to get stream info
            # Use TCP for better compatibility with cameras
            cmd = [
                ffprobe_path,
                '-v', 'error',
                '-rtsp_transport', 'tcp',  # Use TCP instead of UDP for better compatibility
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height,r_frame_rate',
                '-of', 'json',
                stream_url
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

            if result.returncode != 0:
                # Log the error for debugging
                logger.error("FFprobe failed with return code %d", result.returncode)
                logger.debug("stderr: %s", result.stderr)
                logger.debug("stdout: %s", result.stdout)

                # Provide helpful error messages based on common issues
                error_msg = 'Failed to probe stream.'
                troubleshooting = []

                if '5XX Server Error' in result.stderr:
                    troubleshooting.append('Camera connection limit might be reached (too many concurrent streams)')
                    troubleshooting.append('Reboot the camera if it is unresponsive')
                    troubleshooting.append('Verify the stream path/URL is correct')
                elif '401' in result.stderr or '403' in result.stderr:
                    troubleshooting.append('Check camera credentials (username/password)')
                    troubleshooting.append('verify the stream path is correct')
                elif 'Connection refused' in result.stderr or 'Connection timed out' in result.stderr:
                    troubleshooting.append('Check if camera IP address is correct')
                    troubleshooting.append('Verify camera is powered on and accessible')
                    troubleshooting.append('Check network connectivity')
                elif 'Invalid data found' in result.stderr:
                    troubleshooting.append('Stream path might be incorrect')
                    troubleshooting.append('Camera might not be streaming on this path')
                else:
                    troubleshooting.append('Verify stream URL is accessible')
                    troubleshooting.append('Check camera is not overloaded with connections')
                    troubleshooting.append('Try accessing the stream in VLC to confirm it works')

                return jsonify({
                    'error': error_msg,
                    'details': result.stderr,
                    'troubleshooting': troubleshooting,
                    'returnCode': result.returncode
                }), 400

            # Parse the JSON output
            import json as json_module
            probe_data = json_module.loads(result.stdout)

            if 'streams' not in probe_data or len(probe_data['streams']) == 0:
                return jsonify({'error': 'No video stream found'}), 400

            stream_info = probe_data['streams'][0]
            width = stream_info.get('width')
            height = stream_info.get('height')

            # Parse frame rate (format: "30/1" or "30000/1001")
            framerate = 30  # default
            r_frame_rate = stream_info.get('r_frame_rate', '30/1')
            if '/' in r_frame_rate:
                num, den = r_frame_rate.split('/')
                framerate = round(int(num) / int(den))

            return jsonify({
                'width': width,
                'height': height,
                'framerate': framerate,
                'streamType': stream_type
            })

        except subprocess.TimeoutExpired:
            return jsonify({'error': 'Stream probe timeout. Check if the camera is accessible.'}), 400
        except Exception as e:
            return jsonify({'error': f'Failed to fetch stream info: {str(e)}'}), 500

    @app.route('/api/cameras/<int:camera_id>/auto-start', methods=['POST'])
    def toggle_auto_start(camera_id):
        """Toggle auto-start setting for a camera"""
        data = request.json
        auto_start = data.get('autoStart', False)

        camera = manager.get_camera(camera_id)
        if not camera:
            return jsonify({'error': 'Camera not found'}), 404

        try:
            # Update auto-start setting
            camera.auto_start = auto_start
            manager.save_config()

            logger.info("Updated auto-start for %s: %s", camera.name, auto_start)

            return jsonify(camera.to_dict())
        except Exception as e:
            logger.error("Error updating auto-start: %s", e)
            return jsonify({'error': str(e)}), 500



    @app.route('/api/server/stop', methods=['POST'])
    def stop_server():
        """Stop the entire server"""
        def do_stop():
            import time
            import os
            time.sleep(2)  # Give time for response to be sent
            logger.info("Server stop requested from web UI...")
            logger.info("Stopping MediaMTX...")
            manager.mediamtx.stop()
            logger.info("Stopping all cameras...")
            for camera in manager.cameras:
                camera.stop()
            logger.info("Server stopped successfully!")
            logger.info("To restart, run the script again.")
            os._exit(0)  # Force exit

        # Run stop in background thread
        stop_thread = threading.Thread(target=do_stop, daemon=True)
        stop_thread.start()

        return jsonify({'message': 'Server stop initiated'})

    @app.route('/api/settings', methods=['GET'])
    @limiter.limit(RATE_LIMIT_SETTINGS)
    def get_settings():
        return jsonify(manager.load_settings())

    @app.route('/api/settings', methods=['POST'])
    @limiter.limit(RATE_LIMIT_SETTINGS)
    def save_settings():
        data = request.json
        try:
            settings = manager.save_settings(data)
            return jsonify(settings)
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/api/network/interfaces')
    def get_network_interfaces():
        """Get list of physical network interfaces (Linux only)"""
        if not LinuxNetworkManager.is_linux():
            return jsonify([])

        interfaces = LinuxNetworkManager.get_physical_interfaces()
        return jsonify(interfaces)

    return app
