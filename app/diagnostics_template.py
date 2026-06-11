"""
Diagnostics page template for troubleshooting
"""

def get_diagnostics_html(theme=''):
    from .theme_css import APP_THEME_CSS, body_theme_class
    theme_class = body_theme_class(theme)
    
    html = r'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Diagnostics - Tonys Onvif Server</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-color: #0f1012;
            --sidebar-bg: #151619;
            --card-bg: #1a1b1e;
            --header-bg: #151619;
            --text-main: #f0f2f5;
            --text-muted: #888e99;
            --accent-purple: #3b82f6; /* UniFi Blue */
            --accent-pink: #f43f5e;
            --accent-cyan: #00a2ff;
            --accent-green: #10b981;
            --accent-orange: #f97316;
            --accent-red: #ef4444;
            --border-color: #24262b;
            --input-bg: #1a1b1e;
            --console-bg: #0d0e10;
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
            background: transparent;
            color: var(--accent-purple);
            border: 1.5px solid var(--accent-purple);
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.2s ease;
        }
        
        .back-btn:hover {
            background: color-mix(in srgb, var(--accent-purple) 14%, transparent);
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
            transition: all 0.2s ease;
        }

        .clear-btn:hover {
            background: color-mix(in srgb, var(--text-muted) 14%, transparent);
            border-color: var(--text-muted);
            color: var(--text-main);
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
            padding: 0;
            overflow-y: auto;
            flex-shrink: 0;
            display: flex;
            flex-direction: column;
        }

        .tab-nav {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr 1fr;
            gap: 0;
            padding: 12px 12px 0 12px;
            background: var(--sidebar-bg);
            position: sticky;
            top: 0;
            z-index: 10;
            border-bottom: 1px solid var(--border-color);
        }

        .tab-btn {
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 10px 4px;
            font-size: 11px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.25s;
            border-bottom: 2px solid transparent;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 3px;
        }

        .tab-btn:hover {
            color: var(--text-main);
        }

        .tab-btn.active {
            color: var(--accent-purple);
            border-bottom-color: var(--accent-purple);
        }

        .tab-icon {
            font-size: 16px;
            line-height: 1;
        }

        .tab-panel {
            display: none;
            padding: 15px;
            flex: 1;
        }

        .tab-panel.active {
            display: block;
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
        
        .input-group select option {
            background-color: var(--card-bg);
            color: var(--text-main);
        }
        
        .input-group input:focus,
        .input-group select:focus {
            outline: none;
            border-color: var(--accent-purple);
            box-shadow: 0 0 0 2px rgba(189, 147, 249, 0.1);
        }
        
        .btn {
            background: transparent;
            color: var(--accent-purple);
            border: 1.5px solid var(--accent-purple);
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            width: 100%;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .btn:hover {
            background: color-mix(in srgb, var(--accent-purple) 14%, transparent);
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

        .btn-secondary {
            background: transparent;
            color: var(--text-muted);
            border: 1px solid var(--border-color);
        }

        .btn-secondary:hover {
            background: color-mix(in srgb, var(--text-muted) 14%, transparent);
            border-color: var(--text-muted);
            color: var(--text-main);
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

        .soap-pre {
            background: rgba(0,0,0,0.5);
            padding: 15px;
            border-radius: 8px;
            font-size: 11px;
            overflow-x: auto;
            border: 1px solid var(--border-color);
            color: #f8f8f2;
            margin-bottom: 10px;
            max-height: 400px;
            overflow-y: auto;
        }

        .scan-device-card {
            background: var(--input-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 10px;
            transition: all 0.3s;
            cursor: default;
        }

        .scan-device-card:hover {
            border-color: var(--accent-cyan);
            box-shadow: 0 0 12px rgba(139, 233, 253, 0.1);
        }

        .scan-device-name {
            font-weight: 700;
            font-size: 13px;
            color: var(--accent-cyan);
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .scan-device-name .device-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--accent-green);
            flex-shrink: 0;
            animation: pulse-dot 2s ease-in-out infinite;
        }

        @keyframes pulse-dot {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }

        .scan-device-detail {
            font-size: 11px;
            color: var(--text-muted);
            line-height: 1.6;
        }

        .scan-device-detail span {
            color: var(--text-main);
        }

        .scan-use-btn {
            margin-top: 8px;
            background: transparent;
            border: 1px solid var(--border-color);
            color: var(--text-muted);
            padding: 5px 12px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 11px;
            font-weight: 600;
            transition: all 0.2s;
            width: 100%;
        }

        .scan-use-btn:hover {
            background: color-mix(in srgb, var(--accent-purple) 10%, transparent);
            color: var(--accent-purple);
            border-color: var(--accent-purple);
        }

        .scan-count-badge {
            display: inline-block;
            background: var(--accent-green);
            color: #282a36;
            padding: 2px 10px;
            border-radius: 12px;
            font-weight: 700;
            font-size: 12px;
            margin-bottom: 12px;
        }

        .scan-empty {
            text-align: center;
            padding: 15px;
            color: var(--text-muted);
            font-size: 13px;
            font-style: italic;
        }

        .netscan-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 11px;
            margin-top: 8px;
        }

        .netscan-table th {
            text-align: left;
            color: var(--accent-purple);
            font-weight: 700;
            padding: 6px 8px;
            border-bottom: 1px solid var(--border-color);
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .netscan-table td {
            padding: 5px 8px;
            border-bottom: 1px solid rgba(68, 71, 90, 0.4);
            color: var(--text-main);
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 11px;
        }

        .netscan-table tr:hover td {
            background: rgba(189, 147, 249, 0.05);
        }

        .netscan-status {
            display: inline-block;
            width: 7px;
            height: 7px;
            border-radius: 50%;
            margin-right: 5px;
        }

        .netscan-status.online { background: var(--accent-green); }
        .netscan-status.offline { background: var(--accent-red); opacity: 0.5; }

        .netscan-self-badge {
            display: inline-block;
            background: var(--accent-purple);
            color: #282a36;
            padding: 1px 6px;
            border-radius: 8px;
            font-size: 9px;
            font-weight: 700;
            margin-left: 4px;
        }

        .netscan-mac {
            color: var(--text-muted);
            font-size: 10px;
        }

        .netscan-hostname {
            color: var(--accent-cyan);
            font-size: 10px;
            max-width: 140px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .netscan-summary {
            display: flex;
            gap: 12px;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }

        .netscan-stat {
            background: rgba(68, 71, 90, 0.5);
            padding: 4px 10px;
            border-radius: 8px;
            font-size: 11px;
            color: var(--text-main);
            font-weight: 600;
        }

        .netscan-stat span {
            color: var(--accent-green);
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
            <!-- Tab Navigation -->
            <div class="tab-nav">
                <button class="tab-btn active" onclick="switchTab('discovery')" data-tab="discovery">
                    <span class="tab-icon"><i class="fa-solid fa-binoculars"></i></span> Discovery
                </button>
                <button class="tab-btn" onclick="switchTab('network')" data-tab="network">
                    <span class="tab-icon"><i class="fa-solid fa-network-wired"></i></span> Network
                </button>
                <button class="tab-btn" onclick="switchTab('camera')" data-tab="camera">
                    <span class="tab-icon"><i class="fa-solid fa-video"></i></span> Camera
                </button>
                <button class="tab-btn" onclick="switchTab('system')" data-tab="system">
                    <span class="tab-icon"><i class="fa-solid fa-server"></i></span> System
                </button>
            </div>

            <!-- ============ DISCOVERY TAB ============ -->
            <div class="tab-panel active" id="tab-discovery">
                <div class="tool-section">
                    <div class="tool-title">ONVIF Camera Discovery</div>
                    <div class="input-group">
                        <label>Scan Timeout (seconds)</label>
                        <select id="scan-timeout">
                            <option value="3">3 seconds (Quick)</option>
                            <option value="5" selected>5 seconds (Standard)</option>
                            <option value="8">8 seconds (Thorough)</option>
                            <option value="10">10 seconds (Deep)</option>
                        </select>
                    </div>
                    <button class="btn" onclick="runOnvifScan()" id="scan-btn">
                        Scan for ONVIF Cameras
                    </button>
                    <div id="scan-results" style="margin-top: 15px;"></div>
                </div>

                <div class="tool-section">
                    <div class="tool-title">All Network Devices</div>
                    <div class="input-group">
                        <label>Subnet (leave empty to auto-detect)</label>
                        <input type="text" id="net-subnet" placeholder="e.g. 192.168.1.0/24 (auto-detect)">
                    </div>
                    <button class="btn" onclick="runNetworkScan()" id="netscan-btn">
                        Scan All Devices
                    </button>
                    <div id="netscan-results" style="margin-top: 15px;"></div>
                </div>

                <div class="tool-section">
                    <div class="tool-title">ONVIF Event Live Stream (SOAP Logger)</div>
                    <div style="display: flex; gap: 10px; margin-bottom: 10px;">
                        <button class="btn" id="event-toggle-btn" onclick="toggleEventPolling()">Start Live Logging</button>
                        <button class="btn btn-secondary" onclick="clearEventLogs()">Clear Logs</button>
                    </div>
                    <div id="event-stream-results" style="margin-top: 15px; font-family: monospace; font-size: 11px;"></div>
                </div>
            </div>

            <!-- ============ NETWORK TAB ============ -->
            <div class="tab-panel" id="tab-network">
                <div class="tool-section">
                    <div class="tool-title">Ping</div>
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

                <div class="tool-section">
                    <div class="tool-title">Traceroute</div>
                    <div class="input-group">
                        <label>Target Host or IP</label>
                        <input type="text" id="trace-host" placeholder="e.g. example.com">
                    </div>
                    <button class="btn" onclick="runTraceroute()" id="trace-btn">Run Traceroute</button>
                </div>

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

                <div class="tool-section">
                    <div class="tool-title">Network Interface Bandwidth Monitor</div>
                    <button class="btn" id="bandwidth-toggle-btn" onclick="toggleBandwidthMonitoring()">Start Bandwidth Monitor</button>
                    <div id="bandwidth-results" style="margin-top: 15px;"></div>
                </div>

                <div class="tool-section">
                    <div class="tool-title">MediaMTX Live Connections Monitor</div>
                    <button class="btn" onclick="refreshMediaMtxConnections()" id="mediamtx-connections-btn">Refresh Connections</button>
                    <div id="mediamtx-connections-results" style="margin-top: 15px;"></div>
                </div>
            </div>

            <!-- ============ CAMERA TAB ============ -->
            <div class="tab-panel" id="tab-camera">
                <div class="tool-section">
                    <div class="tool-title">ONVIF Diagnostics</div>
                    <div class="input-group">
                        <label>Quick Select Camera</label>
                        <select id="onvif-camera-select" onchange="handleOnvifCameraSelect()">
                            <option value="">- Manual Input -</option>
                        </select>
                    </div>
                    <div class="divider"></div>
                    <div class="input-group">
                        <label>Host/IP</label>
                        <input type="text" id="onvif-host" placeholder="192.168.1.100">
                    </div>
                    <div class="input-group">
                        <label>ONVIF Port</label>
                        <input type="number" id="onvif-port" value="80" min="1" max="65535">
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <div class="input-group">
                            <label>Username</label>
                            <input type="text" id="onvif-user" placeholder="admin">
                        </div>
                        <div class="input-group">
                            <label>Password</label>
                            <input type="password" id="onvif-pass" placeholder="password">
                        </div>
                    </div>
                    <button class="btn" onclick="runOnvifDiag()" id="onvif-btn">Run ONVIF Diag</button>
                </div>

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

                <div class="tool-section">
                    <div class="tool-title">RTSP Latency & Jitter Analyzer</div>
                    <div class="input-group">
                        <label>Quick Select Camera</label>
                        <select id="analyzer-camera-select" onchange="handleAnalyzerCameraSelect()">
                            <option value="">- Manual Input -</option>
                        </select>
                    </div>
                    <div class="input-group">
                        <label>RTSP Stream URL</label>
                        <input type="text" id="analyzer-stream-url" placeholder="rtsp://192.168.1.100:554/stream">
                    </div>
                    <button class="btn" onclick="runRtspAnalyzer()" id="analyzer-btn">Run RTSP Analysis</button>
                </div>
            </div>

            <!-- ============ SYSTEM TAB ============ -->
            <div class="tab-panel" id="tab-system">
                <div class="tool-section">
                    <div class="tool-title">System Health</div>
                    <button class="btn" onclick="getSystemInfo()" id="system-btn">Get System Info</button>
                </div>
                <div class="tool-section">
                    <div class="tool-title">FFmpeg Environment</div>
                    <button class="btn" onclick="getFFmpegInfo()" id="ffmpeg-btn">Get FFmpeg Info</button>
                </div>
                <div class="tool-section">
                    <div class="tool-title">Local AI Diagnostics</div>
                    <button class="btn" onclick="getAIInfo()" id="ai-btn">Get AI Info</button>
                </div>
                <div class="tool-section">
                    <div class="tool-title">FFmpeg Transcode Calculator</div>
                    <div class="input-group">
                        <label>Select Camera</label>
                        <select id="transcode-camera-select">
                            <option value="">- Choose Camera -</option>
                        </select>
                    </div>
                    <div class="input-group">
                        <label>Encoder Driver</label>
                        <select id="transcode-encoder">
                            <option value="libx264">Software CPU (libx264)</option>
                            <option value="h264_videotoolbox">macOS Hardware VideoToolbox (h264_videotoolbox)</option>
                            <option value="h264_nvenc">Nvidia GPU NVENC (h264_nvenc)</option>
                            <option value="h264_vaapi">Linux Hardware VAAPI (h264_vaapi)</option>
                            <option value="h264_qsv">Intel QuickSync QSV (h264_qsv)</option>
                        </select>
                    </div>
                    <button class="btn" onclick="runTranscodeCalculator()" id="transcode-calc-btn">Run Transcode Test</button>
                </div>
                <div class="tool-section">
                    <div class="tool-title">Storage I/O Performance Check</div>
                    <button class="btn" onclick="runStorageCheck()" id="storage-check-btn">Run Disk Benchmark</button>
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
        function switchTab(tabId) {
            // Hide all tab panels
            document.querySelectorAll('.tab-panel').forEach(panel => {
                panel.classList.remove('active');
            });
            // Deactivate all tab buttons
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            // Show current tab panel
            const activePanel = document.getElementById('tab-' + tabId);
            if (activePanel) {
                activePanel.classList.add('active');
            }
            // Activate current tab button
            const activeBtn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
            if (activeBtn) {
                activeBtn.classList.add('active');
            }
        }

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
                const onvifSelect = document.getElementById('onvif-camera-select');
                const analyzerSelect = document.getElementById('analyzer-camera-select');
                const transcodeSelect = document.getElementById('transcode-camera-select');
                
                camerasData.forEach(cam => {
                    const opt = document.createElement('option');
                    opt.value = cam.id;
                    opt.textContent = cam.name;
                    if (select) select.appendChild(opt);
                    
                    const optOnvif = opt.cloneNode(true);
                    if (onvifSelect) onvifSelect.appendChild(optOnvif);

                    const optAnalyzer = opt.cloneNode(true);
                    if (analyzerSelect) analyzerSelect.appendChild(optAnalyzer);

                    const optTranscode = opt.cloneNode(true);
                    if (transcodeSelect) transcodeSelect.appendChild(optTranscode);
                });
                
                if (camerasData.length > 0) {
                    log(`Loaded ${camerasData.length} existing cameras for quick selection.`, 'info');
                }
            } catch (err) {
                console.error('Failed to load cameras:', err);
            }
        }

        function handleOnvifCameraSelect() {
            const select = document.getElementById('onvif-camera-select');
            if (!select.value) return;

            const camera = camerasData.find(c => c.id == select.value);
            if (camera) {
                document.getElementById('onvif-host').value = camera.host;
                document.getElementById('onvif-port').value = camera.onvifPort || 80;
                document.getElementById('onvif-user').value = camera.onvifUsername || camera.username || '';
                document.getElementById('onvif-pass').value = camera.onvifPassword || camera.password || '';
                log(`Selected Camera for ONVIF Diag: ${camera.name}`, 'purple');
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

        // Global to store scan results for "Use" button
        let scanResults = [];

        async function runOnvifScan() {
            const timeout = document.getElementById('scan-timeout').value;
            const btn = document.getElementById('scan-btn');
            const resultsDiv = document.getElementById('scan-results');

            btn.disabled = true;
            const originalText = btn.textContent;
            btn.innerHTML = '<div class="spinner"></div> Scanning...';
            resultsDiv.innerHTML = '<div style="text-align:center; color: var(--text-muted); font-size: 12px; padding: 10px;">Sending WS-Discovery probes...</div>';

            log(`Starting ONVIF network scan (timeout: ${timeout}s)...`, 'purple');
            log('Sending WS-Discovery multicast probes to 239.255.255.250:3702...', 'info');

            try {
                const response = await fetch('/api/diagnostics/onvif-scan', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({timeout: parseInt(timeout)})
                });

                const data = await response.json();

                if (data.success) {
                    scanResults = data.devices;
                    const count = data.count;

                    if (count === 0) {
                        log('No ONVIF cameras discovered on the network.', 'warn');
                        log('Tips: Ensure cameras are on the same subnet, multicast is not blocked, and cameras have ONVIF enabled.', 'info');
                        resultsDiv.innerHTML = '<div class="scan-empty">No devices found. Check that cameras have ONVIF enabled and are on the same subnet.</div>';
                    } else {
                        log(`✓ Discovered ${count} ONVIF device(s)!`, 'success');

                        let html = `<div class="scan-count-badge">${count} device${count > 1 ? 's' : ''} found</div>`;

                        data.devices.forEach((dev, idx) => {
                            log(`  • ${dev.name} — ${dev.ip}:${dev.port}${dev.manufacturer ? ' (' + dev.manufacturer + ' ' + dev.model + ')' : ''}`, 'info');

                            const mfr = dev.manufacturer ? `<div>Make: <span>${dev.manufacturer}</span></div>` : '';
                            const mdl = dev.model ? `<div>Model: <span>${dev.model}</span></div>` : '';
                            const fw = dev.firmware ? `<div>FW: <span>${dev.firmware}</span></div>` : '';

                            html += `
                                <div class="scan-device-card">
                                    <div class="scan-device-name">
                                        <div class="device-dot"></div>
                                        ${dev.name}
                                    </div>
                                    <div class="scan-device-detail">
                                        <div>IP: <span>${dev.ip}</span></div>
                                        <div>ONVIF Port: <span>${dev.port}</span></div>
                                        ${mfr}${mdl}${fw}
                                    </div>
                                    <button class="scan-use-btn" onclick="useScanResult(${idx})">
                                        Use in ONVIF Diagnostics ↓
                                    </button>
                                </div>
                            `;
                        });

                        resultsDiv.innerHTML = html;
                    }
                } else {
                    log('✗ Network scan failed: ' + data.error, 'error');
                    resultsDiv.innerHTML = '<div class="scan-empty" style="color: var(--accent-red);">Scan failed: ' + data.error + '</div>';
                }
            } catch (error) {
                log('Connection error: ' + error.message, 'error');
                resultsDiv.innerHTML = '<div class="scan-empty" style="color: var(--accent-red);">Error: ' + error.message + '</div>';
            } finally {
                btn.disabled = false;
                btn.textContent = originalText;
                log('--------------------------------------------------');
                consoleEl.scrollTop = consoleEl.scrollHeight;
            }
        }

        function useScanResult(idx) {
            const dev = scanResults[idx];
            if (!dev) return;

            document.getElementById('onvif-host').value = dev.ip;
            document.getElementById('onvif-port').value = dev.port;

            // Clear the camera select dropdown since we're using manual input
            document.getElementById('onvif-camera-select').value = '';

            log(`Loaded scan result into ONVIF Diagnostics: ${dev.name} (${dev.ip}:${dev.port})`, 'purple');
            log('Enter credentials and click "Run ONVIF Diag" to probe this device.', 'info');

            // Switch to the Camera tab automatically
            switchTab('camera');

            // Scroll the sidebar to show the ONVIF Diagnostics section
            document.getElementById('onvif-host').scrollIntoView({ behavior: 'smooth', block: 'center' });
            document.getElementById('onvif-host').focus();
        }

        async function runNetworkScan() {
            const subnet = document.getElementById('net-subnet').value;
            const btn = document.getElementById('netscan-btn');
            const resultsDiv = document.getElementById('netscan-results');

            btn.disabled = true;
            const originalText = btn.textContent;
            btn.innerHTML = '<div class="spinner"></div> Scanning...';
            resultsDiv.innerHTML = '<div style="text-align:center; color: var(--text-muted); font-size: 12px; padding: 10px;">Ping sweeping subnet... this may take 5-10 seconds</div>';

            log('Starting network device scan...', 'purple');
            if (subnet) {
                log(`Scanning subnet: ${subnet}`, 'info');
            } else {
                log('Auto-detecting local subnet...', 'info');
            }

            try {
                const body = {};
                if (subnet) body.subnet = subnet;

                const response = await fetch('/api/diagnostics/network-scan', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(body)
                });

                const data = await response.json();

                if (data.success) {
                    const count = data.count;
                    const reachable = data.devices.filter(d => d.reachable).length;

                    log(`✓ Scan complete — ${count} device(s) found on ${data.subnet}`, 'success');
                    log(`  Server IP: ${data.local_ip}  |  ${reachable} reachable via ping`, 'info');

                    if (count === 0) {
                        resultsDiv.innerHTML = '<div class="scan-empty">No devices found on the subnet.</div>';
                    } else {
                        let html = `
                            <div class="netscan-summary">
                                <div class="netscan-stat">Subnet: <span>${data.subnet}</span></div>
                                <div class="netscan-stat">Devices: <span>${count}</span></div>
                                <div class="netscan-stat">Online: <span>${reachable}</span></div>
                            </div>
                        `;

                        data.devices.forEach(dev => {
                            const statusClass = dev.reachable ? 'online' : 'offline';
                            const selfBadge = dev.is_self ? '<span class="netscan-self-badge">YOU</span>' : '';
                            const hostname = dev.hostname ? `<div class="netscan-hostname" title="${dev.hostname}">${dev.hostname}</div>` : '';
                            const mac = dev.mac ? `<span class="netscan-mac">${dev.mac}</span>` : '';
                            const vendor = dev.vendor ? `<div style="color: var(--accent-orange); font-size: 11px; font-weight: 600;">${dev.vendor}</div>` : '';
                            const deviceType = dev.device_type ? `<span style="display:inline-block; background: rgba(139,233,253,0.15); color: var(--accent-cyan); padding: 1px 7px; border-radius: 6px; font-size: 9px; font-weight: 600; margin-top: 3px;">${dev.device_type}</span>` : '';
                            const ports = dev.open_ports && dev.open_ports.length > 0 
                                ? `<div style="font-size: 9px; color: var(--text-muted); margin-top: 2px;">Ports: ${dev.open_ports.map(p => p.port).join(', ')}</div>` 
                                : '';

                            html += `
                                <div class="scan-device-card" style="padding: 10px;">
                                    <div style="display: flex; align-items: flex-start; gap: 8px;">
                                        <span class="netscan-status ${statusClass}" style="margin-top: 5px;"></span>
                                        <div style="flex: 1; min-width: 0;">
                                            <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
                                                <span style="font-weight: 700; font-size: 12px; color: var(--text-main);">${dev.ip}</span>
                                                ${selfBadge}
                                                ${deviceType}
                                            </div>
                                            ${vendor}
                                            ${hostname}
                                            <div style="margin-top: 2px;">${mac}</div>
                                            ${ports}
                                        </div>
                                    </div>
                                </div>
                            `;

                            // Log each device to console
                            const status = dev.reachable ? '●' : '○';
                            const macStr = dev.mac ? ` [${dev.mac}]` : '';
                            const vendorStr = dev.vendor ? ` — ${dev.vendor}` : '';
                            const typeStr = dev.device_type ? ` (${dev.device_type})` : '';
                            const hostStr = dev.hostname ? ` (${dev.hostname})` : '';
                            const selfStr = dev.is_self ? ' ← this server' : '';
                            const portsStr = dev.open_ports && dev.open_ports.length > 0 ? `  [ports: ${dev.open_ports.map(p => p.port).join(',')}]` : '';
                            log(`  ${status} ${dev.ip}${macStr}${vendorStr}${typeStr}${hostStr}${selfStr}${portsStr}`, dev.reachable ? 'success' : 'warn');
                        });

                        resultsDiv.innerHTML = html;
                    }
                } else {
                    log('✗ Network scan failed: ' + data.error, 'error');
                    resultsDiv.innerHTML = '<div class="scan-empty" style="color: var(--accent-red);">Scan failed: ' + data.error + '</div>';
                }
            } catch (error) {
                log('Connection error: ' + error.message, 'error');
                resultsDiv.innerHTML = '<div class="scan-empty" style="color: var(--accent-red);">Error: ' + error.message + '</div>';
            } finally {
                btn.disabled = false;
                btn.textContent = originalText;
                log('--------------------------------------------------');
                consoleEl.scrollTop = consoleEl.scrollHeight;
            }
        }

        async function runOnvifDiag() {
            const host = document.getElementById('onvif-host').value;
            const port = document.getElementById('onvif-port').value;
            const user = document.getElementById('onvif-user').value;
            const pass = document.getElementById('onvif-pass').value;
            const btn = document.getElementById('onvif-btn');
            
            if (!host || !user || !pass) {
                log('Error: Host, username, and password are required.', 'error');
                return;
            }
            
            btn.disabled = true;
            const originalText = btn.textContent;
            btn.innerHTML = '<div class="spinner"></div> Running...';
            
            log(`Starting ONVIF diagnostics for ${host}:${port}...`, 'purple');
            
            try {
                const response = await fetch('/api/diagnostics/onvif', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({host, port: parseInt(port), username: user, password: pass})
                });
                
                const data = await response.json();
                if (data.success) {
                    log(`✓ ONVIF Connection successful.`, 'success');
                    
                    data.diagnostics.forEach(call => {
                        log(`--- ${call.name} ---`, 'purple');
                        if (call.success) {
                            log(`Status: SUCCESS`, 'success');
                            if (call.request_xml) {
                                const details = document.createElement('details');
                                details.style.margin = '10px 0';
                                details.style.cursor = 'pointer';
                                details.innerHTML = `<summary style="color: var(--accent-cyan); font-weight: bold;">View SOAP Request/Response</summary>`;
                                
                                const reqDiv = document.createElement('div');
                                reqDiv.style.marginTop = '10px';
                                reqDiv.innerHTML = `<div style="color: var(--accent-orange); font-size: 12px; margin-bottom: 5px;">SOAP Request:</div>`;
                                const reqPre = document.createElement('pre');
                                reqPre.className = 'soap-pre';
                                reqPre.textContent = call.request_xml;
                                reqDiv.appendChild(reqPre);

                                const respDiv = document.createElement('div');
                                respDiv.style.marginTop = '10px';
                                respDiv.innerHTML = `<div style="color: var(--accent-green); font-size: 12px; margin-bottom: 5px;">SOAP Response:</div>`;
                                const respPre = document.createElement('pre');
                                respPre.className = 'soap-pre';
                                respPre.textContent = call.response_xml;
                                respDiv.appendChild(respPre);
                                
                                details.appendChild(reqDiv);
                                details.appendChild(respDiv);
                                consoleEl.appendChild(details);
                            }
                        } else {
                            log(`Status: FAILED`, 'error');
                            log(`Error: ${call.error}`, 'error');
                        }
                    });
                } else {
                    log('✗ ONVIF diagnostics failed.', 'error');
                    log('Error: ' + data.error, 'error');
                }
            } catch (error) {
                log('Connection error: ' + error.message, 'error');
            } finally {
                btn.disabled = false;
                btn.textContent = originalText;
                log('--------------------------------------------------');
                consoleEl.scrollTop = consoleEl.scrollHeight;
            }
        }

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
            
            // Log the constructed URL (with password masked) for debugging
            const maskedUrl = fullUrl.replace(/:([^:@]+)@/, ':****@');
            log(`Testing URL: ${maskedUrl}`, 'info');
            
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
        
        async function getAIInfo() {
            const btn = document.getElementById('ai-btn');
            btn.disabled = true;
            const originalText = btn.textContent;
            btn.innerHTML = '<div class="spinner"></div> ...';
            
            log('Gathering local AI and object detection environment metrics...', 'purple');
            
            try {
                const response = await fetch('/api/diagnostics/ai-info');
                const data = await response.json();
                
                if (data.success) {
                    log(`AI Environment Info:`, 'info');
                    
                    // Software packages info
                    log(`  Software Stack:`, 'purple');
                    log(`    • YOLOv8 (ultralytics): ${data.yolo_installed ? '✓ ' + data.yolo_version : '✗ Not Installed'}`);
                    log(`    • PyTorch:              ${data.torch_installed ? '✓ ' + data.torch_version : '✗ Not Installed'}`);
                    
                    // Hardware Acceleration Info
                    log(`  Hardware Acceleration:`, 'purple');
                    let accelType = 'None (CPU only)';
                    if (data.cuda_available) {
                        accelType = `NVIDIA CUDA (Device count: ${data.cuda_device_count}, GPU: ${data.cuda_device_name})`;
                    } else if (data.mps_available) {
                        accelType = 'Apple Silicon MPS (Metal Performance Shaders)';
                    }
                    log(`    • Acceleration Type:    ${accelType}`);
                    log(`    • PyTorch Thread Count: ${data.torch_threads}`);
                    log(`    • Active Compute Device: ${data.selected_device.toUpperCase()}`, 'success');
                    
                    // Global settings config
                    log(`  Global AI Configurations:`, 'purple');
                    log(`    • Default Model:        ${data.config.default_model}`);
                    log(`    • Confidence Threshold: ${data.config.confidence_threshold}%`);
                    log(`    • Motion Sensitivity:   ${data.config.motion_sensitivity}%`);
                    log(`    • Inference Width:      ${data.config.inference_width}px`);
                    log(`    • Event Cooldown:       ${data.config.cooldown_seconds}s`);
                    log(`    • Max Sample Rate:      Every ${data.config.target_interval}s`);

                    // Cached models info
                    log(`  Loaded Models Cache:`, 'purple');
                    if (data.cached_models.length > 0) {
                        data.cached_models.forEach(model => {
                            log(`    • ${model} (Active in memory)`);
                        });
                    } else {
                        log(`    • (No models currently loaded in RAM)`);
                    }

                    // Active Cameras Info
                    log(`  Active AI Camera Pipelines:`, 'purple');
                    if (data.active_ai_cameras.length > 0) {
                        data.active_ai_cameras.forEach(cam => {
                            log(`    • [${cam.name}]`, 'success');
                            log(`        - YOLO Model:      ${cam.model}`);
                            log(`        - Targets:         ${cam.targets.join(', ')}`);
                            log(`        - Inference rate:  ${cam.fps} FPS`);
                            log(`        - Total inferences: ${cam.inference_count}`);
                            log(`        - Avg Latency:     ${cam.avg_latency_ms} ms`);
                            if (cam.last_detection.length > 0) {
                                log(`        - Last Seen:       ${cam.last_detection.join(', ')}`, 'warn');
                            } else {
                                log(`        - Last Seen:       Nothing`);
                            }
                        });
                    } else {
                        log(`    • (No cameras currently running active AI inference)`);
                    }
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

        // RTSP Analyzer Selection
        function handleAnalyzerCameraSelect() {
            const select = document.getElementById('analyzer-camera-select');
            const urlInput = document.getElementById('analyzer-stream-url');
            if (!select.value) {
                urlInput.value = '';
                return;
            }
            const camera = camerasData.find(c => c.id == select.value);
            if (camera) {
                urlInput.value = camera.mainStreamUrl;
            }
        }

        // Run RTSP Analyzer
        async function runRtspAnalyzer() {
            const select = document.getElementById('analyzer-camera-select');
            const urlInput = document.getElementById('analyzer-stream-url');
            const btn = document.getElementById('analyzer-btn');
            
            const body = {};
            if (select.value) {
                body.camera_id = parseInt(select.value);
            } else if (urlInput.value) {
                body.url = urlInput.value;
            } else {
                log('Error: Please select a camera or enter a manual RTSP URL.', 'error');
                return;
            }
            
            btn.disabled = true;
            const originalText = btn.textContent;
            btn.innerHTML = '<div class="spinner"></div> Probing...';
            log('Starting RTSP stream analysis (capturing 3 seconds)...', 'purple');
            
            try {
                const response = await fetch('/api/diagnostics/rtsp-analyzer', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(body)
                });
                const data = await response.json();
                
                if (data.success) {
                    log(`RTSP Stream Health: ${data.health}`, data.health.startsWith('Excellent') ? 'success' : 'warn');
                    log(`  • Probe Connect Time: ${data.connect_time_seconds} seconds`);
                    log(`  • Video Framerate:   ${data.fps} FPS`);
                    log(`  • Stream Speed:      ${data.speed}`);
                    log(`  • Probed Frames:     ${data.frames_probed}`);
                    log(`  • Dropped Frames:    ${data.dropped_frames}`, data.dropped_frames > 0 ? 'warn' : 'info');
                    log(`  • Duplicate Frames:  ${data.duplicated_frames}`);
                    log(`  • Video Bitrate:     ${data.bitrate_kbps} kbps`);
                    
                    // Show raw logs if any
                    const details = document.createElement('details');
                    details.style.margin = '10px 0';
                    details.style.cursor = 'pointer';
                    details.innerHTML = '<summary style="color: var(--accent-cyan); font-weight: bold;">View Raw FFprobe Output</summary>';
                    const pre = document.createElement('pre');
                    pre.className = 'soap-pre';
                    pre.textContent = data.raw_stderr;
                    details.appendChild(pre);
                    consoleEl.appendChild(details);
                } else {
                    log('✗ RTSP analysis failed: ' + data.error, 'error');
                }
            } catch (error) {
                log('Connection error: ' + error.message, 'error');
            } finally {
                btn.disabled = false;
                btn.textContent = originalText;
                log('--------------------------------------------------');
            }
        }

        // ONVIF Events Polling
        let eventPollInterval = null;
        let lastEventTimestamp = null;
        
        async function toggleEventPolling() {
            const btn = document.getElementById('event-toggle-btn');
            const resultsDiv = document.getElementById('event-stream-results');
            
            if (eventPollInterval) {
                clearInterval(eventPollInterval);
                eventPollInterval = null;
                btn.textContent = 'Start Live Logging';
                btn.style.background = '';
                btn.style.borderColor = '';
                btn.style.color = '';
                log('ONVIF Event live logging stopped.', 'info');
            } else {
                btn.textContent = 'Stop Live Logging';
                btn.style.background = '#3c1e1e';
                btn.style.borderColor = '#6b2d2d';
                btn.style.color = '#fca5a5';
                log('ONVIF Event live logging started (polling /api/onvif/events every 2s)...', 'purple');
                
                lastEventTimestamp = new Date().toISOString();
                
                eventPollInterval = setInterval(async () => {
                    try {
                        const response = await fetch('/api/onvif/events');
                        const events = await response.json();
                        
                        if (Array.isArray(events)) {
                            const newEvents = events.filter(e => !lastEventTimestamp || e.timestamp > lastEventTimestamp);
                            
                            newEvents.forEach(evt => {
                                if (!lastEventTimestamp || evt.timestamp > lastEventTimestamp) {
                                    lastEventTimestamp = evt.timestamp;
                                }
                                
                                const timeStr = new Date(evt.timestamp).toLocaleTimeString();
                                const div = document.createElement('div');
                                div.style.padding = '4px 8px';
                                div.style.borderBottom = '1px solid rgba(255,255,255,0.05)';
                                
                                const topicColor = evt.value === 'true' ? 'var(--accent-red)' : 'var(--accent-green)';
                                div.innerHTML = `<span style="color: var(--text-muted)">[${timeStr}]</span> <strong style="color: var(--accent-purple)">${evt.camera_name}</strong>: <span style="color: var(--accent-cyan)">${evt.topic}</span> = <span style="color: ${topicColor}">${evt.value}</span>`;
                                resultsDiv.insertBefore(div, resultsDiv.firstChild);
                                
                                while (resultsDiv.children.length > 100) {
                                    resultsDiv.removeChild(resultsDiv.lastChild);
                                }
                                
                                log(`[Event] ${evt.camera_name} - ${evt.topic} = ${evt.value}`, evt.value === 'true' ? 'warn' : 'success');
                            });
                        }
                    } catch (err) {
                        console.error('Error polling events:', err);
                    }
                }, 2000);
            }
        }
        
        async function clearEventLogs() {
            try {
                await fetch('/api/onvif/events/clear', {method: 'POST'});
                document.getElementById('event-stream-results').innerHTML = '';
                log('ONVIF Events log cleared on server.', 'success');
            } catch (err) {
                log('Failed to clear events log: ' + err.message, 'error');
            }
        }

        // Bandwidth Monitor Polling
        let bandwidthInterval = null;
        
        function toggleBandwidthMonitoring() {
            const btn = document.getElementById('bandwidth-toggle-btn');
            const resultsDiv = document.getElementById('bandwidth-results');
            
            if (bandwidthInterval) {
                clearInterval(bandwidthInterval);
                bandwidthInterval = null;
                btn.textContent = 'Start Bandwidth Monitor';
                btn.style.background = '';
                btn.style.borderColor = '';
                btn.style.color = '';
                log('Bandwidth monitoring stopped.', 'info');
            } else {
                btn.textContent = 'Stop Bandwidth Monitor';
                btn.style.background = '#3c1e1e';
                btn.style.borderColor = '#6b2d2d';
                btn.style.color = '#fca5a5';
                log('Bandwidth monitoring started (updating every 1.5s)...', 'purple');
                
                bandwidthInterval = setInterval(async () => {
                    try {
                        const response = await fetch('/api/diagnostics/bandwidth-monitor');
                        const data = await response.json();
                        
                        if (data.success) {
                            let html = `
                                <table class="netscan-table" style="width: 100%;">
                                    <thead>
                                        <tr>
                                            <th>NIC</th>
                                            <th>RX (Down)</th>
                                            <th>TX (Up)</th>
                                            <th>Total Recv</th>
                                            <th>Total Sent</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                            `;
                            
                            data.interfaces.forEach(nic => {
                                const rxSpeed = nic.rx_speed_kbps > 1024 
                                    ? `${(nic.rx_speed_kbps / 1024).toFixed(1)} MB/s`
                                    : `${nic.rx_speed_kbps.toFixed(0)} KB/s`;
                                    
                                const txSpeed = nic.tx_speed_kbps > 1024
                                    ? `${(nic.tx_speed_kbps / 1024).toFixed(1)} MB/s`
                                    : `${nic.tx_speed_kbps.toFixed(0)} KB/s`;
                                    
                                html += `
                                    <tr>
                                        <td style="font-weight: bold; color: var(--accent-cyan);">${nic.interface}</td>
                                        <td style="color: var(--accent-green);">${rxSpeed}</td>
                                        <td style="color: var(--accent-orange);">${txSpeed}</td>
                                        <td>${nic.rx_total_mb.toFixed(1)} MB</td>
                                        <td>${nic.tx_total_mb.toFixed(1)} MB</td>
                                    </tr>
                                `;
                            });
                            
                            html += '</tbody></table>';
                            resultsDiv.innerHTML = html;
                        }
                    } catch (err) {
                        console.error('Error fetching bandwidth metrics:', err);
                    }
                }, 1500);
            }
        }

        // MediaMTX Connections
        async function refreshMediaMtxConnections() {
            const btn = document.getElementById('mediamtx-connections-btn');
            const resultsDiv = document.getElementById('mediamtx-connections-results');
            
            btn.disabled = true;
            const originalText = btn.textContent;
            btn.innerHTML = '<div class="spinner"></div> Loading...';
            
            log('Querying MediaMTX active streaming sessions...', 'purple');
            
            try {
                const response = await fetch('/api/sessions');
                const sessions = await response.json();
                
                if (Array.isArray(sessions)) {
                    log(`✓ Retrieved ${sessions.length} active session(s).`, 'success');
                    
                    if (sessions.length === 0) {
                        resultsDiv.innerHTML = '<div class="scan-empty">No active RTSP/WebRTC viewing sessions.</div>';
                    } else {
                        let html = `
                            <table class="netscan-table" style="width: 100%;">
                                <thead>
                                    <tr>
                                        <th>IP Address</th>
                                        <th>Stream Path</th>
                                        <th>Protocol</th>
                                        <th>Access</th>
                                    </tr>
                                </thead>
                                <tbody>
                        `;
                        
                        sessions.forEach(s => {
                            const badgeColor = s.whitelisted ? 'var(--accent-green)' : 'var(--accent-orange)';
                            const badgeText = s.whitelisted ? 'Whitelist' : 'Public/LAN';
                            
                            html += `
                                <tr>
                                    <td style="font-weight: bold; color: var(--text-main);">${s.cleanIp}</td>
                                    <td style="color: var(--accent-purple);">${s.path || '/'}</td>
                                    <td><span style="background: rgba(139,233,253,0.15); color: var(--accent-cyan); padding: 1px 6px; border-radius: 6px; font-size: 10px;">${s.protocol}</span></td>
                                    <td><span style="color: ${badgeColor}; font-size: 10px; font-weight: bold;">${badgeText}</span></td>
                                </tr>
                            `;
                            log(`  • Client: ${s.cleanIp} | Path: ${s.path} | Protocol: ${s.protocol}`, 'info');
                        });
                        
                        html += '</tbody></table>';
                        resultsDiv.innerHTML = html;
                    }
                } else {
                    log('Error reading sessions data', 'error');
                }
            } catch (err) {
                log('Connection error: ' + err.message, 'error');
            } finally {
                btn.disabled = false;
                btn.textContent = originalText;
                log('--------------------------------------------------');
            }
        }

        // FFmpeg Transcode Resource Calculator
        async function runTranscodeCalculator() {
            const camSelect = document.getElementById('transcode-camera-select');
            const encSelect = document.getElementById('transcode-encoder');
            const btn = document.getElementById('transcode-calc-btn');
            
            if (!camSelect.value) {
                log('Error: Please select a camera to transcode.', 'error');
                return;
            }
            
            btn.disabled = true;
            const originalText = btn.textContent;
            btn.innerHTML = '<div class="spinner"></div> Testing...';
            
            const cameraName = camSelect.options[camSelect.selectedIndex].text;
            const encoderName = encSelect.options[encSelect.selectedIndex].text;
            
            log(`Running FFmpeg transcode load test for camera "${cameraName}"...`, 'purple');
            log(`Using Encoder Driver: ${encoderName} (probing 4 seconds)...`, 'info');
            
            try {
                const response = await fetch('/api/diagnostics/transcode-calculator', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        camera_id: parseInt(camSelect.value),
                        encoder: encSelect.value
                    })
                });
                const data = await response.json();
                
                if (data.success) {
                    const isOptimal = data.status.startsWith('Optimal');
                    log(`Transcode Status: ${data.status}`, isOptimal ? 'success' : 'warn');
                    log(`  • Transcode speed:    ${data.speed}`);
                    log(`  • Processed FPS:      ${data.fps} FPS`);
                    log(`  • Total frames:       ${data.frames_transcoded}`);
                    log(`  • Average CPU load:   ${data.cpu_load_percent}%`);
                    log(`  • Connect/Run time:   ${data.probed_duration_seconds} seconds`);
                    
                    const details = document.createElement('details');
                    details.style.margin = '10px 0';
                    details.style.cursor = 'pointer';
                    details.innerHTML = '<summary style="color: var(--accent-cyan); font-weight: bold;">View Raw FFmpeg Stderr Output</summary>';
                    const pre = document.createElement('pre');
                    pre.className = 'soap-pre';
                    pre.textContent = data.raw_stderr;
                    details.appendChild(pre);
                    consoleEl.appendChild(details);
                } else {
                    log('✗ Transcode calculator failed: ' + data.error, 'error');
                }
            } catch (err) {
                log('Connection error: ' + err.message, 'error');
            } finally {
                btn.disabled = false;
                btn.textContent = originalText;
                log('--------------------------------------------------');
            }
        }

        // Storage I/O Check
        async function runStorageCheck() {
            const btn = document.getElementById('storage-check-btn');
            
            btn.disabled = true;
            const originalText = btn.textContent;
            btn.innerHTML = '<div class="spinner"></div> Benchmarking...';
            
            log('Starting Storage I/O Read/Write Speed Benchmark (20MB test)...', 'purple');
            log('Benchmarking directory. Please wait a few seconds...', 'info');
            
            try {
                const response = await fetch('/api/diagnostics/storage-check');
                const data = await response.json();
                
                if (data.success) {
                    log('✓ Storage benchmark complete.', 'success');
                    log(`Storage Path: ${data.storage_path}`, 'info');
                    log(`  • Read Speed:         ${data.read_speed_mbs} MB/s`, 'success');
                    log(`  • Write Speed:        ${data.write_speed_mbs} MB/s`, 'success');
                    log(`  • Performance Rating: ${data.performance_rating}`, 'purple');
                    log(`  • Disk Space:         ${data.free_gb} GB Free / ${data.total_gb} GB Total (${data.used_percent}% used)`);
                } else {
                    log('✗ Storage check failed: ' + data.error, 'error');
                }
            } catch (err) {
                log('Connection error: ' + err.message, 'error');
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

    # Inject theme styling rules
    themed_style = f"""
        /* Dashboard theme palette (only active when body has a theme class) */
{APP_THEME_CSS}
        body {{
            --bg-color: var(--app-bg, #0f1012);
            --sidebar-bg: var(--app-header, #151619);
            --card-bg: var(--app-card, #1a1b1e);
            --header-bg: var(--app-header, #151619);
            --text-main: var(--app-title, #f0f2f5);
            --text-muted: var(--app-muted, #888e99);
            --accent-purple: var(--app-accent, #3b82f6);
            --accent-pink: var(--app-accent2, #f43f5e);
            --accent-cyan: var(--app-accent, #00a2ff);
            --accent-green: var(--app-success, #10b981);
            --accent-orange: var(--app-accent2, #f97316);
            --accent-red: var(--app-danger, #ef4444);
            --border-color: var(--app-border, #24262b);
            --input-bg: var(--app-input, #1a1b1e);
            --console-bg: var(--app-input, #0d0e10);
        }}
    """
    
    html = html.replace('</style>', themed_style + '\n    </style>')
    html = html.replace('<body>', f'<body class="{theme_class}">')
    return html
