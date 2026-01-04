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
        
        new_analytics = {}
        items = json_data.get('items', [])
        
        for item in items:
            name = item.get('name')
            if not name:
                continue
            
            # Basic info
            analytics = {
                'ready': item.get('ready', False),
                'tracks': item.get('tracks', []),
                'readers': len(item.get('readers', [])),
                'source': item.get('source', {}).get('type', 'unknown'),
                'bytesReceived': item.get('bytesReceived', 0),
                'bytesSent': item.get('bytesSent', 0),
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
                'ready': False,
                'bitrate': 0,
                'readers': 0,
                'tracks': []
            })
