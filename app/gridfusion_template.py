import json
import platform

def get_gridfusion_html(current_settings=None, grid_fusion_config=None):
    """Generate GridFusion Editor Page HTML"""
    
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GridFusion Editor - Tonys Onvif Server</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-accent: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-color: #6366f1;
            --accent-hover: #4f46e5;
            --danger: #ef4444;
            --success: #22c55e;
            --border: #334155;
            --bg-hover: #3e4c5e;
            --card-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Inter', sans-serif;
        }}

        body {{
            background-color: var(--bg-primary);
            color: var(--text-primary);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}

        header {{
            background-color: var(--bg-secondary);
            padding: 1rem 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--border);
            box-shadow: var(--card-shadow);
        }}

        .logo-area {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .logo-text {{
            font-size: 1.25rem;
            font-weight: 700;
            background: linear-gradient(to right, #818cf8, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .nav-actions {{
            display: flex;
            gap: 1rem;
        }}

        .btn {{
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            font-weight: 600;
            font-size: 0.875rem;
            cursor: pointer;
            transition: all 0.2s;
            border: none;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .btn-primary {{
            background-color: var(--accent-color);
            color: white;
        }}

        .btn-primary:hover {{
            background-color: var(--accent-hover);
        }}

        .btn-secondary {{
            background-color: var(--bg-accent);
            color: var(--text-primary);
        }}

        .btn-secondary:hover {{
            background-color: #475569;
        }}

        .btn-danger {{
            background-color: var(--danger);
            color: white;
        }}

        .main-container {{
            display: flex;
            flex: 1;
            overflow: hidden;
            padding: 1.5rem;
            gap: 1.5rem;
        }}

        .sidebar {{
            width: 320px;
            background-color: var(--bg-secondary);
            border-radius: 1rem;
            border: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: var(--card-shadow);
        }}

        .sidebar-header {{
            padding: 1.25rem;
            border-bottom: 1px solid var(--border);
            background-color: rgba(255,255,255,0.02);
        }}

        .sidebar-title {{
            font-size: 0.875rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
        }}

        .camera-list {{
            flex: 1;
            overflow-y: auto;
            padding: 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }}

        .camera-item {{
            background-color: var(--bg-accent);
            padding: 0.75rem;
            border-radius: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            border: 1px solid transparent;
            transition: all 0.2s;
            cursor: grab;
            user-select: none;
        }}

        .camera-item:hover {{
            border-color: var(--accent-color);
            transform: translateY(-2px);
            background-color: #3f4e64;
        }}

        .camera-preview-small {{
            width: 60px;
            height: 36px;
            background-color: #000;
            border-radius: 0.375rem;
            background-size: cover;
            background-position: center;
        }}

        .camera-info {{
            flex: 1;
            min-width: 0;
        }}

        .camera-name {{
            font-size: 0.875rem;
            font-weight: 600;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .add-cam-btn {{
            background-color: var(--accent-color);
            color: white;
            width: 28px;
            height: 28px;
            border-radius: 0.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            transition: transform 0.2s;
        }}

        .add-cam-btn:hover {{
            transform: scale(1.1);
        }}

        .editor-area {{
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }}

        .toolbar {{
            background-color: var(--bg-secondary);
            padding: 1rem 1.5rem;
            border-radius: 1rem;
            border: 1px solid var(--border);
            display: flex;
            align-items: center;
            gap: 2rem;
            flex-wrap: wrap;
            box-shadow: var(--card-shadow);
        }}

        .toolbar-group {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .toolbar-label {{
            font-size: 0.75rem;
            font-weight: 700;
            color: var(--text-secondary);
            text-transform: uppercase;
        }}

        .select-input, .text-input {{
            background-color: var(--bg-accent);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 0.5rem 0.75rem;
            border-radius: 0.5rem;
            font-size: 0.875rem;
            outline: none;
            transition: all 0.2s;
        }}
        
        .select-input:focus, .text-input:focus {{
            border-color: var(--accent-color);
            background-color: var(--bg-hover);
            color: #ffffff;
        }}

        .select-input option {{
            background-color: var(--bg-secondary);
            color: var(--text-primary);
        }}

        .props-panel {{
            padding: 1.25rem;
            border-top: 1px solid var(--border);
            background-color: rgba(255,255,255,0.01);
            display: none;
        }}

        .props-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.75rem;
            margin-top: 0.75rem;
        }}

        .prop-item {{
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }}

        .prop-label {{
            font-size: 0.65rem;
            font-weight: 700;
            color: var(--text-secondary);
            text-transform: uppercase;
        }}

        .prop-input {{
            width: 100%;
            padding: 0.4rem;
            font-size: 0.75rem;
            background: #0f172a;
            border: 1px solid var(--border);
            color: white;
            border-radius: 4px;
        }}


        .canvas-container {{
            flex: 1;
            background-color: #000;
            border-radius: 1rem;
            padding: 2rem;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            position: relative;
            border: 1px solid var(--border);
            box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06);
        }}
        
        .canvas {{
            background-color: #94a3b8;
            position: relative;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
            border: 1px solid #64748b;
        }}
        
        .grid-overlay {{
            position: absolute;
            inset: 0;
            pointer-events: none;
            background-image: radial-gradient(circle, #f8fafc 1px, transparent 1px);
            background-size: 20px 20px;
            opacity: 0.15;
        }}

        .placed-camera {{
            position: absolute;
            background-color: #1e293b;
            border: 2px solid var(--accent-color);
            cursor: move;
            display: flex;
            flex-direction: column;
            border-radius: 4px;
            overflow: hidden;
            z-index: 5;
        }}

        .placed-camera.selected {{
            border-color: var(--success);
            box-shadow: 0 0 20px rgba(34, 197, 94, 0.3);
            z-index: 10;
        }}

        .placed-snapshot {{
            flex: 1;
            width: 100%;
            object-fit: cover;
            background-color: #000;
            opacity: 0.8;
            pointer-events: none;
        }}

        .placed-overlay {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(0,0,0,0.7);
            padding: 0.25rem 0.5rem;
            font-size: 0.7rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: space-between;
            color: white;
            z-index: 10;
        }}
        
        .camera-switcher {{
            background: rgba(15, 23, 42, 0.9);
            border: 1px solid var(--border);
            color: #f8fafc;
            font-size: 0.75rem;
            font-weight: 600;
            outline: none;
            max-width: 140px;
            cursor: pointer;
            padding: 2px 4px;
            border-radius: 4px;
            transition: border-color 0.2s;
        }}
        
        .camera-switcher:focus {{
            border-color: var(--accent-color);
            background: #1e293b;
            color: #fff;
        }}
        
        .camera-switcher option {{
            background: #1e293b;
            color: #f8fafc;
            padding: 8px;
        }}

        .stream-switcher {{
            background: rgba(15, 23, 42, 0.9);
            border: 1px solid var(--border);
            color: #f8fafc;
            font-size: 0.65rem;
            font-weight: 800;
            outline: none;
            cursor: pointer;
            padding: 2px 4px;
            border-radius: 4px;
            transition: all 0.2s;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .stream-switcher:hover {{
            border-color: var(--accent-color);
            background: var(--bg-secondary);
        }}

        .remove-btn {{
            position: absolute;
            top: 0.5rem;
            right: 0.5rem;
            background-color: rgba(239, 68, 68, 0.9);
            color: white;
            width: 22px;
            height: 22px;
            border-radius: 0.25rem;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 11;
            font-size: 1rem;
            transition: all 0.2s;
        }}

        .remove-btn:hover {{
            background-color: var(--danger);
            transform: scale(1.1);
        }}

        .resizer {{
            position: absolute;
            width: 12px;
            height: 12px;
            background-color: white;
            bottom: 0;
            right: 0;
            cursor: nwse-resize;
            z-index: 12;
            border-radius: 2px;
            border: 1px solid var(--accent-color);
        }}

        /* Custom Dropdown Styling */
        .grid-select-wrapper {{
            position: relative;
            width: 220px;
        }}

        .grid-select-trigger {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            background-color: var(--bg-accent);
            border: 1px solid var(--border);
            padding: 0.5rem 0.75rem;
            border-radius: 0.5rem;
            cursor: pointer;
            font-size: 0.875rem;
        }}

        .grid-options {{
            position: absolute;
            top: calc(100% + 5px);
            left: 0;
            right: 0;
            background-color: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            max-height: 400px;
            overflow-y: auto;
            z-index: 100;
            display: none;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        }}

        .grid-option {{
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 0.75rem;
            cursor: pointer;
            transition: background 0.2s;
        }}

        .grid-option:hover {{
            background-color: var(--bg-accent);
        }}

        .grid-icon {{
            width: 40px;
            height: 24px;
            border: 1px solid var(--text-secondary);
            position: relative;
            background-color: rgba(0,0,0,0.3);
        }}

        .grid-icon-box {{
            position: absolute;
            border: 0.5px solid var(--text-secondary);
        }}

        /* Switch Styling */
        .switch {{
            position: relative;
            display: inline-block;
            width: 40px;
            height: 20px;
        }}

        .switch input {{
            opacity: 0;
            width: 0;
            height: 0;
        }}

        .slider {{
            position: absolute;
            cursor: pointer;
            inset: 0;
            background-color: var(--bg-accent);
            transition: .4s;
            border-radius: 20px;
        }}

        .slider:before {{
            position: absolute;
            content: "";
            height: 14px;
            width: 14px;
            left: 3px;
            bottom: 3px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }}

        input:checked + .slider {{
            background-color: var(--success);
        }}
        input:checked + .slider:before {{
            transform: translateX(20px);
        }}

        #stats-bar {{
            background-color: var(--bg-secondary);
            padding: 0.5rem 2rem;
            font-size: 0.75rem;
            display: flex;
            justify-content: space-between;
            color: var(--text-secondary);
            border-top: 1px solid var(--border);
        }}
        
        .btn-xs {{
            padding: 2px 6px;
            font-size: 10px;
            background: var(--bg-accent);
            border: 1px solid var(--border);
            color: var(--text-primary);
            border-radius: 4px;
            cursor: pointer;
        }}
        .btn-xs:hover {{ background: var(--bg-hover); }}
        .btn-xs-danger {{
            padding: 2px 6px;
            font-size: 10px;
            background: rgba(239, 68, 68, 0.2);
            border: 1px solid var(--danger);
            color: var(--danger);
            border-radius: 4px;
            cursor: pointer;
        }}
        .btn-xs-danger:hover {{ background: var(--danger); color: white; }}
        
        .btn-xs-primary {{
            padding: 2px 6px;
            font-size: 10px;
            background: rgba(16, 185, 129, 0.2);
            border: 1px solid var(--success);
            color: var(--success);
            border-radius: 4px;
            cursor: pointer;
        }}
        .btn-xs-primary:hover {{ background: var(--success); color: white; }}
    </style>
</head>
<body>
    <header>
        <div class="logo-area">
            <a href="/" style="text-decoration: none; display: flex; align-items: center; gap: 10px;">
                <div class="logo-text">GridFusion Editor</div>
            </a>
            <div style="background: var(--bg-accent); padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; color: var(--accent-color);">BETA</div>
        </div>
        <div class="nav-actions">
            <div id="save-status" style="display: flex; align-items: center; gap: 10px; margin-right: 20px; font-size: 13px; opacity: 0;">
                <span style="color: var(--success);">✓ Config Saved</span>
            </div>
            <button class="btn btn-secondary" onclick="window.location.href='/'">Back to Dashboard</button>
            <button class="btn btn-primary" onclick="saveGridFusion()">Save & Apply Changes</button>
        </div>
    </header>

    <div class="main-container">
        <div class="sidebar">
            <div style="padding: 1rem; border-bottom: 1px solid var(--border); background: var(--bg-hover);">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 0.5rem;">
                    <div class="sidebar-title">Layouts</div>
                    <div style="display:flex; gap: 5px;">
                        <button class="btn-xs-primary" onclick="createNewLayout()" title="New Layout">Add</button>
                        <button class="btn-xs-danger" onclick="deleteCurrentLayout()" title="Delete Layout">Del</button>
                    </div>
                </div>
                <select id="layout-select" onchange="switchLayout(this.value)" style="width:100%; background: var(--bg-primary); color: white; border: 1px solid var(--border); padding: 5px; border-radius: 4px; margin-bottom: 5px;">
                    <!-- Populated via JS -->
                </select>
                <input type="text" id="layout-name-edit" style="width:100%; background: rgba(0,0,0,0.2); color: var(--text-secondary); border: 1px solid transparent; padding: 4px; border-radius: 4px; font-size: 11px;" placeholder="Layout Name" onchange="updateLayoutName(this.value)">
            </div>

            <div class="sidebar-header">
                <div class="sidebar-title">Available Cameras</div>
            </div>
            <div id="camera-list" class="camera-list">
                <!-- Populated via JS -->
            </div>
            
            <div id="props-panel" class="props-panel">
                <div id="props-cam-name" style="font-size: 0.75rem; font-weight: 700; color: var(--accent-color); margin-bottom: 0.75rem;">No Camera Selected</div>
                <div class="props-grid">
                    <div class="prop-item">
                        <span class="prop-label">X Pos</span>
                        <input type="number" id="prop-x" class="prop-input" oninput="manualPropUpdate()">
                    </div>
                    <div class="prop-item">
                        <span class="prop-label">Y Pos</span>
                        <input type="number" id="prop-y" class="prop-input" oninput="manualPropUpdate()">
                    </div>
                    <div class="prop-item">
                        <span class="prop-label">Width</span>
                        <input type="number" id="prop-w" class="prop-input" oninput="manualPropUpdate()">
                    </div>
                    <div class="prop-item">
                        <span class="prop-label">Height</span>
                        <input type="number" id="prop-h" class="prop-input" oninput="manualPropUpdate()">
                    </div>
                    <div class="prop-item" style="grid-column: span 2;">
                        <span class="prop-label">Stream Type</span>
                        <select id="prop-stream" class="prop-input" onchange="manualPropUpdate()">
                            <option value="main">Main (High Res)</option>
                            <option value="sub">Sub (Low Res)</option>
                        </select>
                    </div>
                </div>
            </div>

            <div style="padding: 1.25rem; border-top: 1px solid var(--border); background: rgba(0,0,0,0.1);">
                <button class="btn btn-secondary" style="width:100%; justify-content: center;" onclick="refreshSnapshots()">Refresh Snapshots</button>
            </div>
        </div>

        <div class="editor-area">
            <div class="toolbar">
                <div class="toolbar-group">
                    <label class="switch">
                        <input type="checkbox" id="gf-enabled" checked onchange="updateGFEnabled()">
                        <span class="slider"></span>
                    </label>
                    <span style="font-size: 0.875rem; font-weight: 600;">Stream Active</span>
                </div>

                <div class="toolbar-group">
                    <span class="toolbar-label">Resolution</span>
                    <select class="select-input" id="resolution-select" onchange="handleResolutionChange(this.value)">
                        <optgroup label="HD Standards">
                            <option value="1280x720">1280x720 (720p HD)</option>
                            <option value="1920x1080" selected>1920x1080 (1080p FHD)</option>
                        </optgroup>
                        <optgroup label="Quad HD (2K)">
                            <option value="2560x1440">2560x1440 (2K QHD)</option>
                            <option value="2048x1080">2048x1080 (2K DCI)</option>
                        </optgroup>
                        <optgroup label="Ultra HD (4K)">
                            <option value="3840x2160">3840x2160 (4K UHD)</option>
                            <option value="4096x2160">4096x2160 (4K DCI)</option>
                        </optgroup>
                        <optgroup label="Extreme High Res">
                            <option value="5120x2880">5120x2880 (5K UHD+)</option>
                            <option value="7680x4320">7680x4320 (8K Ultra HD)</option>
                            <option value="10240x4320">10240x4320 (10K Ultra HD)</option>
                        </optgroup>
                        <optgroup label="IT Standards">
                            <option value="1600x1200">1600x1200 (UXGA Classic)</option>
                            <option value="1024x768">1024x768 (XGA Compact)</option>
                        </optgroup>
                        <optgroup label="Other">
                            <option value="custom">Custom...</option>
                        </optgroup>
                    </select>
                    <div id="custom-res-inputs" style="display:none; align-items: center; gap: 5px;">
                        <input type="number" id="custom-w" class="text-input" style="width: 80px;" placeholder="Width">
                        <span>×</span>
                        <input type="number" id="custom-h" class="text-input" style="width: 80px;" placeholder="Height">
                        <button class="btn btn-primary" style="padding: 0.25rem 0.5rem;" onclick="applyCustomRes()">Set</button>
                    </div>
                </div>

                <div class="toolbar-group">
                    <span class="toolbar-label">Grid Layout</span>
                    <div class="grid-select-wrapper">
                        <div class="grid-select-trigger" onclick="toggleGridOptions()">
                            <span id="current-grid-name">10 Cameras</span>
                            <span>▾</span>
                        </div>
                        <div id="grid-options" class="grid-options">
                            <!-- Populated via JS -->
                        </div>
                    </div>
                </div>

                <div class="toolbar-group">
                    <button class="btn btn-secondary" style="padding: 0.5rem;" title="Clear Canvas" onclick="clearCanvas()">Clear</button>
                </div>

                <div style="flex: 1;"></div>

                <div class="toolbar-group" style="gap: 1.5rem;">
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <span class="toolbar-label">Snap</span>
                        <label class="switch">
                            <input type="checkbox" id="gf-snap" checked>
                            <span class="slider"></span>
                        </label>
                    </div>

                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <span class="toolbar-label">Grid</span>
                        <label class="switch">
                            <input type="checkbox" id="gf-show-grid" checked onchange="toggleGridOverlay()">
                            <span class="slider"></span>
                        </label>
                    </div>
                    
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <span class="toolbar-label">Snapshots</span>
                        <label class="switch">
                            <input type="checkbox" id="gf-show-snapshots" checked onchange="renderGrid()">
                            <span class="slider"></span>
                        </label>
                    </div>

                    <div style="display: flex; align-items: center; gap: 8px; background: rgba(0,0,0,0.3); padding: 5px 10px; border-radius: 8px; border: 1px solid var(--border); margin-left: 0.5rem;">
                        <span style="font-size: 10px; color: var(--text-secondary); font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">RTSP URL</span>
                        <code id="rtsp-url-display" style="font-size: 11px; color: var(--accent-color); font-weight: 600; font-family: 'JetBrains Mono', monospace; background: transparent; padding: 0;">rtsp://localhost:8554/matrix</code>
                        <button class="btn btn-secondary" style="padding: 2px 8px; font-size: 10px; height: 22px; line-height: 1;" onclick="copyRTSPUrl(this)">Copy</button>
                    </div>
                </div>
            </div>

            <div class="canvas-container" id="canvas-container">
                <div id="canvas" class="canvas">
                    <div id="grid-overlay" class="grid-overlay"></div>
                    <!-- Placed cameras -->
                </div>
            </div>
        </div>
    </div>

    <div id="stats-bar">
        <div id="canvas-info">Canvas: 1920 x 1080 | Scaling: 100%</div>
        <div style="color: var(--text-secondary);">Tonys Onvif Server GridFusion Engine</div>
    </div>

    <script>
        function copyRTSPUrl(btn) {{
            const url = document.getElementById('rtsp-url-display').textContent;
            navigator.clipboard.writeText(url).then(() => {{
                // Fallback if btn not passed
                if (!btn && window.event) btn = window.event.target;
                
                if (btn) {{
                    const originalText = btn.textContent;
                    const originalBg = btn.style.backgroundColor;
                    
                    btn.textContent = 'Copied!';
                    btn.style.backgroundColor = '#48bb78'; // Green
                    btn.style.color = 'white';
                    
                    setTimeout(() => {{
                        btn.textContent = originalText;
                        btn.style.backgroundColor = originalBg;
                        btn.style.color = '';
                    }}, 2000);
                }}
            }});
        }}

        let cameras = [];
        // Load full config data
        let gfData = {json.dumps(grid_fusion_config) if grid_fusion_config else '{ "layouts": [] }'};
        
        // Initialize layouts array
        let gfLayouts = gfData.layouts || [];
        
        // Fallback or legacy handling
        if (gfLayouts.length === 0) {{
            // Check if legacy single-layout config exists
            if (gfData.cameras) {{
                gfData.id = 'matrix';
                gfData.name = 'Default Layout';
                gfLayouts.push(gfData);
            }} else {{
                // Create default if completely empty
                gfLayouts.push({{
                    id: 'matrix',
                    name: 'Default Layout',
                    enabled: false,
                    resolution: '1920x1080',
                    cameras: [],
                    snapToGrid: true,
                    showGrid: true,
                    showSnapshots: true
                }});
            }}
        }}

        // Set current layout
        let gfConfig = gfLayouts[0]; // Active working copy reference
        let appSettings = {json.dumps(current_settings) if current_settings else '{ "rtspPort": 8554 }'};
        
        let snapshots = {{}};
        let selectedIdx = -1;
        let isDragging = false;
        let isResizing = false;
        let dragTarget = null;
        let dragOffset = {{ x: 0, y: 0 }};
        let lastMousePos = {{ x: 0, y: 0 }};
        let raftId = null;

        // Layout Management Functions
        function updateLayoutSelector() {{
            const select = document.getElementById('layout-select');
            select.innerHTML = '';
            gfLayouts.forEach(l => {{
                const opt = document.createElement('option');
                opt.value = l.id;
                opt.textContent = l.name || l.id;
                if (l.id === gfConfig.id) opt.selected = true;
                select.appendChild(opt);
            }});
            
            // Update name edit field
            document.getElementById('layout-name-edit').value = gfConfig.name || gfConfig.id;
            
            // Update RTSP URL display
            const port = appSettings.rtspPort || 8554;
            const hostname = window.location.hostname;
            const url = `rtsp://${{hostname}}:${{port}}/${{gfConfig.id}}`;
            document.getElementById('rtsp-url-display').textContent = url;
            
            // Update stats bar
            // document.getElementById('current-grid-name').textContent = gfConfig.name || gfConfig.id;
        }}

        function switchLayout(id) {{
            const layout = gfLayouts.find(l => l.id === id);
            if (layout) {{
                gfConfig = layout;
                selectedIdx = -1;
                syncUI(); // Re-render everything
            }}
        }}

        function createNewLayout() {{
            const name = prompt("Enter new layout name:", "New Layout");
            if (!name) return;
            
            const id = 'matrix_' + Math.floor(Math.random() * 10000);
            const newLayout = {{
                id: id,
                name: name,
                enabled: true,
                resolution: '1920x1080',
                cameras: [],
                snapToGrid: true,
                showGrid: true,
                showSnapshots: true
            }};
            
            gfLayouts.push(newLayout);
            gfConfig = newLayout;
            selectedIdx = -1;
            syncUI();
        }}
        
        function deleteCurrentLayout() {{
            if (gfLayouts.length <= 1) {{
                alert("Cannot delete the last layout.");
                return;
            }}
            
            if (!confirm(`Delete layout "${{gfConfig.name}}"? This cannot be undone.`)) return;
            
            const idx = gfLayouts.findIndex(l => l.id === gfConfig.id);
            if (idx !== -1) {{
                gfLayouts.splice(idx, 1);
                gfConfig = gfLayouts[0]; // Switch to first available
                selectedIdx = -1;
                syncUI();
            }}
        }}

        function updateLayoutName(newName) {{
            if (newName) {{
                gfConfig.name = newName;
                updateLayoutSelector(); // Refresh list names
            }}
        }}

        // Initialize
        async function init() {{
            await fetchCameras();
            populateGridOptions();
            syncUI();
            
            // Re-run canvas update on window resize
            window.addEventListener('resize', updateCanvasSize);
            
            // Keyboard controls for fine-tuning
            window.addEventListener('keydown', handleGlobalKeydown);
            
            // Auto refresh snapshots after short delay
            setTimeout(refreshSnapshots, 1000);
        }}

        function handleGlobalKeydown(e) {{
            if (selectedIdx === -1) return;
            
            // Don't move if typing in an input
            if (['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;
            
            const cam = gfConfig.cameras[selectedIdx];
            const step = e.shiftKey ? 10 : 1;
            
            // Canvas boundaries
            const canvas = document.getElementById('canvas');
            const maxW = parseInt(canvas.getAttribute('data-w'));
            const maxH = parseInt(canvas.getAttribute('data-h'));
            const scale = parseFloat(canvas.getAttribute('data-scale')) || 1;
            
            let moved = false;
            if (e.key === 'ArrowLeft') {{ cam.x -= step; moved = true; }}
            else if (e.key === 'ArrowRight') {{ cam.x += step; moved = true; }}
            else if (e.key === 'ArrowUp') {{ cam.y -= step; moved = true; }}
            else if (e.key === 'ArrowDown') {{ cam.y += step; moved = true; }}
            
            if (moved) {{
                e.preventDefault();
                cam.x = Math.max(0, Math.min(cam.x, maxW - cam.w));
                cam.y = Math.max(0, Math.min(cam.y, maxH - cam.h));
                
                // Update element position directly
                const el = document.querySelector(`.placed-camera[data-idx="${{selectedIdx}}"]`);
                if (el) {{
                    el.style.left = (cam.x * scale) + 'px';
                    el.style.top = (cam.y * scale) + 'px';
                }}
                updatePropsPanel();
            }}
        }}

        async function fetchCameras() {{
            try {{
                const resp = await fetch('/api/cameras');
                cameras = await resp.json();
                populateSidebar();
            }} catch (e) {{
                console.error("Failed to fetch cameras", e);
            }}
        }}

        function populateSidebar() {{
            const list = document.getElementById('camera-list');
            list.innerHTML = '';
            
            cameras.forEach(cam => {{
                const item = document.createElement('div');
                item.className = 'camera-item';
                item.draggable = true;
                item.innerHTML = `
                    <div class="camera-preview-small" id="side-snap-${{cam.id}}"></div>
                    <div class="camera-info">
                        <div class="camera-name">${{cam.name}}</div>
                        <div style="font-size: 0.65rem; color: var(--text-secondary);">${{cam.status.toUpperCase()}}</div>
                    </div>
                    <div class="add-cam-btn" onclick="addCamera(${{cam.id}})">+</div>
                `;
                
                item.ondragstart = (e) => {{
                    e.dataTransfer.setData('camId', cam.id);
                }};
                
                list.appendChild(item);
                
                if (snapshots[cam.id]) {{
                    document.getElementById(`side-snap-${{cam.id}}`).style.backgroundImage = `url(${{snapshots[cam.id]}})`;
                }}
            }});
        }}

        function syncUI() {{
            updateLayoutSelector();
            document.getElementById('gf-enabled').checked = gfConfig.enabled;
            
            const standardRes = [
                '1920x1080', '2560x1440', '3840x2160', '5120x2880', '7680x4320', 
                '10240x4320', '1280x720', '2048x1080', '4096x2160', '1600x1200', '1024x768'
            ];
            
            if (gfConfig.resolution) {{
                if (standardRes.includes(gfConfig.resolution)) {{
                    document.getElementById('resolution-select').value = gfConfig.resolution;
                    document.getElementById('custom-res-inputs').style.display = 'none';
                }} else {{
                    document.getElementById('resolution-select').value = 'custom';
                    document.getElementById('custom-res-inputs').style.display = 'flex';
                    const [w, h] = gfConfig.resolution.split('x');
                    document.getElementById('custom-w').value = w || '';
                    document.getElementById('custom-h').value = h || '';
                }}
            }}
            
            document.getElementById('gf-snap').checked = gfConfig.snapToGrid !== false;
            document.getElementById('gf-show-grid').checked = gfConfig.showGrid !== false;
            document.getElementById('gf-show-snapshots').checked = gfConfig.showSnapshots !== false;
            
            toggleGridOverlay();
            updateCanvasSize();
            renderGrid();
        }}

        function updateCanvasSize() {{
            let res = gfConfig.resolution || '1920x1080';
            const [w, h] = res.split('x').map(Number);
            const canvas = document.getElementById('canvas');
            const container = document.getElementById('canvas-container');
            
            const padding = 60;
            const availW = container.clientWidth - padding;
            const availH = container.clientHeight - padding;
            const scale = Math.min(availW / w, availH / h, 1);
            
            canvas.style.width = (w * scale) + 'px';
            canvas.style.height = (h * scale) + 'px';
            canvas.setAttribute('data-w', w);
            canvas.setAttribute('data-h', h);
            canvas.setAttribute('data-scale', scale);
            
            document.getElementById('canvas-info').textContent = `Canvas: ${{w}} x ${{h}} | Scaling: ${{Math.round(scale * 100)}}%`;
            
            renderGrid();
        }}

        function renderGrid() {{
            const canvas = document.getElementById('canvas');
            const scale = parseFloat(canvas.getAttribute('data-scale')) || 1;
            
            // Clear existing but keep overlay
            Array.from(canvas.children).forEach(el => {{
                if (el.id !== 'grid-overlay') el.remove();
            }});
            
            const showSnaps = document.getElementById('gf-show-snapshots').checked;

            gfConfig.cameras.forEach((gfCam, idx) => {{
                const cam = cameras.find(c => c.id === gfCam.id);
                if (!cam) return;
                
                const el = document.createElement('div');
                el.className = 'placed-camera' + (selectedIdx === idx ? ' selected' : '');
                el.style.left = (gfCam.x * scale) + 'px';
                el.style.top = (gfCam.y * scale) + 'px';
                el.style.width = (gfCam.w * scale) + 'px';
                el.style.height = (gfCam.h * scale) + 'px';
                el.setAttribute('data-idx', idx);
                
                let inner = '';
                if (showSnaps && snapshots[cam.id]) {{
                    inner += `<img src="${{snapshots[cam.id]}}" class="placed-snapshot">`;
                }} else {{
                    inner += `<div style="flex:1; background:#0f172a; display:flex; align-items:center; justify-content:center; color:#334155; font-size:2rem; font-weight:800;">CAM</div>`;
                }}
                
                inner += `
                    <div class="placed-overlay">
                        <select class="camera-switcher" onchange="changeCameraInBox(${{idx}}, this.value)" onpointerdown="event.stopPropagation()" onclick="event.stopPropagation()">
                            ${{cameras.map(c => `<option value="${{c.id}}" ${{c.id === gfCam.id ? 'selected' : ''}}>${{c.name}}</option>`).join('')}}
                        </select>
                        <select class="stream-switcher" onchange="changeStreamType(${{idx}}, this.value)" onpointerdown="event.stopPropagation()" onclick="event.stopPropagation()" title="Switch Stream">
                            <option value="main" ${{gfCam.stream_type === 'main' ? 'selected' : ''}}>Main</option>
                            <option value="sub" ${{gfCam.stream_type !== 'main' ? 'selected' : ''}}>Sub</option>
                        </select>
                    </div>
                    <div class="remove-btn" onclick="removeCamera(event, ${{idx}})">×</div>
                    <div class="resizer"></div>
                `;
                
                el.innerHTML = inner;
                el.onpointerdown = startInteraction;
                
                canvas.appendChild(el);
            }});
        }}
        
        function changeCameraInBox(idx, newId) {{
            gfConfig.cameras[idx].id = parseInt(newId);
            renderGrid();
        }}
        
        function changeStreamType(idx, type) {{
            gfConfig.cameras[idx].stream_type = type;
            renderGrid();
        }}
        
        function handleResolutionChange(val) {{
            if (val === 'custom') {{
                document.getElementById('custom-res-inputs').style.display = 'flex';
            }} else {{
                document.getElementById('custom-res-inputs').style.display = 'none';
                gfConfig.resolution = val;
                updateCanvasSize();
            }}
        }}
        
        function applyCustomRes() {{
            const w = parseInt(document.getElementById('custom-w').value);
            const h = parseInt(document.getElementById('custom-h').value);
            if (w > 0 && h > 0) {{
                gfConfig.resolution = `${{w}}x${{h}}`;
                updateCanvasSize();
            }} else {{
                alert("Please enter valid width and height");
            }}
        }}

        function addCamera(id) {{
            const cam = cameras.find(c => c.id === id);
            if (!cam) return;
            
            // Add at 0,0 with default size
            gfConfig.cameras.push({{
                id: id,
                x: 0,
                y: 0,
                w: 640,
                h: 360,
                stream_type: 'sub'
            }});
            
            selectedIdx = gfConfig.cameras.length - 1;
            renderGrid();
        }}

        function removeCamera(e, idx) {{
            e.stopPropagation();
            gfConfig.cameras.splice(idx, 1);
            selectedIdx = -1;
            renderGrid();
        }}

        function clearCanvas() {{
            if (confirm("Clear all cameras from the layout?")) {{
                gfConfig.cameras = [];
                selectedIdx = -1;
                renderGrid();
            }}
        }}

        function startInteraction(e) {{
            if (e.target.classList.contains('remove-btn') || e.target.classList.contains('camera-switcher')) return;
            
            const idx = parseInt(this.getAttribute('data-idx'));
            if (selectedIdx !== idx) {{
                // Update selection class without full re-render
                const oldSel = document.querySelector('.placed-camera.selected');
                if (oldSel) oldSel.classList.remove('selected');
                
                selectedIdx = idx;
                this.classList.add('selected');
                updatePropsPanel();
            }}
            
            dragTarget = this;
            isResizing = e.target.classList.contains('resizer');
            isDragging = !isResizing;
            
            const rect = this.getBoundingClientRect();
            dragOffset = {{
                x: e.clientX - rect.left,
                y: e.clientY - rect.top
            }};
            lastMousePos = {{ x: e.clientX, y: e.clientY }};
            
            window.addEventListener('pointermove', handleInteraction);
            window.addEventListener('pointerup', endInteraction);
            e.preventDefault();
        }}

        function handleInteraction(e) {{
            if (!dragTarget) return;
            
            const canvas = document.getElementById('canvas');
            const scale = parseFloat(canvas.getAttribute('data-scale')) || 1;
            const canvasRect = canvas.getBoundingClientRect();
            const gfCam = gfConfig.cameras[selectedIdx];
            const snap = document.getElementById('gf-snap').checked ? 20 : 1;
            
            const maxW = parseInt(canvas.getAttribute('data-w'));
            const maxH = parseInt(canvas.getAttribute('data-h'));

            if (isDragging) {{
                let nx = (e.clientX - canvasRect.left - dragOffset.x) / scale;
                let ny = (e.clientY - canvasRect.top - dragOffset.y) / scale;
                
                nx = Math.round(nx / snap) * snap;
                ny = Math.round(ny / snap) * snap;
                
                gfCam.x = Math.max(0, Math.min(nx, maxW - gfCam.w));
                gfCam.y = Math.max(0, Math.min(ny, maxH - gfCam.h));
            }} else if (isResizing) {{
                const dx = (e.clientX - lastMousePos.x) / scale;
                const dy = (e.clientY - lastMousePos.y) / scale;
                
                let nw = gfCam.w + dx;
                let nh = gfCam.h + dy;
                
                nw = Math.round(nw / snap) * snap;
                nh = Math.round(nh / snap) * snap;
                
                gfCam.w = Math.max(100, Math.min(nw, maxW - gfCam.x));
                gfCam.h = Math.max(56, Math.min(nh, maxH - gfCam.y));
                
                lastMousePos.x = e.clientX;
                lastMousePos.y = e.clientY;
            }}
            
            // Performance Optimization: Use requestAnimationFrame
            if (raftId) cancelAnimationFrame(raftId);
            raftId = requestAnimationFrame(() => {{
                if (!dragTarget) return;
                dragTarget.style.left = (gfCam.x * scale) + 'px';
                dragTarget.style.top = (gfCam.y * scale) + 'px';
                dragTarget.style.width = (gfCam.w * scale) + 'px';
                dragTarget.style.height = (gfCam.h * scale) + 'px';
                updatePropsPanel();
            }});
        }}

        function updatePropsPanel() {{
            const panel = document.getElementById('props-panel');
            if (selectedIdx === -1) {{
                panel.style.display = 'none';
                return;
            }}
            
            const cam = gfConfig.cameras[selectedIdx];
            const camInfo = cameras.find(c => c.id === cam.id);
            
            panel.style.display = 'block';
            document.getElementById('props-cam-name').textContent = camInfo ? camInfo.name : 'Unknown Camera';
            
            // Optimization: Only update if not currently typing
            if (document.activeElement.id !== 'prop-x') document.getElementById('prop-x').value = Math.round(cam.x);
            if (document.activeElement.id !== 'prop-y') document.getElementById('prop-y').value = Math.round(cam.y);
            if (document.activeElement.id !== 'prop-w') document.getElementById('prop-w').value = Math.round(cam.w);
            if (document.activeElement.id !== 'prop-h') document.getElementById('prop-h').value = Math.round(cam.h);
            document.getElementById('prop-stream').value = cam.stream_type || 'sub';
        }}

        function manualPropUpdate() {{
            if (selectedIdx === -1) return;
            const cam = gfConfig.cameras[selectedIdx];
            
            cam.x = parseFloat(document.getElementById('prop-x').value) || 0;
            cam.y = parseFloat(document.getElementById('prop-y').value) || 0;
            cam.w = parseFloat(document.getElementById('prop-w').value) || 100;
            cam.h = parseFloat(document.getElementById('prop-h').value) || 56;
            cam.stream_type = document.getElementById('prop-stream').value;
            
            // Clamp to canvas
            const canvas = document.getElementById('canvas');
            const maxW = parseInt(canvas.getAttribute('data-w'));
            const maxH = parseInt(canvas.getAttribute('data-h'));
            
            cam.x = Math.max(0, Math.min(cam.x, maxW - cam.w));
            cam.y = Math.max(0, Math.min(cam.y, maxH - cam.h));
            
            // Re-render to reflect manual changes
            const scale = parseFloat(canvas.getAttribute('data-scale')) || 1;
            const el = document.querySelector(`.placed-camera[data-idx="${{selectedIdx}}"]`);
            if (el) {{
                el.style.left = (cam.x * scale) + 'px';
                el.style.top = (cam.y * scale) + 'px';
                el.style.width = (cam.w * scale) + 'px';
                el.style.height = (cam.h * scale) + 'px';
            }}
        }}

        function endInteraction() {{
            dragTarget = null;
            isDragging = false;
            isResizing = false;
            window.removeEventListener('pointermove', handleInteraction);
            window.removeEventListener('pointerup', endInteraction);
            renderGrid();
        }}

        function toggleGridOverlay() {{
            const show = document.getElementById('gf-show-grid').checked;
            document.getElementById('grid-overlay').style.display = show ? 'block' : 'none';
        }}

        function updateGFEnabled() {{
            gfConfig.enabled = document.getElementById('gf-enabled').checked;
        }}

        async function refreshSnapshots() {{
            if (cameras.length === 0) return;
            
            const btn = document.querySelector('.sidebar button');
            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = 'Updating...';

            const ps = cameras.map(async cam => {{
                try {{
                    const resp = await fetch(`/api/gridfusion/snapshot/${{cam.id}}`);
                    if (resp.ok) {{
                        const blob = await resp.blob();
                        if (snapshots[cam.id]) URL.revokeObjectURL(snapshots[cam.id]);
                        snapshots[cam.id] = URL.createObjectURL(blob);
                    }}
                }} catch(e) {{}}
            }});
            
            await Promise.all(ps);
            
            btn.disabled = false;
            btn.textContent = originalText;
            
            populateSidebar();
            renderGrid();
        }}

        async function saveGridFusion() {{
            const btn = document.querySelector('.btn-primary');
            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = 'Saving...';
            
            // Sync final config
            gfConfig.enabled = document.getElementById('gf-enabled').checked;
            // gfConfig.resolution is updated via handleResolutionChange / applyCustomRes
            gfConfig.snapToGrid = document.getElementById('gf-snap').checked;
            gfConfig.showGrid = document.getElementById('gf-show-grid').checked;
            gfConfig.showSnapshots = document.getElementById('gf-show-snapshots').checked;

            try {{
                const resp = await fetch('/api/gridfusion', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ layouts: gfLayouts }})
                }});
                
                if (resp.ok) {{
                    const status = document.getElementById('save-status');
                    status.style.opacity = '1';
                    setTimeout(() => status.style.opacity = '0', 3000);
                }} else {{
                    alert("Error saving config");
                }}
            }} catch(e) {{
                alert("Connection error");
            }} finally {{
                btn.disabled = false;
                btn.textContent = originalText;
            }}
        }}

        // --- Layout Preset Management ---

        function toggleGridOptions() {{
            const opt = document.getElementById('grid-options');
            opt.style.display = opt.style.display === 'block' ? 'none' : 'block';
        }}

        window.onclick = function(event) {{
            if (!event.target.closest('.grid-select-wrapper')) {{
                document.getElementById('grid-options').style.display = 'none';
            }}
        }}

        function populateGridOptions() {{
            const container = document.getElementById('grid-options');
            container.innerHTML = '';
            
            for (let i = 1; i <= 26; i++) {{
                const opt = document.createElement('div');
                opt.className = 'grid-option';
                opt.onclick = () => applyPreset(i);
                
                const icon = createGridIcon(i);
                
                opt.innerHTML = `
                    <div class="grid-icon">${{icon}}</div>
                    <span>${{i}} Camera${{i > 1 ? 's' : ''}}</span>
                `;
                container.appendChild(opt);
            }}
        }}

        function createGridIcon(count) {{
            // Simple visual representation logic for icons
            let boxes = '';
            const w = 40, h = 24;
            
            if (count === 1) boxes = `<div class="grid-icon-box" style="inset:0"></div>`;
            else if (count === 2) boxes = `<div class="grid-icon-box" style="left:0; top:0; bottom:0; width:50%"></div><div class="grid-icon-box" style="right:0; top:0; bottom:0; width:50%"></div>`;
            else if (count === 3) {{
                boxes = `<div class="grid-icon-box" style="left:0; top:0; bottom:0; width:66%"></div>`;
                boxes += `<div class="grid-icon-box" style="right:0; top:0; height:50%; width:33%"></div>`;
                boxes += `<div class="grid-icon-box" style="right:0; bottom:0; height:50%; width:33%"></div>`;
            }}
            else if (count === 4) {{
                for (let i=0; i<4; i++) boxes += `<div class="grid-icon-box" style="left:${{(i%2)*50}}%; top:${{Math.floor(i/2)*50}}%; width:50%; height:50%"></div>`;
            }}
            else {{
                // Fallback for larger numbers: just a 3x3 or generic grid look
                const cols = Math.ceil(Math.sqrt(count));
                const rows = Math.ceil(count / cols);
                const bw = 100/cols, bh = 100/rows;
                for (let i=0; i<Math.min(count, 9); i++) {{
                    boxes += `<div class="grid-icon-box" style="left:${{(i%cols)*bw}}%; top:${{Math.floor(i/cols)*bh}}%; width:${{bw}}%; height:${{bh}}%"></div>`;
                }}
            }}
            return boxes;
        }}

        function applyPreset(count) {{
            if (gfConfig.cameras.length > 0 && !confirm(`Replace current layout with ${{count}} camera preset?`)) return;
            
            const res = gfConfig.resolution || '1920x1080';
            const [maxW, maxH] = res.split('x').map(Number);
            
            const newLayout = [];
            const availableCams = cameras.length > 0 ? cameras : Array.from({{length: 26}}, (_, i) => ({{id: i+1}}));

            // Grid logic based on common NVR/VMS layouts
            if (count === 1) {{
                newLayout.push({{ id: availableCams[0].id, x: 0, y: 0, w: maxW, h: maxH, stream_type: 'sub' }});
            }}
            else if (count === 2) {{
                // Side by side
                newLayout.push({{ id: availableCams[0].id, x: 0, y: 0, w: maxW/2, h: maxH, stream_type: 'sub' }});
                newLayout.push({{ id: availableCams[1 % availableCams.length].id, x: maxW/2, y: 0, w: maxW/2, h: maxH, stream_type: 'sub' }});
            }}
            else if (count === 3) {{
                // 1 big on left, 2 small on right
                newLayout.push({{ id: availableCams[0].id, x: 0, y: 0, w: (maxW*2)/3, h: maxH, stream_type: 'sub' }});
                newLayout.push({{ id: availableCams[1 % availableCams.length].id, x: (maxW*2)/3, y: 0, w: maxW/3, h: maxH/2, stream_type: 'sub' }});
                newLayout.push({{ id: availableCams[2 % availableCams.length].id, x: (maxW*2)/3, y: maxH/2, w: maxW/3, h: maxH/2, stream_type: 'sub' }});
            }}
            else if (count === 4) {{
                // 2x2
                for (let i=0; i<4; i++) {{
                    newLayout.push({{ id: availableCams[i % availableCams.length].id, x: (i%2)*(maxW/2), y: Math.floor(i/2)*(maxH/2), w: maxW/2, h: maxH/2, stream_type: 'sub' }});
                }}
            }}
            else if (count === 5 || count === 6) {{
                // 1 large (2x2 units), rest small (1x1 units) in a 3x3 grid
                const unitW = maxW/3, unitH = maxH/3;
                newLayout.push({{ id: availableCams[0].id, x: 0, y: 0, w: unitW*2, h: unitH*2, stream_type: 'sub' }});
                // Right Column
                newLayout.push({{ id: availableCams[1 % availableCams.length].id, x: unitW*2, y: 0, w: unitW, h: unitH, stream_type: 'sub' }});
                newLayout.push({{ id: availableCams[2 % availableCams.length].id, x: unitW*2, y: unitH, w: unitW, h: unitH, stream_type: 'sub' }});
                // Bottom Column
                newLayout.push({{ id: availableCams[3 % availableCams.length].id, x: 0, y: unitH*2, w: unitW, h: unitH, stream_type: 'sub' }});
                newLayout.push({{ id: availableCams[4 % availableCams.length].id, x: unitW, y: unitH*2, w: unitW, h: unitH, stream_type: 'sub' }});
                if (count === 6) {{
                    newLayout.push({{ id: availableCams[5 % availableCams.length].id, x: unitW*2, y: unitH*2, w: unitW, h: unitH, stream_type: 'sub' }});
                }}
            }}
            else if (count >= 7 && count <= 9) {{
                // 3x3 grid
                const cols = 3, rows = 3;
                const unitW = maxW/cols, unitH = maxH/rows;
                for (let i=0; i<count; i++) {{
                    newLayout.push({{ id: availableCams[i % availableCams.length].id, x: (i%cols)*unitW, y: Math.floor(i/cols)*unitH, w: unitW, h: unitH, stream_type: 'sub' }});
                }}
            }}
            else if (count >= 10 && count <= 13) {{
                // 1 big (3x3 units), rest small (1x1 units) in a 4x4 grid
                const unitW = maxW/4, unitH = maxH/4;
                newLayout.push({{ id: availableCams[0].id, x: 0, y: 0, w: unitW*3, h: unitH*3, stream_type: 'sub' }});
                // Find empty slots in 4x4
                let idx = 1;
                for (let r=0; r<4; r++) {{
                    for (let c=0; c<4; c++) {{
                        if (r < 3 && c < 3) continue; // occupied by large
                        if (idx < count) {{
                            newLayout.push({{ id: availableCams[idx % availableCams.length].id, x: c*unitW, y: r*unitH, w: unitW, h: unitH, stream_type: 'sub' }});
                            idx++;
                        }}
                    }}
                }}
            }}
            else if (count >= 14 && count <= 16) {{
                // 4x4 grid
                const cols = 4, rows = 4;
                const unitW = maxW/cols, unitH = maxH/rows;
                for (let i=0; i<count; i++) {{
                    newLayout.push({{ id: availableCams[i % availableCams.length].id, x: (i%cols)*unitW, y: Math.floor(i/cols)*unitH, w: unitW, h: unitH, stream_type: 'sub' }});
                }}
            }}
            else if (count >= 17 && count <= 25) {{
                // 5x5 grid
                const cols = 5, rows = 5;
                const unitW = maxW/cols, unitH = maxH/rows;
                for (let i=0; i<count; i++) {{
                    newLayout.push({{ id: availableCams[i % availableCams.length].id, x: (i%cols)*unitW, y: Math.floor(i/cols)*unitH, w: unitW, h: unitH, stream_type: 'sub' }});
                }}
            }}
            else {{
                // Fallback for 26 or more: 6x5 grid
                const cols = 6, rows = 5;
                const unitW = maxW/cols, unitH = maxH/rows;
                for (let i=0; i<count; i++) {{
                    newLayout.push({{ id: availableCams[i % availableCams.length].id, x: (i%cols)*unitW, y: Math.floor(i/cols)*unitH, w: unitW, h: unitH, stream_type: 'sub' }});
                }}
            }}
            
            gfConfig.cameras = newLayout;
            selectedIdx = -1;
            document.getElementById('current-grid-name').textContent = `${{count}} Camera${{count > 1 ? 's' : ''}}`;
            renderGrid();
        }}

        // Canvas drag and drop support
        const canvasEl = document.getElementById('canvas');
        canvasEl.ondragover = (e) => e.preventDefault();
        canvasEl.ondrop = (e) => {{
            e.preventDefault();
            const camId = parseInt(e.dataTransfer.getData('camId'));
            const scale = parseFloat(canvasEl.getAttribute('data-scale')) || 1;
            const rect = canvasEl.getBoundingClientRect();
            
            const x = (e.clientX - rect.left) / scale;
            const y = (e.clientY - rect.top) / scale;
            
            gfConfig.cameras.push({{
                id: camId,
                x: x - 100, // Center roughly
                y: y - 56,
                w: 200,
                h: 112,
                stream_type: 'sub'
            }});
            renderGrid();
        }};

        init();
    </script>
</body>
</html>
    """
