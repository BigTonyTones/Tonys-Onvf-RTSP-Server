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
from .updater import UpdateChecker, check_for_updates, download_and_apply_update, is_trusted_update_url
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
            
            # Fire restart notification
            try:
                manager.notifier.send('server_restarted', 'Server Restarted',
                                      'Tony\'s ONVIF Server has been restarted.')
            except Exception:
                pass
            
        # Run restart in background thread
        import threading
        restart_thread = threading.Thread(target=do_restart, daemon=True)
        restart_thread.start()
        
        return jsonify({'message': 'Server restart initiated'})

    @app.route('/api/server/stop', methods=['POST'])
    @login_required
    def stop_server():
        """Stop the entire server"""
        # Fire notification before stopping
        try:
            manager.notifier.send('server_stopping', 'Server Stopping',
                                  'Tony\'s ONVIF Server is shutting down.')
        except Exception:
            pass

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
                    result = subprocess.run(['systemctl', 'is-active', 'tonys-onvif'], 
                                          capture_output=True, text=True, timeout=2)
                    if result.returncode == 0 and result.stdout.strip() == 'active':
                        print("Detected systemd service. Stopping service...")
                        subprocess.run(['systemctl', 'stop', 'tonys-onvif'], timeout=5)
                        return
                    else:
                        os.killpg(os.getpgid(os.getpid()), signal.SIGTERM)
                else:
                    os._exit(0)
            except:
                os._exit(0)
        
        # Run stop in background thread
        import threading
        stop_thread = threading.Thread(target=do_stop, daemon=True)
        stop_thread.start()
        
        return jsonify({'message': 'Server stop initiated'})

    @app.route('/api/server/reboot', methods=['POST'])
    @login_required
    def reboot_server():
        """Reboot the entire server (Linux only)"""
        # Only allow on Linux
        if not sys.platform.startswith('linux'):
            return jsonify({'error': 'Reboot is only supported on Linux'}), 400
        
        # Fire notification before reboot
        try:
            manager.notifier.send('server_rebooting', 'Server Rebooting',
                                  'Tony\'s ONVIF Server is rebooting.')
        except Exception:
            pass
        
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
    @app.route('/matrix')
    @app.route('/onvif')
    @app.route('/ai')
    @login_required
    def index():
        settings = manager.load_settings()
        response = app.make_response(get_web_ui_html(settings))
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
                camera.ai_zone = data.get("aiZone", [])
                camera.ai_zone_profiles = data.get("aiZoneProfiles", {})
                camera.ai_active_zone_profile = data.get("aiActiveZoneProfile", "")
                camera.send_smart_onvif_topics = data.get('sendSmartOnvifTopics', True)
                camera.notify_ai_enabled = data.get("notifyAiEnabled", False)
                camera.notify_ai_zone_filter = data.get("notifyAiZoneFilter", "")
                camera.notify_ai_schedules = data.get("notifyAiSchedules", [])
                camera.notify_schedule_enabled = bool(camera.notify_ai_schedules)
                camera.notify_ai_cooldown = data.get('notifyAiCooldown', 60)
                camera.notify_ai_targets = data.get('notifyAiTargets', ['person'])
                camera.notify_ai_attach_image = data.get('notifyAiAttachImage', False)
                camera.notify_ai_license_plates = data.get('notifyAiLicensePlates', '')
                camera.notify_schedule_days = data.get('notifyScheduleDays', [0, 1, 2, 3, 4, 5, 6])
                camera.notify_schedule_start = data.get('notifyScheduleStart', '00:00')
                camera.notify_schedule_end = data.get('notifyScheduleEnd', '23:59')
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
                camera.ai_zone = data.get("aiZone", [])
                camera.ai_zone_profiles = data.get("aiZoneProfiles", {})
                camera.ai_active_zone_profile = data.get("aiActiveZoneProfile", "")
                camera.send_smart_onvif_topics = data.get('sendSmartOnvifTopics', True)
                camera.notify_ai_enabled = data.get("notifyAiEnabled", False)
                camera.notify_ai_zone_filter = data.get("notifyAiZoneFilter", "")
                camera.notify_ai_schedules = data.get("notifyAiSchedules", [])
                camera.notify_schedule_enabled = bool(camera.notify_ai_schedules)
                camera.notify_ai_cooldown = data.get('notifyAiCooldown', 60)
                camera.notify_ai_targets = data.get('notifyAiTargets', ['person'])
                camera.notify_ai_attach_image = data.get('notifyAiAttachImage', False)
                camera.notify_ai_license_plates = data.get('notifyAiLicensePlates', '')
                camera.notify_schedule_days = data.get('notifyScheduleDays', [0, 1, 2, 3, 4, 5, 6])
                camera.notify_schedule_start = data.get('notifyScheduleStart', '00:00')
                camera.notify_schedule_end = data.get('notifyScheduleEnd', '23:59')
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

    @app.route('/api/cameras/<int:camera_id>/test-image-notification', methods=['POST'])
    @login_required
    def test_camera_image_notification(camera_id):
        camera = manager.get_camera(camera_id)
        if not camera:
            return jsonify({'error': 'Camera not found'}), 404
        test_img_b64 = "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"
        
        # We need a notify config dict. Let's build a mock one using camera's config,
        # but force notifyAiEnabled to True.
        cam_notify_cfg = {
            'notifyAiEnabled': True,
            'notifyAiCooldown': 0, # Bypass cooldown
            'notifyAiTargets': ['person'],
            'notifyScheduleEnabled': False
        }
        
        try:
            import base64
            img_bytes = base64.b64decode(test_img_b64)
            manager.notifier.send_ai_detection(
                camera_id=camera.id,
                camera_name=camera.name,
                detected_labels=['person'],
                camera_notify_cfg=cam_notify_cfg,
                image_bytes=img_bytes,
                is_test=True
            )
            return jsonify({'status': 'success', 'message': 'Test image notification sent successfully'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

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

    @app.route('/api/ai-alerts', methods=['GET'])
    @login_required
    def list_ai_alerts():
        """List stored AI detection alert images (newest first)"""
        from .ai_alerts import alert_store
        camera_id = request.args.get('camera_id', type=int)
        return jsonify({'alerts': alert_store.list_alerts(camera_id),
                        'max_alerts': alert_store.max_alerts})

    @app.route('/api/ai-alerts/image/<filename>', methods=['GET'])
    @login_required
    def get_ai_alert_image(filename):
        """Serve a stored AI detection alert image"""
        from .ai_alerts import alert_store
        path = alert_store.get_image_path(filename)
        if not path:
            return jsonify({'error': 'Image not found'}), 404
        response = make_response(send_file(path, mimetype='image/jpeg'))
        # Stored images never change, so let the browser cache them
        response.headers['Cache-Control'] = 'private, max-age=86400'
        return response

    @app.route('/api/ai-alerts', methods=['DELETE'])
    @login_required
    def clear_ai_alerts():
        """Clear AI detection alert history (optionally for one camera)"""
        from .ai_alerts import alert_store
        camera_id = request.args.get('camera_id', type=int)
        removed = alert_store.clear(camera_id)
        return jsonify({'status': 'success', 'removed': removed})

    @app.route('/api/ai-alerts/settings', methods=['POST'])
    @login_required
    def set_ai_alerts_settings():
        """Update the stored-image cap for AI detection alerts"""
        from .ai_alerts import alert_store
        data = request.get_json(silent=True) or {}
        if 'max_alerts' not in data:
            return jsonify({'error': 'max_alerts required'}), 400
        applied = alert_store.set_max_alerts(data['max_alerts'])
        return jsonify({'status': 'success', 'max_alerts': applied})

    @app.route('/api/ai-alerts/delete', methods=['POST'])
    @login_required
    def delete_ai_alerts():
        """Delete specific alert images by filename"""
        from .ai_alerts import alert_store
        data = request.get_json(silent=True) or {}
        removed = alert_store.delete_files(data.get('files', []))
        return jsonify({'status': 'success', 'removed': removed})

    @app.route('/api/ai-alerts/download', methods=['POST'])
    @login_required
    def download_ai_alerts():
        """Download selected alert images as a ZIP archive"""
        import io
        import json as _json
        import zipfile
        from .ai_alerts import alert_store
        data = request.get_json(silent=True)
        if data is None:
            # Form submission from the alerts page (browser-native download)
            try:
                data = {'files': _json.loads(request.form.get('files', '[]'))}
            except Exception:
                data = {'files': []}
        buf = io.BytesIO()
        count = 0
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_STORED) as zf:
            for f in data.get('files', []):
                path = alert_store.get_image_path(f)
                if path:
                    zf.write(path, f)
                    count += 1
        if count == 0:
            return jsonify({'error': 'No valid files'}), 400
        buf.seek(0)
        ts = time.strftime('%Y%m%d-%H%M%S')
        return send_file(buf, mimetype='application/zip', as_attachment=True,
                         download_name=f'ai-alerts-{ts}.zip')

    @app.route('/alerts')
    @login_required
    def alerts_page():
        """Standalone AI detection alerts gallery page"""
        from .alerts_template import get_alerts_html
        return get_alerts_html()

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

    @app.route('/api/cameras/<int:camera_id>/sync-stream-info', methods=['POST'])
    @login_required
    def sync_stream_info(camera_id):
        """Apply the probed source stream resolution/framerate to the camera config.

        Resolves the mismatch warning raised by the startup stream probe
        (resolution flapping, issue #42)."""
        camera = manager.get_camera(camera_id)
        if not camera:
            return jsonify({'error': 'Camera not found'}), 404

        probe = getattr(camera, 'stream_probe', {}) or {}
        applied = {}

        main = probe.get('main')
        if isinstance(main, dict) and main.get('width'):
            camera.main_width = main['width']
            camera.main_height = main['height']
            if main.get('framerate'):
                camera.main_framerate = main['framerate']
            main['configuredWidth'] = main['width']
            main['configuredHeight'] = main['height']
            main['mismatch'] = main.get('codec') not in ('h264', '')
            applied['main'] = f"{main['width']}x{main['height']}"

        sub = probe.get('sub')
        if isinstance(sub, dict) and sub.get('width'):
            camera.sub_width = sub['width']
            camera.sub_height = sub['height']
            if sub.get('framerate'):
                camera.sub_framerate = sub['framerate']
            sub['configuredWidth'] = sub['width']
            sub['configuredHeight'] = sub['height']
            sub['mismatch'] = sub.get('codec') not in ('h264', '')
            applied['sub'] = f"{sub['width']}x{sub['height']}"

        if not applied:
            return jsonify({'error': 'No probe data available for this camera yet'}), 400

        probe['mismatch'] = any(e.get('mismatch') for e in probe.values() if isinstance(e, dict))
        camera.stream_probe = probe
        manager.save_config()
        return jsonify({'status': 'success', 'applied': applied, 'camera': camera.to_dict()})

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
    


    @app.route('/api/check-port', methods=['GET'])
    @login_required
    def check_port():
        import socket
        try:
            port = int(request.args.get('port', 0))
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid port'}), 400
        if not (1 <= port <= 65535):
            return jsonify({'error': 'Port must be between 1 and 65535'}), 400
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('0.0.0.0', port))
            return jsonify({'available': True})
        except OSError:
            return jsonify({'available': False})

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

    # --- UniFi Protect ONVIF Listener API Routes ---

    @app.route('/api/protect-listener', methods=['GET'])
    @login_required
    def protect_listener_get():
        """Return all NVR targets + monitor settings (passwords redacted)."""
        return jsonify(manager.protect_listener.get_public_state())

    @app.route('/api/protect-listener', methods=['POST'])
    @login_required
    def protect_listener_add():
        """Add a new NVR target."""
        data = request.json or {}
        try:
            nvr = manager.protect_listener.add_nvr(data)
            return jsonify({'status': 'ok', 'id': nvr['id']})
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/api/protect-listener/settings', methods=['POST'])
    @login_required
    def protect_listener_settings():
        """Update global monitor settings (enabled / interval)."""
        data = request.json or {}
        try:
            manager.protect_listener.update_monitor_settings(
                enabled=data.get('monitorEnabled'),
                interval_minutes=data.get('monitorIntervalMinutes'),
            )
            return jsonify({'status': 'ok'})
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/api/protect-listener/status', methods=['GET'])
    @login_required
    def protect_listener_status_all():
        """Run a health check against every configured NVR."""
        try:
            results = manager.protect_listener.check_all()
            return jsonify({'status': 'ok', 'results': results})
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/api/protect-listener/<nvr_id>', methods=['PUT'])
    @login_required
    def protect_listener_update(nvr_id):
        data = request.json or {}
        if manager.protect_listener.update_nvr(nvr_id, data):
            return jsonify({'status': 'ok'})
        return jsonify({'error': 'NVR not found'}), 404

    @app.route('/api/protect-listener/<nvr_id>', methods=['DELETE'])
    @login_required
    def protect_listener_delete(nvr_id):
        if manager.protect_listener.delete_nvr(nvr_id):
            return jsonify({'status': 'ok'})
        return jsonify({'error': 'NVR not found'}), 404

    @app.route('/api/protect-listener/<nvr_id>/test', methods=['POST'])
    @login_required
    def protect_listener_test(nvr_id):
        """Test SSH connectivity to a single NVR."""
        return jsonify(manager.protect_listener.test_connection(nvr_id))

    @app.route('/api/protect-listener/<nvr_id>/status', methods=['GET'])
    @login_required
    def protect_listener_status_one(nvr_id):
        return jsonify(manager.protect_listener.check_status(nvr_id))

    @app.route('/api/protect-listener/<nvr_id>/reboot', methods=['POST'])
    @login_required
    def protect_listener_reboot(nvr_id):
        """Reboot the Ubiquiti NVR over SSH."""
        return jsonify(manager.protect_listener.reboot(nvr_id))

    @app.route('/api/protect-listener/<nvr_id>/install', methods=['POST'])
    @login_required
    def protect_listener_install(nvr_id):
        """Run the upstream installer on the NVR over SSH (streams logs)."""
        if manager.protect_listener.start_install(nvr_id):
            return jsonify({'status': 'ok'})
        return jsonify({'error': 'Install already running or NVR not found'}), 409

    @app.route('/api/protect-listener/<nvr_id>/install/progress', methods=['GET'])
    @login_required
    def protect_listener_install_progress(nvr_id):
        return jsonify(manager.protect_listener.get_install_progress(nvr_id))

    @app.route('/api/protect-listener/<nvr_id>/uninstall', methods=['POST'])
    @login_required
    def protect_listener_uninstall(nvr_id):
        """Uninstall onvif-recorder over SSH (remove, or purge if requested)."""
        data = request.json or {}
        purge = bool(data.get('purge', False))
        if manager.protect_listener.start_uninstall(nvr_id, purge=purge):
            return jsonify({'status': 'ok'})
        return jsonify({'error': 'Action already running or NVR not found'}), 409

    # --- Notification API Routes ---

    @app.route('/api/notifications/config', methods=['GET'])
    @login_required
    def get_notification_config():
        """Return full notification configuration"""
        from .notifier import NOTIFICATION_EVENTS, DEFAULT_ENABLED_EVENTS
        cfg = manager.get_notification_config()
        # Ensure defaults are present
        if 'enabled_events' not in cfg:
            cfg['enabled_events'] = DEFAULT_ENABLED_EVENTS
        if 'providers' not in cfg:
            cfg['providers'] = {}
        return jsonify({
            'config': cfg,
            'event_labels': NOTIFICATION_EVENTS
        })

    @app.route('/api/notifications/config', methods=['POST'])
    @login_required
    def save_notification_config():
        """Save notification configuration"""
        data = request.json
        try:
            result = manager.save_notification_config(data)
            return jsonify({'status': 'ok', 'config': result})
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/api/notifications/test', methods=['POST'])
    @login_required
    def test_notification():
        """Send a test notification to one or all enabled providers"""
        data = request.json or {}
        provider = data.get('provider')  # optional — if None, test all
        try:
            results = manager.notifier.test(provider=provider)
            all_ok = all(v == 'ok' for v in results.values())
            return jsonify({'status': 'ok' if all_ok else 'partial', 'results': results})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    
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

        # SECURITY (C1): never trust a client-supplied download URL. An attacker on the LAN
        # could otherwise point the updater at an arbitrary archive and gain code execution
        # (the ZIP is extracted over app/ and run on restart, as root on Linux). Re-resolve
        # the authoritative URL from the GitHub release check on the server side instead.
        # check_for_updates() returns the latest release's zipball regardless of whether it
        # is newer, so this also powers the "Reinstall Current Version" (repair) button.
        try:
            update_info = check_for_updates()
        except Exception as e:
            return jsonify({'error': f'Failed to contact update server: {e}'}), 502

        if not update_info:
            return jsonify({'error': 'Could not reach the update server. Please try again.'}), 502

        download_url = update_info.get('download_url')
        if not is_trusted_update_url(download_url):
            return jsonify({'error': 'Could not resolve a trusted update URL from GitHub.'}), 400

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
        theme = (manager.load_settings() or {}).get('theme', '')
        return get_diagnostics_html(theme)
        
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
                
            easyocr_installed = False
            easyocr_version = "Not Installed"
            try:
                import easyocr
                easyocr_installed = True
                easyocr_version = easyocr.__version__
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
                'easyocr_installed': easyocr_installed,
                'easyocr_version': easyocr_version,
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
        theme = (manager.load_settings() or {}).get('theme', '')
        return get_ip_management_html(whitelist, theme)

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
                if rc != 0:
                    with self.lock:
                        self.status = "failed"
                        self.log.append(f"Failed to install opencv-python-headless (exit code {rc})")
                    return

                # Step 5: Install easyocr
                with self.lock:
                    self.log.append("Installing easyocr (License Plate character recognition)...")
                cmd_ocr = [sys.executable, "-m", "pip", "install", "--no-cache-dir", "easyocr"]
                rc = self._run_cmd(cmd_ocr, custom_env)
                
                with self.lock:
                    if rc == 0:
                        self.status = "success"
                        self.log.append("Installation finished successfully!")
                    else:
                        self.status = "failed"
                        self.log.append(f"Failed to install easyocr (exit code {rc})")
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
                
                cmd = [sys.executable, "-m", "pip", "uninstall", "-y", "ultralytics", "torch", "torchvision", "torchaudio", "opencv-python-headless", "easyocr"]
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

    # --- Apprise Installer ---
    class AppriseInstaller:
        def __init__(self):
            self.lock = threading.Lock()
            self.status = "idle"
            self.log = []
            self._thread = None
            
        def start_install(self):
            with self.lock:
                if self.status == "installing":
                    return False
                self.status = "installing"
                self.log = ["Starting Apprise installation..."]
            self._thread = threading.Thread(target=self._run_install, daemon=True)
            self._thread.start()
            return True
            
        def _run_install(self):
            import subprocess
            import sys
            try:
                cmd = [sys.executable, "-m", "pip", "install", "--no-cache-dir", "apprise"]
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                for line in iter(process.stdout.readline, ""):
                    if line:
                        with self.lock:
                            self.log.append(line.rstrip('\n'))
                process.wait()
                with self.lock:
                    if process.returncode == 0:
                        self.status = "success"
                        self.log.append("Apprise installed successfully!")
                    else:
                        self.status = "failed"
                        self.log.append(f"Installation failed with exit code {process.returncode}")
            except Exception as e:
                with self.lock:
                    self.status = "failed"
                    self.log.append(f"Error: {str(e)}")

    apprise_installer = AppriseInstaller()

    @app.route('/api/apprise/status', methods=['GET'])
    @login_required
    def get_apprise_status():
        try:
            import importlib
            importlib.invalidate_caches()
            import apprise as _apprise_mod
            return jsonify({'installed': True, 'version': getattr(_apprise_mod, '__version__', 'unknown')})
        except ImportError:
            return jsonify({'installed': False})

    @app.route('/api/apprise/install', methods=['POST'])
    @login_required
    def start_apprise_install():
        success = apprise_installer.start_install()
        return jsonify({'success': success, 'status': apprise_installer.status})

    @app.route('/api/apprise/install/progress', methods=['GET'])
    @login_required
    def get_apprise_install_progress():
        with apprise_installer.lock:
            return jsonify({
                'status': apprise_installer.status,
                'log': apprise_installer.log
            })

    return app
