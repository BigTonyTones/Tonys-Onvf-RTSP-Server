"""
Diagnostics page template for troubleshooting
"""

def get_diagnostics_html():
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Diagnostics - Tonys Onvif Server</title>
    <style>
        :root {
            --bg-color: #282a36;
            --sidebar-bg: #1e1f29;
            --card-bg: #343746;
            --header-bg: #1e1f29;
            --text-main: #f8f8f2;
            --text-muted: #6272a4;
            --accent-purple: #bd93f9;
            --accent-pink: #ff79c6;
            --accent-cyan: #8be9fd;
            --accent-green: #50fa7b;
            --accent-orange: #ffb86c;
            --accent-red: #ff5555;
            --border-color: #44475a;
            --input-bg: #282a36;
            --console-bg: #191a21;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .header {
            background: var(--header-bg);
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
            flex-shrink: 0;
        }
        
        .header h1 {
            color: var(--accent-purple);
            font-size: 20px;
            font-weight: 700;
        }
        
        .header-actions {
            display: flex;
            gap: 12px;
            align-items: center;
        }

        .back-btn {
            background: var(--accent-purple);
            color: #282a36;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .back-btn:hover {
            background: var(--accent-pink);
            transform: translateY(-1px);
        }

        .clear-btn {
            background: transparent;
            color: var(--text-muted);
            border: 1px solid var(--border-color);
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.3s;
        }

        .clear-btn:hover {
            border-color: var(--accent-red);
            color: var(--accent-red);
        }
        
        .main-layout {
            display: flex;
            flex: 1;
            overflow: hidden;
        }
        
        .sidebar {
            width: 400px;
            background: var(--sidebar-bg);
            border-right: 1px solid var(--border-color);
            padding: 20px;
            overflow-y: auto;
            flex-shrink: 0;
        }
        
        .content {
            flex: 1;
            padding: 0;
            background: var(--console-bg);
            display: flex;
            flex-direction: column;
        }

        .tool-section {
            background: var(--card-bg);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid var(--border-color);
        }

        .tool-title {
            font-size: 14px;
            font-weight: 700;
            color: var(--accent-purple);
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--border-color);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .input-group {
            margin-bottom: 12px;
        }
        
        .input-group label {
            display: block;
            margin-bottom: 6px;
            font-weight: 600;
            color: var(--accent-cyan);
            font-size: 12px;
        }
        
        .input-group input,
        .input-group select {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid var(--border-color);
            background: var(--input-bg);
            color: var(--text-main);
            border-radius: 6px;
            font-size: 13px;
            transition: all 0.2s;
        }
        
        .input-group input:focus,
        .input-group select:focus {
            outline: none;
            border-color: var(--accent-purple);
            box-shadow: 0 0 0 2px rgba(189, 147, 249, 0.1);
        }
        
        .btn {
            background: linear-gradient(135deg, var(--accent-purple) 0%, #a277e3 100%);
            color: #282a36;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            width: 100%;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .btn:hover {
            filter: brightness(1.1);
            transform: translateY(-1px);
        }
        
        .btn:active {
            transform: translateY(0);
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .output-console {
            flex: 1;
            padding: 25px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.6;
            overflow-y: auto;
            color: #f8f8f2;
            word-break: break-all;
            white-space: pre-wrap;
        }

        .output-console::-webkit-scrollbar {
            width: 10px;
        }

        .output-console::-webkit-scrollbar-track {
            background: var(--console-bg);
        }

        .output-console::-webkit-scrollbar-thumb {
            background: var(--border-color);
            border-radius: 5px;
        }

        .output-console::-webkit-scrollbar-thumb:hover {
            background: var(--text-muted);
        }
        
        .log-entry {
            margin-bottom: 4px;
            animation: fadeIn 0.2s ease-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateX(5px); }
            to { opacity: 1; transform: translateX(0); }
        }

        .log-timestamp {
            color: var(--text-muted);
            margin-right: 10px;
            font-size: 12px;
        }

        .log-info { color: var(--accent-cyan); }
        .log-success { color: var(--accent-green); }
        .log-error { color: var(--accent-red); }
        .log-warn { color: var(--accent-orange); }
        .log-purple { color: var(--accent-purple); }
        
        .spinner {
            border: 2px solid rgba(40, 42, 54, 0.3);
            border-top: 2px solid #282a36;
            border-radius: 50%;
            width: 14px;
            height: 14px;
            animation: spin 1s linear infinite;
            margin-right: 8px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .placeholder-text {
            color: var(--text-muted);
            font-style: italic;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: sans-serif;
            font-size: 16px;
        }

        .divider {
            height: 1px;
            background: var(--border-color);
            margin: 15px 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>System Diagnostics</h1>
        <div class="header-actions">
            <button class="clear-btn" onclick="clearConsole()">Clear Console</button>
            <button class="back-btn" onclick="window.location.href='/'">Back to Dashboard</button>
        </div>
    </div>
    
    <div class="main-layout">
        <div class="sidebar">
            <!-- Ping Tool -->
            <div class="tool-section">
                <div class="tool-title">Ping Tool</div>
                <div class="input-group">
                    <label>Target Host or IP</label>
                    <input type="text" id="ping-host" placeholder="e.g. 192.168.1.100">
                </div>
                <div class="input-group">
                    <label>Count</label>
                    <input type="number" id="ping-count" value="4" min="1" max="10">
                </div>
                <button class="btn" onclick="runPing()" id="ping-btn">Run Ping</button>
            </div>

            <!-- Traceroute Tool -->
            <div class="tool-section">
                <div class="tool-title">Traceroute</div>
                <div class="input-group">
                    <label>Target Host or IP</label>
                    <input type="text" id="trace-host" placeholder="e.g. example.com">
                </div>
                <button class="btn" onclick="runTraceroute()" id="trace-btn">Run Traceroute</button>
            </div>
            
            <!-- Stream Test -->
            <div class="tool-section">
                <div class="tool-title">RTSP Stream Test</div>
                
                <div class="input-group">
                    <label>Quick Select Camera</label>
                    <select id="camera-select" onchange="handleCameraSelect()">
                        <option value="">- Manual Input -</option>
                    </select>
                </div>

                <div class="input-group" id="stream-type-group" style="display: none;">
                    <label>Stream Type</label>
                    <select id="stream-type" onchange="handleCameraSelect()">
                        <option value="main">Main Stream</option>
                        <option value="sub">Sub Stream</option>
                    </select>
                </div>

                <div class="divider"></div>

                <div class="input-group">
                    <label>Host/IP & Path</label>
                    <input type="text" id="stream-host" placeholder="192.168.1.100:554/stream">
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <div class="input-group">
                        <label>Username</label>
                        <input type="text" id="stream-user" placeholder="admin">
                    </div>
                    <div class="input-group">
                        <label>Password</label>
                        <input type="password" id="stream-pass" placeholder="password">
                    </div>
                </div>
                <button class="btn" onclick="testStream()" id="stream-btn">Test Connection</button>
            </div>
            
            <!-- Port Scanner -->
            <div class="tool-section">
                <div class="tool-title">Port Check</div>
                <div class="input-group">
                    <label>Host</label>
                    <input type="text" id="port-host" placeholder="e.g. 192.168.1.50">
                </div>
                <div class="input-group">
                    <label>Port</label>
                    <input type="number" id="port-number" placeholder="554" min="1" max="65535">
                </div>
                <button class="btn" onclick="checkPort()" id="port-btn">Check Port</button>
            </div>

            <!-- System Info -->
            <div class="tool-section">
                <div class="tool-title">System Status</div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <button class="btn" onclick="getSystemInfo()" id="system-btn">System Info</button>
                    <button class="btn" onclick="getFFmpegInfo()" id="ffmpeg-btn">FFmpeg Info</button>
                </div>
            </div>
        </div>
        
        <div class="content">
            <div class="output-console" id="console">
                <div class="placeholder-text">Diagnostic output will be displayed here...</div>
            </div>
        </div>
    </div>
    
    <script>
        const consoleEl = document.getElementById('console');
        let hasOutput = false;
        let camerasData = [];

        function log(message, type = 'info') {
            if (!hasOutput) {
                consoleEl.innerHTML = '';
                hasOutput = true;
            }

            const entry = document.createElement('div');
            entry.className = 'log-entry';
            
            const timestamp = new Date().toLocaleTimeString();
            let colorClass = 'log-info';
            if (type === 'error') colorClass = 'log-error';
            if (type === 'success') colorClass = 'log-success';
            if (type === 'warn') colorClass = 'log-warn';
            if (type === 'purple') colorClass = 'log-purple';

            entry.innerHTML = `<span class="log-timestamp">[${timestamp}]</span><span class="${colorClass}">${message}</span>`;
            consoleEl.appendChild(entry);
            consoleEl.scrollTop = consoleEl.scrollHeight;
        }

        function clearConsole() {
            consoleEl.innerHTML = '<div class="placeholder-text">Console cleared. Waiting for next tool...</div>';
            hasOutput = false;
        }

        // Camera loading and handling
        async function loadCameras() {
            try {
                const response = await fetch('/api/cameras');
                camerasData = await response.json();
                const select = document.getElementById('camera-select');
                
                camerasData.forEach(cam => {
                    const opt = document.createElement('option');
                    opt.value = cam.id;
                    opt.textContent = cam.name;
                    select.appendChild(opt);
                });
                
                if (camerasData.length > 0) {
                    log(`Loaded ${camerasData.length} existing cameras for quick selection.`, 'info');
                }
            } catch (err) {
                console.error('Failed to load cameras:', err);
            }
        }

        function handleCameraSelect() {
            const select = document.getElementById('camera-select');
            const typeGroup = document.getElementById('stream-type-group');
            const typeSelect = document.getElementById('stream-type');
            
            if (!select.value) {
                typeGroup.style.display = 'none';
                return;
            }

            typeGroup.style.display = 'block';
            const camera = camerasData.find(c => c.id == select.value);
            if (camera) {
                const isSub = typeSelect.value === 'sub';
                const fullUrl = isSub ? camera.subStreamUrl : camera.mainStreamUrl;
                
                // Extract Host:Port/Path (strip rtsp:// and user:pass@ if present)
                let hostPath = fullUrl.replace(/^rtsp:\/\//i, '');
                if (hostPath.includes('@')) {
                    hostPath = hostPath.split('@')[1];
                }
                
                document.getElementById('stream-host').value = hostPath;
                document.getElementById('stream-user').value = camera.username || '';
                document.getElementById('stream-pass').value = camera.password || '';
                
                log(`Selected Camera: ${camera.name} (${typeSelect.value} stream)`, 'purple');
            }
        }

        // Initialize
        loadCameras();

        async function runPing() {
            const host = document.getElementById('ping-host').value;
            const count = document.getElementById('ping-count').value;
            const btn = document.getElementById('ping-btn');
            
            if (!host) {
                log('Error: Please enter a target host.', 'error');
                return;
            }
            
            btn.disabled = true;
            const originalText = btn.textContent;
            btn.innerHTML = '<div class="spinner"></div> Running...';
            
            log(`Starting ping request to ${host} (Count: ${count})...`, 'purple');
            
            try {
                const response = await fetch('/api/diagnostics/ping', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({host, count: parseInt(count)})
                });
                
                const data = await response.json();
                if (data.success) {
                    log(data.output);
                    log('Ping completed successfully.', 'success');
                } else {
                    log('Ping failed: ' + data.error, 'error');
                }
            } catch (error) {
                log('Connection error: ' + error.message, 'error');
            } finally {
                btn.disabled = false;
                btn.textContent = originalText;
                log('--------------------------------------------------');
            }
        }
        
        async function runTraceroute() {
            const host = document.getElementById('trace-host').value;
            const btn = document.getElementById('trace-btn');
            
            if (!host) {
                log('Error: Please enter a target host.', 'error');
                return;
            }
            
            btn.disabled = true;
            const originalText = btn.textContent;
            btn.innerHTML = '<div class="spinner"></div> Running...';
            
            log(`Tracing route to ${host}. Please wait, this may take up to 60 seconds...`, 'purple');
            
            try {
                const response = await fetch('/api/diagnostics/traceroute', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({host})
                });
                
                const data = await response.json();
                if (data.success) {
                    log(data.output);
                    log('Traceroute completed.', 'success');
                } else {
                    log('Traceroute failed: ' + data.error, 'error');
                }
            } catch (error) {
                log('Connection error: ' + error.message, 'error');
            } finally {
                btn.disabled = false;
                btn.textContent = originalText;
                log('--------------------------------------------------');
            }
        }
        
        async function testStream() {
            const host = document.getElementById('stream-host').value;
            const user = document.getElementById('stream-user').value;
            const pass = document.getElementById('stream-pass').value;
            const btn = document.getElementById('stream-btn');
            
            if (!host) {
                log('Error: Please enter the stream Host/IP & Path.', 'error');
                return;
            }

            // Construct full URL with encoded credentials
            let fullUrl = host;
            // Ensure rtsp:// prefix isn't doubled or missing
            if (fullUrl.toLowerCase().startsWith('rtsp://')) {
                fullUrl = fullUrl.substring(7);
            }

            if (user && pass) {
                const encUser = encodeURIComponent(user);
                const encPass = encodeURIComponent(pass);
                fullUrl = `rtsp://${encUser}:${encPass}@${fullUrl}`;
            } else {
                fullUrl = `rtsp://${fullUrl}`;
            }
            
            btn.disabled = true;
            const originalText = btn.textContent;
            btn.innerHTML = '<div class="spinner"></div> Testing...';
            
            log(`Analyzing stream properties for camera at ${host}...`, 'purple');
            if (user) log(`Using credentials for user: ${user}`, 'info');
            
            try {
                const response = await fetch('/api/diagnostics/stream-test', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url: fullUrl})
                });
                
                const data = await response.json();
                if (data.success) {
                    log('✓ Stream successfully accessed.', 'success');
                    
                    if (data.video) {
                        log(`Video Stream:`, 'purple');
                        log(`  • Resolution: ${data.video.width}x${data.video.height}`);
                        log(`  • Codec:      ${data.video.codec_name} (${data.video.profile || 'unknown profile'})`);
                        log(`  • Pixel FMT:  ${data.video.pix_fmt}`);
                        log(`  • Framerate:  ${data.video.r_frame_rate} (${parseFloat(eval(data.video.r_frame_rate)).toFixed(2)} fps)`);
                        if (data.video.bit_rate) log(`  • Bitrate:    ${(data.video.bit_rate / 1000).toFixed(0)} kbps`);
                    }

                    if (data.audio) {
                        log(`Audio Stream:`, 'purple');
                        log(`  • Codec:      ${data.audio.codec_name}`);
                        log(`  • Channels:   ${data.audio.channels}`);
                        log(`  • Sample:     ${data.audio.sample_rate} Hz`);
                    }

                    if (data.format && data.format.size) {
                        log(`Format Metadata:`, 'info');
                        log(`  • Size:       ${(data.format.size / 1024).toFixed(0)} KB probed`);
                        log(`  • Duration:   ${data.format.duration}s probed`);
                    }

                    log(`Raw Data:`, 'info');
                    log(`  Click to view full JSON probe output below...`);
                    const pre = document.createElement('pre');
                    pre.style.margin = '10px 0';
                    pre.style.padding = '10px';
                    pre.style.background = 'rgba(0,0,0,0.3)';
                    pre.style.borderRadius = '5px';
                    pre.style.fontSize = '12px';
                    pre.style.color = '#bd93f9';
                    pre.textContent = JSON.stringify(data.raw, null, 2);
                    consoleEl.appendChild(pre);

                } else {
                    log('✗ Stream test failed.', 'error');
                    log('Error output: ' + data.error, 'error');
                }
            } catch (error) {
                log('Connection error: ' + error.message, 'error');
            } finally {
                btn.disabled = false;
                btn.textContent = originalText;
                log('--------------------------------------------------');
            }
        }
        
        async function checkPort() {
            const host = document.getElementById('port-host').value;
            const port = document.getElementById('port-number').value;
            const btn = document.getElementById('port-btn');
            
            if (!host || !port) {
                log('Error: Host and port are required.', 'error');
                return;
            }
            
            btn.disabled = true;
            const originalText = btn.textContent;
            btn.innerHTML = '<div class="spinner"></div> Checking...';
            
            log(`Checking connectivity to ${host}:${port}...`, 'purple');
            
            try {
                const response = await fetch('/api/diagnostics/port-check', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({host, port: parseInt(port)})
                });
                
                const data = await response.json();
                if (data.success) {
                    if (data.open) {
                        log(`✓ Port ${port} is OPEN on ${host}.`, 'success');
                    } else {
                        log(`✗ Port ${port} is CLOSED or restricted on ${host}.`, 'error');
                    }
                } else {
                    log('Error performing check: ' + data.error, 'error');
                }
            } catch (error) {
                log('Connection error: ' + error.message, 'error');
            } finally {
                btn.disabled = false;
                btn.textContent = originalText;
                log('--------------------------------------------------');
            }
        }
        
        async function getFFmpegInfo() {
            const btn = document.getElementById('ffmpeg-btn');
            btn.disabled = true;
            const originalText = btn.textContent;
            btn.innerHTML = '<div class="spinner"></div> ...';
            
            log('Retrieving FFmpeg environment details...', 'purple');
            
            try {
                const response = await fetch('/api/diagnostics/ffmpeg-info');
                const data = await response.json();
                
                if (data.success) {
                    log(`Active Version: ${data.version}`, 'info');
                    log('-- Full Output --');
                    log(data.full_output);
                } else {
                    log('Error: ' + data.error, 'error');
                }
            } catch (error) {
                log('Connection error: ' + error.message, 'error');
            } finally {
                btn.disabled = false;
                btn.textContent = originalText;
                log('--------------------------------------------------');
            }
        }
        
        async function getSystemInfo() {
            const btn = document.getElementById('system-btn');
            btn.disabled = true;
            const originalText = btn.textContent;
            btn.innerHTML = '<div class="spinner"></div> ...';
            
            log('Gathering system health and hardware metrics...', 'purple');
            
            try {
                const response = await fetch('/api/diagnostics/system-info');
                const data = await response.json();
                
                if (data.success) {
                    log(`System Info:`, 'info');
                    log(`  OS Platform:      ${data.platform}`);
                    log(`  Python Version:   ${data.python_version}`);
                    log(`  CPU Cores:        ${data.cpu_count}`);
                    log(`  Memory Usage:     ${data.available_memory}GB available / ${data.total_memory}GB total`);
                    log(`  Disk Usage:       ${data.disk_usage}%`);
                    log(`  MediaMTX Version: ${data.mediamtx_version}`, 'purple');
                    log(`  FFmpeg Version:   ${data.ffmpeg_version}`, 'purple');
                } else {
                    log('Error: ' + data.error, 'error');
                }
            } catch (error) {
                log('Connection error: ' + error.message, 'error');
            } finally {
                btn.disabled = false;
                btn.textContent = originalText;
                log('--------------------------------------------------');
            }
        }
    </script>
</body>
</html>
'''
