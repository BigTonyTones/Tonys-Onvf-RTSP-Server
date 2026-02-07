"""
IP Management and Whitelisting template
"""

def get_ip_management_html(whitelist):
    return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IP Management - Tonys Onvif Server</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {{
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
            --table-header: #44475a;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}
        
        .header {{
            background: var(--header-bg);
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
            flex-shrink: 0;
        }}
        
        .header h1 {{
            color: var(--accent-purple);
            font-size: 20px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .header-actions {{
            display: flex;
            gap: 12px;
            align-items: center;
        }}

        .back-btn {{
            background: var(--accent-purple);
            color: #282a36;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.3s;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .back-btn:hover {{
            background: var(--accent-pink);
            transform: translateY(-1px);
        }}

        .main-layout {{
            display: flex;
            flex: 1;
            overflow: hidden;
        }}
        
        .sidebar {{
            width: 350px;
            background: var(--sidebar-bg);
            border-right: 1px solid var(--border-color);
            padding: 20px;
            overflow-y: auto;
            flex-shrink: 0;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        
        .content {{
            flex: 1;
            padding: 30px;
            overflow-y: auto;
            background: var(--bg-color);
        }}

        .section-title {{
            font-size: 14px;
            font-weight: 700;
            color: var(--accent-cyan);
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .card {{
            background: var(--card-bg);
            border-radius: 10px;
            padding: 20px;
            border: 1px solid var(--border-color);
            margin-bottom: 20px;
        }}

        .input-group {{
            margin-bottom: 15px;
        }}
        
        .input-group label {{
            display: block;
            margin-bottom: 6px;
            font-weight: 600;
            color: var(--text-muted);
            font-size: 12px;
        }}
        
        .input-group input {{
            width: 100%;
            padding: 10px 12px;
            border: 1px solid var(--border-color);
            background: var(--input-bg);
            color: var(--text-main);
            border-radius: 6px;
            font-size: 14px;
            transition: all 0.2s;
        }}
        
        .input-group input:focus {{
            outline: none;
            border-color: var(--accent-purple);
        }}
        
        .btn {{
            background: var(--accent-purple);
            color: #282a36;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            width: 100%;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }}
        
        .btn:hover {{
            filter: brightness(1.1);
            transform: translateY(-1px);
        }}

        .btn-success {{ background: var(--accent-green); }}
        .btn-danger {{ background: var(--accent-red); color: white; }}

        /* Sessions List */
        .session-item {{
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 10px;
            font-size: 13px;
            border: 1px solid transparent;
            transition: border-color 0.2s;
        }}
        
        .session-item:hover {{
            border-color: var(--accent-purple);
        }}

        .session-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}

        .session-ip {{
            font-weight: 700;
            color: var(--accent-cyan);
            font-family: monospace;
        }}

        .session-badge {{
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 4px;
            background: var(--accent-purple);
            color: #282a36;
            font-weight: 700;
            text-transform: uppercase;
        }}

        .session-badge.whitelisted {{
            background: var(--accent-green);
        }}

        .session-info {{
            color: var(--text-muted);
            font-size: 12px;
        }}

        .session-path {{
            color: var(--accent-pink);
            font-family: monospace;
        }}

        /* Table Styles */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}

        th {{
            text-align: left;
            padding: 12px 15px;
            background: var(--table-header);
            color: var(--accent-purple);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-bottom: 2px solid var(--border-color);
        }}

        td {{
            padding: 15px;
            border-bottom: 1px solid var(--border-color);
            font-size: 14px;
        }}

        tr:hover {{
            background: rgba(255,255,255,0.02);
        }}

        .ip-cell {{
            font-family: 'Consolas', monospace;
            color: var(--accent-cyan);
            font-weight: 600;
        }}

        .cidr-badge {{
            font-size: 11px;
            padding: 2px 6px;
            border-radius: 4px;
            background: rgba(139, 233, 253, 0.1);
            color: var(--accent-cyan);
            border: 1px solid rgba(139, 233, 253, 0.2);
        }}

        .action-btn {{
            background: transparent;
            border: 1px solid var(--border-color);
            color: var(--text-muted);
            width: 32px;
            height: 32px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .action-btn:hover {{
            border-color: var(--accent-red);
            color: var(--accent-red);
            background: rgba(255, 85, 85, 0.1);
        }}

        .empty-table {{
            text-align: center;
            padding: 40px;
            color: var(--text-muted);
            font-style: italic;
        }}

        .badge-new {{
            background: var(--accent-green);
            color: #282a36;
            font-size: 10px;
            padding: 1px 4px;
            border-radius: 3px;
            margin-left: 5px;
            vertical-align: middle;
        }}
        
        .loading-overlay {{
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(40, 42, 54, 0.5);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }}

        .spinner {{
            width: 40px;
            height: 40px;
            border: 4px solid rgba(189, 147, 249, 0.2);
            border-top: 4px solid var(--accent-purple);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}

        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1><i class="fas fa-shield-network"></i> IP Management & Whitelisting</h1>
        <div class="header-actions">
            <a href="/" class="back-btn"><i class="fas fa-arrow-left"></i> Back to Dashboard</a>
        </div>
    </div>
    
    <div class="main-layout">
        <div class="sidebar">
            <!-- Add to Whitelist -->
            <div class="tool-section">
                <div class="section-title"><i class="fas fa-plus-circle"></i> Add to Whitelist</div>
                <div class="card">
                    <div class="input-group">
                        <label>IP Address or CIDR Range</label>
                        <input type="text" id="new-ip" placeholder="e.g. 192.168.1.50 or 10.0.0.0/24">
                        <small style="color: var(--text-muted); font-size: 11px; margin-top: 5px; display: block;">
                            Whitelisted IPs bypass ONVIF and RTSP authentication.
                        </small>
                    </div>
                    <button class="btn btn-success" onclick="addToWhitelist()">
                        <i class="fas fa-plus"></i> Add Entry
                    </button>
                </div>
            </div>

            <!-- Active Sessions -->
            <div class="tool-section" style="flex: 1; display: flex; flex-direction: column; overflow: hidden;">
                <div class="section-title" style="display: flex; justify-content: space-between;">
                    <span><i class="fas fa-satellite-dish"></i> Active Sessions</span>
                    <i class="fas fa-sync-alt" style="cursor: pointer; font-size: 12px;" onclick="refreshSessions()"></i>
                </div>
                <div id="sessions-list" style="overflow-y: auto; flex: 1; padding-right: 5px;">
                    <div style="text-align: center; color: var(--text-muted); padding: 20px;">
                        <i class="fas fa-circle-notch fa-spin"></i> Loading...
                    </div>
                </div>
            </div>
        </div>
        
        <div class="content">
            <div class="section-title"><i class="fas fa-list"></i> Managed Whitelist</div>
            <div class="card" style="padding: 0; overflow: hidden;">
                <table id="whitelist-table">
                    <thead>
                        <tr>
                            <th>Type</th>
                            <th>IP Address / Range</th>
                            <th style="width: 100px; text-align: center;">Actions</th>
                        </tr>
                    </thead>
                    <tbody id="whitelist-body">
                        <!-- Content loaded via JS -->
                    </tbody>
                </table>
                <div id="empty-whitelist" class="empty-table" style="display: none;">
                    No IPs are currently whitelisted.
                </div>
            </div>
            
            <!-- Reboot Warning -->
            <div class="card" style="background: rgba(255, 184, 108, 0.1); border: 2px solid var(--accent-orange); display: flex; align-items: center; gap: 15px; margin-bottom: 25px;">
                <i class="fas fa-redo-alt fa-2x" style="color: var(--accent-orange);"></i>
                <div>
                    <h3 style="color: var(--accent-orange); margin-bottom: 4px; font-size: 16px;">Reboot Required</h3>
                    <p style="font-size: 13px; opacity: 0.9;">A server reboot is necessary to fully apply IP whitelist changes to all streaming services.</p>
                </div>
            </div>

            <div class="card" style="background: rgba(139, 233, 253, 0.05); border-color: rgba(139, 233, 253, 0.2);">
                <div style="color: var(--accent-cyan); font-size: 14px; display: flex; align-items: flex-start; gap: 12px;">
                    <i class="fas fa-info-circle" style="margin-top: 3px;"></i>
                    <div>
                        <strong>What is Whitelisting?</strong>
                        <p style="margin-top: 5px; color: var(--text-main); font-size: 13px; opacity: 0.8;">
                            Whitelisting allows specified devices to connect to your virtual cameras without entering a username or password. 
                            This is useful for local NVRs, automation systems, or trusted wall tablets that don't support robust authentication or where 
                            ease of access is prioritized over security.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div id="loading" class="loading-overlay">
        <div class="spinner"></div>
    </div>

    <script>
        let currentWhitelist = {whitelist};

        function renderWhitelist() {{
            const tbody = document.getElementById('whitelist-body');
            const empty = document.getElementById('empty-whitelist');
            tbody.innerHTML = '';

            if (currentWhitelist.length === 0) {{
                empty.style.display = 'block';
                return;
            }}

            empty.style.display = 'none';
            currentWhitelist.forEach((entry, index) => {{
                const isCidr = entry.includes('/');
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><span class="cidr-badge">${{isCidr ? 'CIDR Block' : 'Single IP'}}</span></td>
                    <td class="ip-cell">${{entry}}</td>
                    <td style="text-align: center;">
                        <button class="action-btn" onclick="removeFromWhitelist(${{index}})" title="Remove">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            }});
        }}

        async function addToWhitelist() {{
            const input = document.getElementById('new-ip');
            const ip = input.value.trim();
            if (!ip) return;

            // Simple validation
            if (!ip.includes('.') && !ip.includes(':')) {{
                alert('Invalid IP address format');
                return;
            }}

            showLoading(true);
            try {{
                const newWhitelist = [...currentWhitelist, ip];
                const response = await fetch('/api/settings/whitelist', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ whitelist: newWhitelist }})
                }});

                if (response.ok) {{
                    currentWhitelist = newWhitelist;
                    renderWhitelist();
                    input.value = '';
                }} else {{
                    const data = await response.json();
                    alert('Error: ' + (data.error || 'Failed to save whitelist'));
                }}
            }} catch (err) {{
                alert('Connection error: ' + err.message);
            }} finally {{
                showLoading(false);
            }}
        }}

        async function removeFromWhitelist(index) {{
            if (!confirm('Are you sure you want to remove this entry?')) return;

            showLoading(true);
            try {{
                const newWhitelist = currentWhitelist.filter((_, i) => i !== index);
                const response = await fetch('/api/settings/whitelist', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ whitelist: newWhitelist }})
                }});

                if (response.ok) {{
                    currentWhitelist = newWhitelist;
                    renderWhitelist();
                }} else {{
                    alert('Failed to update whitelist');
                }}
            }} catch (err) {{
                alert('Connection error: ' + err.message);
            }} finally {{
                showLoading(false);
            }}
        }}

        async function refreshSessions() {{
            const list = document.getElementById('sessions-list');
            try {{
                const response = await fetch('/api/sessions');
                const sessions = await response.json();
                
                if (sessions.length === 0) {{
                    list.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 40px;">No active connections.</div>';
                    return;
                }}

                list.innerHTML = '';
                sessions.forEach(s => {{
                    const item = document.createElement('div');
                    item.className = 'session-item';
                    item.innerHTML = `
                        <div class="session-header">
                            <span class="session-ip">${{s.cleanIp}}</span>
                            <span class="session-badge ${{s.whitelisted ? 'whitelisted' : ''}}">
                                ${{s.whitelisted ? '<i class="fas fa-check"></i> Whitelisted' : 'Authenticated'}}
                            </span>
                        </div>
                        <div class="session-info">
                            Watching <span class="session-path">/${{s.path}}</span><br>
                            via ${{s.protocol}} • ${{getRelativeTime(s.created)}}
                        </div>
                        ${{!s.whitelisted ? `
                            <button class="btn btn-success" style="padding: 4px 8px; font-size: 10px; width: auto; margin-top: 8px;" onclick="quickWhitelist('${{s.cleanIp}}')">
                                <i class="fas fa-plus"></i> Quick Whitelist
                            </button>
                        ` : ''}}
                    `;
                    list.appendChild(item);
                }});
            }} catch (err) {{
                list.innerHTML = '<div style="color: var(--accent-red); padding: 20px;">Failed to load sessions.</div>';
            }}
        }}

        async function quickWhitelist(ip) {{
            const input = document.getElementById('new-ip');
            input.value = ip;
            addToWhitelist();
        }}

        function getRelativeTime(timestamp) {{
            const date = new Date(timestamp);
            const now = new Date();
            const elapsed = Math.floor((now - date) / 1000);
            
            if (elapsed < 60) return 'Just now';
            if (elapsed < 3600) return Math.floor(elapsed / 60) + 'm ago';
            return Math.floor(elapsed / 3600) + 'h ago';
        }}

        function showLoading(show) {{
            document.getElementById('loading').style.display = show ? 'flex' : 'none';
        }}

        // Initial load
        renderWhitelist();
        refreshSessions();
        // Auto-refresh sessions every 10 seconds
        setInterval(refreshSessions, 10000);
    </script>
</body>
</html>
'''
