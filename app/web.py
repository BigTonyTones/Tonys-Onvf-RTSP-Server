import json
import os
import sys
import psutil
import time
import functools
from datetime import timedelta
from flask import Flask, jsonify, request, session, redirect, url_for, make_response
from flask_cors import CORS

from .web_template import get_web_ui_html

from .ffmpeg_manager import FFmpegManager
from .onvif_client import ONVIFProber
from .linux_network import LinuxNetworkManager


def create_web_app(manager):
    """Create Flask web application"""
    app = Flask(__name__)
    CORS(app)
    
    # Session configuration
    app.secret_key = getattr(manager, 'secret_key', os.urandom(24))
    app.permanent_session_lifetime = timedelta(days=30)
    
    # Initialize stats tracking
    app.stats_last_time = time.time()
    app.stats_last_cpu = 0
    
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    # --- Authentication Decorator ---
    def login_required(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if not manager.auth_enabled:
                return f(*args, **kwargs)
                
            if 'authenticated' not in session:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function

    # --- Auth Routes ---
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if manager.is_setup_required():
            return redirect(url_for('setup'))
            
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            remember = request.form.get('remember') == 'true'
            
            if manager.verify_login(username, password):
                session.permanent = remember
                session['authenticated'] = True
                return jsonify({'success': True})
            return jsonify({'success': False, 'error': 'Invalid username or password'}), 401
            
        from .web_template import get_login_html
        return get_login_html()

    @app.route('/setup', methods=['GET', 'POST'])
    def setup():
        if not manager.is_setup_required():
            return redirect(url_for('login'))
            
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            if not username or not password:
                return jsonify({'success': False, 'error': 'Username and password required'}), 400
                
            manager.setup_user(username, password)
            session.permanent = True
            session['authenticated'] = True
            return jsonify({'success': True})
            
        from .web_template import get_setup_html
        return get_setup_html()

    @app.route('/setup/skip', methods=['POST'])
    def skip_setup():
        if not manager.is_setup_required():
            return jsonify({'success': False, 'error': 'Setup already completed'}), 400
            
        manager.skip_setup()
        session['authenticated'] = True # Mark as "logged in" for this session
        return jsonify({'success': True})

    @app.route('/logout')
    def logout():
        session.pop('authenticated', None)
        return redirect(url_for('login'))

    @app.route('/api/onvif/probe', methods=['POST'])
    @login_required
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
    @login_required
    def restart_server():
        """Restart the RTSP server"""
        def do_restart():
            import time
            time.sleep(2)  # Give time for response to be sent
            print("\n\n🔄 Server restart requested from web UI...")
            print("Stopping MediaMTX...")
            manager.mediamtx.stop()
            print("Restarting MediaMTX...")
            # Use global credentials if RTSP auth is enabled
            rtsp_user = manager.global_username if getattr(manager, 'rtsp_auth_enabled', False) else ''
            rtsp_pass = manager.global_password if getattr(manager, 'rtsp_auth_enabled', False) else ''
            manager.mediamtx.start(manager.cameras, manager.rtsp_port, rtsp_user, rtsp_pass)
            print("✓ Server restarted successfully!\n")
            
        # Run restart in background thread
        import threading
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
    @login_required
    def index():
        settings = manager.load_settings()
        response = app.make_response(get_web_ui_html(settings))
        # Add headers to prevent caching
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    @app.route('/api/cameras', methods=['GET'])
    @login_required
    def get_cameras():
        return jsonify([cam.to_dict() for cam in manager.cameras])
    
    @app.route('/api/cameras', methods=['POST'])
    @login_required
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
    @login_required
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
    @login_required
    def delete_camera(camera_id):
        if manager.delete_camera(camera_id):
            return '', 204
        return jsonify({'error': 'Camera not found'}), 404
    
    @app.route('/api/cameras/<int:camera_id>/start', methods=['POST'])
    @login_required
    def start_camera(camera_id):
        camera = manager.get_camera(camera_id)
        if camera:
            # Only restart MediaMTX if camera wasn't already running
            was_running = camera.status == "running"
            camera.start()
            manager.save_config()
            if not was_running:
                rtsp_user = manager.global_username if getattr(manager, 'rtsp_auth_enabled', False) else ''
                rtsp_pass = manager.global_password if getattr(manager, 'rtsp_auth_enabled', False) else ''
                manager.mediamtx.restart(manager.cameras, manager.rtsp_port, rtsp_user, rtsp_pass)
            return jsonify(camera.to_dict())
        return jsonify({'error': 'Camera not found'}), 404
    
    @app.route('/api/cameras/<int:camera_id>/stop', methods=['POST'])
    @login_required
    def stop_camera(camera_id):
        camera = manager.get_camera(camera_id)
        if camera:
            # Only restart MediaMTX if camera was actually running
            was_running = camera.status == "running"
            camera.stop()
            manager.save_config()
            if was_running:
                rtsp_user = manager.global_username if getattr(manager, 'rtsp_auth_enabled', False) else ''
                rtsp_pass = manager.global_password if getattr(manager, 'rtsp_auth_enabled', False) else ''
                manager.mediamtx.restart(manager.cameras, manager.rtsp_port, rtsp_user, rtsp_pass)
            return jsonify(camera.to_dict())
        return jsonify({'error': 'Camera not found'}), 404
    
    @app.route('/api/cameras/start-all', methods=['POST'])
    @login_required
    def start_all():
        manager.start_all()
        return jsonify([cam.to_dict() for cam in manager.cameras])
    
    @app.route('/api/cameras/stop-all', methods=['POST'])
    @login_required
    def stop_all():
        manager.stop_all()
        return jsonify([cam.to_dict() for cam in manager.cameras])
    
    @app.route('/api/cameras/<int:camera_id>/fetch-stream-info', methods=['POST'])
    @login_required
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
            
            print(f"  Using ffprobe: {ffprobe_path}")
            print(f"  Probing stream: {stream_url}")
            
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
                print(f"  ❌ FFprobe failed with return code {result.returncode}")
                print(f"  stderr: {result.stderr}")
                print(f"  stdout: {result.stdout}")
                
                # Provide helpful error messages based on common issues
                error_msg = 'Failed to probe stream.'
                troubleshooting = []
                
                if '5XX Server Error' in result.stderr:
                    troubleshooting.append('• Camera connection limit might be reached (too many concurrent streams)')
                    troubleshooting.append('• Reboot the camera if it is unresponsive')
                    troubleshooting.append('• Verify the stream path/URL is correct')
                elif '401' in result.stderr or '403' in result.stderr:
                    troubleshooting.append('• Check camera credentials (username/password)')
                    troubleshooting.append('• verify the stream path is correct')
                elif 'Connection refused' in result.stderr or 'Connection timed out' in result.stderr:
                    troubleshooting.append('• Check if camera IP address is correct')
                    troubleshooting.append('• Verify camera is powered on and accessible')
                    troubleshooting.append('• Check network connectivity')
                elif 'Invalid data found' in result.stderr:
                    troubleshooting.append('• Stream path might be incorrect')
                    troubleshooting.append('• Camera might not be streaming on this path')
                else:
                    troubleshooting.append('• Verify stream URL is accessible')
                    troubleshooting.append('• Check camera is not overloaded with connections')
                    troubleshooting.append('• Try accessing the stream in VLC to confirm it works')
                
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
    @login_required
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
            
            print(f"  ✓ Updated auto-start for {camera.name}: {auto_start}")
            
            return jsonify(camera.to_dict())
        except Exception as e:
            print(f"  ❌ Error updating auto-start: {e}")
            return jsonify({'error': str(e)}), 500
    

    
    @app.route('/api/server/stop', methods=['POST'])
    @login_required
    def stop_server():
        """Stop the entire server"""
        def do_stop():
            import time
            import os
            time.sleep(2)  # Give time for response to be sent
            print("\n\n⏹️ Server stop requested from web UI...")
            print("Stopping MediaMTX...")
            manager.mediamtx.stop()
            print("Stopping all cameras...")
            for camera in manager.cameras:
                camera.stop()
            print("✓ Server stopped successfully!")
            print("\nTo restart, run the script again.\n")
            os._exit(0)  # Force exit
        
        # Run stop in background thread
        import threading
        stop_thread = threading.Thread(target=do_stop, daemon=True)
        stop_thread.start()
        
        return jsonify({'message': 'Server stop initiated'})
    
    @app.route('/api/settings', methods=['GET'])
    @login_required
    def get_settings():
        return jsonify(manager.load_settings())
    
    @app.route('/api/settings', methods=['POST'])
    @login_required
    def save_settings():
        data = request.json
        try:
            settings = manager.save_settings(data)
            return jsonify(settings)
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    @app.route('/api/network/interfaces')
    @login_required
    def get_network_interfaces():
        """Get list of physical network interfaces (Linux only)"""
        if not LinuxNetworkManager.is_linux():
            return jsonify([])
        
        interfaces = LinuxNetworkManager.get_physical_interfaces()
        return jsonify(interfaces)
    
    return app
