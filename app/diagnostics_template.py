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
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px 30px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header h1 {
            color: #667eea;
            font-size: 24px;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .back-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s;
        }
        
        .back-btn:hover {
            background: #5568d3;
            transform: translateY(-2px);
        }
        
        .tools-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 20px;
        }
        
        .tool-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }
        
        .tool-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .tool-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 18px;
        }
        
        .tool-title {
            font-size: 18px;
            font-weight: 700;
            color: #2d3748;
        }
        
        .input-group {
            margin-bottom: 15px;
        }
        
        .input-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #4a5568;
            font-size: 13px;
        }
        
        .input-group input,
        .input-group select {
            width: 100%;
            padding: 10px 15px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 14px;
            transition: all 0.3s;
        }
        
        .input-group input:focus,
        .input-group select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            width: 100%;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .output-box {
            background: #1a202c;
            color: #e6f1ff;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
            line-height: 1.6;
            max-height: 400px;
            overflow-y: auto;
            margin-top: 15px;
            white-space: pre-wrap;
            word-break: break-all;
        }
        
        .output-box:empty::before {
            content: 'Output will appear here...';
            color: #718096;
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .status-success {
            background: #48bb78;
            color: white;
        }
        
        .status-error {
            background: #f56565;
            color: white;
        }
        
        .status-warning {
            background: #ed8936;
            color: white;
        }
        
        .spinner {
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-top: 3px solid white;
            border-radius: 50%;
            width: 16px;
            height: 16px;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .info-text {
            font-size: 12px;
            color: #718096;
            margin-top: 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>
                <i class="fas fa-stethoscope"></i>
                System Diagnostics
            </h1>
            <button class="back-btn" onclick="window.location.href='/'">
                <i class="fas fa-arrow-left"></i>
                Back to Dashboard
            </button>
        </div>
        
        <div class="tools-grid">
            <!-- Ping Tool -->
            <div class="tool-card">
                <div class="tool-header">
                    <div class="tool-icon">
                        <i class="fas fa-signal"></i>
                    </div>
                    <div class="tool-title">Ping Test</div>
                </div>
                <div class="input-group">
                    <label>Target Host or IP</label>
                    <input type="text" id="ping-host" placeholder="192.168.1.100 or example.com">
                </div>
                <div class="input-group">
                    <label>Count</label>
                    <input type="number" id="ping-count" value="4" min="1" max="10">
                </div>
                <button class="btn" onclick="runPing()" id="ping-btn">
                    <i class="fas fa-play"></i>
                    Run Ping
                </button>
                <div class="output-box" id="ping-output"></div>
            </div>
            
            <!-- Traceroute Tool -->
            <div class="tool-card">
                <div class="tool-header">
                    <div class="tool-icon">
                        <i class="fas fa-route"></i>
                    </div>
                    <div class="tool-title">Traceroute</div>
                </div>
                <div class="input-group">
                    <label>Target Host or IP</label>
                    <input type="text" id="trace-host" placeholder="192.168.1.100 or example.com">
                </div>
                <button class="btn" onclick="runTraceroute()" id="trace-btn">
                    <i class="fas fa-play"></i>
                    Run Traceroute
                </button>
                <div class="output-box" id="trace-output"></div>
                <div class="info-text">
                    <i class="fas fa-info-circle"></i>
                    Traceroute may take 30-60 seconds to complete
                </div>
            </div>
            
            <!-- Stream Test -->
            <div class="tool-card">
                <div class="tool-header">
                    <div class="tool-icon">
                        <i class="fas fa-video"></i>
                    </div>
                    <div class="tool-title">RTSP Stream Test</div>
                </div>
                <div class="input-group">
                    <label>RTSP URL</label>
                    <input type="text" id="stream-url" placeholder="rtsp://user:pass@192.168.1.100:554/stream">
                </div>
                <button class="btn" onclick="testStream()" id="stream-btn">
                    <i class="fas fa-play"></i>
                    Test Stream
                </button>
                <div class="output-box" id="stream-output"></div>
                <div class="info-text">
                    <i class="fas fa-info-circle"></i>
                    Tests stream connectivity and retrieves video properties
                </div>
            </div>
            
            <!-- Port Scanner -->
            <div class="tool-card">
                <div class="tool-header">
                    <div class="tool-icon">
                        <i class="fas fa-network-wired"></i>
                    </div>
                    <div class="tool-title">Port Check</div>
                </div>
                <div class="input-group">
                    <label>Host</label>
                    <input type="text" id="port-host" placeholder="192.168.1.100">
                </div>
                <div class="input-group">
                    <label>Port</label>
                    <input type="number" id="port-number" placeholder="554" min="1" max="65535">
                </div>
                <button class="btn" onclick="checkPort()" id="port-btn">
                    <i class="fas fa-play"></i>
                    Check Port
                </button>
                <div class="output-box" id="port-output"></div>
            </div>
            
            <!-- FFmpeg Version -->
            <div class="tool-card">
                <div class="tool-header">
                    <div class="tool-icon">
                        <i class="fas fa-film"></i>
                    </div>
                    <div class="tool-title">FFmpeg Info</div>
                </div>
                <button class="btn" onclick="getFFmpegInfo()" id="ffmpeg-btn">
                    <i class="fas fa-info-circle"></i>
                    Get FFmpeg Details
                </button>
                <div class="output-box" id="ffmpeg-output"></div>
            </div>
            
            <!-- System Info -->
            <div class="tool-card">
                <div class="tool-header">
                    <div class="tool-icon">
                        <i class="fas fa-server"></i>
                    </div>
                    <div class="tool-title">System Information</div>
                </div>
                <button class="btn" onclick="getSystemInfo()" id="system-btn">
                    <i class="fas fa-info-circle"></i>
                    Get System Info
                </button>
                <div class="output-box" id="system-output"></div>
            </div>
        </div>
    </div>
    
    <script>
        async function runPing() {
            const host = document.getElementById('ping-host').value;
            const count = document.getElementById('ping-count').value;
            const output = document.getElementById('ping-output');
            const btn = document.getElementById('ping-btn');
            
            if (!host) {
                output.textContent = 'Error: Please enter a host or IP address';
                return;
            }
            
            btn.disabled = true;
            btn.innerHTML = '<div class="spinner"></div> Running...';
            output.textContent = 'Pinging ' + host + '...\\n';
            
            try {
                const response = await fetch('/api/diagnostics/ping', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({host, count: parseInt(count)})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    output.textContent = data.output;
                } else {
                    output.textContent = 'Error: ' + data.error;
                }
            } catch (error) {
                output.textContent = 'Error: ' + error.message;
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-play"></i> Run Ping';
            }
        }
        
        async function runTraceroute() {
            const host = document.getElementById('trace-host').value;
            const output = document.getElementById('trace-output');
            const btn = document.getElementById('trace-btn');
            
            if (!host) {
                output.textContent = 'Error: Please enter a host or IP address';
                return;
            }
            
            btn.disabled = true;
            btn.innerHTML = '<div class="spinner"></div> Running...';
            output.textContent = 'Tracing route to ' + host + '...\\nThis may take up to 60 seconds...\\n';
            
            try {
                const response = await fetch('/api/diagnostics/traceroute', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({host})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    output.textContent = data.output;
                } else {
                    output.textContent = 'Error: ' + data.error;
                }
            } catch (error) {
                output.textContent = 'Error: ' + error.message;
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-play"></i> Run Traceroute';
            }
        }
        
        async function testStream() {
            const url = document.getElementById('stream-url').value;
            const output = document.getElementById('stream-output');
            const btn = document.getElementById('stream-btn');
            
            if (!url) {
                output.textContent = 'Error: Please enter an RTSP URL';
                return;
            }
            
            btn.disabled = true;
            btn.innerHTML = '<div class="spinner"></div> Testing...';
            output.textContent = 'Testing stream: ' + url + '...\\n';
            
            try {
                const response = await fetch('/api/diagnostics/stream-test', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    let result = '✓ Stream is accessible\\n\\n';
                    result += 'Stream Properties:\\n';
                    result += '  Resolution: ' + data.width + 'x' + data.height + '\\n';
                    result += '  Framerate: ' + data.framerate + ' fps\\n';
                    result += '  Codec: ' + data.codec + '\\n';
                    output.textContent = result;
                } else {
                    output.textContent = '✗ Stream test failed\\n\\nError: ' + data.error;
                }
            } catch (error) {
                output.textContent = 'Error: ' + error.message;
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-play"></i> Test Stream';
            }
        }
        
        async function checkPort() {
            const host = document.getElementById('port-host').value;
            const port = document.getElementById('port-number').value;
            const output = document.getElementById('port-output');
            const btn = document.getElementById('port-btn');
            
            if (!host || !port) {
                output.textContent = 'Error: Please enter both host and port';
                return;
            }
            
            btn.disabled = true;
            btn.innerHTML = '<div class="spinner"></div> Checking...';
            output.textContent = 'Checking ' + host + ':' + port + '...\\n';
            
            try {
                const response = await fetch('/api/diagnostics/port-check', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({host, port: parseInt(port)})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    if (data.open) {
                        output.textContent = '✓ Port ' + port + ' is OPEN on ' + host;
                    } else {
                        output.textContent = '✗ Port ' + port + ' is CLOSED on ' + host;
                    }
                } else {
                    output.textContent = 'Error: ' + data.error;
                }
            } catch (error) {
                output.textContent = 'Error: ' + error.message;
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-play"></i> Check Port';
            }
        }
        
        async function getFFmpegInfo() {
            const output = document.getElementById('ffmpeg-output');
            const btn = document.getElementById('ffmpeg-btn');
            
            btn.disabled = true;
            btn.innerHTML = '<div class="spinner"></div> Loading...';
            output.textContent = 'Retrieving FFmpeg information...\\n';
            
            try {
                const response = await fetch('/api/diagnostics/ffmpeg-info');
                const data = await response.json();
                
                if (data.success) {
                    let result = 'FFmpeg Version: ' + data.version + '\\n\\n';
                    result += 'Full Output:\\n' + data.full_output;
                    output.textContent = result;
                } else {
                    output.textContent = 'Error: ' + data.error;
                }
            } catch (error) {
                output.textContent = 'Error: ' + error.message;
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-info-circle"></i> Get FFmpeg Details';
            }
        }
        
        async function getSystemInfo() {
            const output = document.getElementById('system-output');
            const btn = document.getElementById('system-btn');
            
            btn.disabled = true;
            btn.innerHTML = '<div class="spinner"></div> Loading...';
            output.textContent = 'Retrieving system information...\\n';
            
            try {
                const response = await fetch('/api/diagnostics/system-info');
                const data = await response.json();
                
                if (data.success) {
                    let result = 'System Information:\\n\\n';
                    result += 'Platform: ' + data.platform + '\\n';
                    result += 'Python Version: ' + data.python_version + '\\n';
                    result += 'CPU Cores: ' + data.cpu_count + '\\n';
                    result += 'Total Memory: ' + data.total_memory + ' GB\\n';
                    result += 'Available Memory: ' + data.available_memory + ' GB\\n';
                    result += 'Disk Usage: ' + data.disk_usage + '%\\n';
                    result += '\\nMediaMTX Version: ' + data.mediamtx_version + '\\n';
                    result += 'FFmpeg Version: ' + data.ffmpeg_version + '\\n';
                    output.textContent = result;
                } else {
                    output.textContent = 'Error: ' + data.error;
                }
            } catch (error) {
                output.textContent = 'Error: ' + error.message;
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-info-circle"></i> Get System Info';
            }
        }
    </script>
</body>
</html>
'''
