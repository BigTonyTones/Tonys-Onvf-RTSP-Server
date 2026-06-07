import json
import os
import sys
from urllib.parse import quote
try:
    import psutil
except ImportError:
    psutil = None
import time
import functools
from datetime import timedelta
from flask import Flask, jsonify, request, session, redirect, url_for, make_response, send_file
from flask_cors import CORS

from .web_template import get_web_ui_html
from .diagnostics_template import get_diagnostics_html
from .ip_management_template import get_ip_management_html
from .config import AI_DEFAULT_MODEL, AI_CONFIDENCE_THRESHOLD, AI_MOTION_SENSITIVITY

from .ffmpeg_manager import FFmpegManager
from .onvif_client import ONVIFProber
from .linux_network import LinuxNetworkManager
from .utils import get_captured_logs
from .updater import UpdateChecker, check_for_updates, download_and_apply_update
import subprocess
import threading
import tempfile
import shutil


_cached_sys_info = None

def get_static_sys_info():
    global _cached_sys_info
    if _cached_sys_info is not None:
        return _cached_sys_info
    
    import platform
    os_type = platform.system()
    os_release = platform.release()
    cpu_count = 0
    total_mem_gb = 0.0
    cpu_model = "Unknown CPU"
    
    if os_type == "Linux":
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        os_type = line.split("=")[1].strip().strip('"')
                        os_release = ""
                        break
        except Exception:
            pass
    
    if psutil:
        try:
            cpu_count = psutil.cpu_count() or 0
            mem = psutil.virtual_memory()
            total_mem_gb = round(mem.total / (1024**3), 1)
        except Exception:
            pass
            
    # Resolve CPU model
    try:
        if os_type == "Windows":
            cpu_model = os.environ.get("PROCESSOR_IDENTIFIER", platform.processor() or "Intel/AMD CPU")
        elif os_type == "Darwin":
            import subprocess
            cpu_model = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).strip().decode()
        elif platform.system() == "Linux":
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    line_lower = line.lower()
                    if line_lower.startswith("model name"):
                        cpu_model = line.split(":", 1)[1].strip()
                        break
                    elif line_lower.startswith("hardware") or line_lower.startswith("model"):
                        cpu_model = line.split(":", 1)[1].strip()
            if cpu_model == "Unknown CPU":
                cpu_model = platform.processor() or "Linux CPU"
    except Exception:
        cpu_model = platform.processor() or "Unknown CPU"
        
    _cached_sys_info = {
        'os_type': os_type,
        'os_release': os_release,
        'cpu_count': cpu_count,
        'cpu_model': cpu_model,
        'total_memory_gb': total_mem_gb
    }
    return _cached_sys_info

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
    if getattr(manager, 'debug_mode', False):
        log.setLevel(logging.INFO)
    else:
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
            print("\n\nServer restart requested from web UI...")
            
            # Check if running on Linux
            if sys.platform.startswith('linux'):
                print("Linux detected - performing full server restart...")
                # Stop everything cleanly
                print("Stopping MediaMTX...")
                manager.mediamtx.stop()
                print("Stopping all cameras...")
                for camera in manager.cameras:
                    camera.stop()
                
                print("Killing server process...")
                # Exit with special code 42 to signal restart needed
                # This immediately releases all ports
                os._exit(42)
            else:
                # Windows - just restart MediaMTX
                print("Stopping MediaMTX...")
                manager.mediamtx.stop()
                print("Restarting MediaMTX...")
                # Use global credentials if RTSP auth is enabled
                rtsp_user = manager.global_username if getattr(manager, 'rtsp_auth_enabled', False) else ''
                rtsp_pass = manager.global_password if getattr(manager, 'rtsp_auth_enabled', False) else ''
                manager.mediamtx.start(manager.cameras, manager.rtsp_port, rtsp_user, rtsp_pass)
                print("Server restarted successfully!\n")
            
        # Run restart in background thread
        import threading
        restart_thread = threading.Thread(target=do_restart, daemon=True)
        restart_thread.start()
        
        return jsonify({'message': 'Server restart initiated'})

    @app.route('/api/server/reboot', methods=['POST'])
    @login_required
    def reboot_server():
        """Reboot the entire server (Linux only)"""
        # Only allow on Linux
        if not sys.platform.startswith('linux'):
            return jsonify({'error': 'Reboot is only supported on Linux'}), 400
        
        def do_reboot():
            import time
            time.sleep(2)  # Give time for response to be sent
            print("\n\nServer reboot requested from web UI...")
            print("Stopping MediaMTX...")
            manager.mediamtx.stop()
            print("Stopping all cameras...")
            for camera in manager.cameras:
                camera.stop()
            
            print("Initiating system reboot...")
            # Execute system reboot command
            subprocess.run(['sudo', 'reboot'], check=False)
            
        # Run reboot in background thread
        import threading
        reboot_thread = threading.Thread(target=do_reboot, daemon=True)
        reboot_thread.start()
        
        return jsonify({'message': 'Server reboot initiated'})


    @app.route('/api/stats')
    def get_stats():
        """Get CPU and memory usage for the app and its children using delta timings"""
        if psutil is None:
            return jsonify({'cpu_percent': 0.0, 'memory_mb': 0.0})

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
                cpu_percent = (delta_cpu / delta_time) * 100 / cpu_count
            else:
                cpu_percent = 0.0
            
            # System-wide metrics
            system_cpu = psutil.cpu_percent()
            virtual_mem = psutil.virtual_memory()
            system_mem_percent = virtual_mem.percent
            system_mem_used_gb = round(virtual_mem.used / (1024**3), 1)
            
            static_info = get_static_sys_info()
            
            server_uptime = round(current_time - parent.create_time())
            system_uptime = round(current_time - psutil.boot_time())
            
            return jsonify({
                'cpu_percent': min(100.0, round(max(0.0, cpu_percent), 1)),
                'memory_mb': round(memory_info / (1024 * 1024), 1),
                'system_cpu': system_cpu,
                'system_memory_percent': system_mem_percent,
                'system_memory_used_gb': system_mem_used_gb,
                'server_uptime': server_uptime,
                'system_uptime': system_uptime,
                'static_info': static_info
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/analytics')
    @login_required
    def get_analytics():
        """Get per-stream analytics from MediaMTX"""
        try:
            return jsonify(manager.analytics.get_analytics())
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

    @app.route('/gridfusion')
    @login_required
    def gridfusion():
        settings = manager.load_settings()
        grid_fusion_config = manager.get_grid_fusion()
        from .gridfusion_template import get_gridfusion_html
        return get_gridfusion_html(settings, grid_fusion_config)
    
    @app.route('/api/cameras/reorder', methods=['POST'])
    @login_required
    def reorder_cameras():
        data = request.json
        ordered_ids = data.get('ordered_ids', [])
        try:
            manager.reorder_cameras(ordered_ids)
            return jsonify({'status': 'success'})
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/api/cameras/reorder/reset', methods=['POST'])
    @login_required
    def reset_cameras_order():
        try:
            manager.reset_camera_order()
            return jsonify({'status': 'success'})
        except Exception as e:
            return jsonify({'error': str(e)}), 400

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
                disable_substream=data.get('disableSubstream', False),
                use_main_as_substream=data.get('useMainAsSubstream', False),
                enable_audio=data.get('enableAudio', False),
                transcode_main_audio=data.get('transcodeMainAudio', False),
                transcode_sub_audio=data.get('transcodeSubAudio', False),
                use_virtual_nic=data.get('useVirtualNic', False),
                vnic_keepalive=data.get('vnicKeepalive', False),
                parent_interface=data.get('parentInterface', ''),
                nic_mac=data.get('nicMac', ''),
                ip_mode=data.get('ipMode', 'dhcp'),
                static_ip=data.get('staticIp', ''),
                netmask=data.get('netmask', '24'),
                gateway=data.get('gateway', ''),
                uuid=data.get('uuid'),
                enable_event_forwarding=data.get('enableEventForwarding', False),
                physical_onvif_port=data.get('physicalOnvifPort', 80),
                onvif_forwarding_username=data.get('onvifForwardingUsername', ''),
                onvif_forwarding_password=data.get('onvifForwardingPassword', ''),
                event_source=data.get('eventSource', 'onvif'),
                ai_targets=data.get('aiTargets'),
                ai_model=data.get('aiModel', AI_DEFAULT_MODEL),
                send_smart_onvif_topics=data.get('sendSmartOnvifTopics', True)
            )
            if camera:
                camera.ai_motion_detection_enabled = data.get('aiMotionDetectionEnabled', True)
                camera.ai_motion_sensitivity = data.get('aiMotionSensitivity', AI_MOTION_SENSITIVITY)
                camera.ai_confidence_threshold = data.get('aiConfidenceThreshold', AI_CONFIDENCE_THRESHOLD)
                camera.ai_zone = data.get('aiZone', [])
                manager.save_config()
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
                disable_substream=data.get('disableSubstream', False),
                use_main_as_substream=data.get('useMainAsSubstream', False),
                enable_audio=data.get('enableAudio', False),
                transcode_main_audio=data.get('transcodeMainAudio', False),
                transcode_sub_audio=data.get('transcodeSubAudio', False),
                use_virtual_nic=data.get('useVirtualNic', False),
                vnic_keepalive=data.get('vnicKeepalive', False),
                parent_interface=data.get('parentInterface', ''),
                nic_mac=data.get('nicMac', ''),
                ip_mode=data.get('ipMode', 'dhcp'),
                static_ip=data.get('staticIp', ''),
                netmask=data.get('netmask', '24'),
                gateway=data.get('gateway', ''),
                uuid=data.get('uuid'),
                enable_event_forwarding=data.get('enableEventForwarding', False),
                physical_onvif_port=data.get('physicalOnvifPort', 80),
                onvif_forwarding_username=data.get('onvifForwardingUsername', ''),
                onvif_forwarding_password=data.get('onvifForwardingPassword', ''),
                event_source=data.get('eventSource', 'onvif'),
                ai_targets=data.get('aiTargets'),
                ai_model=data.get('aiModel', AI_DEFAULT_MODEL),
                send_smart_onvif_topics=data.get('sendSmartOnvifTopics', True)
            )
            if camera:
                camera.ai_motion_detection_enabled = data.get('aiMotionDetectionEnabled', True)
                camera.ai_motion_sensitivity = data.get('aiMotionSensitivity', AI_MOTION_SENSITIVITY)
                camera.ai_confidence_threshold = data.get('aiConfidenceThreshold', AI_CONFIDENCE_THRESHOLD)
                camera.ai_zone = data.get('aiZone', [])
                camera.send_smart_onvif_topics = data.get('sendSmartOnvifTopics', True)
                manager.save_config()
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
            # Start camera and restart mediamtx in a background thread (non-blocking)
            was_running = camera.status == "running"
            
            def _async_start():
                try:
                    camera.start()
                    manager.save_config()
                    if not was_running:
                        manager.restart_mediamtx()
                except Exception as e:
                    print(f"Error starting camera {camera_id} in background: {e}")
                    
            import threading
            threading.Thread(target=_async_start, daemon=True).start()
            
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
                manager.mediamtx.restart(manager.cameras, manager.rtsp_port, rtsp_user, rtsp_pass, manager.get_grid_fusion())
            return jsonify(camera.to_dict())
        return jsonify({'error': 'Camera not found'}), 404

    @app.route('/api/cameras/<int:camera_id>/test-event', methods=['POST'])
    @login_required
    def test_camera_event(camera_id):
        camera = manager.get_camera(camera_id)
        if camera:
            tag = None
            if request.is_json:
                tag = request.get_json().get('tag')
            if not tag:
                tag = request.args.get('tag')
            camera.trigger_test_event(tag=tag)
            return jsonify({'status': 'success', 'message': f'Test event for {tag or "generic"} triggered successfully'})
        return jsonify({'error': 'Camera not found'}), 404

    @app.route('/api/cameras/<int:camera_id>/copy-ai-settings', methods=['POST'])
    @login_required
    def copy_ai_settings(camera_id):
        source = manager.get_camera(camera_id)
        if not source:
            return jsonify({'error': 'Source camera not found'}), 404
        
        data = request.get_json()
        target_ids = data.get('targetCameraIds', [])
        
        updated = []
        for tid in target_ids:
            target = manager.get_camera(tid)
            if target and target.id != source.id:
                target.enable_event_forwarding = source.enable_event_forwarding
                target.event_source = source.event_source
                target.ai_model = source.ai_model
                target.ai_targets = list(source.ai_targets)
                target.ai_motion_detection_enabled = source.ai_motion_detection_enabled
                target.ai_motion_sensitivity = source.ai_motion_sensitivity
                target.ai_confidence_threshold = getattr(source, 'ai_confidence_threshold', 50)
                target.send_smart_onvif_topics = source.send_smart_onvif_topics
                # NOTE: ai_zone is NOT copied (per user request)
                updated.append(target.id)
        
        manager.save_config()
        return jsonify({'status': 'success', 'updated': updated})

    @app.route('/api/cameras/<int:camera_id>/snapshot', methods=['GET'])
    @login_required
    def get_ai_snapshot(camera_id):
        """Get a snapshot for AI zone drawing"""
        camera = manager.get_camera(camera_id)
        if not camera:
            return jsonify({'error': 'Camera not found'}), 404
        
        if camera.status == "running":
            rtsp_port = getattr(manager, 'rtsp_port', 8554)
            if getattr(manager, 'rtsp_auth_enabled', False):
                user = quote(getattr(manager, 'global_username', 'admin'))
                pw = quote(getattr(manager, 'global_password', 'admin'))
                stream_url = f"rtsp://{user}:{pw}@localhost:{rtsp_port}/{camera.path_name}_sub"
            else:
                stream_url = f"rtsp://localhost:{rtsp_port}/{camera.path_name}_sub"
        else:
            stream_url = camera.sub_stream_url or camera.main_stream_url
        
        ffmpeg_mgr = FFmpegManager()
        fd, path = tempfile.mkstemp(suffix='.jpg')
        os.close(fd)
        
        try:
            success, error = ffmpeg_mgr.capture_snapshot(stream_url, path)
            if success:
                with open(path, 'rb') as f:
                    content = f.read()
                response = make_response(content)
                response.headers['Content-Type'] = 'image/jpeg'
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                return response
            else:
                return jsonify({'error': error}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass

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
    
    @app.route('/api/cameras/reset-uuids', methods=['POST'])
    @login_required
    def reset_uuids():
        manager.reset_all_uuids()
        return jsonify({'status': 'success', 'message': 'All camera UUIDs have been reset.'})

    @app.route('/api/cameras/reset-macs', methods=['POST'])
    @login_required
    def reset_macs():
        manager.reset_all_macs()
        return jsonify({'status': 'success', 'message': 'All camera MAC addresses have been reset.'})

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
                print(f"  FFprobe failed with return code {result.returncode}")
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
            
            print(f"  Updated auto-start for {camera.name}: {auto_start}")
            
            return jsonify(camera.to_dict())
        except Exception as e:
            print(f"  Error updating auto-start: {e}")
            return jsonify({'error': str(e)}), 500
    

    
    @app.route('/api/server/stop', methods=['POST'])
    @login_required
    def stop_server():
        """Stop the entire server"""
        def do_stop():
            import time
            import os
            import signal
            import subprocess
            time.sleep(2)  # Give time for response to be sent
            print("\n\nServer stop requested from web UI...")
            print("Stopping MediaMTX...")
            manager.mediamtx.stop()
            print("Stopping all cameras...")
            for camera in manager.cameras:
                camera.stop()
            print("Server stopped successfully!")
            print("\nTo restart, run the script again.\n")
            
            # Check if running as systemd service
            try:
                if sys.platform.startswith('linux'):
                    # Check if we're running under systemd
                    result = subprocess.run(['systemctl', 'is-active', 'tonys-onvif'], 
                                          capture_output=True, text=True, timeout=2)
                    if result.returncode == 0 and result.stdout.strip() == 'active':
                        print("Detected systemd service. Stopping service...")
                        # Stop the systemd service properly
                        subprocess.run(['systemctl', 'stop', 'tonys-onvif'], timeout=5)
                        return
                    else:
                        # Not running as service, kill process group
                        os.killpg(os.getpgid(os.getpid()), signal.SIGTERM)
                else:
                    # On Windows, just exit normally
                    os._exit(0)
            except:
                # Fallback to regular exit
                os._exit(0)
        
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
    
    @app.route('/api/system/versions', methods=['GET'])
    @login_required
    def get_system_versions():
        """Get MediaMTX and FFmpeg versions"""
        try:
            from .ffmpeg_manager import FFmpegManager
            import shutil
            
            # Get MediaMTX version
            mediamtx_version = manager.mediamtx._get_latest_version()
            
            # Get FFmpeg version - use the same logic as the rest of the app
            ffmpeg_mgr = FFmpegManager()
            ffmpeg_version_tuple = ffmpeg_mgr.get_active_version()
            
            if ffmpeg_version_tuple:
                ffmpeg_version = f"{ffmpeg_version_tuple[0]}.{ffmpeg_version_tuple[1]}.{ffmpeg_version_tuple[2]}"
            else:
                ffmpeg_version = "Not installed"
            
            from .ai_device import select_device
            device = select_device()
            if device == 'cuda':
                ai_device_str = "NVIDIA GPU (CUDA)"
            elif device == 'mps':
                ai_device_str = "Apple Silicon GPU/ANE (MPS)"
            else:
                ai_device_str = "CPU (No acceleration)"

            return jsonify({
                'mediamtx': mediamtx_version,
                'ffmpeg': ffmpeg_version,
                'ai_device': ai_device_str
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/config/backup', methods=['GET'])
    @login_required
    def backup_config():
        """Download configuration backup"""
        try:
            return send_file(
                manager.config_file,
                mimetype='application/json',
                as_attachment=True,
                download_name='camera_config.json'
            )
        except Exception as e:
            return jsonify({'error': f'Failed to download config: {str(e)}'}), 500

    @app.route('/api/config/restore', methods=['POST'])
    @login_required
    def restore_config():
        """Restore configuration from backup"""
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        if file:
            try:
                # Read and validate JSON first
                content = file.read()
                try:
                    config_data = json.loads(content)
                except json.JSONDecodeError:
                    return jsonify({'error': 'Invalid JSON file'}), 400
                
                # Basic validation: Check for 'cameras' or 'settings' keys
                if 'cameras' not in config_data and 'settings' not in config_data:
                    return jsonify({'error': 'Invalid configuration file format'}), 400

                # Save file
                with open(manager.config_file, 'wb') as f:
                    f.write(content)
                
                # Reload config in manager
                manager.load_config()
                
                # Trigger server restart to apply all changes
                def do_restart():
                    time.sleep(1)
                    print("\n\nWait... Config restored. Restarting system...")
                    manager.mediamtx.stop()
                    
                    rtsp_user = manager.global_username if getattr(manager, 'rtsp_auth_enabled', False) else ''
                    rtsp_pass = manager.global_password if getattr(manager, 'rtsp_auth_enabled', False) else ''
                    manager.mediamtx.start(manager.cameras, manager.rtsp_port, rtsp_user, rtsp_pass, manager.get_grid_fusion())
                
                import threading
                threading.Thread(target=do_restart, daemon=True).start()
                
                return jsonify({'success': True, 'message': 'Configuration restored. Server restarting...'})
            except Exception as e:
                 return jsonify({'error': f'Failed to restore config: {str(e)}'}), 500

    @app.route('/api/logs', methods=['GET'])
    @login_required
    def get_logs():
        """Retrieve captured terminal logs"""
        return jsonify({'logs': get_captured_logs()})
    
    @app.route('/api/network/interfaces')
    @login_required
    def get_network_interfaces():
        """Get list of physical network interfaces (Linux only)"""
        if not LinuxNetworkManager.is_linux():
            return jsonify([])
        
        interfaces = LinuxNetworkManager.get_physical_interfaces()
        return jsonify(interfaces)
    
    # --- GridFusion Endpoints ---
    
    @app.route('/api/gridfusion', methods=['GET'])
    @login_required
    def get_gridfusion():
        """Get GridFusion configuration"""
        return jsonify(manager.get_grid_fusion())
    
    @app.route('/api/gridfusion', methods=['POST'])
    @login_required
    def save_gridfusion():
        """Save GridFusion configuration"""
        data = request.json
        try:
            result = manager.save_grid_fusion(data)
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/api/gridfusion/debug', methods=['GET'])
    @login_required
    def get_gridfusion_debug():
        """Get real-time debug info for GridFusion from MediaMTX logs"""
        # Get logs from mediamtx manager buffer
        with manager.mediamtx._log_lock:
            logs = list(manager.mediamtx.log_buffer)
        
        # Look for the last 'speed=' in the logs
        speed = "unknown"
        for line in reversed(logs):
            if "speed=" in line:
                import re
                # FFmpeg speed output looks like: speed=1.01x
                match = re.search(r'speed=\s*([\d.]+x)', line)
                if match:
                    speed = match.group(1)
                    break
        
        return jsonify({
            'speed': speed,
            'log_tail': logs[-10:] if logs else []
        })

    @app.route('/api/gridfusion/snapshot/<int:camera_id>')
    @login_required
    def get_camera_snapshot(camera_id):
        """Get a single snapshot from a camera stream"""
        camera = manager.get_camera(camera_id)
        if not camera:
            return jsonify({'error': 'Camera not found'}), 404
            
        # Optimization: If camera is running, pull from local MediaMTX instead of hitting real camera
        # This is MUCH faster and avoids overloading physical cameras
        if camera.status == "running":
            rtsp_port = getattr(manager, 'rtsp_port', 8554)
            # Include credentials if RTSP auth is enabled
            if getattr(manager, 'rtsp_auth_enabled', False):
                user = quote(getattr(manager, 'global_username', 'admin'))
                pw = quote(getattr(manager, 'global_password', 'admin'))
                stream_url = f"rtsp://{user}:{pw}@localhost:{rtsp_port}/{camera.path_name}_sub"
            else:
                stream_url = f"rtsp://localhost:{rtsp_port}/{camera.path_name}_sub"
            print(f"  Capture: Using local stream for {camera.name}")
        else:
            # Fallback to direct camera URL (use sub stream for speed)
            stream_url = camera.sub_stream_url
            print(f"  Capture: Using direct stream for {camera.name}")
        
        ffmpeg_mgr = FFmpegManager()
        
        # Create a temp file for the snapshot
        fd, path = tempfile.mkstemp(suffix='.jpg')
        os.close(fd)
        
        try:
            success, error = ffmpeg_mgr.capture_snapshot(stream_url, path)
            
            if success:
                # Send file content
                with open(path, 'rb') as f:
                    content = f.read()
                    
                response = make_response(content)
                response.headers['Content-Type'] = 'image/jpeg'
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                return response
            else:
                print(f"  Error capturing snapshot for {camera.name}: {error}")
                return jsonify({'error': error}), 500
            
        except Exception as e:
            print(f"  Error capturing snapshot for {camera.name}: {e}")
            return jsonify({'error': str(e)}), 500
        finally:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass

    
    # --- Update System Endpoints ---
    
    # Global variable to track update progress
    update_progress = {'status': 'idle', 'progress': 0, 'message': ''}
    
    @app.route('/api/updates/check', methods=['GET'])
    @login_required
    def check_updates():
        """Check for available updates from GitHub"""
        try:
            update_info = check_for_updates()
            if update_info:
                update_info['is_docker'] = os.path.exists('/.dockerenv')
                return jsonify(update_info)
            else:
                return jsonify({'error': 'Failed to check for updates'}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/updates/apply', methods=['POST'])
    @login_required
    def apply_update():
        """Download and apply update"""
        if os.path.exists('/.dockerenv'):
            return jsonify({'error': 'Self-updating is disabled in Docker. Please rebuild or pull the new image.'}), 400
            
        data = request.json
        download_url = data.get('download_url')
        
        if not download_url:
            return jsonify({'error': 'Download URL required'}), 400
        
        def progress_callback(status, progress):
            """Update progress for frontend polling"""
            update_progress['status'] = status
            update_progress['progress'] = progress
            if status == 'downloading':
                update_progress['message'] = f'Downloading update... {int(progress)}%'
            elif status == 'backing_up':
                update_progress['message'] = 'Creating backup...'
            elif status == 'extracting':
                update_progress['message'] = 'Extracting files...'
            elif status == 'applying':
                update_progress['message'] = 'Applying update...'
            elif status == 'complete':
                update_progress['message'] = 'Update complete! Restarting server...'
        
        def do_update():
            try:
                # Reset progress
                update_progress['status'] = 'starting'
                update_progress['progress'] = 0
                update_progress['message'] = 'Initializing update...'
                
                # Download and apply update
                success = download_and_apply_update(download_url, progress_callback)
                
                if success:
                    update_progress['status'] = 'complete'
                    update_progress['progress'] = 100
                    update_progress['message'] = 'Update complete! Restarting server...'
                    
                    # Wait a moment for the status to be read
                    time.sleep(2)
                    
                    # Restart server
                    print("\n\nUpdate applied successfully! Restarting server...")
                    manager.mediamtx.stop()
                    
                    # Exit with code 42 to trigger restart (Linux) or just exit (Windows)
                    if sys.platform.startswith('linux'):
                        os._exit(42)
                    else:
                        print("\nPlease restart the server manually to complete the update.")
                        os._exit(0)
                else:
                    update_progress['status'] = 'error'
                    update_progress['message'] = 'Update failed. Check logs for details.'
            except Exception as e:
                update_progress['status'] = 'error'
                update_progress['message'] = f'Update failed: {str(e)}'
                print(f"Update error: {e}")
        
        # Start update in background thread
        import threading
        update_thread = threading.Thread(target=do_update, daemon=True)
        update_thread.start()
        
        return jsonify({'message': 'Update started', 'status': 'started'})
    
    @app.route('/api/updates/status', methods=['GET'])
    @login_required
    def get_update_status():
        """Get current update progress"""
        return jsonify(update_progress)
    
    # --- Diagnostics Endpoints ---
    
    @app.route('/diagnostics')
    @login_required
    def diagnostics():
        """Serve the diagnostic tools page"""
        return get_diagnostics_html()
        
    @app.route('/api/diagnostics/ping', methods=['POST'])
    @login_required
    def diag_ping():
        """Run ping test"""
        data = request.json
        host = data.get('host')
        count = min(10, data.get('count', 4))
        
        if not host:
            return jsonify({'success': False, 'error': 'Host required'}), 400
            
        try:
            # -n on Windows, -c on Linux
            param = '-n' if sys.platform.startswith('win') else '-c'
            cmd = ['ping', param, str(count), host]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            return jsonify({
                'success': True, 
                'output': result.stdout if result.returncode == 0 else result.stderr
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/diagnostics/traceroute', methods=['POST'])
    @login_required
    def diag_traceroute():
        """Run traceroute test"""
        data = request.json
        host = data.get('host')
        
        if not host:
            return jsonify({'success': False, 'error': 'Host required'}), 400
            
        try:
            # tracert on Windows, traceroute on Linux
            cmd_name = 'tracert' if sys.platform.startswith('win') else 'traceroute'
            cmd = [cmd_name, host]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return jsonify({
                'success': True, 
                'output': result.stdout if result.returncode == 0 else result.stderr
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/diagnostics/port-check', methods=['POST'])
    @login_required
    def diag_port_check():
        """Check if a specific port is open"""
        import socket
        data = request.json
        host = data.get('host')
        port = int(data.get('port', 554))
        
        if not host:
            return jsonify({'success': False, 'error': 'Host required'}), 400
            
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((host, port))
            sock.close()
            return jsonify({'success': True, 'open': result == 0})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/diagnostics/stream-test', methods=['POST'])
    @login_required
    def diag_stream_test():
        """Test RTSP stream with ffprobe"""
        data = request.json
        url = data.get('url')
        
        if not url:
            return jsonify({'success': False, 'error': 'URL required'}), 400
            
        try:
            ffmpeg_mgr = FFmpegManager()
            ffprobe_exe = ffmpeg_mgr.get_ffprobe_path()
            
            if not ffprobe_exe:
                return jsonify({'success': False, 'error': 'FFprobe not found'}), 404
                
            cmd = [
                ffprobe_exe,
                '-v', 'error',  # Show errors but suppress warnings about missing reference frames
                '-rtsp_transport', 'tcp',
                '-analyzeduration', '5000000',  # Analyze up to 5 seconds of stream
                '-probesize', '5000000',  # Read up to 5MB to find stream info
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                # Combine stderr and stdout for better error context
                error_msg = result.stderr.strip() if result.stderr.strip() else result.stdout.strip()
                if not error_msg:
                    error_msg = f'Connection failed (exit code: {result.returncode})'
                
                # Log the full error for debugging
                print(f"  [Stream Test] FFprobe failed for URL: {url}")
                print(f"  [Stream Test] Return code: {result.returncode}")
                print(f"  [Stream Test] Stderr: {result.stderr}")
                print(f"  [Stream Test] Stdout: {result.stdout}")
                
                return jsonify({'success': False, 'error': error_msg}), 400
                
            import json as json_mod
            try:
                info = json_mod.loads(result.stdout)
            except json_mod.JSONDecodeError:
                return jsonify({
                    'success': False, 
                    'error': 'Failed to parse stream information. The camera may be sending an incomplete or corrupted stream.'
                }), 400
            
            # Check if we got any stream data
            if not info or 'streams' not in info or len(info.get('streams', [])) == 0:
                return jsonify({
                    'success': False, 
                    'error': 'No stream data received. The camera may need more time to send keyframes, or the stream path may be incorrect.'
                }), 400
            
            video_stream = next((s for s in info.get('streams', []) if s.get('codec_type') == 'video'), None)
            audio_stream = next((s for s in info.get('streams', []) if s.get('codec_type') == 'audio'), None)
            format_info = info.get('format', {})
            
            if not video_stream:
                return jsonify({
                    'success': False, 
                    'error': 'No video stream found in the response.'
                }), 400
            
            response_data = {
                'success': True,
                'raw': info,
                'video': video_stream,
                'audio': audio_stream,
                'format': format_info
            }
            
            if video_stream:
                response_data.update({
                    'width': video_stream.get('width'),
                    'height': video_stream.get('height'),
                    'framerate': video_stream.get('r_frame_rate'),
                    'codec': video_stream.get('codec_name'),
                    'profile': video_stream.get('profile'),
                    'pix_fmt': video_stream.get('pix_fmt')
                })
                
            return jsonify(response_data)
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/diagnostics/network-scan', methods=['POST'])
    @login_required
    def diag_network_scan():
        """Scan the local subnet for all devices using ping sweep + ARP table + vendor lookup + port probing"""
        import socket
        import threading
        import ipaddress
        from .mac_vendor import lookup_vendor, probe_ports

        data = request.json or {}
        subnet = data.get('subnet', '')  # optional manual override

        try:
            # Auto-detect local IP and subnet if not provided
            if not subnet:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                try:
                    s.connect(('8.8.8.8', 80))
                    local_ip = s.getsockname()[0]
                finally:
                    s.close()
                # Assume /24 subnet
                network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
            else:
                network = ipaddress.IPv4Network(subnet, strict=False)
                local_ip = str(list(network.hosts())[0])

            # Phase 1: Parallel ping sweep to populate ARP table
            pinged_hosts = set()
            ping_lock = threading.Lock()

            def ping_host(ip_str):
                try:
                    param = '-n' if sys.platform.startswith('win') else '-c'
                    timeout_flag = '-w' if sys.platform.startswith('win') else '-W'
                    timeout_val = '500' if sys.platform.startswith('win') else '1'
                    cmd = ['ping', param, '1', timeout_flag, timeout_val, ip_str]
                    result = subprocess.run(cmd, capture_output=True, timeout=3)
                    if result.returncode == 0:
                        with ping_lock:
                            pinged_hosts.add(ip_str)
                except Exception:
                    pass

            threads = []
            for host in network.hosts():
                t = threading.Thread(target=ping_host, args=(str(host),), daemon=True)
                threads.append(t)
                t.start()

            # Wait for all pings to complete (max ~4 seconds)
            for t in threads:
                t.join(timeout=5)

            # Phase 2: Read ARP table
            arp_entries = {}
            try:
                if sys.platform.startswith('win'):
                    result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=5)
                    import re
                    for line in result.stdout.splitlines():
                        match = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+([\da-fA-F]{2}[:-][\da-fA-F]{2}[:-][\da-fA-F]{2}[:-][\da-fA-F]{2}[:-][\da-fA-F]{2}[:-][\da-fA-F]{2})\s+(\w+)', line)
                        if match:
                            ip = match.group(1)
                            mac = match.group(2).replace('-', ':').upper()
                            entry_type = match.group(3)
                            if mac != 'FF:FF:FF:FF:FF:FF' and ip != '255.255.255.255':
                                arp_entries[ip] = {'mac': mac, 'type': entry_type}
                else:
                    # Try 'ip neigh' first (modern Linux), fallback to 'arp -a'
                    result = subprocess.run(['ip', 'neigh'], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        import re
                        for line in result.stdout.splitlines():
                            match = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+.*lladdr\s+([\da-fA-F:]+)', line)
                            if match:
                                ip = match.group(1)
                                mac = match.group(2).upper()
                                arp_entries[ip] = {'mac': mac, 'type': 'dynamic'}
                    else:
                        result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=5)
                        import re
                        for line in result.stdout.splitlines():
                            match = re.search(r'\((\d+\.\d+\.\d+\.\d+)\)\s+at\s+([\da-fA-F:]+)', line)
                            if match:
                                ip = match.group(1)
                                mac = match.group(2).upper()
                                arp_entries[ip] = {'mac': mac, 'type': 'dynamic'}
            except Exception:
                pass

            # Phase 3: Merge ping results + ARP
            all_ips = pinged_hosts | set(arp_entries.keys())
            # Filter to only IPs in our subnet
            all_ips = {ip for ip in all_ips if ipaddress.IPv4Address(ip) in network}

            # Phase 4: Parallel port probing + hostname resolution for all discovered IPs
            device_data = {}
            data_lock = threading.Lock()

            def enrich_device(ip_str):
                info = {}
                
                # Hostname resolution
                try:
                    hostname = socket.getfqdn(ip_str)
                    if hostname == ip_str:
                        hostname = socket.gethostbyaddr(ip_str)[0]
                    info['hostname'] = hostname
                except Exception:
                    info['hostname'] = ''
                
                # Port probing (only for reachable hosts to save time)
                if ip_str in pinged_hosts:
                    port_info = probe_ports(ip_str, timeout=0.4)
                    info['open_ports'] = port_info['open_ports']
                    info['device_type'] = port_info['device_type']
                else:
                    info['open_ports'] = []
                    info['device_type'] = ''
                
                with data_lock:
                    device_data[ip_str] = info

            enrich_threads = []
            for ip in all_ips:
                t = threading.Thread(target=enrich_device, args=(ip,), daemon=True)
                enrich_threads.append(t)
                t.start()
            
            for t in enrich_threads:
                t.join(timeout=8)

            # Phase 5: Build final device list
            devices = []
            for ip in sorted(all_ips, key=lambda x: ipaddress.IPv4Address(x)):
                mac = arp_entries.get(ip, {}).get('mac', '')
                entry_type = arp_entries.get(ip, {}).get('type', '')
                enriched = device_data.get(ip, {})

                # MAC vendor lookup
                vendor = lookup_vendor(mac)
                
                # Determine if this is the local machine
                is_self = (ip == local_ip)

                devices.append({
                    'ip': ip,
                    'mac': mac,
                    'hostname': enriched.get('hostname', ''),
                    'vendor': vendor,
                    'device_type': enriched.get('device_type', ''),
                    'open_ports': enriched.get('open_ports', []),
                    'type': entry_type,
                    'is_self': is_self,
                    'reachable': ip in pinged_hosts,
                })

            return jsonify({
                'success': True,
                'devices': devices,
                'count': len(devices),
                'local_ip': local_ip,
                'subnet': str(network),
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/diagnostics/onvif-scan', methods=['POST'])
    @login_required
    def diag_onvif_scan():
        """Scan the local network for ONVIF cameras using WS-Discovery"""
        data = request.json or {}
        timeout = min(10, int(data.get('timeout', 4)))
        
        try:
            prober = ONVIFProber()
            devices = prober.network_scan(timeout=timeout)
            return jsonify({'success': True, 'devices': devices, 'count': len(devices)})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/diagnostics/onvif', methods=['POST'])
    @login_required
    def diag_onvif():
        """Connect to an ONVIF camera and return detailed diagnostic info"""
        data = request.json
        host = data.get('host')
        port = int(data.get('port', 80))
        username = data.get('username')
        password = data.get('password')
        
        if not host or not username or not password:
            return jsonify({'success': False, 'error': 'Host, username, and password are required'}), 400
            
        prober = ONVIFProber()
        result = prober.get_detailed_diagnostics(host, port, username, password)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400

    @app.route('/api/diagnostics/ffmpeg-info')
    @login_required
    def diag_ffmpeg_info():
        """Get full FFmpeg version info"""
        try:
            ffmpeg_mgr = FFmpegManager()
            ffmpeg_exe = ffmpeg_mgr.get_ffmpeg_path()
            
            if not ffmpeg_exe:
                return jsonify({'success': False, 'error': 'FFmpeg not found'}), 404
            
            result = subprocess.run([ffmpeg_exe, '-version'], capture_output=True, text=True)
            return jsonify({
                'success': True,
                'version': result.stdout.split('\n')[0],
                'full_output': result.stdout
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/diagnostics/system-info')
    @login_required
    def diag_system_info():
        """Get detailed system information"""
        try:
            import platform
            
            # Fetch versions
            ffmpeg_mgr = FFmpegManager()
            ff_ver = ffmpeg_mgr.get_active_version()
            ff_ver_str = f"{ff_ver[0]}.{ff_ver[1]}.{ff_ver[2]}" if ff_ver else "Unknown"
            
            mm_ver = manager.mediamtx._get_latest_version()
            
            system_info = {
                'success': True,
                'platform': f"{platform.system()} {platform.release()} ({platform.machine()})",
                'python_version': sys.version.split()[0],
                'mediamtx_version': mm_ver,
                'ffmpeg_version': ff_ver_str
            }
            
            if psutil:
                mem = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                system_info.update({
                    'cpu_count': psutil.cpu_count(),
                    'total_memory': round(mem.total / (1024**3), 2),
                    'available_memory': round(mem.available / (1024**3), 2),
                    'disk_usage': disk.percent
                })
            else:
                system_info.update({
                    'cpu_count': 'Unknown',
                    'total_memory': 'Unknown',
                    'available_memory': 'Unknown',
                    'disk_usage': 0
                })
                
            return jsonify(system_info)
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/diagnostics/ai-info')
    @login_required
    def diag_ai_info():
        """Get detailed AI and YOLO environment/metrics info"""
        try:
            from .ai_device import select_device, _AI_MODELS
            
            # Check packages
            yolo_installed = False
            torch_installed = False
            yolo_version = "Not Installed"
            torch_version = "Not Installed"
            cuda_available = False
            cuda_device_count = 0
            cuda_device_name = "N/A"
            mps_available = False
            torch_threads = "N/A"
            
            try:
                import ultralytics
                yolo_installed = True
                yolo_version = ultralytics.__version__
            except ImportError:
                pass
                
            try:
                import torch
                torch_installed = True
                torch_version = torch.__version__
                cuda_available = torch.cuda.is_available()
                if cuda_available:
                    cuda_device_count = torch.cuda.device_count()
                    try:
                        cuda_device_name = torch.cuda.get_device_name(0)
                    except Exception:
                        cuda_device_name = "Unknown CUDA Device"
                mps_available = hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
                torch_threads = torch.get_num_threads()
            except ImportError:
                pass
                
            selected_device = select_device()
            
            # Active cached models
            cached_models = list(_AI_MODELS.keys())
            
            # Active camera AI threads
            active_ai_cameras = []
            for cam in manager.cameras:
                if getattr(cam, '_ai_running', False):
                    active_ai_cameras.append({
                        'name': cam.name,
                        'model': cam.ai_model,
                        'targets': cam.ai_targets,
                        'fps': getattr(cam, 'ai_fps_measurement', 0.0),
                        'inference_count': getattr(cam, 'ai_inference_count', 0),
                        'avg_latency_ms': round(getattr(cam, 'ai_avg_inference_latency', 0.0) * 1000, 1),
                        'last_detection': getattr(cam, 'ai_last_detection', [])
                    })
                    
            from .config import AI_DEFAULT_MODEL, AI_CONFIDENCE_THRESHOLD, AI_MOTION_SENSITIVITY, AI_INFERENCE_FRAME_WIDTH, AI_COOLDOWN_SECONDS, AI_TARGET_INTERVAL
            
            return jsonify({
                'success': True,
                'yolo_installed': yolo_installed,
                'yolo_version': yolo_version,
                'torch_installed': torch_installed,
                'torch_version': torch_version,
                'cuda_available': cuda_available,
                'cuda_device_count': cuda_device_count,
                'cuda_device_name': cuda_device_name,
                'mps_available': mps_available,
                'torch_threads': torch_threads,
                'selected_device': selected_device,
                'cached_models': cached_models,
                'active_ai_cameras': active_ai_cameras,
                'config': {
                    'default_model': AI_DEFAULT_MODEL,
                    'confidence_threshold': AI_CONFIDENCE_THRESHOLD,
                    'motion_sensitivity': AI_MOTION_SENSITIVITY,
                    'inference_width': AI_INFERENCE_FRAME_WIDTH,
                    'cooldown_seconds': AI_COOLDOWN_SECONDS,
                    'target_interval': AI_TARGET_INTERVAL
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/diagnostics/rtsp-analyzer', methods=['POST'])
    @login_required
    def diag_rtsp_analyzer():
        """Probes RTSP stream for latency, frame drops, and network speed"""
        try:
            data = request.json or {}
            camera_id = data.get('camera_id')
            url = data.get('url')
            
            if camera_id is not None:
                cam = manager.get_camera(int(camera_id))
                if cam:
                    url = cam.main_stream_url
                    
            if not url:
                return jsonify({'success': False, 'error': 'No camera_id or stream URL provided'}), 400
                
            ffmpeg_mgr = FFmpegManager()
            ffmpeg_exe = ffmpeg_mgr.get_ffmpeg_path()
            if not ffmpeg_exe:
                return jsonify({'success': False, 'error': 'FFmpeg executable not found'}), 404
                
            # Construct a test command that copies frames to null for 3 seconds
            cmd = [
                ffmpeg_exe,
                '-y',
                '-rtsp_transport', 'tcp',
                '-i', url,
                '-t', '3',
                '-f', 'null',
                '-'
            ]
            
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            duration = time.time() - start_time
            
            stderr = result.stderr or ""
            
            fps = 0.0
            speed = 1.0
            frame_count = 0
            dropped_frames = 0
            dup_frames = 0
            bitrate_kbps = 0.0
            
            import re
            frame_match = re.search(r'frame=\s*(\d+)', stderr)
            fps_match = re.search(r'fps=\s*([\d\.]+)', stderr)
            speed_match = re.search(r'speed=\s*([\d\.]+)x', stderr)
            drop_match = re.search(r'drop=\s*(\d+)', stderr)
            dup_match = re.search(r'dup=\s*(\d+)', stderr)
            bitrate_match = re.search(r'bitrate=\s*([\d\.]+)kbits/s', stderr)
            
            if frame_match:
                frame_count = int(frame_match.group(1))
            if fps_match:
                fps = float(fps_match.group(1))
            if speed_match:
                speed = float(speed_match.group(1))
            if drop_match:
                dropped_frames = int(drop_match.group(1))
            if dup_match:
                dup_frames = int(dup_match.group(1))
            if bitrate_match:
                bitrate_kbps = float(bitrate_match.group(1))
                
            stream_health = "Excellent"
            if dropped_frames > 5 or speed < 0.90:
                stream_health = "Poor (Frame drops/slowdowns detected)"
            elif dropped_frames > 0 or speed < 0.98:
                stream_health = "Fair (Minor jitter/dropped frames)"
                
            return jsonify({
                'success': True,
                'health': stream_health,
                'connect_time_seconds': round(duration, 2),
                'fps': fps,
                'speed': f"{speed}x",
                'frames_probed': frame_count,
                'dropped_frames': dropped_frames,
                'duplicated_frames': dup_frames,
                'bitrate_kbps': bitrate_kbps,
                'raw_stderr': stderr[-1500:]
            })
        except subprocess.TimeoutExpired:
            return jsonify({'success': False, 'error': 'Connection to RTSP stream timed out (10s limit)'}), 504
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/diagnostics/bandwidth-monitor', methods=['GET'])
    @login_required
    def diag_bandwidth_monitor():
        """Measures network interface bandwidth RX/TX rates"""
        try:
            if not psutil:
                return jsonify({'success': False, 'error': 'psutil library not available'}), 500
                
            io1 = psutil.net_io_counters(pernic=True)
            time.sleep(1.0)
            io2 = psutil.net_io_counters(pernic=True)
            
            interfaces = []
            for nic, counters in io2.items():
                if nic in io1:
                    prev = io1[nic]
                    rx_speed = counters.bytes_recv - prev.bytes_recv
                    tx_speed = counters.bytes_sent - prev.bytes_sent
                    
                    if rx_speed == 0 and tx_speed == 0 and counters.bytes_recv == 0:
                        continue
                        
                    interfaces.append({
                        'interface': nic,
                        'rx_speed_kbps': round(rx_speed / 1024, 1),
                        'tx_speed_kbps': round(tx_speed / 1024, 1),
                        'rx_total_mb': round(counters.bytes_recv / (1024*1024), 1),
                        'tx_total_mb': round(counters.bytes_sent / (1024*1024), 1)
                    })
                    
            return jsonify({
                'success': True,
                'interfaces': interfaces,
                'timestamp': time.time()
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/diagnostics/transcode-calculator', methods=['POST'])
    @login_required
    def diag_transcode_calculator():
        """Runs a mock transcode test to calculate transcoding speed and resource load"""
        try:
            data = request.json or {}
            camera_id = data.get('camera_id')
            encoder = data.get('encoder', 'libx264')
            
            if not camera_id:
                return jsonify({'success': False, 'error': 'camera_id is required'}), 400
                
            cam = manager.get_camera(int(camera_id))
            if not cam:
                return jsonify({'success': False, 'error': f'Camera ID {camera_id} not found'}), 404
                
            url = cam.main_stream_url
            
            ffmpeg_mgr = FFmpegManager()
            ffmpeg_exe = ffmpeg_mgr.get_ffmpeg_path()
            if not ffmpeg_exe:
                return jsonify({'success': False, 'error': 'FFmpeg executable not found'}), 404
                
            cmd = [
                ffmpeg_exe,
                '-y',
                '-rtsp_transport', 'tcp',
                '-i', url,
                '-t', '4',
                '-c:v', encoder
            ]
            
            # h264_videotoolbox and h264_vaapi do not support the generic -preset argument in FFmpeg
            if encoder not in ('h264_videotoolbox', 'h264_vaapi'):
                cmd.extend(['-preset', 'veryfast' if encoder == 'libx264' else 'fast'])
                
            cmd.extend(['-f', 'null', '-'])
            
            start_time = time.time()
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            cpu_samples = []
            if psutil:
                for _ in range(2):
                    cpu_samples.append(psutil.cpu_percent(interval=1.0))
            else:
                time.sleep(2.0)
                
            try:
                stdout, stderr = proc.communicate(timeout=6)
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()
                
            duration = time.time() - start_time
            stderr = stderr or ""
            
            import re
            fps_match = re.search(r'fps=\s*([\d\.]+)', stderr)
            speed_match = re.search(r'speed=\s*([\d\.]+)x', stderr)
            frame_match = re.search(r'frame=\s*(\d+)', stderr)
            
            fps = float(fps_match.group(1)) if fps_match else 0.0
            speed = float(speed_match.group(1)) if speed_match else 0.0
            frames = int(frame_match.group(1)) if frame_match else 0
            
            avg_cpu = round(sum(cpu_samples) / len(cpu_samples), 1) if cpu_samples else 0.0
            success = proc.returncode == 0 and frames > 0
            
            status_msg = "Success"
            if not success:
                status_msg = "Failed (Check FFmpeg output for driver/encoder error)"
            elif speed < 1.0:
                status_msg = "Slow (Transcoding speed is below 1.0x - stream will lag in real-time!)"
            elif speed >= 1.0:
                status_msg = "Optimal (Can handle real-time transcoding)"
                
            return jsonify({
                'success': True,
                'status': status_msg,
                'encoder_used': encoder,
                'fps': fps,
                'speed': f"{speed}x",
                'frames_transcoded': frames,
                'probed_duration_seconds': round(duration, 2),
                'cpu_load_percent': avg_cpu if psutil else 'N/A',
                'return_code': proc.returncode,
                'raw_stderr': stderr[-1500:]
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/diagnostics/storage-check', methods=['GET'])
    @login_required
    def diag_storage_check():
        """Benchmarks read/write speeds of the storage disk and reports capacity"""
        try:
            from .config import DATA_DIR
            
            total_gb = 0.0
            free_gb = 0.0
            used_percent = 0.0
            
            if psutil:
                disk = psutil.disk_usage(DATA_DIR)
                total_gb = round(disk.total / (1024**3), 1)
                free_gb = round(disk.free / (1024**3), 1)
                used_percent = disk.percent
            else:
                if hasattr(os, 'statvfs'):
                    st = os.statvfs(DATA_DIR)
                    free_gb = round((st.f_bavail * st.f_frsize) / (1024**3), 1)
                    total_gb = round((st.f_blocks * st.f_frsize) / (1024**3), 1)
                    used_percent = round((1 - free_gb/total_gb)*100, 1) if total_gb > 0 else 0
                    
            test_file = os.path.join(DATA_DIR, ".storage_bench.tmp")
            data_size_mb = 20
            payload = os.urandom(data_size_mb * 1024 * 1024)
            
            t0 = time.time()
            with open(test_file, 'wb') as f:
                f.write(payload)
                f.flush()
                try:
                    os.fsync(f.fileno())
                except:
                    pass
            write_duration = time.time() - t0
            write_speed = round(data_size_mb / write_duration, 1) if write_duration > 0 else 0.0
            
            t0 = time.time()
            with open(test_file, 'rb') as f:
                read_payload = f.read()
            read_duration = time.time() - t0
            read_speed = round(data_size_mb / read_duration, 1) if read_duration > 0 else 0.0
            
            if os.path.exists(test_file):
                os.remove(test_file)
                
            rating = "Excellent (SSD/NVMe)"
            if write_speed < 15.0 or read_speed < 30.0:
                rating = "Poor (USB 2.0 or failing HDD)"
            elif write_speed < 50.0 or read_speed < 80.0:
                rating = "Fair (Standard HDD or slow network share)"
                
            return jsonify({
                'success': True,
                'storage_path': os.path.abspath(DATA_DIR),
                'total_gb': total_gb,
                'free_gb': free_gb,
                'used_percent': used_percent,
                'write_speed_mbs': write_speed,
                'read_speed_mbs': read_speed,
                'performance_rating': rating
            })
        except Exception as e:
            test_file = os.path.join(DATA_DIR, ".storage_bench.tmp")
            if os.path.exists(test_file):
                try:
                    os.remove(test_file)
                except:
                    pass
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/server/restart', methods=['POST'])
    @login_required
    def server_restart():
        """Restart the application"""
        import threading
        def do_restart():
            import signal
            time.sleep(1)
            print("\n\nServer restart requested via UI...")
            manager.mediamtx.stop()
            for camera in manager.cameras:
                camera.stop()
            # Exit with code 42 to trigger restart (Linux) or just exit (Windows)
            if sys.platform.startswith('linux'):
                os._exit(42)
            else:
                os._exit(0)
        
        threading.Thread(target=do_restart, daemon=True).start()
        return jsonify({'success': True, 'message': 'Restarting...'})

    @app.route('/api/server/reboot', methods=['POST'])
    @login_required
    def server_reboot():
        """Reboot the host machine (Linux only)"""
        if not sys.platform.startswith('linux'):
            return jsonify({'success': False, 'error': 'Reboot is only supported on Linux'}), 400
            
        import threading
        def do_reboot():
            time.sleep(1)
            print("\n\nSystem reboot requested via UI...")
            manager.mediamtx.stop()
            # Send the command to reboot
            os.system('sudo reboot')
            
        threading.Thread(target=do_reboot, daemon=True).start()
        return jsonify({'success': True, 'message': 'Rebooting system...'})
    
    @app.route('/ip-management')
    @login_required
    def ip_management():
        whitelist = manager.get_ip_whitelist()
        return get_ip_management_html(whitelist)

    @app.route('/api/sessions', methods=['GET'])
    @login_required
    def get_sessions():
        return jsonify(manager.get_active_sessions())

    @app.route('/api/settings/whitelist', methods=['POST'])
    @login_required
    def save_whitelist():
        data = request.json
        whitelist = data.get('whitelist', [])
        try:
            manager.save_ip_whitelist(whitelist)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/auth', methods=['POST'])
    def mediamtx_auth():
        """Handle authentication requests from MediaMTX"""
        try:
            data = request.json
            if not data:
                return jsonify({'error': 'Invalid request'}), 400
            
            client_ip = data.get('ip', '')
            
            # Normalize IPv6-mapped IPv4 addresses (e.g., ::ffff:127.0.0.1)
            if client_ip.startswith('::ffff:'):
                client_ip = client_ip.replace('::ffff:', '')
            
            user = data.get('user', '')
            password = data.get('password', '')
            
            if manager.debug_mode:
                 print(f"  [RTSP Auth Check] IP: {client_ip}, Path: {data.get('path')}, User: {user}")

            # 1. ALWAYS allow whitelisted IPs
            if manager.is_ip_whitelisted(client_ip):
                if manager.debug_mode:
                    print(f"  [RTSP] Auth bypass for whitelisted IP: {client_ip}")
                return '', 200
                
            # 2. Allow local loopback connections
            if client_ip in ['127.0.0.1', '127.0.1.1', '::1', 'localhost']:
                 if manager.debug_mode:
                     print(f"  [RTSP] Local bypass granted for {client_ip}")
                 return '', 200

            # 3. Check if global RTSP auth is enabled
            if not getattr(manager, 'rtsp_auth_enabled', False):
                return '', 200
                
            # 4. Validate credentials
            if user == manager.global_username and password == manager.global_password:
                return '', 200
                
            # print(f"  Auth: Denied for {user} from {client_ip}")
            return jsonify({'error': 'Unauthorized'}), 401
            
        except Exception as e:
            print(f"  Error in MediaMTX auth hook: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/onvif/events', methods=['GET'])
    @login_required
    def get_onvif_events():
        events = getattr(manager, 'onvif_events', [])
        return jsonify(events)

    @app.route('/api/onvif/events/clear', methods=['POST'])
    @login_required
    def clear_onvif_events():
        if hasattr(manager, 'onvif_events'):
            manager.onvif_events = []
        for cam in manager.cameras:
            if hasattr(cam, 'event_logs'):
                cam.event_logs = []
        return jsonify({'status': 'success'})

    # --- Local AI Dependancy Checker & Installer ---
    class AIInstaller:
        def __init__(self):
            import threading
            self.status = "idle"  # idle, installing, success, failed
            self.log = []
            self.lock = threading.Lock()
            self._thread = None

        def start_install(self, mode="cpu"):
            with self.lock:
                if self.status in ("installing", "uninstalling"):
                    return False
                self.status = "installing"
                self.log = ["Starting installation..."]
                import threading
                self._thread = threading.Thread(target=self._run_install, args=(mode,), daemon=True)
                self._thread.start()
                return True

        def start_uninstall(self):
            with self.lock:
                if self.status in ("installing", "uninstalling"):
                    return False
                self.status = "uninstalling"
                self.log = ["Starting uninstallation..."]
                import threading
                self._thread = threading.Thread(target=self._run_uninstall, daemon=True)
                self._thread.start()
                return True

        def _run_cmd(self, cmd, custom_env):
            import subprocess
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    env=custom_env
                )
                
                for line in iter(process.stdout.readline, ''):
                    line_str = line.strip()
                    if line_str:
                        with self.lock:
                            self.log.append(line_str)
                            if len(self.log) > 1000:
                                self.log.pop(0)
                                
                process.stdout.close()
                return process.wait()
            except Exception as e:
                with self.lock:
                    self.log.append(f"Command execution error: {str(e)}")
                return -1

        def _run_install(self, mode="cpu"):
            import shutil
            local_tmp = None
            try:
                import sys
                import os
                
                # Get the root directory of the application
                app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                local_tmp = os.path.join(app_dir, "tmp")
                os.makedirs(local_tmp, exist_ok=True)
                
                try:
                    os.chmod(local_tmp, 0o777)
                except Exception:
                    pass

                # Copy environment and override temp variables to use local workspace directory (has 19GB free)
                custom_env = os.environ.copy()
                custom_env["TMPDIR"] = local_tmp
                custom_env["TEMP"] = local_tmp
                custom_env["TMP"] = local_tmp
                
                with self.lock:
                    self.log.append("Starting installation...")
                    self.log.append(f"Redirecting pip temporary directory to: {local_tmp}")
                    self.log.append(f"Selected PyTorch backend: {mode}")

                # Step 1: Install PyTorch with the selected backend
                if mode == "cuda":
                    with self.lock:
                        self.log.append("Installing PyTorch with NVIDIA CUDA support (~2.5GB download)...")
                    # Try to detect CUDA version via nvidia-smi
                    torch_index = "https://download.pytorch.org/whl/cu121"
                    try:
                        import subprocess as _sp
                        nv = _sp.run(["nvidia-smi"], capture_output=True, text=True, timeout=10)
                        if nv.returncode == 0:
                            import re
                            m = re.search(r'CUDA Version:\s+([\d]+)', nv.stdout)
                            if m:
                                cuda_major = int(m.group(1))
                                if cuda_major >= 13:
                                    torch_index = "https://download.pytorch.org/whl/cu130"
                                    with self.lock:
                                        self.log.append(f"Detected CUDA {cuda_major}.x — using cu130 wheels")
                                else:
                                    with self.lock:
                                        self.log.append(f"Detected CUDA {cuda_major}.x — using cu121 wheels")
                    except Exception:
                        with self.lock:
                            self.log.append("Could not detect CUDA version, defaulting to cu121")
                    cmd_torch = [sys.executable, "-m", "pip", "install", "--no-cache-dir",
                                 "torch", "torchvision", "torchaudio", "--index-url", torch_index]
                elif mode == "mps":
                    with self.lock:
                        self.log.append("Installing PyTorch with Apple Silicon auto-detect...")
                    cmd_torch = [sys.executable, "-m", "pip", "install", "--no-cache-dir",
                                 "torch", "torchvision", "torchaudio"]
                else:
                    with self.lock:
                        self.log.append("Installing PyTorch CPU-only (~200MB download)...")
                    cmd_torch = [sys.executable, "-m", "pip", "install", "--no-cache-dir",
                                 "torch", "torchvision", "torchaudio",
                                 "--index-url", "https://download.pytorch.org/whl/cpu"]

                rc = self._run_cmd(cmd_torch, custom_env)
                if rc != 0:
                    with self.lock:
                        self.status = "failed"
                        self.log.append(f"Failed to install PyTorch (exit code {rc})")
                    return

                # Step 2: Install ultralytics
                with self.lock:
                    self.log.append("Installing ultralytics (YOLO framework)...")
                cmd_ultra = [sys.executable, "-m", "pip", "install", "--no-cache-dir", "ultralytics"]
                rc = self._run_cmd(cmd_ultra, custom_env)
                if rc != 0:
                    with self.lock:
                        self.status = "failed"
                        self.log.append(f"Failed to install ultralytics (exit code {rc})")
                    return

                # Step 3: Uninstall opencv-python (GUI version) to prevent libGL conflict
                cmd_un = [sys.executable, "-m", "pip", "uninstall", "-y", "opencv-python"]
                self._run_cmd(cmd_un, custom_env)

                # Step 4: Install opencv-python-headless
                cmd_head = [sys.executable, "-m", "pip", "install", "--no-cache-dir", "opencv-python-headless"]
                rc = self._run_cmd(cmd_head, custom_env)
                
                with self.lock:
                    if rc == 0:
                        self.status = "success"
                        self.log.append("Installation finished successfully!")
                    else:
                        self.status = "failed"
                        self.log.append(f"Failed to install opencv-python-headless (exit code {rc})")
            except Exception as e:
                with self.lock:
                    self.status = "failed"
                    self.log.append(f"Installation error: {str(e)}")
            finally:
                if local_tmp and os.path.exists(local_tmp):
                    try:
                        shutil.rmtree(local_tmp, ignore_errors=True)
                    except Exception:
                        pass

        def _run_uninstall(self):
            try:
                import sys
                import os
                import time
                with self.lock:
                    self.log.append("Uninstalling AI dependencies...")
                
                cmd = [sys.executable, "-m", "pip", "uninstall", "-y", "ultralytics", "torch", "torchvision", "torchaudio", "opencv-python-headless"]
                rc = self._run_cmd(cmd, os.environ.copy())
                
                with self.lock:
                    if rc == 0:
                        self.status = "idle"
                        self.log.append("Uninstall completed successfully! Restarting server...")
                    else:
                        self.status = "failed"
                        self.log.append(f"Failed to uninstall dependencies (exit code {rc})")
                
                if rc == 0:
                    time.sleep(2)
                    print("\n\nUninstall complete! Restarting server...")
                    if hasattr(manager, 'mediamtx') and manager.mediamtx:
                        try:
                            manager.mediamtx.stop()
                        except Exception:
                            pass
                    if sys.platform.startswith('linux'):
                        os._exit(42)
                    else:
                        os._exit(0)
            except Exception as e:
                with self.lock:
                    self.status = "failed"
                    self.log.append(f"Uninstall error: {str(e)}")

    ai_installer = AIInstaller()

    @app.route('/api/ai/status', methods=['GET'])
    @login_required
    def get_ai_status():
        try:
            import importlib
            importlib.invalidate_caches()
            import cv2
            import ultralytics
            return jsonify({
                'installed': True,
                'opencv_version': getattr(cv2, '__version__', 'unknown'),
                'ultralytics_version': getattr(ultralytics, '__version__', 'unknown')
            })
        except ImportError:
            return jsonify({'installed': False})

    @app.route('/api/ai/install', methods=['POST'])
    @login_required
    def start_ai_install():
        data = request.json or {}
        mode = data.get('mode', 'cpu')
        if mode not in ('cpu', 'cuda', 'mps'):
            mode = 'cpu'
        success = ai_installer.start_install(mode=mode)
        return jsonify({'success': success, 'status': ai_installer.status})

    @app.route('/api/ai/uninstall', methods=['POST'])
    @login_required
    def start_ai_uninstall():
        success = ai_installer.start_uninstall()
        return jsonify({'success': success, 'status': ai_installer.status})

    @app.route('/api/ai/install/progress', methods=['GET'])
    @login_required
    def get_ai_install_progress():
        with ai_installer.lock:
            return jsonify({
                'status': ai_installer.status,
                'log': ai_installer.log
            })

    return app
