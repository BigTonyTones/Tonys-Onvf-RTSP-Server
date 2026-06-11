import time
import requests
import threading
from .config import MEDIAMTX_API_PORT

class AnalyticsManager:
    """Polls MediaMTX API for real-time stream analytics"""
    
    def __init__(self, poll_interval=3):
        self.poll_interval = poll_interval
        self.data = {}
        self.last_poll_time = 0
        self.running = False
        self.thread = None
        self._lock = threading.Lock()
        
        # History for bitrate calculation
        # { path_name: { 'bytesReceived': val, 'time': val } }
        self._history = {}

    def start(self):
        """Start the background polling thread"""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print(f"Analytics thread started (Interval: {self.poll_interval}s)")

    def stop(self):
        """Stop the background polling thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)

    def _run(self):
        """Main polling loop"""
        while self.running:
            try:
                self._poll()
            except Exception as e:
                # Silently ignore errors if MediaMTX is restarting/down
                pass
            time.sleep(self.poll_interval)

    def _poll(self):
        """Poll MediaMTX for path statistics"""
        url = f"http://127.0.0.1:{MEDIAMTX_API_PORT}/v3/paths/list"
        response = requests.get(url, timeout=2)
        if response.status_code != 200:
            return

        json_data = response.json()
        current_time = time.time()
        
        # Fetch active RTSP and WebRTC sessions to map ID -> IP address
        session_ips = {}
        try:
            rtsp_resp = requests.get(f"http://127.0.0.1:{MEDIAMTX_API_PORT}/v3/rtspsessions/list", timeout=2)
            if rtsp_resp.status_code == 200:
                for item in rtsp_resp.json().get('items', []):
                    s_id = item.get('id')
                    r_addr = item.get('remoteAddr')
                    if s_id and r_addr:
                        session_ips[s_id] = r_addr
        except Exception:
            pass

        try:
            webrtc_resp = requests.get(f"http://127.0.0.1:{MEDIAMTX_API_PORT}/v3/webrtcsessions/list", timeout=2)
            if webrtc_resp.status_code == 200:
                for item in webrtc_resp.json().get('items', []):
                    s_id = item.get('id')
                    r_addr = item.get('remoteAddr')
                    if s_id and r_addr:
                        session_ips[s_id] = r_addr
        except Exception:
            pass
        
        new_analytics = {}
        items = json_data.get('items', [])
        
        for item in items:
            name = item.get('name')
            if not name:
                continue
            
            # Basic info — v1.17+ uses 'online' (replaces deprecated 'ready')
            # Keep 'ready' fallback for any older binary still present during upgrade
            is_online = item.get('online', item.get('ready', False))
            # v1.17 - readers renamed to outboundSessions
            sessions = item.get('outboundSessions') or item.get('readers') or []
            reader_ips = []
            for s in sessions:
                if isinstance(s, dict):
                    s_id = s.get('id')
                    remote_addr = s.get('remoteAddr') or s.get('remoteAddress')
                    if not remote_addr and s_id:
                        remote_addr = session_ips.get(s_id)
                        
                    if remote_addr:
                        # strip the port (e.g. "192.168.1.10:54321" -> "192.168.1.10")
                        if ']' in remote_addr:
                            ip = remote_addr.split(']')[0].replace('[', '')
                        else:
                            ip = remote_addr.split(':')[0]
                        reader_ips.append(ip)

            analytics = {
                'online': is_online,
                'ready': is_online,  # Backwards-compat alias
                'tracks': item.get('tracks', []),
                'readers': len(sessions),
                'reader_ips': reader_ips,
                'source': item.get('source', {}).get('type', 'unknown') if isinstance(item.get('source'), dict) else 'unknown',
                # v1.17 moved bytesReceived/Sent into source object
                'bytesReceived': item.get('bytesReceived') or item.get('source', {}).get('bytesReceived', 0) if isinstance(item.get('source'), dict) else item.get('bytesReceived', 0),
                'bytesSent': item.get('bytesSent') or item.get('source', {}).get('bytesSent', 0) if isinstance(item.get('source'), dict) else item.get('bytesSent', 0),
                'bitrate': 0  # To be calculated
            }
            
            # Bitrate and Health tracking
            if name in self._history:
                last_data = self._history[name]
                delta_bytes = analytics['bytesReceived'] - last_data['bytesReceived']
                delta_time = current_time - last_data['time']
                
                # Update last_recv_time if bytes increased
                if delta_bytes > 0:
                    analytics['last_recv_time'] = current_time
                else:
                    analytics['last_recv_time'] = last_data.get('last_recv_time', current_time)

                if delta_time > 0 and delta_bytes >= 0:
                    # (bytes * 8) / (1024 * seconds) = kbps
                    analytics['bitrate'] = round((delta_bytes * 8) / (1024 * delta_time), 1)
            else:
                analytics['last_recv_time'] = current_time
            
            # Update history
            self._history[name] = {
                'bytesReceived': analytics['bytesReceived'],
                'time': current_time,
                'last_recv_time': analytics['last_recv_time']
            }
            
            # Health check: if no bytes for 10 seconds, it's 'stale'
            analytics['stale'] = (current_time - analytics['last_recv_time']) > 10
            
            new_analytics[name] = analytics
            
        with self._lock:
            self.data = new_analytics
            self.last_poll_time = current_time

    def get_analytics(self):
        """Get the latest collected analytics data"""
        with self._lock:
            return self.data.copy()

    def get_stream_stats(self, path_name):
        """Get stats for a specific stream path"""
        with self._lock:
            return self.data.get(path_name, {
                'online': False,
                'ready': False,  # Backwards-compat alias
                'bitrate': 0,
                'readers': 0,
                'reader_ips': [],
                'tracks': []
            })
