import json
import os
import platform
from .version import CURRENT_VERSION

# HTML for Web UI (generated dynamically with timezone data)
def get_web_ui_html(current_settings=None):
    """Generate Web UI HTML"""
    
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tonys Onvif-RTSP Server</title>
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {{
            --primary-bg: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --body-bg: transparent;
            --card-bg: #ffffff;
            --header-bg: #ffffff;
            --text-title: #2d3748;
            --text-body: #718096;
            --text-muted: #a0aec0;
            --btn-primary: #667eea;
            --btn-primary-hover: #5a67d8;
            --btn-success: #48bb78;
            --btn-success-hover: #38a169;
            --btn-danger: #f56565;
            --btn-danger-hover: #e53e3e;
            --border-color: #e2e8f0;
            --card-border: #cbd5e0;
            --shadow: 0 4px 6px rgba(0,0,0,0.1);
            --input-bg: #ffffff;
            --input-text: #2d3748;
            --input-border: #e2e8f0;
            --alert-info-bg: #edf2f7;
            --alert-info-text: #4a5568;
            --alert-warning-bg: #fef5e7;
            --alert-warning-text: #7a5c0f;
            --toggle-bg: #cbd5e0;
            --toggle-active: #48bb78;
            --modal-bg: #ffffff;
            --text-code: #2d3748;
        }}

        body.theme-dark {{
            --primary-bg: #0d1117;
            --body-bg: #0d1117;
            --card-bg: #161b22;
            --header-bg: #161b22;
            --text-title: #f0f6fc;
            --text-body: #8b949e;
            --text-muted: #484f58;
            --btn-primary: #238636;
            --btn-primary-hover: #2ea043;
            --btn-success: #238636;
            --btn-success-hover: #2ea043;
            --btn-danger: #da3633;
            --btn-danger-hover: #f85149;
            --border-color: #30363d;
            --card-border: #30363d;
            --shadow: 0 0 0 1px #30363d;
            --input-bg: #0d1117;
            --input-text: #c9d1d9;
            --input-border: #30363d;
            --alert-info-bg: #0d1117;
            --alert-info-text: #58a6ff;
            --alert-warning-bg: #0d1117;
            --alert-warning-text: #d29922;
            --toggle-bg: #30363d;
            --toggle-active: #238636;
            --modal-bg: #161b22;
            --text-code: #58a6ff;
        }}

        body.theme-nord {{
            --primary-bg: #2e3440;
            --body-bg: #2e3440;
            --card-bg: #3b4252;
            --header-bg: #3b4252;
            --text-title: #eceff4;
            --text-body: #d8dee9;
            --text-muted: #4c566a;
            --btn-primary: #88c0d0;
            --btn-primary-hover: #81a1c1;
            --btn-success: #a3be8c;
            --btn-success-hover: #8fbcbb;
            --btn-danger: #bf616a;
            --btn-danger-hover: #d08770;
            --border-color: #434c5e;
            --card-border: #434c5e;
            --shadow: 0 2px 10px rgba(0,0,0,0.2);
            --input-bg: #2e3440;
            --input-text: #eceff4;
            --input-border: #4c566a;
            --alert-info-bg: #434c5e;
            --alert-info-text: #8fbcbb;
            --toggle-bg: #4c566a;
            --toggle-active: #a3be8c;
            --modal-bg: #3b4252;
            --text-code: #88c0d0;
        }}

        body.theme-dracula {{
            --primary-bg: radial-gradient(circle at 10% 20%, #282a36 0%, #1e1f29 90%);
            --body-bg: #1e1f29;
            --card-bg: #282a36;
            --header-bg: #282a36;
            --text-title: #f8f8f2;
            --text-body: #e2e2e9;
            --text-muted: #6272a4;
            --btn-primary: #bd93f9;
            --btn-primary-hover: #ff79c6;
            --btn-success: #50fa7b;
            --btn-success-hover: #40e06a;
            --btn-danger: #ff5555;
            --btn-danger-hover: #ff6e6e;
            --border-color: #44475a;
            --card-border: #6272a444;
            --shadow: 0 12px 40px rgba(0,0,0,0.5);
            --input-bg: #1e1f29;
            --input-text: #f8f8f2;
            --input-border: #44475a;
            --alert-info-bg: #21222c;
            --alert-info-text: #8be9fd;
            --toggle-bg: #44475a;
            --toggle-active: #50fa7b;
            --modal-bg: #282a36;
            --text-code: #8be9fd;
        }}

        body.theme-solar-light {{
            --primary-bg: #fdf6e3;
            --body-bg: #fdf6e3;
            --card-bg: #eee8d5;
            --header-bg: #eee8d5;
            --text-title: #073642;
            --text-body: #586e75;
            --text-muted: #93a1a1;
            --btn-primary: #268bd2;
            --btn-primary-hover: #2aa198;
            --btn-success: #859900;
            --btn-success-hover: #b58900;
            --btn-danger: #dc322f;
            --btn-danger-hover: #cb4b16;
            --border-color: #dcdccc;
            --card-border: #93a1a1;
            --input-bg: #fdf6e3;
            --input-text: #073642;
            --alert-info-bg: #eee8d5;
            --toggle-active: #859900;
            --modal-bg: #eee8d5;
            --text-code: #b58900;
        }}

        body.theme-midnight {{
            --primary-bg: #050a14;
            --body-bg: #050a14;
            --card-bg: #0d1829;
            --header-bg: #0d1829;
            --text-title: #e6f1ff;
            --text-body: #a8b2d1;
            --text-muted: #495670;
            --btn-primary: #64ffda;
            --btn-primary-hover: #172a45;
            --btn-success: #64ffda;
            --btn-danger: #f56565;
            --border-color: #1d2d50;
            --input-bg: #050a14;
            --input-text: #e6f1ff;
            --alert-info-text: #64ffda;
            --toggle-active: #64ffda;
            --modal-bg: #0d1829;
            --text-code: #64ffda;
        }}

        body.theme-emerald {{
            --primary-bg: #064e3b;
            --body-bg: #064e3b;
            --card-bg: #065f46;
            --header-bg: #065f46;
            --text-title: #ecfdf5;
            --text-body: #a7f3d0;
            --text-muted: #047857;
            --btn-primary: #10b981;
            --btn-primary-hover: #059669;
            --btn-success: #34d399;
            --btn-danger: #ef4444;
            --border-color: #047857;
            --input-bg: #064e3b;
            --input-text: #ecfdf5;
            --alert-info-bg: #064e3b;
            --toggle-active: #34d399;
            --modal-bg: #065f46;
            --text-code: #a7f3d0;
        }}

        body.theme-sunset {{
            --primary-bg: linear-gradient(45deg, #ff512f 0%, #dd2476 100%);
            --body-bg: transparent;
            --card-bg: rgba(255, 255, 255, 0.95);
            --header-bg: rgba(255, 255, 255, 0.95);
            --text-title: #1a202c;
            --text-body: #4a5568;
            --btn-primary: #fa5252;
            --btn-success: #fab005;
            --btn-danger: #e03131;
            --modal-bg: #ffffff;
            --text-code: #d03131;
        }}

        body.theme-matrix {{
            --primary-bg: #000000;
            --body-bg: #000000;
            --card-bg: #0a0a0a;
            --header-bg: #0a0a0a;
            --text-title: #00ff41;
            --text-body: #008f11;
            --text-muted: #003b00;
            --btn-primary: #00ff41;
            --btn-primary-hover: #008f11;
            --btn-success: #00ff41;
            --btn-danger: #ff0000;
            --border-color: #00ff41;
            --card-border: #00ff41;
            --input-bg: #000000;
            --input-text: #00ff41;
            --input-border: #00ff41;
            --alert-info-bg: #000000;
            --alert-info-text: #00ff41;
            --toggle-active: #00ff41;
            --modal-bg: #0a0a0a;
            --text-code: #00ff41;
        }}

        body.theme-slate {{
            --primary-bg: #334155;
            --body-bg: #334155;
            --card-bg: #1e293b;
            --header-bg: #1e293b;
            --text-title: #f8fafc;
            --text-body: #94a3b8;
            --text-muted: #475569;
            --btn-primary: #38bdf8;
            --btn-success: #22c55e;
            --btn-danger: #f43f5e;
            --border-color: #334155;
            --input-bg: #0f172a;
            --input-text: #f1f5f9;
            --toggle-active: #38bdf8;
            --modal-bg: #1e293b;
            --text-code: #38bdf8;
        }}

        body.theme-cyberpunk {{
            --primary-bg: #fcee0a;
            --body-bg: #fcee0a;
            --card-bg: #000000;
            --header-bg: #000000;
            --text-title: #00f0ff;
            --text-body: #fcee0a;
            --text-muted: #333333;
            --btn-primary: #ff003c;
            --btn-success: #00f0ff;
            --btn-danger: #ff003c;
            --border-color: #00f0ff;
            --card-border: #00f0ff;
            --input-bg: #000000;
            --input-text: #00f0ff;
            --alert-info-text: #fcee0a;
            --toggle-active: #ff003c;
            --modal-bg: #000000;
            --text-code: #00f0ff;
        }}

        body.theme-amoled {{
            --primary-bg: #000000;
            --body-bg: #000000;
            --card-bg: #000000;
            --header-bg: #000000;
            --text-title: #ffffff;
            --text-body: #ffffff;
            --text-muted: #333333;
            --btn-primary: #ffffff;
            --btn-primary-hover: #cccccc;
            --btn-success: #00ff00;
            --btn-danger: #ff0000;
            --border-color: #333333;
            --card-border: #333333;
            --input-bg: #000000;
            --input-text: #ffffff;
            --alert-info-bg: #000000;
            --alert-info-text: #ffffff;
            --toggle-bg: #333333;
            --toggle-active: #ffffff;
            --modal-bg: #000000;
            --text-code: #ffffff;
        }}

        body.theme-ui {{
            --primary-bg: #f4f5f7;
            --body-bg: #f4f5f7;
            --card-bg: #ffffff;
            --header-bg: #ffffff;
            --text-title: #0f172a;
            --text-body: #475569;
            --text-muted: #94a3b8;
            --btn-primary: #0055ff;
            --btn-primary-hover: #0044cc;
            --btn-success: #10b981;
            --btn-success-hover: #059669;
            --btn-danger: #ef4444;
            --btn-danger-hover: #dc2626;
            --border-color: #cbd5e1;
            --card-border: #cbd5e1;
            --shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.05);
            --input-bg: #ffffff;
            --input-text: #0f172a;
            --input-border: #cbd5e1;
            --alert-info-bg: #eff6ff;
            --alert-info-text: #0055ff;
            --alert-warning-bg: #fffbeb;
            --alert-warning-text: #d97706;
            --toggle-bg: #cbd5e1;
            --toggle-active: #0055ff;
            --modal-bg: #ffffff;
            --text-code: #0055ff;
        }}

        body.theme-ui .version-badge {{
            background: rgba(0, 85, 255, 0.12);
            color: #0055ff;
            border-color: rgba(0, 85, 255, 0.25);
        }}

        body.theme-ui .diagnostics-table th {{
            border-bottom: 2px solid var(--border-color);
            color: var(--text-muted);
        }}
        body.theme-ui .diagnostics-table td {{
            border-bottom: 1px solid var(--border-color);
        }}
        body.theme-ui .diagnostics-table tr:hover {{
            background: rgba(0, 0, 0, 0.02);
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--body-bg);
            background-image: var(--primary-bg);
            background-attachment: fixed;
            min-height: 100vh;
            padding: 20px;
            color: var(--text-main);
        }}
        .container {{ 
            width: 100%;
            max-width: var(--container-width, 1600px); 
            margin: 0 auto; 
            transition: max-width 0.3s ease;
            display: flex;
            flex-direction: column;
        }}
        .header {{
            background: var(--header-bg);
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 24px;
            box-shadow: var(--shadow);
            border: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            gap: 16px;
            width: 100%;
        }}
        
        .header-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
            padding-bottom: 14px;
            border-bottom: 1px solid var(--border-color);
        }}
        
        .header-title-area {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .header-title-area h1 {{
            color: var(--text-title);
            font-size: 22px;
            font-weight: 700;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .version-badge {{
            font-size: 11px;
            font-weight: 700;
            background: rgba(102, 126, 234, 0.1);
            color: #667eea;
            padding: 2px 8px;
            border-radius: 12px;
            border: 1px solid rgba(102, 126, 234, 0.2);
            align-self: center;
        }}
        
        body.theme-dark .version-badge,
        body.theme-dracula .version-badge,
        body.theme-nord .version-badge,
        body.theme-slate .version-badge,
        body.theme-midnight .version-badge {{
            background: rgba(189, 147, 249, 0.15);
            color: #bd93f9;
            border-color: rgba(189, 147, 249, 0.3);
        }}
        
        .header-meta-area {{
            display: flex;
            align-items: center;
            gap: 16px;
        }}
        
        .stats-badge {{
            padding: 6px 12px;
            background: var(--body-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            font-weight: 600;
            color: var(--text-body);
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 11px;
            white-space: nowrap;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .theme-select-container {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding-left: 16px;
            border-left: 1px solid var(--border-color);
        }}
        
        .theme-select-container span {{
            font-size: 11px;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .theme-select {{
            width: auto;
            padding: 6px 12px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            border: 1px solid var(--border-color);
            background: var(--body-bg);
            color: var(--text-title);
            border-radius: 6px;
            outline: none;
            transition: all 0.2s;
        }}
        
        .theme-select:focus {{
            border-color: var(--btn-primary);
        }}

        .header-bottom {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
            width: 100%;
        }}

        .actions {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin: 0;
            align-items: center;
        }}
        
        .control-toggles {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .toggle-stack {{
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}
        
        .toggle-group {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: var(--body-bg);
            padding: 2px 8px;
            border-radius: 6px;
            border: 1px solid var(--border-color);
            height: 22px;
            min-width: 140px;
            gap: 8px;
        }}
        
        .toggle-group span {{
            font-size: 11px;
            font-weight: 600;
            color: var(--text-title);
            white-space: nowrap;
        }}
        .btn {{
            padding: 10px 20px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            background: var(--card-bg);
            color: var(--text-title);
        }}
        .btn:hover {{
            background: var(--body-bg);
            border-color: var(--btn-primary);
            color: var(--btn-primary);
            transform: translateY(-1px);
        }}
        .btn-primary {{ 
            background: var(--btn-primary); 
            color: white; 
            border-color: var(--btn-primary);
        }}
        .btn-primary:hover {{ 
            background: var(--btn-primary-hover); 
            border-color: var(--btn-primary-hover);
            color: white;
        }}
        .btn-success {{ 
            background: var(--btn-primary); 
            color: white; 
            border-color: var(--btn-primary);
        }}
        .btn-success:hover {{ 
            background: var(--btn-primary-hover); 
            border-color: var(--btn-primary-hover);
        }}
        .btn-danger {{ 
            background: transparent; 
            color: var(--text-body);
            border-color: var(--border-color);
        }}
        .btn-danger:hover {{ 
            background: #fee2e2; 
            color: #dc2626; 
            border-color: #fca5a5;
        }}
        body.theme-dark .btn-danger:hover,
        body.theme-dracula .btn-danger:hover {{
            background: #450a0a;
            color: #f87171;
            border-color: #991b1b;
        }}
        .camera-grid {{ 
            display: grid; 
            gap: 20px; 
            grid-template-columns: repeat(var(--grid-cols, 3), 1fr); 
        }}
        .camera-card {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 24px;
            box-shadow: var(--shadow);
            border: 1px solid var(--card-border);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}

        .camera-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 20px;
        }}
        .camera-title {{ display: flex; align-items: center; gap: 12px; }}
        .status-badge {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: var(--text-muted);
        }}
        .status-badge.running {{
            background: var(--btn-success);
            box-shadow: 0 0 0 4px rgba(35, 134, 54, 0.2);
        }}
        .camera-name {{
            font-size: 20px;
            font-weight: 600;
            color: var(--text-title);
        }}
        .camera-actions {{ display: flex; gap: 8px; }}
        .icon-btn {{
            padding: 6px 12px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            cursor: pointer;
            border-radius: 6px;
            color: var(--text-body);
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            font-size: 12px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .metric-badge {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 800;
            background: rgba(0,0,0,0.6);
            color: white;
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.2s;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            backdrop-filter: blur(4px);
        }}
        .metric-badge.live {{
            background: rgba(46, 204, 113, 0.4);
            color: #2ecc71;
            border-color: rgba(46, 204, 113, 0.4);
        }}
        .metric-badge.warn {{
            background: rgba(243, 156, 18, 0.4);
            color: #f39c12;
            border-color: rgba(243, 156, 18, 0.4);
        }}
        .metric-badge.error {{
            background: rgba(231, 76, 60, 0.4);
            color: #e74c3c;
            border-color: rgba(231, 76, 60, 0.4);
        }}
        .metrics-overlay {{
            position: absolute;
            top: 10px;
            left: 10px;
            display: none; /* Hidden by default */
            gap: 6px;
            z-index: 5;
            pointer-events: none;
        }}
        body.show-bandwidth .metrics-overlay {{
            display: flex;
        }}
        .icon-btn i {{ font-size: 14px; }}
        .icon-btn:hover {{ 
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .icon-btn-start:hover {{
            background: #2ecc71;
            color: white;
            border-color: #27ae60;
        }}
        .icon-btn-stop:hover {{
            background: #f39c12;
            color: white;
            border-color: #e67e22;
        }}
        .icon-btn-edit:hover {{
            background: #3498db;
            color: white;
            border-color: #2980b9;
        }}
        .icon-btn-delete:hover {{
            background: #e74c3c;
            color: white;
            border-color: #c0392b;
        }}
        
        body.theme-light .icon-btn {{
            background: rgba(0, 0, 0, 0.03);
        }}
        .video-preview {{
            width: 100%;
            height: 0;
            padding-bottom: 56.25%;
            background: #000;
            border-radius: 8px;
            margin-bottom: 16px;
            position: relative;
            overflow: hidden;
        }}
        .video-preview video {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: contain;
        }}
        .fullscreen-btn {{
            position: absolute;
            bottom: 10px;
            right: 10px;
            background: rgba(0, 0, 0, 0.6);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 4px;
            padding: 5px 10px;
            cursor: pointer;
            opacity: 0;
            transition: all 0.2s;
            z-index: 10;
            font-size: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(4px);
        }}
        .video-preview:hover .fullscreen-btn {{
            opacity: 1;
        }}
        .fullscreen-btn:hover {{
            background: rgba(0, 0, 0, 0.9);
            transform: scale(1.1);
        }}
        .video-placeholder {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background: var(--input-bg, #e2e8f0);
            color: var(--text-body, #718096);
        }}
        .form-group {{ margin-bottom: 16px; }}
        .form-label {{
            display: block;
            font-size: 14px;
            font-weight: 600;
            color: var(--text-title);
            margin-bottom: 8px;
        }}
        .form-input {{
            width: 100%;
            padding: 12px;
            border: 1px solid var(--input-border);
            border-radius: 8px;
            font-size: 14px;
            background: var(--input-bg);
            color: var(--input-text);
            transition: border-color 0.2s;
        }}
        .form-input:focus {{
            outline: none;
            border-color: var(--btn-primary);
        }}
        .form-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
        .info-section {{
            padding: 16px;
            background: var(--body-bg);
            border-radius: 8px;
            margin-top: 16px;
        }}
        .info-label {{
            font-size: 11px;
            color: var(--text-muted);
            font-weight: 700;
            text-transform: uppercase;
            margin-bottom: 4px;
        }}

        /* Dropdown Menu Styles */
        .dropdown {{
            position: relative;
            display: inline-block;
        }}
        .dropdown-content {{
            display: none;
            position: absolute;
            right: 0;
            background: var(--card-bg);
            min-width: 180px;
            box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2);
            z-index: 100;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            margin-top: 5px;
            overflow: visible; /* Changed to visible to allow pseudo-element bridge */
        }}
        /* Hover Bridge to prevent dropdown from closing when moving mouse from button to menu */
        .dropdown-content::before {{
            content: '';
            position: absolute;
            top: -10px;
            left: 0;
            width: 100%;
            height: 10px;
            background: transparent;
        }}
        .dropdown-content-inner {{
            overflow: hidden;
            border-radius: 8px;
        }}
        .dropdown-content button {{
            color: var(--text-title);
            padding: 12px 16px;
            text-decoration: none;
            display: block;
            width: 100%;
            border: none;
            background: none;
            text-align: left;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }}
        .dropdown-content button i {{
            margin-right: 10px;
            width: 16px;
            text-align: center;
        }}
        .dropdown-content button:hover {{
            background-color: var(--body-bg);
            color: var(--btn-primary);
        }}
        .dropdown-content button.btn-reboot:hover {{
            color: #f56565 !important;
        }}
        .dropdown:hover .dropdown-content {{
            display: block;
        }}
        /* Toast Notifications */
        .toast {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 12px 24px;
            border-radius: 8px;
            color: white;
            z-index: 10000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            font-weight: 600;
            animation: slideIn 0.3s ease-out;
            pointer-events: none;
        }}
        @keyframes slideIn {{
            from {{ transform: translateX(100%); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        @keyframes slideOut {{
            from {{ transform: translateX(0); opacity: 1; }}
            to {{ transform: translateX(100%); opacity: 0; }}
        }}
        .info-value {{
            font-family: 'Courier New', monospace;
            font-size: 13px;
            color: var(--text-code);
            margin-bottom: 12px;
            word-break: break-all;
            background: rgba(0,0,0,0.05);
            padding: 4px 8px;
            border-radius: 4px;
        }}
        body.theme-dark .info-value, 
        body.theme-nord .info-value,
        body.theme-dracula .info-value,
        body.theme-midnight .info-value,
        body.theme-matrix .info-value,
        body.theme-slate .info-value,
        body.theme-cyberpunk .info-value,
        body.theme-amoled .info-value,
        body.theme-emerald .info-value {{
            background: rgba(255,255,255,0.05);
        }}
        .copy-btn {{
            font-size: 11px;
            padding: 4px 8px;
            background: var(--btn-primary);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-left: 8px;
        }}
        .copy-btn:hover {{ background: var(--btn-primary-hover); }}
        .modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }}
        .modal.active {{ display: flex; }}
        .modal-content {{
            background: var(--modal-bg);
            border-radius: 12px;
            padding: 30px;
            max-width: 900px;
            width: 90%;
            max-height: 90vh;
            overflow-y: auto;
            color: var(--text-main);
        }}
        .modal-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
        }}
        .modal-title {{
            font-size: 24px;
            font-weight: 600;
            color: var(--text-title);
        }}
        .close-btn {{
            font-size: 24px;
            color: var(--text-muted);
            cursor: pointer;
            background: none;
            border: none;
        }}
        /* Settings Tabs */
        .settings-tabs {{
            display: flex;
            gap: 8px;
            border-bottom: 2px solid var(--border-color);
            margin-bottom: 24px;
            padding-bottom: 2px;
            flex-wrap: wrap;
        }}
        .settings-tab-btn {{
            background: none;
            border: none;
            border-bottom: 2px solid transparent;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            border-radius: 6px 6px 0 0;
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: -2px;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        .settings-tab-btn i {{
            font-size: 14px;
            transition: transform 0.2s ease, color 0.2s ease, opacity 0.2s ease;
            opacity: 0.6;
        }}
        .settings-tab-btn:hover i {{
            transform: scale(1.15);
            opacity: 1 !important;
        }}
        
        /* Individual Styling for Server Settings Tabs (Normal, Hover, Active) */
        
        /* General Tab (Blue) */
        #settings-tab-general {{
            color: rgba(99, 179, 237, 0.65);
        }}
        #settings-tab-general i {{
            color: #63b3ed;
        }}
        #settings-tab-general:hover {{
            color: #63b3ed;
            background: rgba(49, 130, 206, 0.05);
        }}
        #settings-tab-general.active {{
            color: #3182ce !important;
            background: rgba(49, 130, 206, 0.08) !important;
            border-bottom: 2px solid #3182ce !important;
        }}
        #settings-tab-general.active i {{
            color: #3182ce;
            opacity: 1;
        }}
        
        /* Security Tab (Orange) */
        #settings-tab-security {{
            color: rgba(246, 173, 85, 0.65);
        }}
        #settings-tab-security i {{
            color: #f6ad55;
        }}
        #settings-tab-security:hover {{
            color: #f6ad55;
            background: rgba(221, 107, 32, 0.05);
        }}
        #settings-tab-security.active {{
            color: #dd6b20 !important;
            background: rgba(221, 107, 32, 0.08) !important;
            border-bottom: 2px solid #dd6b20 !important;
        }}
        #settings-tab-security.active i {{
            color: #dd6b20;
            opacity: 1;
        }}
        
        /* Engine Tab (Purple) */
        #settings-tab-engine {{
            color: rgba(214, 188, 250, 0.65);
        }}
        #settings-tab-engine i {{
            color: #d6bcfa;
        }}
        #settings-tab-engine:hover {{
            color: #d6bcfa;
            background: rgba(159, 122, 234, 0.05);
        }}
        #settings-tab-engine.active {{
            color: #9f7aea !important;
            background: rgba(159, 122, 234, 0.08) !important;
            border-bottom: 2px solid #9f7aea !important;
        }}
        #settings-tab-engine.active i {{
            color: #9f7aea;
            opacity: 1;
        }}
        
        /* Maintenance Tab (Teal) */
        #settings-tab-maintenance {{
            color: rgba(79, 209, 197, 0.65);
        }}
        #settings-tab-maintenance i {{
            color: #4fd1c5;
        }}
        #settings-tab-maintenance:hover {{
            color: #4fd1c5;
            background: rgba(56, 178, 172, 0.05);
        }}
        #settings-tab-maintenance.active {{
            color: #38b2ac !important;
            background: rgba(56, 178, 172, 0.08) !important;
            border-bottom: 2px solid #38b2ac !important;
        }}
        #settings-tab-maintenance.active i {{
            color: #38b2ac;
            opacity: 1;
        }}
        .settings-tab-content {{
            display: none;
        }}
        .settings-tab-content.active {{
            display: block;
        }}
        .empty-state {{
            background: var(--header-bg);
            border-radius: 12px;
            padding: 60px 30px;
            text-align: center;
        }}
        .empty-icon {{ font-size: 64px; margin-bottom: 20px; }}
        .empty-title {{
            font-size: 20px;
            font-weight: 600;
            color: var(--text-title);
            margin-bottom: 10px;
        }}
        .empty-text {{ color: var(--text-body); margin-bottom: 24px; }}
        .alert {{ padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; }}
        .alert-info {{ background: var(--alert-info-bg); color: var(--alert-info-text); }}
        .alert-warning {{
            background: var(--alert-warning-bg);
            color: var(--alert-warning-text);
            border-left: 4px solid #f39c12;
        }}
        .alert-success {{ background: #c6f6d5; color: #22543d; }}
        .toggle-switch {{
            position: relative;
            display: inline-block;
            width: 48px;
            height: 24px;
        }}
        .toggle-switch input {{
            opacity: 0;
            width: 0;
            height: 0;
        }}
        .toggle-slider {{
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: var(--toggle-bg);
            transition: .3s;
            border-radius: 24px;
        }}
        .toggle-slider:before {{
            position: absolute;
            content: "";
            height: 18px;
            width: 18px;
            left: 3px;
            bottom: 3px;
            background-color: white;
            transition: .3s;
            border-radius: 50%;
        }}
        .toggle-switch input:checked + .toggle-slider {{
            background-color: var(--toggle-active);
        }}
        .toggle-switch input:checked + .toggle-slider:before {{
            transform: translateX(24px);
        }}
        .auto-start-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 16px;
            background: var(--body-bg);
            border-radius: 8px;
            margin-top: 12px;
        }}
        .auto-start-label {{
            font-size: 14px;
            color: #4a5568;
            font-weight: 600;
        }}
        
        /* Matrix View Styles */
        .matrix-overlay {{
            display: none;
            position: fixed;
            top: 0; left: 0; 
            width: 100vw; height: 100vh;
            background: var(--body-bg, #000);
            z-index: 3000;
            padding: 10px;
            overflow: hidden;
        }}
        .matrix-overlay.active {{ display: flex; flex-direction: column-reverse; }}
        
        .matrix-grid {{
            display: grid;
            gap: 8px;
            flex: 1;
            width: 100%;
            height: 100%;
        }}
        
        .matrix-item {{
            position: relative;
            background: var(--card-bg, #111);
            border: 1px solid var(--border-color, #333);
            border-radius: 4px;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: grab;
        }}
        .matrix-item:active {{
            cursor: grabbing;
        }}
        .matrix-item.dragging {{
            opacity: 0.4;
            border: 2px dashed #6366f1 !important;
        }}
        
        .matrix-item video {{
            width: 100%;
            height: 100%;
            object-fit: contain;
        }}
        
        .matrix-label {{
            position: absolute;
            top: 8px; left: 8px;
            background: rgba(0,0,0,0.7);
            color: #fff;
            padding: 2px 8px;
            font-size: 12px;
            border-radius: 4px;
            pointer-events: none;
            z-index: 5;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        
        .matrix-controls {{
            display: flex;
            justify-content: flex-end;
            align-items: center;
            gap: 16px;
            padding: 12px 20px;
            background: var(--card-bg, #111827);
            border-top: 1px solid var(--border-color, #1f2937);
            margin-top: 8px;
            border-radius: 6px;
        }}
        
        .matrix-controls label {{
            color: var(--text-title, #f3f4f6) !important;
            font-size: 13px;
            font-weight: 600;
        }}
        
        .matrix-controls span {{
            color: var(--text-body, #d1d5db) !important;
            font-weight: 500;
        }}
        
        .btn-matrix {{
            background: var(--card-bg);
            color: var(--text-title);
            border: 1px solid var(--border-color);
            padding: 4px 10px;
            font-size: 12px;
            font-weight: 600;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .btn-matrix:hover {{ 
            background: var(--btn-primary); 
            color: white; 
            border-color: var(--btn-primary);
        }}
        
        /* Stretch Fill & Hide Names Styles */
        .matrix-overlay.stretch-fill {{
            padding: 0px !important;
        }}
        .matrix-overlay.stretch-fill .matrix-grid {{
            gap: 0px !important;
            height: 100vh !important;
            width: 100vw !important;
        }}
        .matrix-overlay.stretch-fill .matrix-item {{
            border: none !important;
            border-radius: 0px !important;
        }}
        .matrix-overlay.stretch-fill .matrix-item video {{
            object-fit: cover !important;
        }}
        .matrix-overlay.stretch-fill .matrix-controls {{
            position: absolute;
            bottom: 15px; right: 15px; left: 15px;
            top: auto !important;
            z-index: 10000;
            background: rgba(17, 24, 39, 0.95) !important;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-radius: 8px !important;
            padding: 12px 20px !important;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8) !important;
            opacity: 0;
            transition: opacity 0.3s ease;
            pointer-events: none;
            margin-bottom: 0 !important;
        }}
        .matrix-overlay.stretch-fill .matrix-controls * {{
            pointer-events: auto;
        }}
        .matrix-overlay.stretch-fill:hover .matrix-controls {{
            opacity: 1;
        }}
        .matrix-overlay.hide-names .matrix-label {{
            display: none !important;
        }}
        
        /* Focused Camera Grid Styles */
        .matrix-grid.focused-active .matrix-item:not(.focused) {{
            display: none !important;
        }}
        .matrix-grid.focused-active .matrix-item.focused {{
            grid-column: 1 / -1 !important;
            grid-row: 1 / -1 !important;
            width: 100% !important;
            height: 100% !important;
        }}
        
        /* AI alert pulsing border style */
        @keyframes alert-pulse {{
            0% {{ box-shadow: inset 0 0 0 4px #f56565; border-color: #f56565; }}
            50% {{ box-shadow: inset 0 0 0 8px #e53e3e; border-color: #e53e3e; }}
            100% {{ box-shadow: inset 0 0 0 4px #f56565; border-color: #f56565; }}
        }}
        .matrix-item.ai-alert {{
            animation: alert-pulse 1.2s infinite !important;
            border: 2px solid #f56565 !important;
        }}
        
        /* Hover details overlay inside matrix-item */
        .matrix-item-overlay {{
            position: absolute;
            bottom: 8px; right: 8px;
            display: flex;
            gap: 6px;
            opacity: 0;
            transition: opacity 0.2s ease;
            z-index: 10;
        }}
        .matrix-item:hover .matrix-item-overlay {{
            opacity: 1;
        }}
        .matrix-item-badge {{
            background: rgba(0, 0, 0, 0.75);
            color: #e2e8f0;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 4px;
            border: 1px solid rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(4px);
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }}
        .matrix-item-btn {{
            background: rgba(0, 0, 0, 0.75);
            color: #cbd5e0;
            border: 1px solid rgba(255, 255, 255, 0.15);
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s ease;
            backdrop-filter: blur(4px);
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }}
        .matrix-item-btn:hover {{
            background: #2d3748;
            color: #fff;
            transform: scale(1.05);
        }}
        .matrix-item-btn.active {{
            background: #48bb78;
            color: #fff;
            border-color: #48bb78;
        }}
        
        /* ONVIF Event Table Styles */
        .diagnostics-table th {{
            font-weight: 600;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.05em;
            color: #718096;
            border-bottom: 2px solid #2d3748;
        }}
        .diagnostics-table td {{
            padding: 12px 10px;
            border-bottom: 1px solid #1a202c;
        }}
        .diagnostics-table tr:hover {{
            background: rgba(255, 255, 255, 0.02);
        }}
        .badge-event-active {{
            background: rgba(245, 101, 101, 0.15);
            color: #fc8181;
            border: 1px solid rgba(245, 101, 101, 0.3);
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: bold;
            display: inline-block;
        }}
        .badge-event-inactive {{
            background: rgba(72, 187, 120, 0.15);
            color: #68d391;
            border: 1px solid rgba(72, 187, 120, 0.3);
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: bold;
            display: inline-block;
        }}
        @keyframes badge-flash {{
            0% {{ background-color: #ecc94b; transform: scale(1); }}
            50% {{ background-color: #ffffff; transform: scale(1.2); box-shadow: 0 0 12px #ecc94b; }}
            100% {{ background-color: #ecc94b; transform: scale(1); }}
        }}
        .ai-badge-flash {{
            animation: badge-flash 0.5s ease-in-out 3;
        }}
        
        .view-toggle-btn {{
            background: #ed64a6;
            color: white;
        }}
        .view-toggle-btn:hover {{ background: #d53f8c; }}
        
        /* Tabs */
        .tabs {{
            display: flex;
            margin-bottom: 20px;
            border-bottom: 2px solid #e2e8f0;
        }}
        .tab {{
            padding: 10px 20px;
            cursor: pointer;
            font-weight: 600;
            color: #718096;
            margin-bottom: -2px;
            border-bottom: 2px solid transparent;
        }}
        .tab.active {{
            color: #4a5568;
            border-bottom: 2px solid #667eea;
        }}
        .tab:hover {{ color: #4a5568; }}
        
        /* Form Tabs */
        /* Form Tabs */
        .form-tabs {{
            display: flex;
            margin-bottom: 20px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
            gap: 8px;
            padding-bottom: 2px;
        }}
        .form-tab {{
            padding: 10px 18px;
            cursor: pointer;
            font-weight: 600;
            margin-bottom: -2px;
            border-bottom: 2px solid transparent;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            border-radius: 6px 6px 0 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .form-tab i {{
            transition: transform 0.2s ease, color 0.2s ease, opacity 0.2s ease;
            opacity: 0.6;
        }}
        .form-tab:hover i {{
            transform: scale(1.15);
            opacity: 1 !important;
        }}
        
        /* Individual Styling for Tabs (Normal, Hover, Active) */
        
        /* Camera Tab (Blue) */
        #form-tab-camera {{
            color: rgba(99, 179, 237, 0.65);
        }}
        #form-tab-camera i {{
            color: #63b3ed;
        }}
        #form-tab-camera:hover {{
            color: #63b3ed;
            background: rgba(49, 130, 206, 0.05);
        }}
        #form-tab-camera.active {{
            color: #3182ce;
            border-bottom: 2px solid #3182ce;
            background: rgba(49, 130, 206, 0.08);
        }}
        #form-tab-camera.active i {{
            color: #3182ce;
            opacity: 1;
        }}
        
        /* Audio Tab (Orange) */
        #form-tab-audio {{
            color: rgba(246, 173, 85, 0.65);
        }}
        #form-tab-audio i {{
            color: #f6ad55;
        }}
        #form-tab-audio:hover {{
            color: #f6ad55;
            background: rgba(221, 107, 32, 0.05);
        }}
        #form-tab-audio.active {{
            color: #dd6b20;
            border-bottom: 2px solid #dd6b20;
            background: rgba(221, 107, 32, 0.08);
        }}
        #form-tab-audio.active i {{
            color: #dd6b20;
            opacity: 1;
        }}
        
        /* AI Settings Tab (Purple) */
        #form-tab-ai {{
            color: rgba(214, 188, 250, 0.65);
        }}
        #form-tab-ai i {{
            color: #d6bcfa;
        }}
        #form-tab-ai:hover {{
            color: #d6bcfa;
            background: rgba(159, 122, 234, 0.05);
        }}
        #form-tab-ai.active {{
            color: #9f7aea;
            border-bottom: 2px solid #9f7aea;
            background: rgba(159, 122, 234, 0.08);
        }}
        #form-tab-ai.active i {{
            color: #9f7aea;
            opacity: 1;
        }}
        
        /* Networking Tab (Teal) */
        #form-tab-networking {{
            color: rgba(79, 209, 197, 0.65);
        }}
        #form-tab-networking i {{
            color: #4fd1c5;
        }}
        #form-tab-networking:hover {{
            color: #4fd1c5;
            background: rgba(56, 178, 172, 0.05);
        }}
        #form-tab-networking.active {{
            color: #38b2ac;
            border-bottom: 2px solid #38b2ac;
            background: rgba(56, 178, 172, 0.08);
        }}
        #form-tab-networking.active i {{
            color: #38b2ac;
            opacity: 1;
        }}
        .form-section {{
            display: none;
        }}
        .form-section.active {{
            display: block;
        }}
        
        /* Make AI settings section text slightly larger and easier to read */
        #form-sec-ai, #form-sec-ai div, #form-sec-ai label, #form-sec-ai span, #form-sec-ai small, #form-sec-ai input, #form-sec-ai select {{
            font-size: 13.5px !important;
        }}
        #form-sec-ai [style*="font-size: 12px"], #form-sec-ai [style*="font-size:12px"] {{
            font-size: 14.5px !important;
        }}
        #form-sec-ai [style*="font-size: 11px"], #form-sec-ai [style*="font-size:11px"] {{
            font-size: 13.5px !important;
        }}
        #form-sec-ai [style*="font-size: 10px"], #form-sec-ai [style*="font-size:10px"] {{
            font-size: 12.5px !important;
        }}
        #form-sec-ai [style*="font-size: 8px"], #form-sec-ai [style*="font-size:8px"] {{
            font-size: 10.5px !important;
        }}
        
        .result-item {{
            background: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .result-item:hover {{
            background: #eef2f7;
            border-color: #cbd5e0;
        }}
        .footer {{
            margin-top: 40px;
            padding: 20px 0;
            text-align: center;
            border-top: 1px solid var(--card-border);
            color: var(--text-muted);
            font-size: 13px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
        }}
        .coffee-link {{
            display: inline-block;
            transition: transform 0.2s, filter 0.2s;
        }}
        .coffee-link:hover {{
            transform: translateY(-3px);
            filter: drop-shadow(0 6px 12px rgba(0,0,0,0.2));
        }}
        .coffee-link img {{
            height: 50px;
        }}
        .coffee-link-small {{
            display: inline-block;
            transition: transform 0.2s;
        }}
        .coffee-link-small:hover {{
            transform: scale(1.05);
        }}
        .coffee-link-small img {{
            height: 35px;
        }}

        /* GridFusion Editor Styles */
        .gridfusion-container {{
            display: flex;
            gap: 20px;
            height: 700px;
            margin-top: 10px;
        }}
        .gridfusion-sidebar {{
            width: 250px;
            background: rgba(0,0,0,0.2);
            border-radius: 12px;
            padding: 15px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            overflow-y: auto;
        }}
        .gridfusion-canvas-container {{
            flex: 1;
            background: #000;
            border-radius: 12px;
            position: relative;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 2px solid var(--card-border);
        }}
        .gridfusion-canvas {{
            background: #1a1a1a;
            position: relative;
            box-shadow: 0 0 50px rgba(0,0,0,0.5);
        }}
        .grid-overlay {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            background-image: 
                linear-gradient(to right, rgba(255,255,255,0.05) 1px, transparent 1px),
                linear-gradient(to bottom, rgba(255,255,255,0.05) 1px, transparent 1px);
            background-size: 20px 20px;
            display: none;
        }}
        .gf-camera-item {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 8px;
            display: flex;
            align-items: center;
            gap: 10px;
            cursor: grab;
            user-select: none;
            transition: transform 0.2s;
        }}
        .gf-camera-item:hover {{
            transform: scale(1.02);
            border-color: var(--btn-primary);
        }}
        .gf-camera-img {{
            width: 50px;
            height: 30px;
            background: #333;
            border-radius: 4px;
            object-fit: cover;
        }}
        .gf-camera-name {{
            font-size: 13px;
            font-weight: 600;
            flex: 1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .gf-add-btn {{
            background: var(--btn-primary);
            color: white;
            border: none;
            border-radius: 4px;
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: 16px;
        }}
        .gf-placed-camera {{
            position: absolute;
            background: #333;
            border: 2px solid #667eea;
            cursor: move;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            overflow: hidden;
        }}
        .gf-placed-camera.selected {{
            border-color: #48bb78;
            box-shadow: 0 0 15px rgba(72, 187, 120, 0.5);
            z-index: 10;
        }}
        .gf-placed-snapshot {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            opacity: 0.6;
            pointer-events: none;
        }}
        .gf-placed-label {{
            position: absolute;
            background: rgba(0,0,0,0.7);
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            max-width: 90%;
            text-align: center;
        }}
        .gf-remove-btn {{
            position: absolute;
            top: 5px;
            right: 5px;
            background: #f56565;
            color: white;
            border: none;
            border-radius: 4px;
            width: 20px;
            height: 20px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            z-index: 11;
        }}
        .gf-resizer {{
            position: absolute;
            width: 10px;
            height: 10px;
            background: white;
            border: 1px solid #667eea;
            bottom: 0;
            right: 0;
            cursor: nwse-resize;
            z-index: 12;
        }}
        .gf-toolbar {{
            display: flex;
            align-items: center;
            gap: 15px;
            background: rgba(255,255,255,0.05);
            padding: 10px 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }}
        .gf-status-bar {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 13px;
            color: var(--text-muted);
        }}
        .gf-copy-link {{
            background: rgba(0,0,0,0.3);
            padding: 4px 10px;
            border-radius: 4px;
            font-family: monospace;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        /* Custom Tooltip Styling */
        .custom-tooltip {{
            position: absolute;
            z-index: 10000;
            background: #1e293b;
            color: #f8fafc;
            padding: 10px 14px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            line-height: 1.5;
            max-width: 360px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -4px rgba(0, 0, 0, 0.4);
            border: 1px solid #334155;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.15s ease-in-out;
            white-space: normal;
            word-wrap: break-word;
        }}
        .custom-tooltip.visible {{
            opacity: 1;
        }}
    </style>
</head>
<body class="theme-{current_settings.get('theme', 'classic') if current_settings else 'classic'}">
    <div class="container">
        <div class="header">
            <!-- Top section: Title, version, stats, and theme selector -->
            <div class="header-top">
                <div class="header-title-area">
                    <h1>
                        <span>Tonys Onvif-RTSP Server</span>
                        <a href="https://github.com/BigTonyTones/Tonys-Onvf-RTSP-Server" target="_blank" style="color: inherit; text-decoration: none; margin-left: 10px; font-size: 18px; display: inline-flex; align-items: center; opacity: 0.7; transition: opacity 0.2s;" onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=0.7" title="View on GitHub">
                            <i class="fa-brands fa-github"></i>
                        </a>
                        <span class="version-badge">v{CURRENT_VERSION}</span>
                    </h1>
                </div>
                <div class="header-meta-area">
                    <span id="server-stats" class="stats-badge">
                        <i class="fa-solid fa-microchip" style="opacity: 0.75; color: var(--btn-primary);"></i> CPU: ... &nbsp;&nbsp;•&nbsp;&nbsp; <i class="fa-solid fa-memory" style="opacity: 0.75; color: var(--btn-primary);"></i> MEM: ...
                    </span>
                    <div class="theme-select-container">
                        <span>Theme</span>
                        <select id="themeSwitcher" class="theme-select" onchange="changeTheme(this.value)">
                            <option value="classic" {"selected" if current_settings and current_settings.get('theme') == 'classic' else ""}>Classic</option>
                            <option value="dark" {"selected" if current_settings and current_settings.get('theme') == 'dark' else ""}>Modern Dark</option>
                            <option value="nord" {"selected" if current_settings and current_settings.get('theme') == 'nord' else ""}>Nordic</option>
                            <option value="dracula" {"selected" if not current_settings or current_settings.get('theme') == 'dracula' else ""}>Dracula (Pro Dark)</option>
                            <option value="solar-light" {"selected" if current_settings and current_settings.get('theme') == 'solar-light' else ""}>Solarized</option>
                            <option value="midnight" {"selected" if current_settings and current_settings.get('theme') == 'midnight' else ""}>Midnight</option>
                            <option value="emerald" {"selected" if current_settings and current_settings.get('theme') == 'emerald' else ""}>Emerald</option>
                            <option value="sunset" {"selected" if current_settings and current_settings.get('theme') == 'sunset' else ""}>Sunset</option>
                            <option value="matrix" {"selected" if current_settings and current_settings.get('theme') == 'matrix' else ""}>Matrix</option>
                            <option value="slate" {"selected" if current_settings and current_settings.get('theme') == 'slate' else ""}>Slate</option>
                            <option value="cyberpunk" {"selected" if current_settings and current_settings.get('theme') == 'cyberpunk' else ""}>Cyberpunk</option>
                            <option value="amoled" {"selected" if current_settings and current_settings.get('theme') == 'amoled' else ""}>Amoled</option>
                            <option value="ui" {"selected" if current_settings and current_settings.get('theme') == 'ui' else ""}>UI</option>
                        </select>
                    </div>
                </div>
            </div>
            
            <!-- Bottom section: Navigation buttons, toggles, logout -->
            <div class="header-bottom">
                <div class="actions">
                    <button class="btn btn-primary" onclick="openAddModal()">
                        <i class="fa-solid fa-plus"></i> Add Camera
                    </button>
                    <button class="btn" onclick="window.location.href='/gridfusion'">
                        <i class="fa-solid fa-grip"></i> GridFusion
                    </button>
                    <button class="btn" onclick="toggleMatrixView(true)">
                        <i class="fa-solid fa-table-cells"></i> Matrix View
                    </button>
                    <button class="btn" onclick="toggleONVIFView(true)">
                        <i class="fa-solid fa-brain"></i> AI/ONVIF
                    </button>
                    <button class="btn" onclick="window.location.href='/ip-management'">
                        <i class="fa-solid fa-network-wired"></i> IP Management
                    </button>
                    <button class="btn" onclick="startAll()">
                        <i class="fa-solid fa-play"></i> Start All
                    </button>
                    <button class="btn" onclick="stopAll()">
                        <i class="fa-solid fa-stop"></i> Stop All
                    </button>
                    <button class="btn" onclick="openSettingsModal()">
                        <i class="fa-solid fa-gear"></i> Settings
                    </button>
                    <button class="btn" onclick="window.location.href='/diagnostics'">
                        <i class="fa-solid fa-gauge"></i> Diagnostics
                    </button>
                    
                    <div class="dropdown">
                        <button class="btn">
                            <i class="fa-solid fa-server"></i> Server <i class="fa-solid fa-chevron-down" style="font-size: 10px; margin-left: 5px;"></i>
                        </button>
                        <div class="dropdown-content">
                            <div class="dropdown-content-inner">
                                <button onclick="openLogsModal()">
                                    <i class="fa-solid fa-list-alt"></i> System Logs
                                </button>
                                <button onclick="restartServer()" style="border-top: 1px solid var(--border-color);">
                                    <i class="fa-solid fa-sync"></i> Restart Server
                                </button>
                                <button onclick="stopServer()" style="color: #f56565; border-top: 1px solid var(--border-color);">
                                    <i class="fa-solid fa-stop-circle"></i> Stop Server
                                </button>
                                <button onclick="rebootServer()" class="reboot-host" style="border-top: 1px solid var(--border-color);">
                                    <i class="fa-solid fa-power-off"></i> Reboot Host
                                </button>
                            </div>
                        </div>
                    </div>
                    
                    <button class="btn" onclick="openAboutModal()">
                        <i class="fa-solid fa-circle-info"></i> About
                    </button>
                </div>
                
                <div class="control-toggles">
                    <div class="toggle-stack">
                        <div class="toggle-group" title="Use WebRTC for sub-second latency (recommended for PTZ and real-time viewing)">
                            <span>Low Latency</span>
                            <label class="toggle-switch" style="margin: 0; transform: scale(0.65); transform-origin: right center;">
                                <input type="checkbox" id="latencyToggle" onchange="toggleLatencyMode(this.checked)">
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                        <div class="toggle-group" title="Display real-time bitrate, stream status, and active viewer count on camera previews">
                            <span>Bandwidth</span>
                            <label class="toggle-switch" style="margin: 0; transform: scale(0.65); transform-origin: right center;">
                                <input type="checkbox" id="bandwidthToggle" onchange="toggleBandwidth(this.checked)">
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                    </div>
                    <a href="/logout" id="logoutBtn" class="btn btn-danger" style="text-decoration: none; display: none;">
                        <i class="fa-solid fa-right-from-bracket"></i> Logout
                    </a>
                </div>
            </div>
        </div>
        
        <div id="camera-list" class="camera-grid"></div>
        
        <div id="empty-state" class="empty-state" style="display:none;">
            <div class="empty-icon"></div>
            <div class="empty-title">No Cameras Configured</div>
            <div class="empty-text">Add your first virtual ONVIF camera to get started</div>
            <button class="btn btn-success" onclick="openAddModal()">Add Your First Camera</button>
        </div>
        <div class="footer">
            <p>© 2026 <a href="https://github.com/BigTonyTones/Tonys-Onvf-RTSP-Server" target="_blank" style="color: inherit; text-decoration: none; font-weight: 600;">Tonys Onvif-RTSP Server</a> • Created by <a href="https://github.com/BigTonyTones" target="_blank" style="color: inherit; text-decoration: none; font-weight: 600;">Tony</a></p>
            <a href="https://buymeacoffee.com/tonytones" target="_blank" class="coffee-link-small">
                <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee">
            </a>
        </div>
    </div>
    
    <!-- Matrix View Overlay -->
    <div id="matrix-overlay" class="matrix-overlay">
        <div class="matrix-controls">
            <span style="color: #718096; margin-right: auto; padding-left: 10px; font-size: 14px; align-self: center;">
                F11 for Full Screen • ESC to Exit
            </span>
            <label style="display: flex; align-items: center; gap: 8px; color: var(--text-body); font-size: 13px; font-weight: 600; cursor: pointer; user-select: none; margin-right: 15px;" title="Flash red border around camera feed on active AI detections">
                <input type="checkbox" id="matrixAiFlashToggle" onchange="updateMatrixSettings()" style="width: 16px; height: 16px; cursor: pointer;"> AI Alerts
            </label>
            <label style="display: flex; align-items: center; gap: 8px; color: var(--text-body); font-size: 13px; font-weight: 600; cursor: pointer; user-select: none; margin-right: 15px;" title="Automatically unmute audio when hovering over a camera feed">
                <input type="checkbox" id="matrixAudioHoverToggle" onchange="updateMatrixSettings()" style="width: 16px; height: 16px; cursor: pointer;"> Audio Hover
            </label>
            <!-- Cams Per Page Dropdown -->
            <div style="display: flex; align-items: center; gap: 8px; margin-right: 15px; border-left: 1px solid var(--border-color); padding-left: 15px;">
                <span style="color: var(--text-title); font-size: 13px; font-weight: 600; user-select: none;">Cams Per Page:</span>
                <select id="matrixCamsPerPageSelect" onchange="updateCamsPerPage()" style="background: var(--input-bg); color: var(--input-text); border: 1px solid var(--input-border); border-radius: 4px; padding: 2px 4px; font-size: 11px; cursor: pointer;" title="Number of cameras to display per page">
                    <option value="All">All</option>
                    <option value="1">1 Cam</option>
                    <option value="2">2 Cams</option>
                    <option value="4">4 Cams</option>
                    <option value="6">6 Cams</option>
                    <option value="9">9 Cams</option>
                    <option value="12">12 Cams</option>
                    <option value="16">16 Cams</option>
                </select>
            </div>
            
            <!-- Manual Navigation Controls -->
            <div id="matrixNavControls" style="display: none; align-items: center; gap: 8px; margin-right: 15px; border-left: 1px solid var(--border-color); padding-left: 15px;">
                <button class="btn-matrix" onclick="changeMatrixPage(-1)" style="padding: 2px 8px; font-size: 11px; border-radius: 4px;">&lt; Prev</button>
                <span id="matrixPageIndicator" style="color: var(--text-title); font-size: 12px; font-weight: 600; user-select: none;">Page 1 of 1</span>
                <button class="btn-matrix" onclick="changeMatrixPage(1)" style="padding: 2px 8px; font-size: 11px; border-radius: 4px;">Next &gt;</button>
            </div>

            <!-- Carousel Settings Group -->
            <div id="matrixCarouselGroup" style="display: none; align-items: center; gap: 6px; margin-right: 15px; border-left: 1px solid var(--border-color); padding-left: 15px;">
                <label style="display: flex; align-items: center; gap: 8px; color: var(--text-body); font-size: 13px; font-weight: 600; cursor: pointer; user-select: none;">
                    <input type="checkbox" id="matrixCarouselToggle" onchange="toggleCarouselMode()" style="width: 16px; height: 16px; cursor: pointer;"> Carousel
                </label>
                <select id="carouselIntervalSelect" onchange="updateCarouselSettings()" style="background: var(--input-bg); color: var(--input-text); border: 1px solid var(--input-border); border-radius: 4px; padding: 2px 4px; font-size: 11px; cursor: pointer;" title="Rotate interval duration">
                    <option value="3000">3s</option>
                    <option value="5000">5s</option>
                    <option value="10000">10s</option>
                    <option value="15000">15s</option>
                    <option value="30000">30s</option>
                    <option value="60000">1m</option>
                    <option value="120000">2m</option>
                    <option value="300000">5m</option>
                </select>
            </div>
            <label style="display: flex; align-items: center; gap: 8px; color: var(--text-body); font-size: 13px; font-weight: 600; cursor: pointer; user-select: none; margin-right: 15px;" title="Force high-definition (Main) streams for all cameras in Matrix View">
                <input type="checkbox" id="matrixForceHighStreamToggle" onchange="updateMatrixSettings()" style="width: 16px; height: 16px; cursor: pointer;"> High Stream All
            </label>
            <label style="display: flex; align-items: center; gap: 8px; color: var(--text-body); font-size: 13px; font-weight: 600; cursor: pointer; user-select: none; margin-right: 15px;">
                <input type="checkbox" id="matrixStretchToggle" onchange="updateMatrixSettings()" style="width: 16px; height: 16px; cursor: pointer;"> Stretch Fill
            </label>
            <label style="display: flex; align-items: center; gap: 8px; color: var(--text-body); font-size: 13px; font-weight: 600; cursor: pointer; user-select: none; margin-right: 15px;">
                <input type="checkbox" id="matrixHideNamesToggle" onchange="updateMatrixSettings()" style="width: 16px; height: 16px; cursor: pointer;"> Hide Names
            </label>
            <button class="btn-matrix" onclick="resetMatrixOrder()" style="background: var(--card-bg);" title="Reset drag-and-drop order to default (creation order)">Reset Order</button>
            <button class="btn-matrix" onclick="toggleFullScreen()">Full Screen</button>
            <button class="btn-matrix" onclick="toggleMatrixView(false)" style="background: var(--btn-danger); color: white; border-color: var(--btn-danger);">Close Matrix</button>
        </div>
        <div id="matrix-grid" class="matrix-grid"></div>
    </div>
    
    <!-- Copy AI Settings Modal -->
    <div id="copy-ai-modal" class="modal" style="z-index: 1100;">
        <div class="modal-content" style="max-width: 480px;">
            <div class="modal-header">
                <h3 id="copy-ai-title" style="margin: 0; color: var(--text-title); font-size: 16px; display: flex; align-items: center; gap: 8px;">
                    <i class="fas fa-copy" style="color: var(--btn-primary);"></i> Copy AI Settings
                </h3>
                <button class="close-btn" onclick="closeCopyAiModal()">&times;</button>
            </div>
            <div style="padding: 20px;">
                <div style="background: rgba(0, 85, 255, 0.1); padding: 10px 14px; border-radius: 8px; border-left: 3px solid var(--btn-primary); margin-bottom: 16px;">
                    <div style="font-size: 11px; color: var(--text-body); line-height: 1.5;">
                        Copies: Event source, AI model, target classes, and sensitivity.<br>
                        <strong style="color: var(--alert-warning-text);">Does NOT copy:</strong> Motion detection zones.
                    </div>
                </div>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
                    <div style="font-size: 13px; color: var(--text-body); font-weight: 600;">Select Target Cameras</div>
                    <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                        <input type="checkbox" id="copyAiSelectAll" onchange="toggleCopyAiSelectAll()" style="width: auto; cursor: pointer;">
                        <span style="font-size: 11px; color: var(--text-muted);">Select All</span>
                    </label>
                </div>
                <div id="copyAiCameraList" style="max-height: 280px; overflow-y: auto; border: 1px solid var(--border-color); border-radius: 8px; background: var(--input-bg);">
                    <!-- Populated dynamically -->
                </div>
                <div style="margin-top: 16px; display: flex; gap: 10px; justify-content: flex-end;">
                    <button type="button" onclick="closeCopyAiModal()" style="padding: 8px 18px; font-size: 12px; background: var(--card-bg); color: var(--text-body); border: 1px solid var(--border-color); border-radius: 6px; cursor: pointer;">Cancel</button>
                    <button type="button" id="btnApplyCopyAi" onclick="applyCopyAiSettings()" style="padding: 8px 18px; font-size: 12px; font-weight: 600; background: var(--btn-primary); color: white; border: 1px solid var(--btn-primary); border-radius: 6px; cursor: pointer; display: inline-flex; align-items: center; gap: 6px;">
                        <i class="fas fa-check"></i> Apply to Selected
                    </button>
                </div>
                <div id="copyAiFeedback" style="font-size: 11px; margin-top: 8px; text-align: center; color: var(--text-muted);"></div>
            </div>
        </div>
    </div>
    
    <!-- ONVIF Events Overlay -->
    <div id="onvif-overlay" class="matrix-overlay">
        <div class="matrix-controls" style="align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 15px; margin-bottom: 15px; flex-wrap: wrap; gap: 15px;">
            <div style="color: var(--text-title); font-size: 18px; font-weight: 600; margin-right: auto; display: flex; align-items: center; gap: 10px; padding-left: 10px;">
                <span>AI & ONVIF Event Log Stream</span>
            </div>
            <div style="display: flex; align-items: center; gap: 12px; margin-right: 15px;">
                <label class="form-label" style="margin: 0; color: var(--text-body); font-size: 14px;">Filter by Camera:</label>
                <select id="onvif-camera-filter" class="form-input" style="width: 160px; padding: 6px 12px; margin: 0; background: var(--input-bg); border-color: var(--input-border); color: var(--input-text);" onchange="renderONVIFEvents()">
                    <option value="all">All Cameras</option>
                </select>
            </div>
            <div style="display: flex; align-items: center; gap: 12px; margin-right: 15px;">
                <label class="form-label" style="margin: 0; color: var(--text-body); font-size: 14px;">Event Type:</label>
                <select id="onvif-type-filter" class="form-input" style="width: 140px; padding: 6px 12px; margin: 0; background: var(--input-bg); border-color: var(--input-border); color: var(--input-text);" onchange="renderONVIFEvents()">
                    <option value="all">All Events</option>
                    <option value="onvif">ONVIF Events</option>
                    <option value="ai">AI Detections</option>
                </select>
            </div>
            <div style="display: flex; align-items: center; gap: 12px; margin-right: 15px;">
                <label class="form-label" style="margin: 0; color: var(--text-body); font-size: 14px;">Target/State:</label>
                <select id="onvif-target-filter" class="form-input" style="width: 160px; padding: 6px 12px; margin: 0; background: var(--input-bg); border-color: var(--input-border); color: var(--input-text);" onchange="renderONVIFEvents()">
                    <option value="all">All Targets/States</option>
                    <option value="person">Person Detections</option>
                    <option value="vehicle">Vehicle Detections</option>
                    <option value="animal">Animal Detections</option>
                    <option value="package">Package Detections</option>
                    <option value="active">Active Only</option>
                    <option value="clear">Clear Only</option>
                </select>
            </div>
            <div style="display: flex; align-items: center; gap: 12px; margin-right: 15px;">
                <label class="form-label" style="margin: 0; color: var(--text-body); font-size: 14px;">Search:</label>
                <input type="text" id="onvif-event-search" class="form-input" placeholder="Search events..." style="width: 180px; padding: 6px 12px; margin: 0; background: var(--input-bg); border-color: var(--input-border); color: var(--input-text);" oninput="renderONVIFEvents()">
            </div>
            <button class="btn btn-primary" onclick="clearONVIFEvents()" style="background: var(--btn-danger); border-color: var(--btn-danger); color: white; margin-right: 10px;">Clear Events</button>
            <button class="btn-matrix" onclick="toggleONVIFView(false)" style="background: var(--btn-primary); border-color: var(--btn-primary); color: white; border-radius: 6px; padding: 6px 16px;">Close Log</button>
        </div>
        
        <!-- AI Diagnostics Panel -->
        <div id="ai-diagnostics-panel" style="margin-bottom: 20px; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 8px; padding: 15px; display: none;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="color: var(--btn-primary); font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 8px;">
                    Local AI Object Detection Threads Status
                </div>
                <div id="ai-diagnostics-summary" style="font-size: 12px; color: var(--text-muted); font-weight: 500;"></div>
            </div>
            <div style="max-height: 180px; overflow-y: auto; border: 1px solid var(--border-color); border-radius: 6px; background: var(--body-bg);">
                <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 12px;">
                    <thead>
                        <tr style="border-bottom: 1px solid var(--border-color); color: var(--text-muted); background: var(--body-bg);">
                            <th style="padding: 8px 12px;">Camera</th>
                            <th style="padding: 8px 12px;">YOLO Model</th>
                            <th style="padding: 8px 12px; text-align: center;">FPS</th>
                            <th style="padding: 8px 12px; text-align: center;">Inference Latency</th>
                            <th style="padding: 8px 12px; text-align: center;">Queue Wait</th>
                            <th style="padding: 8px 12px;">Current Detection</th>
                            <th style="padding: 8px 12px; text-align: right;">Total Runs</th>
                        </tr>
                    </thead>
                    <tbody id="ai-diagnostics-body" style="color: var(--text-body); font-family: monospace;">
                        <!-- Populated dynamically -->
                    </tbody>
                </table>
            </div>
        </div>

        <div style="flex: 1; overflow-y: auto; background: var(--body-bg); border-radius: 8px; border: 1px solid var(--border-color); padding: 15px;">
            <table class="diagnostics-table" style="width: 100%; border-collapse: collapse; text-align: left;">
                <thead>
                    <tr style="border-bottom: 2px solid var(--border-color); color: var(--text-body); font-size: 14px;">
                        <th style="padding: 10px; width: 180px;">Timestamp</th>
                        <th style="padding: 10px; width: 180px;">Camera</th>
                        <th style="padding: 10px; width: 130px;">Source Type</th>
                        <th style="padding: 10px;">Topic / Event</th>
                        <th style="padding: 10px; width: 220px;">State / Detections</th>
                    </tr>
                </thead>
                <tbody id="onvif-events-body" style="color: var(--text-body); font-size: 13px; font-family: monospace;">
                    <!-- Dynamically populated -->
                </tbody>
            </table>
        </div>
    </div>
    
    <div id="logs-modal" class="modal">
        <div class="modal-content" style="max-width: 1200px; width: 95%;">
            <div class="modal-header">
                <div class="modal-title">Terminal Logs</div>
                <div style="display: flex; gap: 10px; align-items: center;">
                    <div style="display: flex; align-items: center; background: rgba(0,0,0,0.2); padding: 4px 8px; border-radius: 6px; border: 1px solid var(--border-color); margin-right: 10px;">
                        <span style="font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-right: 8px;">Font Size</span>
                        <button class="btn" style="padding: 2px 8px; font-size: 12px; min-width: 30px;" onclick="adjustLogFontSize(-1)">−</button>
                        <span id="logFontSizeDisplay" style="padding: 0 10px; font-size: 13px; font-weight: 600; color: var(--text-title); min-width: 40px; text-align: center;">16px</span>
                        <button class="btn" style="padding: 2px 8px; font-size: 12px; min-width: 30px;" onclick="adjustLogFontSize(1)">+</button>
                    </div>
                    <button class="btn" onclick="refreshLogs()">Refresh</button>
                    <button class="close-btn" onclick="closeLogsModal()">×</button>
                </div>
            </div>
            <div id="logs-container" style="background: #0d1117; color: #e6f1ff; padding: 25px; border-radius: 10px; font-family: 'Consolas', 'Monaco', 'Courier New', monospace; font-size: 16px; line-height: 1.6; max-height: 700px; overflow-y: auto; white-space: pre-wrap; word-break: break-all; border: 1px solid #30363d;">
                Loading logs...
            </div>
            <div style="margin-top: 18px; display: flex; justify-content: space-between; align-items: center; color: var(--text-muted); font-size: 14px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;">
                <span>Total 2,000 lines captured in memory</span>
                <label style="display: flex; align-items: center; gap: 10px; cursor: pointer; font-weight: 500;">
                    <input type="checkbox" id="autoScrollLogs" style="width: auto; cursor: pointer; transform: scale(1.1);">
                    <span>Auto-scroll to bottom</span>
                </label>
            </div>
        </div>
    </div>
    
    <div id="camera-modal" class="modal">
        <div class="modal-content" style="max-width: 950px;">
            <div class="modal-header">
                <div class="modal-title" id="modal-title">Add New Camera</div>
                <button class="close-btn" onclick="closeModal()">×</button>
            </div>
            
            
            <div class="tabs">
                <div class="tab active" onclick="switchAddMode('manual')" id="tab-manual">Manual Entry</div>
                <div class="tab" onclick="switchAddMode('onvif')" id="tab-onvif">Import from ONVIF</div>
            </div>
            
            <!-- ONVIF Probe Form -->
            <div id="onvif-probe-form" style="display: none;">
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Camera IP / Host</label>
                        <input type="text" class="form-input" id="probeHost" placeholder="192.168.1.50">
                    </div>
                    <div class="form-group">
                        <label class="form-label">ONVIF Port</label>
                        <input type="number" class="form-input" id="probePort" value="80">
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Username</label>
                        <input type="text" class="form-input" id="probeUser" value="admin">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Password</label>
                        <input type="text" class="form-input" id="probePass">
                    </div>
                </div>
                <button type="button" class="btn btn-primary" style="width: 100%;" onclick="probeOnvif()" id="btnProbe">
                    Scan Camera
                </button>
                
                <div id="probe-results" style="margin-top: 20px;"></div>
            </div>
                 <form id="camera-form" onsubmit="saveCamera(event)">
                <input type="hidden" id="camera-id" value="">
                
                <div class="form-group" id="copy-from-group">
                    <label class="form-label">Copy Settings From</label>
                    <select class="form-input" id="copyFrom" onchange="copyCameraSettings(this.value)">
                        <option value="">Select a camera to copy...</option>
                    </select>
                    <small style="color: #718096; font-size: 12px; margin-top: 4px; display: block;">
                        Select an existing camera to automatically fill in the details below
                    </small>
                </div>
                
                <hr style="margin: 16px 0; border: none; border-top: 1px solid #e2e8f0;">
                
                <!-- Form Tabs -->
                <div class="form-tabs">
                    <div class="form-tab active" onclick="switchFormTab('camera')" id="form-tab-camera"><i class="fas fa-video"></i> Camera</div>
                    <div class="form-tab" onclick="switchFormTab('audio')" id="form-tab-audio"><i class="fas fa-volume-up"></i> Audio</div>
                    <div class="form-tab" onclick="switchFormTab('ai')" id="form-tab-ai"><i class="fas fa-brain"></i> AI Settings</div>
                    <div class="form-tab" onclick="switchFormTab('networking')" id="form-tab-networking"><i class="fas fa-network-wired"></i> Networking</div>
                </div>

                <!-- CAMERA SECTION -->
                <div id="form-sec-camera" class="form-section active">
                    <div class="form-group">
                        <label class="form-label">Camera Name</label>
                        <input type="text" class="form-input" id="name" placeholder="Front Door" required>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label">Camera IP/Host</label>
                            <input type="text" class="form-input" id="host" placeholder="192.168.1.100" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label">RTSP Port</label>
                            <input type="number" class="form-input" id="rtspPort" value="554" required>
                        </div>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label">Username</label>
                            <input type="text" class="form-input" id="username" value="admin">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Password</label>
                            <input type="text" class="form-input" id="password">
                        </div>
                    </div>

                    <div id="sub-stream-management-header" style="margin-top: 24px; padding-top: 24px; border-top: 1px solid #e2e8f0;">
                        <h3 style="margin-top: 0; margin-bottom: 16px; color: var(--text-title); font-size: 16px; display: flex; align-items: center; gap: 8px;">
                            <i class="fas fa-microchip"></i> Sub Stream Management
                        </h3>
                        
                        <div class="form-row" style="gap: 24px; margin-bottom: 0;">
                            <div class="form-group" style="flex: 1; margin-bottom: 0; background: rgba(0,0,0,0.03); padding: 15px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.08);">
                                 <label class="auto-start-row" style="cursor: pointer; display: flex; align-items: center; justify-content: space-between;">
                                    <span class="auto-start-label" style="font-size: 13px; font-weight: 600;">Disable Substream</span>
                                    <label class="toggle-switch">
                                        <input type="checkbox" id="disableSubstream" onchange="toggleSubStreamFields()">
                                        <span class="toggle-slider"></span>
                                    </label>
                                </label>
                                <small style="color: #718096; font-size: 11px; display: block; margin-top: 4px;">For cameras that only support one stream</small>
                            </div>

                            <div class="form-group" style="flex: 1; margin-bottom: 0; background: rgba(0,0,0,0.03); padding: 15px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.08);">
                                 <label class="auto-start-row" style="cursor: pointer; display: flex; align-items: center; justify-content: space-between;">
                                    <span class="auto-start-label" style="font-size: 13px; font-weight: 600;">Use Main as Substream</span>
                                    <label class="toggle-switch">
                                        <input type="checkbox" id="useMainAsSubstream" onchange="toggleSubStreamFields()">
                                        <span class="toggle-slider"></span>
                                    </label>
                                </label>
                                <small style="color: #718096; font-size: 11px; display: block; margin-top: 4px;">Efficient: Source sub-stream from server's main stream</small>
                            </div>
                        </div>
                    </div>

                    <div class="form-row" style="align-items: flex-start; gap: 24px; border-top: 1px solid #e2e8f0; padding-top: 24px; margin-top: 24px;">
                        <!-- Main Stream Column -->
                        <div class="form-col" style="flex: 1; padding-right: 12px; border-right: 1px solid #e2e8f0;">
                            <h3 style="margin-top: 0; margin-bottom: 16px; color: var(--text-title); font-size: 16px; display: flex; align-items: center; gap: 8px;">
                                <i class="fas fa-video"></i> Main Stream Settings
                            </h3>
                            
                            <div style="background: rgba(0,0,0,0.03); padding: 15px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.08); margin-bottom: 20px;">
                                <div class="form-group">
                                    <label class="form-label">Main Stream Path</label>
                                    <input type="text" class="form-input" id="mainPath" placeholder="/stream1" value="/stream1" required>
                                </div>
                                
                                <label class="form-label">Resolution & FPS</label>
                                <div class="form-row" style="margin-bottom: 0;">
                                    <div class="form-group" style="margin-bottom: 0;">
                                        <input type="number" class="form-input" id="mainWidth" placeholder="Width" value="1920" required>
                                    </div>
                                    <div class="form-group" style="margin-bottom: 0;">
                                        <input type="number" class="form-input" id="mainHeight" placeholder="Height" value="1080" required>
                                    </div>
                                    <div class="form-group" style="margin-bottom: 0; flex: 0.5;">
                                        <input type="number" class="form-input" id="mainFramerate" placeholder="FPS" value="30" required>
                                    </div>
                                </div>
                            </div>
                            
                            <button type="button" class="btn btn-secondary" onclick="fetchStreamInfo('main')" style="width:100%; margin-bottom: 20px; font-size: 13px;">
                                Fetch Main Stream Info
                            </button>
                            
                            <div class="form-group" style="background: rgba(0,0,0,0.03); padding: 15px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.08);">
                                <div class="auto-start-row" style="margin-bottom: 0;">
                                    <span class="auto-start-label" style="font-size: 13px;">Transcode Main Video Stream</span>
                                    <label class="toggle-switch">
                                        <input type="checkbox" id="transcodeMain" onchange="toggleTranscodeNotice('main')">
                                        <span class="toggle-slider"></span>
                                    </label>
                                </div>
                                <div id="mainTranscodeNotice" style="display: none; color: #f6ad55; font-size: 11px; margin-top: 10px; font-weight: 500;">
                                    <i class="fas fa-info-circle"></i> Video will be transcoded to the resolution set in the Resolution and FPS section above.
                                </div>
                            </div>
                        </div>

                        <!-- Sub Stream Column -->
                        <div class="form-col" style="flex: 1; padding-left: 12px;" id="sub-stream-col">
                            <h3 style="margin-top: 0; margin-bottom: 16px; color: var(--text-title); font-size: 16px; display: flex; align-items: center; gap: 8px;">
                                <i class="fas fa-compress-alt"></i> Sub Stream Settings
                            </h3>
                            
                            <div id="sub-stream-fields-container">
                                <div style="background: rgba(0,0,0,0.03); padding: 15px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.08); margin-bottom: 20px;">
                                    <div class="form-group" id="subPathContainer">
                                        <label class="form-label">Sub Stream Path</label>
                                        <input type="text" class="form-input" id="subPath" placeholder="/stream2" value="/stream2">
                                    </div>
                                    
                                    <label class="form-label">Resolution & FPS</label>
                                    <div class="form-row" style="margin-bottom: 0;">
                                        <div class="form-group" style="margin-bottom: 0;">
                                            <input type="number" class="form-input" id="subWidth" placeholder="Width" value="640">
                                        </div>
                                        <div class="form-group" style="margin-bottom: 0;">
                                            <input type="number" class="form-input" id="subHeight" placeholder="Height" value="480">
                                        </div>
                                        <div class="form-group" style="margin-bottom: 0; flex: 0.5;">
                                            <input type="number" class="form-input" id="subFramerate" placeholder="FPS" value="15">
                                        </div>
                                    </div>
                                </div>
                                
                                <button type="button" class="btn btn-secondary" id="btnFetchSub" onclick="fetchStreamInfo('sub')" style="width:100%; margin-bottom: 20px; font-size: 13px;">
                                    Fetch Sub Stream Info
                                </button>

                                <div class="form-group" style="background: rgba(0,0,0,0.03); padding: 15px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.08);">
                                    <div class="auto-start-row" style="margin-bottom: 0;">
                                        <span class="auto-start-label" style="font-size: 13px;">Transcode Sub Video Stream</span>
                                        <label class="toggle-switch">
                                            <input type="checkbox" id="transcodeSub" onchange="toggleTranscodeNotice('sub')">
                                            <span class="toggle-slider"></span>
                                        </label>
                                    </div>
                                    <div id="subTranscodeNotice" style="display: none; color: #f6ad55; font-size: 11px; margin-top: 10px; font-weight: 500;">
                                        <i class="fas fa-info-circle"></i> Video will be transcoded to the resolution set in the Resolution and FPS section above.
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row" style="margin-top: 24px; border-top: 1px solid #e2e8f0; padding-top: 24px;">
                        <div class="form-group" style="flex: 1;">
                            <label class="form-label">ONVIF Port (leave empty for auto-assign)</label>
                            <input type="number" class="form-input" id="onvifPort" placeholder="Auto-assigned">
                        </div>
                        <div class="form-group" style="flex: 1.5;">
                            <label class="form-label" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                                <span>Device UUID</span>
                                <button type="button" class="btn" style="padding: 2px 8px; font-size: 11px; height: auto; background: rgba(49, 130, 206, 0.15); border: 1px solid rgba(49, 130, 206, 0.3); color: #63b3ed; cursor: pointer; border-radius: 4px; display: inline-flex; align-items: center; gap: 4px;" onclick="generateNewUuid()">
                                    <i class="fas fa-random"></i> Generate
                                </button>
                            </label>
                            <input type="text" class="form-input" id="cameraUuid" placeholder="Auto-assigned on first save" style="font-family: monospace; font-size: 12px;">
                        </div>
                    </div>

                    <div class="form-group" style="margin-bottom: 10px;">
                        <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                            <input type="checkbox" id="autoStart" style="width: auto; cursor: pointer;">
                            <span class="form-label" style="margin: 0;">Auto-start camera on server startup</span>
                        </label>
                    </div>
                    
                    <div class="alert alert-info" style="margin-top: 20px;">
                        <strong>Common formats:</strong><br>
                        Hikvision: /Streaming/Channels/101<br>
                        Reolink: /h264Preview_01_main<br>
                        Dahua: /cam/realmonitor?channel=1&subtype=0
                    </div>
                </div>

                <!-- AUDIO SECTION -->
                <div id="form-sec-audio" class="form-section">
                    <div style="background: rgba(0,0,0,0.03); padding: 20px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.08); margin-bottom: 24px;">
                        <label class="auto-start-row" style="cursor: pointer; display: flex; align-items: center; justify-content: space-between; margin-bottom: 0;">
                            <div style="display: flex; align-items: center; gap: 12px;">
                                <div style="background: var(--primary-color); color: white; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                                    <i class="fas fa-volume-up"></i>
                                </div>
                                <div>
                                    <span class="auto-start-label" style="font-size: 14px; font-weight: 700; color: var(--text-title); display: block; line-height: 1.2;">Enable RTSP Audio</span>
                                    <small style="color: #718096; font-size: 11px;">Enable audio support for both Main and Sub streams (UniFi Protect ONLY supports AAC)</small>
                                </div>
                            </div>
                            <label class="toggle-switch">
                                <input type="checkbox" id="enableAudio">
                                <span class="toggle-slider"></span>
                            </label>
                        </label>
                        <small style="color: #f6ad55; font-size: 11px; display: block; margin-top: 10px;"><i class="fas fa-info-circle"></i> If you're running UniFi Protect version 7.1 or newer, make sure to enable "Stream Compatibility Mode – Improved" in your UniFi Console's camera settings to ensure audio is properly supported.</small>
                    </div>

                    <div class="form-row" style="align-items: flex-start; gap: 24px;">
                        <!-- Main Stream Audio -->
                        <div class="form-col" style="flex: 1; background: rgba(0,0,0,0.03); padding: 15px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.08);">
                            <label class="auto-start-row" style="cursor: pointer; display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px;">
                                <div>
                                    <span class="auto-start-label" style="font-size: 13px; font-weight: 600; color: var(--text-title); display: block;">Transcode Main Audio</span>
                                    <small style="color: #718096; font-size: 11px;">If native audio is not AAC</small>
                                </div>
                                <label class="toggle-switch">
                                    <input type="checkbox" id="transcodeMainAudio" onchange="toggleAudioSettings('main')">
                                    <span class="toggle-slider"></span>
                                </label>
                            </label>

                            <div id="mainAudioSettings" style="display: none; padding: 12px; background: rgba(255,255,255,0.05); border-radius: 6px; border: 1px solid rgba(255,255,255,0.1);">
                                <div class="form-group" style="margin-bottom: 12px;">
                                    <label class="form-label" style="font-size: 11px;">Audio Encoding</label>
                                    <select class="form-input" id="audioEncodingMain" style="font-size: 12px; padding: 6px 10px;">
                                        <option value="aac">AAC</option>
                                        <option value="g711ulaw">G.711ulaw</option>
                                        <option value="g711alaw">G.711alaw</option>
                                        <option value="g722.1">G.722.1</option>
                                        <option value="mp2l2">MP2L2</option>
                                        <option value="g726">G.726</option>
                                        <option value="pcm">PCM</option>
                                        <option value="mp3">MP3</option>
                                    </select>
                                </div>
                                <div class="form-row" style="gap: 12px; margin-bottom: 0;">
                                    <div class="form-group" style="flex: 1; margin-bottom: 0;">
                                        <label class="form-label" style="font-size: 11px;">Sampling Rate</label>
                                        <select class="form-input" id="audioSampleRateMain" style="font-size: 12px; padding: 6px 10px;">
                                            <option value="8000">8kHz</option>
                                            <option value="16000">16kHz</option>
                                            <option value="32000">32kHz</option>
                                            <option value="44100">44.1kHz</option>
                                            <option value="48000">48kHz</option>
                                        </select>
                                    </div>
                                    <div class="form-group" style="flex: 1; margin-bottom: 0;">
                                        <label class="form-label" style="font-size: 11px;">Audio Stream Bitrate</label>
                                        <select class="form-input" id="audioBitrateMain" style="font-size: 12px; padding: 6px 10px;">
                                            <option value="16k">16kbps</option>
                                            <option value="32k">32kbps</option>
                                            <option value="64k">64kbps</option>
                                            <option value="128k">128kbps</option>
                                            <option value="256k">256kbps</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Sub Stream Audio -->
                        <div class="form-col" style="flex: 1; background: rgba(0,0,0,0.03); padding: 15px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.08);">
                            <label class="auto-start-row" style="cursor: pointer; display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px;">
                                <div>
                                    <span class="auto-start-label" style="font-size: 13px; font-weight: 600; color: var(--text-title); display: block;">Transcode Sub Audio</span>
                                    <small style="color: #718096; font-size: 11px;">If native audio is not AAC</small>
                                </div>
                                <label class="toggle-switch">
                                    <input type="checkbox" id="transcodeSubAudio" onchange="toggleAudioSettings('sub')">
                                    <span class="toggle-slider"></span>
                                </label>
                            </label>

                            <div id="subAudioSettings" style="display: none; padding: 12px; background: rgba(255,255,255,0.05); border-radius: 6px; border: 1px solid rgba(255,255,255,0.1);">
                                <div class="form-group" style="margin-bottom: 12px;">
                                    <label class="form-label" style="font-size: 11px;">Audio Encoding</label>
                                    <select class="form-input" id="audioEncodingSub" style="font-size: 12px; padding: 6px 10px;">
                                        <option value="aac">AAC</option>
                                        <option value="g711ulaw">G.711ulaw</option>
                                        <option value="g711alaw">G.711alaw</option>
                                        <option value="g722.1">G.722.1</option>
                                        <option value="mp2l2">MP2L2</option>
                                        <option value="g726">G.726</option>
                                        <option value="pcm">PCM</option>
                                        <option value="mp3">MP3</option>
                                    </select>
                                </div>
                                <div class="form-row" style="gap: 12px; margin-bottom: 0;">
                                    <div class="form-group" style="flex: 1; margin-bottom: 0;">
                                        <label class="form-label" style="font-size: 11px;">Sampling Rate</label>
                                        <select class="form-input" id="audioSampleRateSub" style="font-size: 12px; padding: 6px 10px;">
                                            <option value="8000">8kHz</option>
                                            <option value="16000">16kHz</option>
                                            <option value="32000">32kHz</option>
                                            <option value="44100">44.1kHz</option>
                                            <option value="48000">48kHz</option>
                                        </select>
                                    </div>
                                    <div class="form-group" style="flex: 1; margin-bottom: 0;">
                                        <label class="form-label" style="font-size: 11px;">Audio Stream Bitrate</label>
                                        <select class="form-input" id="audioBitrateSub" style="font-size: 12px; padding: 6px 10px;">
                                            <option value="16k">16kbps</option>
                                            <option value="32k">32kbps</option>
                                            <option value="64k">64kbps</option>
                                            <option value="128k">128kbps</option>
                                            <option value="256k">256kbps</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- AI SECTION -->
                <div id="form-sec-ai" class="form-section">
                    <div class="form-group" style="margin-bottom: 15px;">
                        <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                            <input type="checkbox" id="enableEventForwarding" style="width: auto; cursor: pointer;" onchange="toggleEventForwardingFields()">
                            <span class="form-label" style="margin: 0; font-weight: 500; display: inline-flex; align-items: center; gap: 6px;">
                                Enable AI Onvif Events or ONVIF Event Forwarding
                                <span style="font-size: 10px; background-color: #d69e2e; color: #1a202c; padding: 1px 6px; border-radius: 4px; font-weight: bold; text-transform: uppercase;">Beta</span>
                            </span>
                        </label>
                        <div style="color: var(--text-body); font-size: 11px; margin-left: 24px; margin-top: 4px;">
                            Forward original motion and inputs from physical camera's ONVIF to virtual server. (Beta - please report any issues)
                        </div>
                    </div>
                    
                    <div class="form-group" id="eventSourceGroup" style="display: none; margin-left: 24px; margin-top: 10px;">
                        <label class="form-label" style="font-size: 12px;">Event Source Mode</label>
                        <select class="form-input" id="eventSource" onchange="toggleEventSourceFields()" style="background-color: var(--input-bg); color: var(--input-text); border: 1px solid var(--input-border);">
                            <option value="onvif">Forward Physical Camera ONVIF Events</option>
                            <option value="ai">Local AI Object Detection (YOLOv8)</option>
                        </select>
                    </div>

                    <div class="form-group" id="physicalOnvifPortGroup" style="display: none; margin-left: 24px;">
                        <label class="form-label" style="font-size: 12px;">Physical Camera ONVIF Port</label>
                        <input type="number" class="form-input" id="physicalOnvifPort" placeholder="80" value="80" style="max-width: 150px;">
                    </div>

                    <div id="onvifForwardingCredGroup" style="display: none; margin-left: 24px; margin-top: 10px;">
                        <div style="font-size: 12px; color: var(--text-body); font-weight: 600; margin-bottom: 8px;">ONVIF Credentials</div>
                        <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; margin-bottom: 10px;">
                            <input type="checkbox" id="onvifUseAboveCredentials" style="width: auto; cursor: pointer;" checked onchange="toggleOnvifCredFields()">
                            <span style="font-size: 12px; color: var(--text-title);">Use above camera credentials</span>
                        </label>
                        <div id="onvifCustomCredFields" style="display: none;">
                            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                                <div style="flex: 1; min-width: 120px;">
                                    <label class="form-label" style="font-size: 11px;">ONVIF Username</label>
                                    <input type="text" class="form-input" id="onvifForwardingUsername" placeholder="admin" autocomplete="off">
                                </div>
                                <div style="flex: 1; min-width: 120px;">
                                    <label class="form-label" style="font-size: 11px;">ONVIF Password</label>
                                    <input type="password" class="form-input" id="onvifForwardingPassword" placeholder="password" autocomplete="new-password">
                                </div>
                            </div>
                        </div>
                    </div>

                    <div id="aiHardwareInfoGroup" style="display: none; margin-left: 24px; margin-top: 12px; margin-bottom: 8px; font-size: 11px; padding: 10px; border-radius: 6px; background-color: var(--alert-info-bg); color: var(--alert-info-text); border-left: 3px solid #10b981; line-height: 1.5;">
                        <i class="fas fa-microchip"></i> <strong>AI HW Acceleration:</strong> Supported on NVIDIA (CUDA) and Apple Silicon (MPS/CoreML).<br>
                        <i class="fas fa-desktop"></i> <strong>Active Host Hardware:</strong> <span id="settings-ai-device" style="color: var(--btn-primary); font-weight: bold;">Loading...</span>
                    </div>

                    <div id="aiModelGroup" style="display: none; margin-left: 24px; margin-top: 12px; margin-bottom: 12px;">
                        <label class="form-label" style="font-size: 12px; margin-bottom: 4px; display: block;">AI Object Detection Model</label>
                        <select class="form-input" id="aiModel" onchange="updateModelDescription()" style="background-color: var(--input-bg); color: var(--input-text); border: 1px solid var(--input-border); max-width: 100%;">
                            <option value="yolov8n.pt">YOLOv8 Nano (yolov8n.pt) - Default</option>
                            <option value="yolo11n.pt">YOLO11 Nano (yolo11n.pt) - Newest & Recommended</option>
                            <option value="yolo11s.pt">YOLO11 Small (yolo11s.pt)</option>
                            <option value="yolov8s.pt">YOLOv8 Small (yolov8s.pt)</option>
                            <option value="yolov8m.pt">YOLOv8 Medium (yolov8m.pt)</option>
                            <option value="yolo11l.pt">YOLO11 Large (yolo11l.pt)</option>
                            <option value="yolo11x.pt">YOLO11 Extra-Large (yolo11x.pt)</option>
                            <option value="yolov8l.pt">YOLOv8 Large (yolov8l.pt)</option>
                            <option value="yolov8x.pt">YOLOv8 Extra-Large (yolov8x.pt)</option>
                        </select>
                        <div id="aiModelDescription" style="margin-top: 8px; font-size: 11px; padding: 10px; border-radius: 6px; background-color: var(--alert-info-bg); line-height: 1.4; color: var(--alert-info-text); border-left: 3px solid var(--btn-primary);">
                            <!-- Dynamically populated description -->
                        </div>
                    </div>

                    <div id="aiTargetClassesGroup" style="display: none; margin-left: 24px; margin-top: 12px;">
                        <div style="font-size: 12px; color: #a0aec0; font-weight: 600; margin-bottom: 8px;">AI Target Detection (COCO Objects)</div>
                        <div style="display: flex; gap: 15px; flex-wrap: wrap;">
                            <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                                <input type="checkbox" id="aiTargetPerson" style="width: auto; cursor: pointer;" checked>
                                <span style="font-size: 12px; color: #cbd5e0;">Person</span>
                            </label>
                            <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                                <input type="checkbox" id="aiTargetVehicle" style="width: auto; cursor: pointer;" checked>
                                <span style="font-size: 12px; color: #cbd5e0;">Vehicle</span>
                            </label>
                            <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                                <input type="checkbox" id="aiTargetAnimal" style="width: auto; cursor: pointer;">
                                <span style="font-size: 12px; color: #cbd5e0;">Animal</span>
                            </label>
                            <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                                <input type="checkbox" id="aiTargetPackage" style="width: auto; cursor: pointer;">
                                <span style="font-size: 12px; color: #cbd5e0;">Package</span>
                            </label>
                        </div>
                    </div>

                    <div id="sendSmartOnvifTopicsGroup" style="display: none; margin-left: 24px; margin-top: 12px;">
                        <div style="font-size: 12px; color: #a0aec0; font-weight: 600; margin-bottom: 8px;">ONVIF Event Formatting</div>
                        <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                            <input type="checkbox" id="sendSmartOnvifTopics" style="width: auto; cursor: pointer;" checked onchange="toggleSmartOnvifWarning()">
                            <span style="font-size: 12px; color: #cbd5e0;">Send Smart ONVIF Topics (HumanShapeDetect, VehicleDetect, AnimalDetect, PackageDetect)</span>
                        </label>
                        <div style="font-size: 11px; color: #718096; margin-top: 4px; margin-left: 20px; line-height: 1.4;">
                            If enabled, triggers specific smart ONVIF events when objects are detected. If disabled, reverts to standard generic motion events.
                        </div>
                        <div id="smartOnvifWarning" style="display: none; margin-top: 12px; margin-left: 20px; padding: 12px; background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 6px; font-size: 11px; color: #f6ad55; line-height: 1.5;">
                            ⚠️ <strong>UniFi NVR Compatibility Note:</strong> To display Smart Detections (Person, Vehicle, etc.) in UniFi Protect, you currently need to run this third party project <a href="https://github.com/danielwoz/ubiquiti-protect-onvif-event-listener" target="_blank" style="color: #63b3ed; text-decoration: underline; font-weight: 500;">ubiquiti-protect-onvif-event-listener</a>. Without it, smart events will not be registered by the NVR. While I expect native support from Ubiquiti in a future update, this event listener is required for now. It is recommended you reboot the NVR after adding all your cameras.
                        </div>
                    </div>

                    <div id="aiSensitivityGroup" style="display: none; margin-left: 24px; margin-top: 12px;">
                        <div style="font-size: 12px; color: #a0aec0; font-weight: 600; margin-bottom: 8px;">Detection Sensitivity</div>
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <span style="font-size: 10px; color: #718096; white-space: nowrap;">Low</span>
                            <div style="flex: 1; display: flex; flex-direction: column; gap: 4px; position: relative;">
                                <input type="range" id="aiMotionSensitivity" min="10" max="95" value="50" style="width: 100%; cursor: pointer; accent-color: #3182ce; margin: 0;" oninput="updateAiSensitivityDisplay(this.value)">
                                <div style="position: relative; height: 6px; background: #2d3748; border-radius: 3px; overflow: hidden; margin-top: 2px;">
                                    <div style="position: absolute; left: 35.3%; width: 23.5%; height: 100%; background: rgba(16, 185, 129, 0.45);" title="Recommended Indoor Range (40% - 60%)"></div>
                                    <div style="position: absolute; left: 76.5%; width: 11.8%; height: 100%; background: rgba(245, 158, 11, 0.55);" title="Recommended Outdoor Range (75% - 85%)"></div>
                                </div>
                                <div style="position: relative; height: 12px; margin-top: 2px;">
                                    <span style="position: absolute; left: 47%; transform: translateX(-50%); font-size: 8px; color: #10b981; font-weight: bold; white-space: nowrap;">INDOOR (40-60%)</span>
                                    <span style="position: absolute; left: 82.3%; transform: translateX(-50%); font-size: 8px; color: #f59e0b; font-weight: bold; white-space: nowrap;">OUTDOOR (75-85%)</span>
                                </div>
                            </div>
                            <span style="font-size: 10px; color: #718096; white-space: nowrap;">High</span>
                            <span id="aiSensitivityValue" style="font-size: 12px; color: #3182ce; font-weight: 700; min-width: 36px; text-align: center;">50%</span>
                        </div>
                        <div style="color: #718096; font-size: 10px; margin-top: 14px; display: flex; justify-content: space-between; align-items: center;">
                            <span>Higher sensitivity detects more objects. Lower is more strict.</span>
                            <span id="aiSensitivityStatus" style="font-weight: 600; padding: 2px 6px; border-radius: 4px; font-size: 9px; text-transform: uppercase; border: 1px solid transparent;"></span>
                        </div>
                    </div>

                    <div id="aiConfidenceGroup" style="display: none; margin-left: 24px; margin-top: 12px;">
                        <div style="font-size: 12px; color: #a0aec0; font-weight: 600; margin-bottom: 8px;">AI Confidence Threshold</div>
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <span style="font-size: 10px; color: #718096; white-space: nowrap;">10%</span>
                            <div style="flex: 1; display: flex; flex-direction: column; gap: 4px; position: relative;">
                                <input type="range" id="aiConfidenceThreshold" min="10" max="95" value="50" style="width: 100%; cursor: pointer; accent-color: #3182ce; margin: 0;" oninput="updateAiConfidenceDisplay(this.value)">
                            </div>
                            <span style="font-size: 10px; color: #718096; white-space: nowrap;">95%</span>
                            <span id="aiConfidenceValue" style="font-size: 12px; color: #3182ce; font-weight: 700; min-width: 36px; text-align: center;">50%</span>
                        </div>
                        <div style="color: #718096; font-size: 10px; margin-top: 6px;">
                            Objects detected with confidence below this threshold will be ignored. Higher confidence reduces false positives.
                        </div>
                    </div>

                    <div id="aiZoneGroup" style="display: none; margin-left: 24px; margin-top: 15px; padding-top: 12px; border-top: 1px dashed #2d3748;">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                            <div style="font-size: 12px; color: #a0aec0; font-weight: 600;">Detection Zone</div>
                            <div style="display: flex; gap: 6px;">
                                <button type="button" id="btnLoadZoneSnapshot" onclick="loadZoneSnapshot()" style="padding: 4px 10px; font-size: 10px; background: #2d3748; color: #a0aec0; border: 1px solid #4a5568; border-radius: 4px; cursor: pointer; display: inline-flex; align-items: center; gap: 4px;">
                                    <i class="fas fa-camera"></i> Load Snapshot
                                </button>
                                <button type="button" id="btnClearZone" onclick="clearZone()" style="padding: 4px 10px; font-size: 10px; background: #2d3748; color: #f56565; border: 1px solid #4a5568; border-radius: 4px; cursor: pointer; display: inline-flex; align-items: center; gap: 4px;">
                                    <i class="fas fa-trash"></i> Clear Zone
                                </button>
                            </div>
                        </div>
                        <div id="zoneCanvasContainer" style="position: relative; width: 100%; background: #0f172a; border-radius: 8px; border: 1px solid #1e293b; overflow: hidden; aspect-ratio: 16/9; cursor: crosshair;">
                            <canvas id="zoneCanvas" style="width: 100%; height: 100%; display: block;"></canvas>
                            <div id="zoneEmptyState" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; pointer-events: none;">
                                <i class="fas fa-draw-polygon" style="font-size: 24px; color: #4a5568; margin-bottom: 8px; display: block;"></i>
                                <div style="font-size: 11px; color: #4a5568;">Click "Load Snapshot" then click to draw a detection zone polygon</div>
                            </div>
                        </div>
                        <div style="color: #718096; font-size: 10px; margin-top: 4px;">
                            Draw a polygon zone. Only detections inside this zone will trigger events. Leave empty to monitor the full frame.
                        </div>
                    </div>

                    <div id="aiCopySettingsGroup" style="display: none; margin-left: 24px; margin-top: 15px; padding-top: 12px; border-top: 1px dashed #2d3748;">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                            <div style="font-size: 12px; color: #a0aec0; font-weight: 600;">Copy AI Settings to Other Cameras</div>
                        </div>
                        <button type="button" onclick="openCopyAiSettingsModal()" style="padding: 6px 14px; font-size: 12px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); color: white; border: none; border-radius: 4px; cursor: pointer; transition: all 0.2s ease;">
                            <i class="fas fa-copy"></i> Copy Settings to Cameras...
                        </button>
                        <div style="color: #718096; font-size: 10px; margin-top: 4px;">
                            Copies event source, AI model, targets, and sensitivity to selected cameras. Motion zones are NOT copied.
                        </div>
                    </div>

                    <div id="aiInstallGroup" style="display: none; margin-left: 24px; margin-top: 12px;">
                        <div style="background: rgba(246, 173, 85, 0.1); padding: 12px; border-radius: 8px; border-left: 4px solid #f6ad55; margin-bottom: 12px;">
                            <div style="font-weight: bold; color: #f6ad55; font-size: 13px; margin-bottom: 5px;"><i class="fas fa-exclamation-triangle"></i> Local AI Dependencies Missing</div>
                            <div style="color: #cbd5e0; font-size: 12px; line-height: 1.4;">The required AI libraries (<code>ultralytics</code> and <code>opencv-python-headless</code>) are not installed on this server. This is required for local object detection.</div>
                        </div>
                        <div style="margin-top: 10px;">
                            <div style="font-size: 11px; font-weight: 600; color: #a0aec0; margin-bottom: 6px;">PyTorch Backend:</div>
                            <div style="display: flex; flex-direction: column; gap: 6px;">
                                <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; background: rgba(255,255,255,0.03); padding: 8px 10px; border-radius: 6px; border: 1px solid #2d3748;">
                                    <input type="radio" name="aiBackend" value="cpu" checked style="width: auto; accent-color: #3182ce;">
                                    <div>
                                        <span style="font-size: 12px; font-weight: 600; color: #e2e8f0;">CPU Only</span>
                                        <span style="font-size: 10px; color: #718096; margin-left: 6px;">~200MB download, works everywhere</span>
                                    </div>
                                </label>
                                <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; background: rgba(255,255,255,0.03); padding: 8px 10px; border-radius: 6px; border: 1px solid #2d3748;">
                                    <input type="radio" name="aiBackend" value="cuda" style="width: auto; accent-color: #48bb78;">
                                    <div>
                                        <span style="font-size: 12px; font-weight: 600; color: #e2e8f0;">NVIDIA CUDA GPU</span>
                                        <span style="font-size: 10px; color: #718096; margin-left: 6px;">~2.5GB download, requires NVIDIA GPU</span>
                                    </div>
                                </label>
                                <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; background: rgba(255,255,255,0.03); padding: 8px 10px; border-radius: 6px; border: 1px solid #2d3748;">
                                    <input type="radio" name="aiBackend" value="mps" style="width: auto; accent-color: #9f7aea;">
                                    <div>
                                        <span style="font-size: 12px; font-weight: 600; color: #e2e8f0;">Apple Silicon (MPS)</span>
                                        <span style="font-size: 10px; color: #718096; margin-left: 6px;">Auto-detect, uses Metal on macOS</span>
                                    </div>
                                </label>
                            </div>
                        </div>
                        <button type="button" class="btn-submit" id="installAiBtn" onclick="startAiInstallation()" style="margin-top: 15px; width: 100%; display: flex; align-items: center; justify-content: center; gap: 8px; font-size: 13px; padding: 10px; background-color: #3182ce; color: white; border: none; border-radius: 6px; cursor: pointer;">
                            <i class="fas fa-download"></i> Install AI Dependencies
                        </button>
                        <div id="aiInstallProgressContainer" style="display: none; margin-top: 15px;">
                            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                                <span id="aiInstallStatusText" style="font-size: 12px; font-weight: 600; color: #3182ce;">Installing...</span>
                                <span id="aiInstallSpinner"><i class="fas fa-spinner fa-spin" style="color: #3182ce;"></i></span>
                            </div>
                            <pre id="aiInstallLogs" style="background-color: #0f172a; color: #38bdf8; font-family: monospace; font-size: 11px; padding: 12px; border-radius: 8px; max-height: 180px; overflow-y: auto; white-space: pre-wrap; margin: 0; border: 1px solid #1e293b;"></pre>
                        </div>
                    </div>
                    
                    <div id="aiTestEventGroup" style="display: none; margin-left: 24px; margin-top: 15px; padding-top: 15px; border-top: 1px dashed #2d3748;">
                        <div style="font-size: 12px; color: #a0aec0; font-weight: 600; margin-bottom: 8px;">Test Event Delivery</div>
                        <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                            <button type="button" class="btn" id="btnTestOnvifEvent" onclick="sendTestOnvifEvent()" style="padding: 6px 12px; font-size: 12px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; border: none; border-radius: 4px; cursor: pointer; transition: all 0.2s ease;">
                                <i class="fas fa-paper-plane"></i> Send Test ONVIF Event
                            </button>
                            <button type="button" class="btn" id="btnTestPersonEvent" onclick="sendTestOnvifEvent('person')" style="padding: 6px 12px; font-size: 12px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; background: linear-gradient(135deg, #3182ce 0%, #2b6cb0 100%); color: white; border: none; border-radius: 4px; cursor: pointer; transition: all 0.2s ease;">
                                <i class="fas fa-user"></i> Person
                            </button>
                            <button type="button" class="btn" id="btnTestVehicleEvent" onclick="sendTestOnvifEvent('vehicle')" style="padding: 6px 12px; font-size: 12px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; background: linear-gradient(135deg, #805ad5 0%, #6b46c1 100%); color: white; border: none; border-radius: 4px; cursor: pointer; transition: all 0.2s ease;">
                                <i class="fas fa-car"></i> Vehicle
                            </button>
                            <button type="button" class="btn" id="btnTestAnimalEvent" onclick="sendTestOnvifEvent('animal')" disabled style="padding: 6px 12px; font-size: 12px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; background: linear-gradient(135deg, #38a169 0%, #2f855a 100%); color: white; border: none; border-radius: 4px; cursor: not-allowed; opacity: 0.5; transition: all 0.2s ease;">
                                <i class="fas fa-paw"></i> Animal
                            </button>
                            <button type="button" class="btn" id="btnTestPackageEvent" onclick="sendTestOnvifEvent('package')" disabled style="padding: 6px 12px; font-size: 12px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; background: linear-gradient(135deg, #dd6b20 0%, #c05621 100%); color: white; border: none; border-radius: 4px; cursor: not-allowed; opacity: 0.5; transition: all 0.2s ease;">
                                <i class="fas fa-box"></i> Package
                            </button>
                            <span id="aiTestEventFeedback" style="font-size: 11px; color: #a0aec0;"></span>
                        </div>
                        <div style="color: #718096; font-size: 10px; margin-top: 5px;">
                            Sends a 3-second motion event to all ONVIF clients (e.g., UniFi Protect) currently subscribed to this camera.
                        </div>
                    </div>
                    
                    <div id="aiUninstallGroup" style="display: none; margin-left: 24px; margin-top: 15px; padding-top: 15px; border-top: 1px dashed #2d3748;">
                        <div style="font-size: 12px; color: #a0aec0; font-weight: 600; margin-bottom: 8px;">Maintenance</div>
                        <button type="button" class="btn" id="uninstallAiBtn" onclick="startAiUninstall()" style="padding: 6px 12px; font-size: 12px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; background-color: #e53e3e; color: white; border: none; border-radius: 4px; cursor: pointer; transition: all 0.2s ease;">
                            <i class="fas fa-trash-alt"></i> Uninstall AI Dependencies
                        </button>
                        <div style="color: #718096; font-size: 10px; margin-top: 5px;">
                            Uninstalls YOLO framework, PyTorch, and related components from the python environment to free up disk space or allow a fresh reinstall.
                        </div>
                    </div>
                </div>

                <!-- NETWORKING SECTION -->
                <div id="form-sec-networking" class="form-section">
                    <div id="linux-network-section">
                        <div style="font-size: 14px; font-weight: 600; color: #a0aec0; margin-bottom: 15px; display: flex; align-items: center; gap: 8px;">
                            <span>Network Settings (Linux Only)</span>
                        </div>

                        <div class="form-group">
                            <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                                <input type="checkbox" id="useVirtualNic" onchange="toggleNetworkFields()" style="width: auto; cursor: pointer;">
                                <span class="form-label" style="margin: 0;">Use Virtual Network Interface (MACVLAN)</span>
                            </label>
                        </div>

                        <div id="vnic-fields" style="display: none;">
                            <div class="form-group" style="margin-bottom: 15px;">
                                <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                                    <input type="checkbox" id="vnicKeepalive" style="width: auto; cursor: pointer;">
                                    <span class="form-label" style="margin: 0; font-weight: normal;">Enable Switch Keepalive (Pings gateway/broadcast every 60s)</span>
                                </label>
                                <div style="font-size: 11px; color: #718096; margin-left: 22px; margin-top: 4px; line-height: 1.4;">
                                    Highly recommended if using UniFi or switches that drop inactive MAC addresses, preventing streams from timing out.
                                </div>
                            </div>

                            <div class="form-group" style="background: rgba(246, 173, 85, 0.1); padding: 12px; border-radius: 8px; border-left: 4px solid #f6ad55; margin-bottom: 20px;">
                                <div style="font-size: 12px; color: #f6ad55; font-weight: 600; margin-bottom: 4px;"><i class="fas fa-exclamation-triangle"></i> Ubiquiti / UniFi Protect Alert</div>
                                <div style="font-size: 11px; color: #a0aec0; line-height: 1.4;">
                                    UniFi Protect requires each camera to have a unique MAC address.
                                </div>
                            </div>
                            <div class="form-group" style="margin-bottom: 15px;">
                                <label class="form-label">Virtual NIC MAC Address (Optional)</label>
                                <div style="display: flex; gap: 8px;">
                                    <input type="text" class="form-input" id="nicMac" placeholder="00:00:00:00:00:00" style="flex: 1; font-family: monospace; font-size: 13px;">
                                    <button type="button" class="btn btn-secondary" onclick="randomizeMac()" style="padding: 0 15px; font-size: 12px;">Randomize</button>
                                </div>
                            </div>

                            <div class="form-group">
                                <label class="form-label">Parent Interface</label>
                                <select class="form-input" id="parentInterface" onchange="toggleManualInterface()">
                                    <option value="">Detecting interfaces...</option>
                                </select>
                                <div id="manual-interface-container" style="display: none; margin-top: 10px;">
                                    <input type="text" class="form-input" id="parentInterfaceManual" placeholder="Type interface name (e.g. ens34)">
                                    <small style="color: #a0aec0; font-size: 11px; margin-top: 4px; display: block;">
                                        Enter the exact name from 'ip link' command
                                    </small>
                                </div>
                                <small style="color: #718096; font-size: 11px; margin-top: 4px; display: block;">
                                    Select the physical network port to bridge with
                                </small>
                            </div>

                            <div class="form-group">
                                <label class="form-label">IP Configuration</label>
                                <select class="form-input" id="ipMode" onchange="toggleStaticFields()">
                                    <option value="dhcp">DHCP (Automatic)</option>
                                    <option value="static">Static IP</option>
                                </select>
                            </div>

                            <div id="static-ip-fields" style="display: none;">
                                <div class="form-group">
                                    <label class="form-label">Static IP Address</label>
                                    <input type="text" class="form-input" id="staticIp" placeholder="192.168.1.50">
                                </div>
                                <div class="form-row">
                                    <div class="form-col">
                                        <div class="form-group">
                                            <label class="form-label">Netmask (CIDR)</label>
                                            <input type="text" class="form-input" id="netmask" value="24" placeholder="24">
                                        </div>
                                    </div>
                                    <div class="form-col">
                                        <div class="form-group">
                                            <label class="form-label">Gateway</label>
                                            <input type="text" class="form-input" id="gateway" placeholder="192.168.1.1">
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <button type="submit" class="btn btn-success" style="width:100%">Save Camera</button>
            </form>
        </div>
    </div>
    
    <div id="settings-modal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <div class="modal-title">Server Settings</div>
                <button class="close-btn" onclick="closeSettingsModal()">×</button>
            </div>
            
            <div class="settings-tabs">
                <button type="button" class="settings-tab-btn active" onclick="switchSettingsTab('settings-general')" id="settings-tab-general">
                    <i class="fas fa-cog"></i> General
                </button>
                <button type="button" class="settings-tab-btn" onclick="switchSettingsTab('settings-security')" id="settings-tab-security">
                    <i class="fas fa-shield-alt"></i> Security
                </button>
                <button type="button" class="settings-tab-btn" onclick="switchSettingsTab('settings-engine')" id="settings-tab-engine">
                    <i class="fas fa-sliders-h"></i> Engine
                </button>
                <button type="button" class="settings-tab-btn" onclick="switchSettingsTab('settings-maintenance')" id="settings-tab-maintenance">
                    <i class="fas fa-wrench"></i> Maintenance
                </button>
            </div>

            <form onsubmit="saveSettings(event)">
                <!-- Tab 1: General Settings -->
                <div id="settings-general" class="settings-tab-content active">
                    <div class="form-group">
                        <label class="form-label">Server IP / Hostname (for RTSP URLs)</label>
                        <input type="text" class="form-input" id="serverIp" placeholder="192.168.1.10">
                        <small style="color: #718096; font-size: 12px; margin-top: 4px; display: block;">
                            Leave as 'localhost' for local access, or enter your server's IP address for network access
                        </small>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">RTSP Server Port</label>
                        <input type="number" class="form-input" id="rtspPortSettings" placeholder="8554">
                        <small style="color: #718096; font-size: 12px; margin-top: 4px; display: block;">
                            The main port for the RTSP broadcast (Default: 8554). Requires restart to take effect.
                        </small>
                    </div>

                    <div class="form-group">
                        <label class="form-label">UI Theme</label>
                        <select class="form-input" id="themeSelect">
                            <option value="classic">Classic (Purple Gradient)</option>
                            <option value="dark">Modern Dark (Blue Contrast)</option>
                            <option value="nord">Nordic Frost (Arctic Blue)</option>
                            <option value="dracula">Dracula (Pro Dark)</option>
                            <option value="solar-light">Solarized Light (Earthy Warmth)</option>
                            <option value="midnight">Midnight Ocean (Deep Blue)</option>
                            <option value="emerald">Emerald Forest (Nature Green)</option>
                            <option value="sunset">Sunset Glow (Vibrant Gradient)</option>
                            <option value="matrix">Matrix Code (Digital Rain)</option>
                            <option value="slate">Slate Professional (Neutral Grey)</option>
                            <option value="cyberpunk">Cyberpunk 2077 (Neon Yellow)</option>
                            <option value="amoled">Amoled Black (Pure OLED)</option>
                            <option value="ui">UI</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Dashboard Layout</label>
                        <select class="form-input" id="gridColumnsSelect">
                            <option value="2">2 Columns (Large Cards)</option>
                            <option value="3">3 Columns (Compact View)</option>
                            <option value="4">4 Columns (Extra Compact View)</option>
                            <option value="5">5 Columns (Super Compact View)</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                            <input type="checkbox" id="openBrowser" style="width: auto; cursor: pointer;">
                            <span class="form-label" style="margin: 0;">Open Browser on Startup</span>
                        </label>
                    </div>

                    <div class="form-group linux-only">
                        <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                            <input type="checkbox" id="autoBoot" style="width: auto; cursor: pointer;">
                            <span class="form-label" style="margin: 0;">Auto-start on System Boot (Ubuntu Service)</span>
                        </label>
                        <small style="color: #718096; font-size: 12px; margin-top: 4px; display: block;">
                            Creates and enables a systemd service to start this server automatically when the computer turns on.
                        </small>
                    </div>
                </div>

                <!-- Tab 2: Security Settings -->
                <div id="settings-security" class="settings-tab-content">
                    <div class="form-group" style="background: rgba(255, 121, 198, 0.05); padding: 15px; border-radius: 8px; border: 1px dashed var(--border-color);">
                        <div style="font-size: 14px; font-weight: 600; color: var(--text-title); margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                            <span>Global RTSP & ONVIF Credentials</span>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-col">
                                <div class="form-group" style="margin-bottom: 0;">
                                    <label class="form-label">Global Username</label>
                                    <input type="text" class="form-input" id="globalUsername" placeholder="admin" value="admin">
                                </div>
                            </div>
                            <div class="form-col">
                                <div class="form-group" style="margin-bottom: 0;">
                                    <label class="form-label">Global Password</label>
                                    <input type="text" class="form-input" id="globalPassword" placeholder="admin" value="admin">
                                </div>
                            </div>
                        </div>
                        
                        <div class="form-group" style="margin-top: 15px; margin-bottom: 0;">
                            <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                                <input type="checkbox" id="rtspAuthEnabled" style="width: auto; cursor: pointer;">
                                <span class="form-label" style="margin: 0; color: var(--text-body);">Enable RTSP Authentication</span>
                            </label>
                            <small style="color: var(--text-muted); font-size: 11px; margin-top: 4px; display: block; margin-left: 24px;">
                                If enabled, RTSP streams will require the Global Username/Password above. Disabling will allow anonymous RTSP access.
                            </small>
                        </div>
                    </div>

                    <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid var(--border-color);">
                        <div class="form-group">
                            <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                                <input type="checkbox" id="authEnabled" style="width: auto; cursor: pointer;" onchange="toggleAuthFields()">
                                <span class="form-label" style="margin: 0; color: #667eea; font-weight: 700;">Enable Web Interface Login</span>
                            </label>
                            <small style="color: #718096; font-size: 12px; margin-top: 4px; display: block;">
                                Require a username and password to access this dashboard.
                            </small>
                        </div>
                        
                        <div id="auth-settings-fields" style="display: none; padding: 15px; background: rgba(102, 126, 234, 0.05); border-radius: 8px; border: 1px dashed #667eea;">
                            <div class="form-group">
                                <label class="form-label">Admin Username</label>
                                <input type="text" class="form-input" id="authUsername" placeholder="admin">
                            </div>
                            <div class="form-group" style="margin-bottom: 0;">
                                <label class="form-label">New Password (leave blank to keep current)</label>
                                <input type="password" class="form-input" id="authPassword" placeholder="••••••••">
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Tab 3: Engine & Advanced -->
                <div id="settings-engine" class="settings-tab-content">
                    <div class="form-group">
                        <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                            <input type="checkbox" id="ffmpeg_hardwareEncoding" style="width: auto; cursor: pointer;">
                            <span class="form-label" style="margin: 0; color: #f6ad55; font-weight: 700;">Enable Hardware Encoding (Experimental)</span>
                        </label>
                        <small style="color: #718096; font-size: 11px; margin-top: 4px; display: block; margin-left: 24px;">
                            Attempts to use NVIDIA NVENC, Intel QSV, or AMD AMF for GridFusion encoding. Disables if not found.
                        </small>
                    </div>

                    <div class="form-group">
                        <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                            <input type="checkbox" id="debugMode" style="width: auto; cursor: pointer;">
                            <span class="form-label" style="margin: 0; color: #f6ad55; font-weight: 700;">Debug Mode (Show detailed logs)</span>
                        </label>
                        <small style="color: #718096; font-size: 11px; margin-top: 4px; display: block; margin-left: 24px;">
                            Enables verbose MediaMTX logging. Helpful for troubleshooting stream issues.
                        </small>
                    </div>

                    <div class="form-group">
                        <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                            <input type="checkbox" id="watchdogEnabled" style="width: auto; cursor: pointer;">
                            <span class="form-label" style="margin: 0; color: #f6ad55; font-weight: 700;">
                                <i class="fas fa-flask" style="font-size: 11px; margin-right: 3px;"></i>
                                Stream Watchdog (Experimental)
                            </span>
                        </label>
                        <small style="color: #718096; font-size: 11px; margin-top: 4px; display: block; margin-left: 24px;">
                            Monitors running streams and automatically restarts MediaMTX if a stream is dead or stale for &gt;2 minutes.
                            Disabled by default. May cause unexpected restarts — enable only if you experience persistent stream failures.
                        </small>
                    </div>

                    <div class="form-group" style="margin-top: 15px;">
                        <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;" onclick="toggleAdvancedSettings()">
                            <span class="form-label" style="margin: 0; color: var(--text-title); font-weight: 700; display: flex; align-items: center; gap: 5px;">
                                <i class="fas fa-tools"></i> Advanced Settings (MediaMTX & FFmpeg)
                                <i id="advancedChevron" class="fas fa-chevron-down" style="font-size: 12px; transition: transform 0.3s; margin-left: auto;"></i>
                            </span>
                        </label>
                    </div>

                    <div id="advancedSettingsSection" style="display: none; padding: 20px; background: var(--body-bg); border-radius: 10px; border: 1px solid var(--border-color); margin-bottom: 25px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                            <div>
                                <h3 style="font-size: 14px; margin: 0 0 12px 0; color: var(--text-title); border-bottom: 2px solid var(--btn-primary); padding-bottom: 6px; display: flex; align-items: center; gap: 8px;">
                                    <i class="fas fa-server" style="font-size: 12px; color: var(--btn-primary);"></i> MediaMTX Core
                                </h3>
                                <div class="form-group" style="margin-bottom: 12px;">
                                    <label class="form-label" style="font-size: 12px; margin-bottom: 4px; color: var(--text-title);">Write Queue Size</label>
                                    <input type="number" class="form-input" id="mediamtx_writeQueueSize" style="font-size: 13px; padding: 8px 10px; background: var(--input-bg); color: var(--input-text); border: 1px solid var(--input-border);">
                                </div>
                                <div class="form-group" style="margin-bottom: 12px;">
                                    <label class="form-label" style="font-size: 12px; margin-bottom: 4px; color: var(--text-title);">Read Timeout (duration)</label>
                                    <input type="text" class="form-input" id="mediamtx_readTimeout" style="font-size: 13px; padding: 8px 10px; background: var(--input-bg); color: var(--input-text); border: 1px solid var(--input-border);">
                                </div>
                                <div class="form-group" style="margin-bottom: 12px;">
                                    <label class="form-label" style="font-size: 12px; margin-bottom: 4px; color: var(--text-title);">Write Timeout (duration)</label>
                                    <input type="text" class="form-input" id="mediamtx_writeTimeout" style="font-size: 13px; padding: 8px 10px; background: var(--input-bg); color: var(--input-text); border: 1px solid var(--input-border);">
                                </div>
                                <div class="form-group" style="margin-bottom: 12px;">
                                    <label class="form-label" style="font-size: 12px; margin-bottom: 4px; color: var(--text-title);">UDP Max Payload</label>
                                    <input type="number" class="form-input" id="mediamtx_udpMaxPayloadSize" style="font-size: 13px; padding: 8px 10px; background: var(--input-bg); color: var(--input-text); border: 1px solid var(--input-border);">
                                </div>
                            </div>
                            <div>
                                <h3 style="font-size: 14px; margin: 0 0 12px 0; color: var(--text-title); border-bottom: 2px solid var(--btn-primary); padding-bottom: 6px; display: flex; align-items: center; gap: 8px;">
                                    <i class="fas fa-stream" style="font-size: 12px; color: var(--btn-primary);"></i> HLS Optimized
                                </h3>
                                <div class="form-group" style="margin-bottom: 12px;">
                                    <label class="form-label" style="font-size: 12px; margin-bottom: 4px; color: var(--text-title);">Segment Count</label>
                                    <input type="number" class="form-input" id="mediamtx_hlsSegmentCount" style="font-size: 13px; padding: 8px 10px; background: var(--input-bg); color: var(--input-text); border: 1px solid var(--input-border);">
                                </div>
                                <div class="form-group" style="margin-bottom: 12px;">
                                    <label class="form-label" style="font-size: 12px; margin-bottom: 4px; color: var(--text-title);">Segment Duration</label>
                                    <input type="text" class="form-input" id="mediamtx_hlsSegmentDuration" style="font-size: 13px; padding: 8px 10px; background: var(--input-bg); color: var(--input-text); border: 1px solid var(--input-border);">
                                </div>
                                <div class="form-group" style="margin-bottom: 12px;">
                                    <label class="form-label" style="font-size: 12px; margin-bottom: 4px; color: var(--text-title);">Part Duration</label>
                                    <input type="text" class="form-input" id="mediamtx_hlsPartDuration" style="font-size: 13px; padding: 8px 10px; background: var(--input-bg); color: var(--input-text); border: 1px solid var(--input-border);">
                                </div>
                            </div>
                        </div>

                        <h3 style="font-size: 14px; margin: 20px 0 12px 0; color: var(--text-title); border-bottom: 2px solid var(--btn-primary); padding-bottom: 6px; display: flex; align-items: center; gap: 8px;">
                            <i class="fas fa-video" style="font-size: 12px; color: var(--btn-primary);"></i> FFmpeg Transcoding Global
                        </h3>
                        <div class="form-group" style="margin-bottom: 12px;">
                            <label class="form-label" style="font-size: 12px; margin-bottom: 4px; color: var(--text-title);">Global Arguments (Flags)</label>
                            <input type="text" class="form-input" id="ffmpeg_globalArgs" style="font-size: 13px; padding: 10px; font-family: 'Consolas', monospace; background: var(--input-bg); color: var(--input-text); border: 1px solid var(--input-border);">
                        </div>
                        <div class="form-group" style="margin-bottom: 12px;">
                            <label class="form-label" style="font-size: 12px; margin-bottom: 4px; color: var(--text-title);">Input Arguments (Before -i)</label>
                            <input type="text" class="form-input" id="ffmpeg_inputArgs" style="font-size: 13px; padding: 10px; font-family: 'Consolas', monospace; background: var(--input-bg); color: var(--input-text); border: 1px solid var(--input-border);">
                        </div>
                        <div class="form-group" style="margin-bottom: 12px;">
                            <label class="form-label" style="font-size: 12px; margin-bottom: 4px; color: var(--text-title);">Process & Codec Arguments</label>
                            <input type="text" class="form-input" id="ffmpeg_processArgs" style="font-size: 13px; padding: 10px; font-family: 'Consolas', monospace; background: var(--input-bg); color: var(--input-text); border: 1px solid var(--input-border);">
                        </div>

                        <div style="background: var(--alert-warning-bg); border-left: 3px solid var(--alert-warning-text); padding: 10px; margin-top: 15px; border-radius: 4px;">
                            <small style="color: var(--alert-warning-text); font-size: 11px; font-weight: 600; display: block;">
                                <i class="fas fa-exclamation-triangle"></i> Note: MediaMTX will restart automatically to apply these changes. Incorrect FFmpeg arguments may cause camera streams to fail.
                            </small>
                        </div>
                        <div style="margin-top: 20px; display: flex; justify-content: flex-end;">
                            <button type="button" class="btn btn-primary" style="background: var(--card-bg); border: 1px solid var(--border-color); font-size: 11px; padding: 6px 14px; color: var(--text-title);" onclick="resetAdvancedSettings()">
                                <i class="fas fa-undo"></i> Reset to Defaults
                            </button>
                        </div>
                    </div>
                </div>
                
                <button id="settings-save-btn" type="submit" class="btn btn-success" style="width:100%">Save Settings</button>
            </form>

            <!-- Tab 4: Maintenance -->
            <div id="settings-maintenance" class="settings-tab-content">
                <!-- Maintenance & Extra Tools (OUTSIDE form to prevent submit confusion) -->
                <div style="margin-bottom: 20px;">
                    <div style="font-size: 14px; font-weight: 600; color: var(--text-title); margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                        <i class="fas fa-tools"></i> <span>Maintenance & Safety</span>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                        <button type="button" class="btn" style="background: rgba(246, 173, 85, 0.1); border: 1px solid rgba(246, 173, 85, 0.3); color: #f6ad55; font-size: 12px; padding: 10px;" onclick="resetAllUUIDs()">
                            <i class="fas fa-id-card"></i> Reset All UUIDs
                        </button>
                        <button type="button" class="btn" style="background: rgba(246, 173, 85, 0.1); border: 1px solid rgba(246, 173, 85, 0.3); color: #f6ad55; font-size: 12px; padding: 10px;" onclick="resetAllMACs()">
                            <i class="fas fa-network-wired"></i> Reset All MACs
                        </button>
                    </div>
                    <small style="color: #718096; font-size: 11px; margin-top: 8px; display: block;">
                        Warning: Resetting UUIDs or MAC addresses will force clients (like Ubiquiti or NVRs) to re-discover/re-add the cameras.
                    </small>
                </div>
                
                <div style="margin: 20px 0; padding-top: 15px; border-top: 1px solid var(--border-color);">
                    <div style="font-size: 14px; font-weight: 600; color: var(--text-title); margin-bottom: 10px;">Configuration Backup</div>
                    <div style="display: flex; gap: 10px;">
                        <button type="button" class="btn btn-secondary" onclick="downloadBackup()" style="flex: 1; background: var(--toggle-bg); border-color: var(--border-color); color: var(--text-body);">
                            <i class="fas fa-download"></i> Backup Config
                        </button>
                        <button type="button" id="restoreBtn" class="btn btn-secondary" onclick="restoreBackup()" style="flex: 1; background: var(--toggle-bg); border-color: var(--border-color); color: var(--text-body);">
                            <i class="fas fa-upload"></i> Restore Config
                        </button>
                    </div>
                </div>
                
                <div style="margin: 20px 0; padding-top: 15px; border-top: 1px solid var(--border-color);">
                    <div style="font-size: 14px; font-weight: 600; color: var(--text-title); margin-bottom: 10px;">System Updates</div>
                    <button type="button" class="btn btn-secondary" onclick="checkForUpdates()" style="width:100%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-color: #667eea; color: white; font-weight: 600;">
                        <i class="fas fa-sync-alt"></i> Check for Updates
                    </button>
                </div>
                
                <!-- Reboot Server Button (Linux Only) -->
                <button type="button" class="btn reboot-host" onclick="rebootServer()" style="width:100%; margin-top: 15px; background: linear-gradient(135deg, #e53e3e 0%, #c53030 100%); border-color: #c53030; color: white; font-weight: 600;">
                    <i class="fas fa-power-off"></i> Reboot Server
                </button>
            </div>
        </div>
    </div>
    
    <!-- About Modal -->
    <div id="about-modal" class="modal">
        <div class="modal-content" style="max-width: 850px;">
            <div class="modal-header">
                <div class="modal-title">About Tonys Onvif-RTSP Server</div>
                <button class="close-btn" onclick="closeAboutModal()">×</button>
            </div>
            <div style="line-height: 1.6; color: var(--text-body); font-size: 15px;">
                <p style="margin-bottom: 15px;">Hello, my name is <strong style="color: var(--text-title);">Tony</strong>. This program was developed to address two primary needs:</p>
                <div style="background: rgba(0,0,0,0.1); padding: 20px; border-radius: 8px; border-left: 4px solid var(--btn-primary); margin-bottom: 20px;">
                    <p style="margin-bottom: 15px;"><strong style="color: var(--text-title);">1. Ubiquiti Protect NVR Compatibility:</strong><br>
                    The Ubiquiti Protect NVR platform has limited compatibility with many generic ONVIF cameras. This tool bridges that gap by allowing incompatible RTSP streams to be imported and presented as fully compliant virtual ONVIF cameras, ensuring seamless integration and reliable operation within the Protect ecosystem.</p>

                    <p style="margin-bottom: 10px;">Additionally, Ubiquiti Protect requires a <strong>unique MAC address</strong> for each camera. This can be achieved in several ways:</p>
                    <ul style="margin-bottom: 20px; padding-left: 20px;">
                        <li>Running the application in a virtualized environment and assigning multiple virtual network interfaces</li>
                        <li>Physically installing additional network interface cards (NICs) on the host system</li>
                        <li>Using Linux macvlan networking. The program fully supports macvlan and has been tested on Ubuntu 25 for compatibility and stable operation.</li>
                    </ul>
                    
                    <p><strong style="color: var(--text-title);">2. Stream Rebroadcasting and Performance Optimization:</strong><br>
                    The application also enables reliable rebroadcasting of a single RTSP stream. Many physical cameras struggle to handle multiple concurrent connections, often resulting in lag or instability. This server functions as a high-performance proxy, efficiently managing multiple viewers while minimizing load on the original camera hardware.</p>
                </div>
                
                <!-- System Information -->
                <div style="background: rgba(102, 126, 234, 0.08); padding: 15px; border-radius: 8px; border: 1px solid rgba(102, 126, 234, 0.3); margin-bottom: 20px;">
                    <div style="font-size: 13px; font-weight: 600; color: var(--text-title); margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                        <i class="fas fa-info-circle" style="color: #667eea;"></i>
                        <span>System Information</span>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; font-size: 12px;">
                        <div style="background: rgba(0,0,0,0.2); padding: 10px; border-radius: 6px;">
                            <div style="color: var(--text-muted); margin-bottom: 4px;">MediaMTX Version</div>
                            <div id="about-mediamtx-version" style="color: var(--text-title); font-weight: 600; font-family: monospace;">Loading...</div>
                        </div>
                        <div style="background: rgba(0,0,0,0.2); padding: 10px; border-radius: 6px;">
                            <div style="color: var(--text-muted); margin-bottom: 4px;">FFmpeg Version</div>
                            <div id="about-ffmpeg-version" style="color: var(--text-title); font-weight: 600; font-family: monospace;">Loading...</div>
                        </div>
                        <div style="background: rgba(0,0,0,0.2); padding: 10px; border-radius: 6px;">
                            <div style="color: var(--text-muted); margin-bottom: 4px;">AI Acceleration</div>
                            <div id="about-ai-device" style="color: var(--text-title); font-weight: 600; font-family: monospace; font-size: 11px;">Loading...</div>
                        </div>
                    </div>
                </div>
                
                <div style="display: flex; flex-direction: column; align-items: center; gap: 15px;">
                    <div style="display: flex; gap: 15px;">
                        <a href="https://github.com/BigTonyTones/Tonys-Onvf-RTSP-Server" target="_blank" class="coffee-link" style="background: #24292e; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2); padding: 10px 20px; border-radius: 8px; text-decoration: none; display: inline-flex; align-items: center; gap: 10px;">
                            <i class="fab fa-github" style="font-size: 24px; color: white;"></i>
                            <span style="color: white; font-weight: 600;">View on GitHub</span>
                        </a>
                        <a href="https://buymeacoffee.com/tonytones" target="_blank" class="coffee-link">
                            <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee">
                        </a>
                    </div>
                    <p style="font-size: 13px; color: var(--text-muted); text-align: center; margin: 0;">Built with ❤️ for the surveillance community.</p>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Update Modal -->
    <div id="update-modal" class="modal">
        <div class="modal-content" style="max-width: 600px;">
            <div class="modal-header">
                <div class="modal-title" style="text-align: center; flex: 1;">Check for Updates</div>
                <button class="close-btn" onclick="closeUpdateModal()">×</button>
            </div>
            <div id="update-modal-content">
                <div id="docker-update-warning" style="display: none; background: rgba(237, 137, 54, 0.1); border-left: 3px solid #ed8936; padding: 15px; border-radius: 4px; margin-bottom: 20px; font-size: 13px; color: #ed8936; line-height: 1.4; text-align: left;">
                    <i class="fas fa-exclamation-triangle"></i> <strong>Running in Docker:</strong> Self-updating through the Web UI is disabled to prevent configuration and data loss. Please update your container using:
                    <code style="display: block; background: rgba(0,0,0,0.3); padding: 8px; border-radius: 4px; margin-top: 8px; color: #cbd5e0; word-break: break-all; font-family: monospace;">git pull && docker compose down && docker compose up -d --build</code>
                </div>
                <div id="update-info" style="display: none;">
                    <div style="background: rgba(102, 126, 234, 0.1); padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid rgba(102, 126, 234, 0.3);">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                            <div>
                                <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 4px;">Current Version</div>
                                <div id="current-version" style="font-size: 18px; font-weight: 700; color: var(--text-title);"></div>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 4px;">Latest Version</div>
                                <div id="latest-version" style="font-size: 18px; font-weight: 700; color: #48bb78;"></div>
                            </div>
                        </div>
                        <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 4px;">Release Date</div>
                        <div id="release-date" style="font-size: 14px; color: var(--text-body);"></div>
                    </div>
                    
                    <div style="margin-bottom: 20px;">
                        <div style="font-size: 14px; font-weight: 600; color: var(--text-title); margin-bottom: 10px;">Release Notes</div>
                        <div id="release-notes" style="background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px; max-height: 200px; overflow-y: auto; font-size: 13px; line-height: 1.6; color: var(--text-body); white-space: pre-wrap;"></div>
                    </div>
                    
                    <button id="download-update-btn" class="btn btn-success" onclick="downloadAndInstallUpdate()" style="width:100%; font-weight: 600;">
                        <i class="fas fa-download"></i> Download and Install
                    </button>
                    
                    <button class="btn btn-secondary reinstall-btn" onclick="reinstallCurrentVersion()" style="width:100%; margin-top: 10px; background: var(--toggle-bg); border-color: var(--border-color); color: var(--text-body);">
                        <i class="fas fa-redo"></i> Reinstall Current Version
                    </button>
                </div>
                
                <div id="update-progress" style="display: none;">
                    <div style="text-align: center; margin-bottom: 20px;">
                        <div id="progress-message" style="font-size: 16px; font-weight: 600; color: var(--text-title); margin-bottom: 15px;">Initializing update...</div>
                        <div style="background: rgba(0,0,0,0.3); border-radius: 10px; height: 20px; overflow: hidden; margin-bottom: 10px;">
                            <div id="progress-bar" style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); height: 100%; width: 0%; transition: width 0.3s ease;"></div>
                        </div>
                        <div id="progress-percent" style="font-size: 14px; color: var(--text-muted);">0%</div>
                    </div>
                    <div style="background: rgba(237, 137, 54, 0.1); border-left: 3px solid #ed8936; padding: 15px; border-radius: 4px;">
                        <small style="color: #f6ad55; font-size: 12px;">
                            <i class="fas fa-info-circle"></i> Please do not close this window. The server will restart automatically after the update is complete.
                        </small>
                    </div>
                </div>
                
                <div id="update-checking" style="text-align: center; padding: 40px 20px;">
                    <i class="fas fa-sync-alt fa-spin" style="font-size: 48px; color: var(--primary-color); margin-bottom: 20px;"></i>
                    <div style="font-size: 16px; color: var(--text-title);">Checking for updates...</div>
                </div>
                
                <div id="update-no-updates" style="display: none; text-align: center; padding: 40px 20px;">
                    <i class="fas fa-check-circle" style="font-size: 48px; color: #48bb78; margin-bottom: 20px;"></i>
                    <div style="font-size: 18px; font-weight: 600; color: var(--text-title); margin-bottom: 10px;">You're up to date!</div>
                    <div id="no-update-version" style="font-size: 14px; color: var(--text-muted); margin-bottom: 20px;"></div>
                    
                    <button class="btn btn-secondary reinstall-btn" onclick="reinstallCurrentVersion()" style="background: var(--toggle-bg); border-color: var(--border-color); color: var(--text-body);">
                        <i class="fas fa-redo"></i> Reinstall Current Version
                    </button>
                </div>
                
                <div id="update-error" style="display: none; text-align: center; padding: 40px 20px;">
                    <i class="fas fa-exclamation-triangle" style="font-size: 48px; color: #f56565; margin-bottom: 20px;"></i>
                    <div style="font-size: 18px; font-weight: 600; color: var(--text-title); margin-bottom: 10px;">Update Check Failed</div>
                    <div id="error-message" style="font-size: 14px; color: var(--text-muted);"></div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let cameras = [];
        let matrixActive = false;
        // Inject server-side settings
        let settings = {json.dumps(current_settings) if current_settings else '{{}}'};
        
        // Use localStorage to persist the "last known good" IP
        if (settings.serverIp && settings.serverIp !== 'localhost') {{
            localStorage.setItem('onvif_last_good_ip', settings.serverIp);
        }}

        // Platform detection for UI features
        const isLinux = {str(platform.system().lower() == "linux").lower()};
        const isDocker = {str(os.path.exists("/.dockerenv")).lower()};
        window.addEventListener('DOMContentLoaded', () => {{
            if (!isLinux) {{
                const linuxSections = document.querySelectorAll('.linux-only');
                linuxSections.forEach(s => s.style.display = 'none');
                
                // Legacy support for specific ID
                const linuxSection = document.getElementById('linux-network-section');
                if (linuxSection) linuxSection.style.display = 'none';
            }}
            // Hide host-reboot buttons when running inside Docker or on non-Linux
            if (isDocker || !isLinux) {{
                document.querySelectorAll('.reboot-host').forEach(s => s.style.display = 'none');
            }}
        }});

        let logInterval = null;

        let logFontSize = parseInt(localStorage.getItem('logFontSize')) || 16;

        function adjustLogFontSize(direction) {{
            logFontSize += direction;
            if (logFontSize < 10) logFontSize = 10;
            if (logFontSize > 32) logFontSize = 32;
            
            localStorage.setItem('logFontSize', logFontSize);
            applyLogFontSize();
        }}

        function applyLogFontSize() {{
            const container = document.getElementById('logs-container');
            const display = document.getElementById('logFontSizeDisplay');
            if (container) container.style.fontSize = logFontSize + 'px';
            if (display) display.textContent = logFontSize + 'px';
        }}

        function openLogsModal() {{
            document.getElementById('logs-modal').classList.add('active');
            applyLogFontSize();
            refreshLogs();
            // Auto-refresh logs every 3 seconds while open
            if (logInterval) clearInterval(logInterval);
            logInterval = setInterval(refreshLogs, 3000);
        }}

        function closeLogsModal() {{
            document.getElementById('logs-modal').classList.remove('active');
            if (logInterval) {{
                clearInterval(logInterval);
                logInterval = null;
            }}
        }}

        async function refreshLogs() {{
            try {{
                const response = await fetch('/api/logs');
                if (response.ok) {{
                    const data = await response.json();
                    const container = document.getElementById('logs-container');
                    
                    // Simple ANSI escape code stripping (common in terminal output)
                    const cleanLogs = data.logs.replace(/\\u001b\\[[0-9;]*[a-zA-Z]/g, '');
                    
                    function formatLogText(text) {{
                        if (!text) return "No logs available.";
                        let html = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                        
                        // Phrases
                        const cyanPhrases = ['Starting Web UI', 'SERVER RUNNING', 'Web Interface:', 'RTSP Server:', '\\\\\\* Serving Flask app'];
                        cyanPhrases.forEach(phrase => {{
                            html = html.replace(new RegExp('(' + phrase + ')', 'g'), '<span style="color: #8be9fd;">$1</span>');
                        }});
                        
                        // Words
                        html = html.replace(/\\b(successfully)\\b/gi, '<span style="color: #50fa7b;">$&</span>');
                        html = html.replace(/\\b(Shutdown|stopped|Warning)\\b/gi, '<span style="color: #f1fa8c;">$&</span>');
                        html = html.replace(/\\b(failed|Error|Exception|faile)\\b/gi, '<span style="color: #ff5555;">$&</span>');
                        
                        // rtsp tags
                        html = html.replace(/(\\[rtsp @ 0x[0-9a-f]+\\])/gi, '<span style="color: #ff79c6;">$1</span>');
                        
                        // General brackets
                        html = html.replace(/(\\[([^\\]]+)\\])/g, function(match) {{
                            if (match.includes('rtsp @')) return match;
                            if (match.includes('<span')) return match;
                            return '<span style="color: #8be9fd;">' + match + '</span>';
                        }});
                        
                        // IP addresses
                        html = html.replace(/\\b(\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3})\\b/g, '<span style="color: #ff79c6;">$1</span>');
                        
                        return html;
                    }}
                    
                    container.innerHTML = formatLogText(cleanLogs);
                    
                    if (document.getElementById('autoScrollLogs').checked) {{
                        container.scrollTop = container.scrollHeight;
                    }}
                }}
            }} catch (error) {{
                console.error('Error fetching logs:', error);
            }}
        }}

        function updateAiSensitivityDisplay(val) {{
            val = parseInt(val);
            document.getElementById('aiSensitivityValue').textContent = val + '%';
            
            const statusEl = document.getElementById('aiSensitivityStatus');
            if (!statusEl) return;
            
            if (val >= 75 && val <= 85) {{
                statusEl.textContent = 'Outdoor Rec';
                statusEl.style.color = '#f59e0b';
                statusEl.style.background = 'rgba(245, 158, 11, 0.15)';
                statusEl.style.border = '1px solid rgba(245, 158, 11, 0.3)';
            }} else if (val >= 40 && val <= 60) {{
                statusEl.textContent = 'Indoor Rec';
                statusEl.style.color = '#10b981';
                statusEl.style.background = 'rgba(16, 185, 129, 0.15)';
                statusEl.style.border = '1px solid rgba(16, 185, 129, 0.3)';
            }} else {{
                statusEl.textContent = 'Custom';
                statusEl.style.color = '#a0aec0';
                statusEl.style.background = 'rgba(160, 174, 192, 0.1)';
                statusEl.style.border = '1px solid rgba(160, 174, 192, 0.2)';
            }}
        }}
        
        function updateAiConfidenceDisplay(val) {{
            val = parseInt(val);
            document.getElementById('aiConfidenceValue').textContent = val + '%';
        }}
        
        async function loadData() {{
            try {{
                // 1. Fetch Settings (with cache busting)
                const settingsResp = await fetch('/api/settings?t=' + new Date().getTime());
                if (settingsResp.ok) {{
                    const newSettings = await settingsResp.json();
                    
                    if (newSettings && typeof newSettings === 'object') {{
                        // Sticky IP: Never let it drop back to localhost if we have a better one
                        const newIp = newSettings.serverIp;
                        const currentIp = settings.serverIp || localStorage.getItem('onvif_last_good_ip');
                        
                        if (newIp && newIp !== 'localhost') {{
                            localStorage.setItem('onvif_last_good_ip', newIp);
                        }} else if (currentIp && currentIp !== 'localhost' && (!newIp || newIp === 'localhost')) {{
                            console.log('Using persistent IP fallback:', currentIp);
                            newSettings.serverIp = currentIp;
                        }}
                        
                        settings = newSettings;
                        applyTheme(settings.theme);
                        applyGridLayout(settings.gridColumns || 3);
                    }}
                }}
                
                // 2. Fetch Cameras (with cache busting)
                const camerasResp = await fetch('/api/cameras?t=' + new Date().getTime());
                if (camerasResp.ok) {{
                    const newCameras = await camerasResp.json();
                    if (Array.isArray(newCameras)) {{
                        cameras = newCameras;
                    }}
                }}
                
                // 3. Render
                renderCameras();
                if (matrixActive) {{
                    renderMatrix();
                }}
                
                // Handle logout button visibility
                const logoutBtn = document.getElementById('logoutBtn');
                if (logoutBtn) {{
                    logoutBtn.style.display = settings.authEnabled ? 'flex' : 'none';
                }}
            }} catch (error) {{
                console.error('Error loading data:', error);
            }}
        }}
        
        function renderCameras() {{
            const list = document.getElementById('camera-list');
            const empty = document.getElementById('empty-state');
            
            if (cameras.length === 0) {{
                list.style.display = 'none';
                empty.style.display = 'block';
                list.innerHTML = '';
                return;
            }}
            
            list.style.display = 'grid';
            empty.style.display = 'none';
            
            // Determine Server IP with robust fallback hierarchy:
            // 1. Explicit setting from config (if it's not localhost)
            // 2. Persistent IP from localStorage
            // 3. Current browser hostname (if it's not localhost/127.0.0.1)
            // 4. Default to settings.serverIp or 'localhost'
            
            let finalIp = 'localhost';
            const configIp = settings.serverIp;
            const storedIp = localStorage.getItem('onvif_last_good_ip');
            const browserIp = window.location.hostname;
            
            if (configIp && configIp !== 'localhost' && configIp !== '127.0.0.1') {{
                finalIp = configIp;
            }} else if (storedIp && storedIp !== 'localhost') {{
                finalIp = storedIp;
            }} else if (browserIp && browserIp !== 'localhost' && browserIp !== '127.0.0.1') {{
                finalIp = browserIp;
            }} else {{
                finalIp = configIp || 'localhost';
            }}
            
            // Diagnostics in console
            console.log(`Resolution: Config=${{configIp}}, Stored=${{storedIp}}, Browser=${{browserIp}} -> FINAL=${{finalIp}}`);

            // Server IP resolution for backwards compatibility with rest of function
            const serverIp = finalIp; 
            
            // Track existing IDs
            const currentIds = new Set(cameras.map(c => c.id.toString()));
            
            // Remove deleted cameras
            Array.from(list.children).forEach(card => {{
                if (!currentIds.has(card.dataset.id)) {{
                    card.remove();
                }}
            }});
            
            cameras.forEach(cam => {{
                let card = list.querySelector(`.camera-card[data-id="${{cam.id}}"]`);
                const content = getCameraCardContent(cam, serverIp);
                
                if (!card) {{
                    card = document.createElement('div');
                    card.className = `camera-card ${{cam.status === 'running' ? 'running' : ''}}`;
                    card.dataset.id = cam.id;
                    card.dataset.status = cam.status;
                    card.innerHTML = content;
                    list.appendChild(card);
                    
                    if (cam.status === 'running') {{
                        initVideoPlayer(cam.id, cam.pathName);
                    }}
                }} else {{
                    // Existing camera - check for status change
                    if (card.dataset.status !== cam.status) {{
                        // Status changed, full re-render
                        card.className = `camera-card ${{cam.status === 'running' ? 'running' : ''}}`;
                        card.dataset.status = cam.status;
                        card.innerHTML = content;
                        
                        if (cam.status === 'running') {{
                            initVideoPlayer(cam.id, cam.pathName);
                        }}
                    }} else {{
                        // Status same, only update text parts if needed (preserves video)
                        const nameEl = card.querySelector('.camera-name');
                        if (nameEl && nameEl.textContent !== cam.name) nameEl.textContent = cam.name;
                        
                        const autoStartEl = card.querySelector('.toggle-switch input');
                        if (autoStartEl && autoStartEl.checked !== cam.autoStart) autoStartEl.checked = cam.autoStart;

                        // Check if AI detection count increased to trigger flash
                        const oldAiBadge = card.querySelector('.ai-badge');
                        const oldCount = oldAiBadge ? parseInt(oldAiBadge.dataset.count || '0') : 0;
                        const newCount = cam.aiDetectionCount || 0;

                        // Always update info section to ensure IP is correct
                        // This is safe because it doesn't affect the video player (video-preview div)
                        const existingWarning = card.querySelector(`#codec-warning-${{cam.id}}`);
                        const warningHtml = existingWarning ? existingWarning.innerHTML : '';
                        
                        const newInfoContent = getCameraCardContent(cam, serverIp);
                        const tempDiv = document.createElement('div');
                        tempDiv.innerHTML = newInfoContent;
                        
                        // Update camera header (to refresh status badges)
                        const headerEl = card.querySelector('.camera-header');
                        if (headerEl) {{
                            headerEl.innerHTML = tempDiv.querySelector('.camera-header').innerHTML;
                        }}
                        
                        // Update info section
                        card.querySelector('.info-section').innerHTML = tempDiv.querySelector('.info-section').innerHTML;
                        
                        // Restore warning
                        if (warningHtml) {{
                            const newWarning = card.querySelector(`#codec-warning-${{cam.id}}`);
                            if (newWarning) newWarning.innerHTML = warningHtml;
                        }}

                        // If count increased, trigger flash on the new badge
                        if (newCount > oldCount && oldCount > 0) {{
                            const newAiBadge = card.querySelector('.ai-badge');
                            if (newAiBadge) {{
                                newAiBadge.classList.add('ai-badge-flash');
                                setTimeout(() => {{
                                    newAiBadge.classList.remove('ai-badge-flash');
                                }}, 1500);
                            }}
                        }}
                    }}
                }}
            }});
        }}

        function destroyPlayer(videoId) {{
            // Cleanup HLS
            if (hlsPlayers.has(videoId)) {{
                const hls = hlsPlayers.get(videoId);
                hls.destroy();
                hlsPlayers.delete(videoId);
            }}
            
            // Cleanup WebRTC
            if (webrtcConnections.has(videoId)) {{
                const pc = webrtcConnections.get(videoId);
                pc.close();
                webrtcConnections.delete(videoId);
            }}
            
            // Cleanup Retry Counters
            if (recoveryAttempts.has(videoId)) {{
                recoveryAttempts.delete(videoId);
            }}
        }}

        let focusedCameraId = null;
        let matrixStreamProfiles = {{}}; // cameraId -> 'sub' | 'main'
        let matrixMutedStates = {{}}; // cameraId -> boolean
        let carouselIntervalId = null;
        let carouselPage = 0;
        let cachedAnalytics = {{}};

        function toggleMatrixView(active) {{
            matrixActive = active;
            const overlay = document.getElementById('matrix-overlay');
            if (active) {{
                overlay.classList.add('active');
                
                // Update URL to support bookmarking/direct link
                const url = new URL(window.location.href);
                url.searchParams.set('view', 'matrix');
                window.history.replaceState({{}}, '', url.toString());
                
                // Initialize checkboxes from global settings
                document.getElementById('matrixStretchToggle').checked = settings.matrixStretchFill === true;
                document.getElementById('matrixHideNamesToggle').checked = settings.matrixHideNames === true;
                document.getElementById('matrixAiFlashToggle').checked = settings.matrixAiFlash === true;
                document.getElementById('matrixAudioHoverToggle').checked = settings.matrixAudioHover === true;
                document.getElementById('matrixCarouselToggle').checked = settings.matrixCarousel === true;
                document.getElementById('matrixForceHighStreamToggle').checked = settings.matrixForceHighStream === true;
                document.getElementById('matrixCamsPerPageSelect').value = settings.matrixCamsPerPage || 'All';
                document.getElementById('carouselIntervalSelect').value = settings.carouselInterval || '10000';
                
                // Apply classes
                overlay.classList.toggle('stretch-fill', settings.matrixStretchFill === true);
                overlay.classList.toggle('hide-names', settings.matrixHideNames === true);
                overlay.classList.toggle('ai-flash-active', settings.matrixAiFlash === true);
                
                // Initialize carousel mode
                if (settings.matrixCarousel === true && settings.matrixCamsPerPage !== 'All') {{
                    startCarousel();
                }} else {{
                    stopCarousel();
                }}
                
                renderMatrix();
            }} else {{
                overlay.classList.remove('active');
                
                // Remove view=matrix from URL
                const url = new URL(window.location.href);
                url.searchParams.delete('view');
                window.history.replaceState({{}}, '', url.toString());
                
                stopCarousel();
                focusedCameraId = null;
                // Stop any video players in matrix
                const grid = document.getElementById('matrix-grid');
                if (grid) {{
                    const players = grid.querySelectorAll('video');
                    players.forEach(el => destroyPlayer(el.id));
                    grid.innerHTML = '';
                }}
            }}
        }}

        async function updateMatrixSettings() {{
            const stretchFill = document.getElementById('matrixStretchToggle').checked;
            const hideNames = document.getElementById('matrixHideNamesToggle').checked;
            const aiFlash = document.getElementById('matrixAiFlashToggle').checked;
            const audioHover = document.getElementById('matrixAudioHoverToggle').checked;
            const forceHighStream = document.getElementById('matrixForceHighStreamToggle').checked;
            const camsPerPage = document.getElementById('matrixCamsPerPageSelect').value;
            const carousel = document.getElementById('matrixCarouselToggle').checked;
            
            const overlay = document.getElementById('matrix-overlay');
            overlay.classList.toggle('stretch-fill', stretchFill);
            overlay.classList.toggle('hide-names', hideNames);
            overlay.classList.toggle('ai-flash-active', aiFlash);
            
            // If global override is changed, we need to re-initialize video streams that changed profile
            const recreateStreams = settings.matrixForceHighStream !== forceHighStream;
            
            // Update global settings
            settings.matrixStretchFill = stretchFill;
            settings.matrixHideNames = hideNames;
            settings.matrixAiFlash = aiFlash;
            settings.matrixAudioHover = audioHover;
            settings.matrixForceHighStream = forceHighStream;
            settings.matrixCamsPerPage = camsPerPage;
            settings.matrixCarousel = carousel;
            
            try {{
                await fetch('/api/settings', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify(settings)
                }});
            }} catch (e) {{
                console.error('Failed to save matrix settings:', e);
            }}
            
            if (recreateStreams) {{
                // Stop all video players and force full re-render to load main streams
                const grid = document.getElementById('matrix-grid');
                if (grid) {{
                    grid.querySelectorAll('video').forEach(el => destroyPlayer(el.id));
                    grid.innerHTML = ''; // Force complete DOM rebuild on next render
                }}
            }}
            
            renderMatrix();
        }}

        // Carousel & Pagination Controller Functions
        function startCarousel() {{
            stopCarousel();
            const camsPerPageVal = document.getElementById('matrixCamsPerPageSelect').value;
            if (camsPerPageVal === 'All') return;
            const interval = parseInt(document.getElementById('carouselIntervalSelect').value) || 10000;
            
            carouselIntervalId = setInterval(() => {{
                const runningCameras = cameras.filter(c => c.status === 'running');
                if (runningCameras.length === 0) return;
                const pageSize = parseInt(camsPerPageVal) || 4;
                const pageCount = Math.ceil(runningCameras.length / pageSize);
                if (pageCount <= 1) return;
                
                // Force destroy existing player resources before transition to avoid leaking contexts
                const grid = document.getElementById('matrix-grid');
                if (grid) {{
                    grid.querySelectorAll('video').forEach(el => destroyPlayer(el.id));
                    grid.innerHTML = '';
                }}
                
                carouselPage = (carouselPage + 1) % pageCount;
                renderMatrix();
            }}, interval);
        }}

        function stopCarousel() {{
            if (carouselIntervalId) {{
                clearInterval(carouselIntervalId);
                carouselIntervalId = null;
            }}
            carouselPage = 0;
        }}

        function toggleCarouselMode() {{
            const isEnabled = document.getElementById('matrixCarouselToggle').checked;
            settings.matrixCarousel = isEnabled;
            if (isEnabled) {{
                startCarousel();
            }} else {{
                stopCarousel();
            }}
            updateMatrixSettings();
        }}

        function updateCarouselSettings() {{
            const interval = parseInt(document.getElementById('carouselIntervalSelect').value) || 10000;
            settings.carouselInterval = interval;
            
            if (document.getElementById('matrixCarouselToggle').checked) {{
                startCarousel();
            }}
            updateMatrixSettings();
        }}

        function updateCamsPerPage() {{
            const camsPerPage = document.getElementById('matrixCamsPerPageSelect').value;
            settings.matrixCamsPerPage = camsPerPage;
            
            // If camsPerPage is 'All', disable carousel
            if (camsPerPage === 'All') {{
                settings.matrixCarousel = false;
                document.getElementById('matrixCarouselToggle').checked = false;
                stopCarousel();
            }}
            
            // Reset page counters
            carouselPage = 0;
            
            // Stop all video players and force full re-render to load correct cameras
            const grid = document.getElementById('matrix-grid');
            if (grid) {{
                grid.querySelectorAll('video').forEach(el => destroyPlayer(el.id));
                grid.innerHTML = '';
            }}
            
            if (settings.matrixCarousel === true) {{
                startCarousel();
            }} else {{
                stopCarousel();
            }}
            
            updateMatrixSettings();
        }}

        function changeMatrixPage(direction) {{
            const runningCameras = cameras.filter(c => c.status === 'running');
            if (runningCameras.length === 0) return;
            
            const camsPerPageVal = document.getElementById('matrixCamsPerPageSelect').value;
            if (camsPerPageVal === 'All') return;
            
            const pageSize = parseInt(camsPerPageVal) || 4;
            const pageCount = Math.ceil(runningCameras.length / pageSize);
            if (pageCount <= 1) return;
            
            // Change page with wrap-around
            carouselPage = (carouselPage + direction + pageCount) % pageCount;
            
            // Force destroy existing player resources before transition
            const grid = document.getElementById('matrix-grid');
            if (grid) {{
                grid.querySelectorAll('video').forEach(el => destroyPlayer(el.id));
                grid.innerHTML = '';
            }}
            
            // Reset carousel timer if it's currently running
            if (carouselIntervalId) {{
                startCarousel();
            }}
            
            renderMatrix();
        }}

        // Drag and Drop Sorting for Matrix View
        let draggedCameraId = null;

        function handleDragStart(e, cameraId) {{
            draggedCameraId = cameraId;
            e.dataTransfer.effectAllowed = 'move';
            
            const item = document.querySelector(`.matrix-item[data-id="${{cameraId}}"]`);
            if (item) {{
                item.classList.add('dragging');
            }}
        }}

        function handleDragOver(e) {{
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
        }}

        async function handleDrop(e, targetCameraId) {{
            e.preventDefault();
            if (draggedCameraId === null || draggedCameraId === targetCameraId) return;
            
            // Find indices in global cameras array
            const draggedIdx = cameras.findIndex(c => c.id === draggedCameraId);
            const targetIdx = cameras.findIndex(c => c.id === targetCameraId);
            
            if (draggedIdx !== -1 && targetIdx !== -1) {{
                // Swap/Move item in cameras array
                const [movedCam] = cameras.splice(draggedIdx, 1);
                cameras.splice(targetIdx, 0, movedCam);
                
                // Get all camera IDs in order
                const orderedIds = cameras.map(c => c.id);
                
                // Save sorting order to backend
                try {{
                    await fetch('/api/cameras/reorder', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ ordered_ids: orderedIds }})
                    }});
                }} catch (err) {{
                    console.error('Failed to save sorted camera order:', err);
                }}
                
                // Force full rebuild of grid players
                const grid = document.getElementById('matrix-grid');
                if (grid) {{
                    grid.querySelectorAll('video').forEach(el => destroyPlayer(el.id));
                    grid.innerHTML = '';
                }}
                
                renderMatrix();
                
                // Re-render main page camera list to match new order
                renderCameras();
            }}
        }}

        function handleDragEnd(e) {{
            draggedCameraId = null;
            const items = document.querySelectorAll('.matrix-item');
            items.forEach(item => item.classList.remove('dragging'));
        }}

        async function resetMatrixOrder() {{
            if (!confirm('Are you sure you want to reset the camera order to default?')) return;
            try {{
                const resp = await fetch('/api/cameras/reorder/reset', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }}
                }});
                if (resp.ok) {{
                    cameras.sort((a, b) => a.id - b.id);
                    
                    const grid = document.getElementById('matrix-grid');
                    if (grid) {{
                        grid.querySelectorAll('video').forEach(el => destroyPlayer(el.id));
                        grid.innerHTML = '';
                    }}
                    
                    renderMatrix();
                    renderCameras();
                }}
            }} catch (err) {{
                console.error('Failed to reset camera order:', err);
            }}
        }}

        // Double-click grid focus toggle
        function toggleCameraFocus(cameraId) {{
            const grid = document.getElementById('matrix-grid');
            const items = grid.querySelectorAll('.matrix-item');
            const clickedItem = grid.querySelector(`.matrix-item[data-id="${{cameraId}}"]`);
            
            if (focusedCameraId === cameraId) {{
                // Release focus
                focusedCameraId = null;
                grid.classList.remove('focused-active');
                if (clickedItem) clickedItem.classList.remove('focused');
            }} else {{
                // Focus this camera
                focusedCameraId = cameraId;
                items.forEach(el => el.classList.remove('focused'));
                grid.classList.add('focused-active');
                if (clickedItem) clickedItem.classList.add('focused');
            }}
        }}

        // Stream profile (HD/SD) switcher
        function toggleMatrixStreamProfile(cameraId, pathName) {{
            const current = matrixStreamProfiles[cameraId] || 'sub';
            const next = current === 'sub' ? 'main' : 'sub';
            matrixStreamProfiles[cameraId] = next;
            
            // Re-create the player with the new profile suffix
            const videoId = `matrix-player-${{cameraId}}`;
            destroyPlayer(videoId);
            
            // Re-initialize player
            initVideoPlayer(cameraId, pathName, videoId);
            
            // Update button label / style
            const btn = document.querySelector(`.matrix-item[data-id="${{cameraId}}"] .stream-profile-btn`);
            if (btn) {{
                btn.textContent = next === 'main' ? 'HD' : 'SD';
                btn.classList.toggle('active', next === 'main');
            }}
        }}

        // Audio controls
        function toggleMatrixAudio(cameraId) {{
            const video = document.getElementById(`matrix-player-${{cameraId}}`);
            if (!video) return;
            
            const isMuted = !video.muted;
            video.muted = isMuted;
            matrixMutedStates[cameraId] = isMuted;
            
            // Update button UI
            const btn = document.querySelector(`.matrix-item[data-id="${{cameraId}}"] .audio-btn`);
            if (btn) {{
                btn.innerHTML = isMuted ? '<i class="fas fa-volume-mute"></i>' : '<i class="fas fa-volume-up"></i>';
                btn.classList.toggle('active', !isMuted);
            }}
        }}

        function handleMatrixItemHover(cameraId, isHover) {{
            const audioHoverEnabled = document.getElementById('matrixAudioHoverToggle').checked;
            if (!audioHoverEnabled) return;
            
            const video = document.getElementById(`matrix-player-${{cameraId}}`);
            if (!video) return;
            
            if (isHover) {{
                // Unmute on hover
                video.muted = false;
            }} else {{
                // Mute when mouse leaves
                // Only if user hasn't explicitly set unmuted via button
                if (matrixMutedStates[cameraId] !== false) {{
                    video.muted = true;
                }}
            }}
            
            // Update button UI state
            const btn = document.querySelector(`.matrix-item[data-id="${{cameraId}}"] .audio-btn`);
            if (btn) {{
                btn.innerHTML = video.muted ? '<i class="fas fa-volume-mute"></i>' : '<i class="fas fa-volume-up"></i>';
                btn.classList.toggle('active', !video.muted);
            }}
        }}

        function renderMatrix() {{
            const grid = document.getElementById('matrix-grid');
            let runningCameras = cameras.filter(c => c.status === 'running');
            
            if (runningCameras.length === 0) {{
                grid.innerHTML = '<div style="color: white; grid-column: 1/-1; text-align: center; padding-top: 100px;">No cameras are currently running.</div>';
                return;
            }}
            
            // Pagination/Carousel calculations
            const camsPerPageVal = document.getElementById('matrixCamsPerPageSelect').value;
            const hasCamsPerPage = camsPerPageVal !== 'All';
            const navControls = document.getElementById('matrixNavControls');
            const carouselGroup = document.getElementById('matrixCarouselGroup');
            
            if (hasCamsPerPage) {{
                const pageSize = parseInt(camsPerPageVal) || 4;
                const pageCount = Math.ceil(runningCameras.length / pageSize);
                if (carouselPage >= pageCount) carouselPage = 0;
                if (carouselPage < 0) carouselPage = pageCount - 1;
                
                // Show or hide Prev/Next controls and Page Indicator
                if (pageCount > 1) {{
                    if (navControls) navControls.style.display = 'flex';
                    const indicator = document.getElementById('matrixPageIndicator');
                    if (indicator) indicator.textContent = `Page ${{carouselPage + 1}} of ${{pageCount}}`;
                }} else {{
                    if (navControls) navControls.style.display = 'none';
                }}
                
                // Enable carousel options since we have pages
                if (carouselGroup) carouselGroup.style.display = 'flex';
                
                runningCameras = runningCameras.slice(carouselPage * pageSize, (carouselPage + 1) * pageSize);
            }} else {{
                if (navControls) navControls.style.display = 'none';
                if (carouselGroup) carouselGroup.style.display = 'none';
            }}
            
            const count = runningCameras.length;
            let cols = 1;
            if (focusedCameraId) cols = 1;
            else if (count > 9) cols = 4;
            else if (count > 4) cols = 3;
            else if (count > 1) cols = 2;
            
            grid.style.gridTemplateColumns = `repeat(${{cols}}, 1fr)`;
            
            // Toggle focus-active class
            grid.classList.toggle('focused-active', focusedCameraId !== null);
            
            // Check if we need to re-render
            const currentMatrixIds = Array.from(grid.querySelectorAll('.matrix-item')).map(el => el.dataset.id).join(',');
            const newMatrixIds = runningCameras.map(c => c.id).join(',');
            
            if (currentMatrixIds !== newMatrixIds) {{
                // Cleanup existing players before re-rendering
                grid.querySelectorAll('video').forEach(el => destroyPlayer(el.id));
                
                grid.innerHTML = runningCameras.map(cam => {{
                    const isFocused = focusedCameraId === cam.id;
                    const hasAiAlert = settings.matrixAiFlash && cam.aiLastDetection && cam.aiLastDetection.length > 0;
                    
                    if (cam.disableSubstream) {{
                        return `
                            <div class="matrix-item ${{isFocused ? 'focused' : ''}} ${{hasAiAlert ? 'ai-alert' : ''}}" data-id="${{cam.id}}" draggable="true" ondragstart="handleDragStart(event, ${{cam.id}})" ondragover="handleDragOver(event)" ondrop="handleDrop(event, ${{cam.id}})" ondragend="handleDragEnd(event)" ondblclick="toggleCameraFocus(${{cam.id}})" style="display: flex; align-items: center; justify-content: center; background: #1a202c; border: 1px solid var(--border-color); flex-direction: column;">
                                <div class="matrix-label">${{cam.name}}</div>
                                <div style="font-size: 24px; color: #a0aec0; margin-bottom: 5px;"><i class="fas fa-video-slash"></i></div>
                                <div style="color: #a0aec0; font-size: 12px; font-weight: 500;">Substream Disabled</div>
                            </div>
                        `;
                    }}
                    
                    const isForceHigh = settings.matrixForceHighStream === true;
                    const profile = isForceHigh ? 'main' : (matrixStreamProfiles[cam.id] || 'sub');
                    const isMuted = matrixMutedStates[cam.id] !== false; // Muted by default
                    const hdBtnText = isForceHigh ? 'HD (Forced)' : (profile === 'main' ? 'HD' : 'SD');
                    const hdDisabledAttr = isForceHigh ? 'disabled style="opacity: 0.6; cursor: not-allowed;" title="HD forced globally"' : '';
                    
                    return `
                        <div class="matrix-item ${{isFocused ? 'focused' : ''}} ${{hasAiAlert ? 'ai-alert' : ''}}" data-id="${{cam.id}}" draggable="true" ondragstart="handleDragStart(event, ${{cam.id}})" ondragover="handleDragOver(event)" ondrop="handleDrop(event, ${{cam.id}})" ondragend="handleDragEnd(event)" ondblclick="toggleCameraFocus(${{cam.id}})" onmouseenter="handleMatrixItemHover(${{cam.id}}, true)" onmouseleave="handleMatrixItemHover(${{cam.id}}, false)">
                            <div class="matrix-label">${{cam.name}}</div>
                            <video id="matrix-player-${{cam.id}}" autoplay ${{isMuted ? 'muted' : ''}} playsinline></video>
                            
                            <!-- Hover Tools Overlay -->
                            <div class="matrix-item-overlay">
                                <span class="matrix-item-badge codec-badge" id="matrix-codec-${{cam.id}}">-</span>
                                <span class="matrix-item-badge bitrate-badge" id="matrix-bitrate-${{cam.id}}">-</span>
                                <button class="matrix-item-btn stream-profile-btn ${{profile === 'main' ? 'active' : ''}}" ${{hdDisabledAttr}} onclick="event.stopPropagation(); toggleMatrixStreamProfile(${{cam.id}}, '${{cam.pathName}}')">${{hdBtnText}}</button>
                                <button class="matrix-item-btn audio-btn ${{!isMuted ? 'active' : ''}}" onclick="event.stopPropagation(); toggleMatrixAudio(${{cam.id}})">
                                    ${{isMuted ? '<i class="fas fa-volume-mute"></i>' : '<i class="fas fa-volume-up"></i>'}}
                                </button>
                            </div>
                        </div>
                    `;
                }}).join('');
                
                runningCameras.forEach(cam => {{
                    if (!cam.disableSubstream) {{
                        initVideoPlayer(cam.id, cam.pathName, `matrix-player-${{cam.id}}`);
                    }}
                }});
            }} else {{
                // Update dynamic properties: focus class, alert status, metrics
                runningCameras.forEach(cam => {{
                    const el = grid.querySelector(`.matrix-item[data-id="${{cam.id}}"]`);
                    if (el) {{
                        el.classList.toggle('focused', focusedCameraId === cam.id);
                        
                        const hasAiAlert = settings.matrixAiFlash && cam.aiLastDetection && cam.aiLastDetection.length > 0;
                        el.classList.toggle('ai-alert', hasAiAlert);
                        
                        // Update metrics overlay
                        const pName = cam.pathName || cam.path_name;
                        const profile = (settings.matrixForceHighStream === true) ? 'main' : (matrixStreamProfiles[cam.id] || 'sub');
                        const stats = cachedAnalytics[pName + '_' + profile];
                        
                        const codecEl = el.querySelector('.codec-badge');
                        const bitrateEl = el.querySelector('.bitrate-badge');
                        
                        if (stats) {{
                            if (bitrateEl) bitrateEl.textContent = stats.bitrate ? stats.bitrate.toFixed(0) + ' kbps' : '0 kbps';
                            if (codecEl && stats.tracks && stats.tracks.length > 0) {{
                                // Find video track codec name
                                let codec = 'H264';
                                stats.tracks.forEach(track => {{
                                    const t = (typeof track === 'string' ? track : JSON.stringify(track)).toLowerCase();
                                    if (t.includes('h265') || t.includes('hevc')) codec = 'H265';
                                }});
                                codecEl.textContent = codec;
                            }}
                        }}
                    }}
                }});
            }}
        }}

        function toggleFullScreen() {{
            const elem = document.getElementById('matrix-overlay');
            if (!document.fullscreenElement) {{
                elem.requestFullscreen().catch(err => {{
                    alert(`Error: ${{err.message}}`);
                }});
            }} else {{
                document.exitFullscreen();
            }}
        }}

        function toggleFullScreenPlayer(cameraId) {{
            const video = document.getElementById(`player-${{cameraId}}`);
            if (!video) return;
            
            if (video.requestFullscreen) {{
                video.requestFullscreen();
            }} else if (video.webkitRequestFullscreen) {{
                video.webkitRequestFullscreen();
            }} else if (video.webkitEnterFullscreen) {{
                video.webkitEnterFullscreen();
            }} else if (video.msRequestFullscreen) {{
                video.msRequestFullscreen();
            }}
        }}

        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape' && matrixActive) {{
                toggleMatrixView(false);
            }}
            if (e.key === 'Escape' && onvifViewActive) {{
                toggleONVIFView(false);
            }}
        }});

        function getCameraCardContent(cam, serverIp) {{
            const displayIp = cam.assignedIp || serverIp;
            return `
                <div class="camera-header" style="display: flex; flex-direction: column; align-items: stretch; gap: 10px; margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                        <div class="camera-title" style="display: flex; align-items: center; gap: 12px;">
                            <div class="status-badge ${{cam.status === 'running' ? 'running' : ''}}"></div>
                            <div class="camera-name">${{cam.name}}</div>
                        </div>
                        <div class="camera-actions">
                            ${{cam.status === 'running' 
                                ? `<button class="icon-btn icon-btn-stop" onclick="stopCamera(${{cam.id}})" title="Stop"><i class="fas fa-stop"></i> Stop</button>`
                                : `<button class="icon-btn icon-btn-start" onclick="startCamera(${{cam.id}})" title="Start"><i class="fas fa-play"></i> Start</button>`
                            }}
                            <button class="icon-btn icon-btn-edit" onclick="openEditModal(${{cam.id}})" title="Edit"><i class="fas fa-edit"></i> Edit</button>
                            <button class="icon-btn icon-btn-delete" onclick="deleteCamera(${{cam.id}})" title="Delete"><i class="fas fa-trash"></i> Delete</button>
                        </div>
                    </div>
                    
                    <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 6px; padding-left: 24px;">
                        <div class="status-badge ${{cam.assignedIp ? 'running' : ''}}" style="width: auto; height: auto; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; ${{!cam.assignedIp ? 'background: #4a5568; color: white;' : ''}}" title="${{cam.assignedIp ? 'Virtual IP Address: Assigned to this camera\\\'s Virtual NIC interface.' : 'Server IP Address: Camera stream is served from the main server IP.'}}">IP: ${{displayIp}}</div>
                        <div class="status-badge" style="width: auto; height: auto; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; background: #4a5568; color: white;" title="${{cam.nicMac ? 'Virtual MAC: Custom MAC address assigned to this camera\\\'s Virtual NIC. Full MAC: ' + (cam.nicMac || cam.macAddress || '').toUpperCase() : 'MAC Address: Stable generated MAC address representing this virtual camera. Full MAC: ' + (cam.nicMac || cam.macAddress || '').toUpperCase()}}">MAC: ${{ (cam.nicMac || cam.macAddress || '').toUpperCase() }}</div>
                        ${{cam.uuid ? `<div class="status-badge" style="width: auto; height: auto; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; background: #805ad5; color: white;" title="UUID: ${{cam.uuid}}">UUID: ${{cam.uuid.split('-')[0]}}</div>` : ''}}
                        ${{(() => {{
                            let onvifText = 'ONVIF: Offline';
                            let onvifBg = '#4a5568';
                            let onvifTooltip = 'Camera is offline/stopped.';
                            if (cam.status === 'running') {{
                                const subs = cam.onvifActiveSubscriptions || 0;
                                const ips = cam.onvifSubscribersIPs || [];
                                if (subs > 0) {{
                                    onvifText = 'ONVIF: (' + subs + ')';
                                    onvifBg = '#48bb78';
                                    const ipListStr = ips.length > 0 ? ' (IPs: ' + ips.join(', ') + ')' : '';
                                    onvifTooltip = 'ONVIF Events Subscription is Active: ' + subs + ' NVR/Client(s)' + ipListStr + ' are actively subscribed to receive ONVIF events.';
                                }} else {{
                                    onvifText = 'ONVIF: No Subs';
                                    onvifBg = '#e53e3e';
                                    onvifTooltip = 'ONVIF Events: No NVR/Client is currently subscribed to events from this virtual camera. If the camera is not receiving ONVIF events in Protect, try removing the camera from Protect and adding it again.';
                                }}
                            }}
                            return '<div class="status-badge" style="width: auto; height: auto; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; background: ' + onvifBg + '; color: white; display: flex; align-items: center; gap: 4px; white-space: nowrap;" title="' + onvifTooltip.replace(/"/g, '&quot;') + '">' + onvifText + '</div>';
                        }})()}}
                        ${{cam.enableAudio ? `<div class="status-badge" style="width: auto; height: auto; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; background: #4299e1; color: white; display: flex; align-items: center; gap: 4px; white-space: nowrap;" title="Audio: RTSP audio stream forwarding is enabled for main/sub streams (AAC format).">Audio</div>` : ''}}
                        ${{(cam.transcodeMainAudio || cam.transcodeSubAudio) ? `<div class="status-badge" style="width: auto; height: auto; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; background: #3182ce; color: white; display: flex; align-items: center; gap: 4px; white-space: nowrap;" title="Audio Transcoded: Audio stream is actively transcoded to AAC format for compatibility (e.g. with UniFi Protect).">Audio Transcoded</div>` : ''}}
                        ${{cam.eventSource === 'ai' && cam.enableEventForwarding ? `<div class="status-badge ai-badge" data-count="${{cam.aiDetectionCount || 0}}" style="width: auto; height: auto; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; background: #ecc94b; color: #744210; display: flex; align-items: center; gap: 4px; white-space: nowrap; cursor: pointer; transition: transform 0.2s;" onclick="event.stopPropagation(); toggleONVIFView(true, ${{cam.id}}, 'ai');" title="AI: Local AI object detection is active on this stream, analyzing for targets: ${{cam.aiTargets ? cam.aiTargets.join(', ') : 'person, vehicle'}} using model ${{cam.aiModel}}. Click to view AI events.">AI: ${{cam.aiDetectionCount || 0}}</div>` : ''}}
                    </div>
                </div>
                
                <div class="video-preview" id="video-${{cam.id}}">
                    <div id="metrics-${{cam.id}}" class="metrics-overlay"></div>
                    ${{cam.status === 'running' 
                        ? (cam.disableSubstream 
                            ? `<div class="video-placeholder" style="background: #1a202c; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                                <div style="font-size: 48px; color: #a0aec0; margin-bottom: 10px;"><i class="fas fa-video-slash"></i></div>
                                <div style="color: #e2e8f0; font-weight: 500;">Substream Disabled</div>
                                <div style="font-size: 12px; color: #a0aec0; margin-top: 4px;">Enable substream in settings to preview video here</div>
                               </div>`
                            : `<video id="player-${{cam.id}}" autoplay muted playsinline></video>
                               <button class="fullscreen-btn" onclick="toggleFullScreenPlayer(${{cam.id}})" title="Maximize">Full Screen</button>`)
                        : `<div class="video-placeholder">
                            <div style="font-size: 48px;"></div>
                            <div>Camera Stopped</div>
                           </div>`
                    }}

                </div>
                
                <div class="info-section">
                    <div id="codec-warning-${{cam.id}}"></div>
                    <div class="info-label">
                        RTSP Main Stream (Full Quality)
                        ${{cam.transcodeMain ? '<span style="display: inline-block; margin-left: 8px; padding: 2px 8px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; border-radius: 12px; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Transcoded</span>' : ''}}
                    </div>
                    <div class="info-value">
                        rtsp://${{settings.rtspAuthEnabled ? encodeURIComponent(settings.globalUsername || 'admin') + ':' + encodeURIComponent(settings.globalPassword || 'admin') + '@' : ''}}${{displayIp}}:${{settings.rtspPort || 8554}}/${{cam.pathName}}_main
                        <button class="copy-btn" onclick="copyToClipboard('rtsp://${{settings.rtspAuthEnabled ? encodeURIComponent(settings.globalUsername || 'admin') + ':' + encodeURIComponent(settings.globalPassword || 'admin') + '@' : ''}}${{displayIp}}:${{settings.rtspPort || 8554}}/${{cam.pathName}}_main', this)">Copy</button>
                    </div>
                    
                    <div class="info-label">
                        RTSP Sub Stream (Lower Quality)
                        ${{cam.transcodeSub ? '<span style="display: inline-block; margin-left: 8px; padding: 2px 8px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; border-radius: 12px; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Transcoded</span>' : ''}}
                    </div>
                    <div class="info-value">
                        rtsp://${{settings.rtspAuthEnabled ? encodeURIComponent(settings.globalUsername || 'admin') + ':' + encodeURIComponent(settings.globalPassword || 'admin') + '@' : ''}}${{displayIp}}:${{settings.rtspPort || 8554}}/${{cam.pathName}}_sub
                        <button class="copy-btn" onclick="copyToClipboard('rtsp://${{settings.rtspAuthEnabled ? encodeURIComponent(settings.globalUsername || 'admin') + ':' + encodeURIComponent(settings.globalPassword || 'admin') + '@' : ''}}${{displayIp}}:${{settings.rtspPort || 8554}}/${{cam.pathName}}_sub', this)">Copy</button>
                    </div>
                    
                    <div class="info-label">ONVIF Service URL</div>
                    <div class="info-value">
                        <div style="display: flex; align-items: center; justify-content: space-between; width: 100%;">
                            <span>${{displayIp}}:${{cam.onvifPort}}</span>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <div style="font-size: 11px; color: var(--text-muted); background: var(--bg-secondary); padding: 2px 6px; border-radius: 4px; border: 1px solid var(--border-color);">
                                    ${{settings.globalUsername || 'admin'}} / ${{settings.globalPassword || 'admin'}}
                                </div>
                                <button class="copy-btn" onclick="copyToClipboard('${{displayIp}}:${{cam.onvifPort}}', this)">Copy</button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="auto-start-row">
                    <span class="auto-start-label">Auto-start on server startup</span>
                    <label class="toggle-switch">
                        <input type="checkbox" ${{cam.autoStart ? 'checked' : ''}} onchange="toggleAutoStart(${{cam.id}}, this.checked)">
                        <span class="toggle-slider"></span>
                    </label>
                </div>
            `;
        }}
        
        async function copyToClipboard(text, btn) {{
            // Attempt to resolve button if not passed explicitly (for backward compatibility)
            if (!btn && window.event) btn = window.event.target;
            
            try {{
                await navigator.clipboard.writeText(text);
                
                if (btn) {{
                    const originalText = btn.textContent;
                    const originalBg = btn.style.backgroundColor; // Store inline style if any
                    
                    btn.textContent = 'Copied!';
                    btn.style.backgroundColor = '#48bb78'; // Green success color
                    btn.style.color = '#ffffff';
                    
                    // Revert after 2 seconds
                    setTimeout(() => {{ 
                        btn.textContent = originalText;
                        btn.style.backgroundColor = originalBg; 
                        btn.style.color = ''; // Remove inline color to revert to CSS
                    }}, 2000);
                }}
            }} catch (err) {{
                console.error('Failed to copy: ', err);
                // Fallback for older browsers or insecure contexts
                const textArea = document.createElement("textarea");
                textArea.value = text;
                textArea.style.position = "fixed";  // Avoid scrolling to bottom
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                try {{
                    document.execCommand('copy');
                    if (btn) {{
                        const originalText = btn.textContent;
                        btn.textContent = 'Copied!';
                        btn.style.backgroundColor = '#48bb78';
                        setTimeout(() => {{ 
                            btn.textContent = originalText;
                            btn.style.backgroundColor = '';
                        }}, 2000);
                    }}
                }} catch (e) {{
                    console.error('Fallback copy failed', e);
                    alert('Could not copy text. Please select and copy manually.');
                }}
                document.body.removeChild(textArea);
            }}
        }}
        
        // Global HLS/WebRTC player management
        const hlsPlayers = new Map();
        const webrtcConnections = new Map();
        let recoveryAttempts = new Map();

        const storedLatency = localStorage.getItem('useWebRTC');
        let useLowLatency = storedLatency === null ? true : storedLatency === 'true';

        const storedBandwidth = localStorage.getItem('showBandwidth');
        let showBandwidth = storedBandwidth === 'true'; // Default is false

        window.addEventListener('DOMContentLoaded', () => {{
            const toggle = document.getElementById('latencyToggle');
            if (toggle) toggle.checked = useLowLatency;

            const bwToggle = document.getElementById('bandwidthToggle');
            if (bwToggle) bwToggle.checked = showBandwidth;
            
            if (showBandwidth) document.body.classList.add('show-bandwidth');
        }});

        function toggleLatencyMode(enabled) {{
            useLowLatency = enabled;
            localStorage.setItem('useWebRTC', enabled);
            window.location.reload();
        }}

        function toggleBandwidth(enabled) {{
            showBandwidth = enabled;
            localStorage.setItem('showBandwidth', enabled);
            if (enabled) {{
                document.body.classList.add('show-bandwidth');
            }} else {{
                document.body.classList.remove('show-bandwidth');
            }}
        }}

        async function initWebRTCPlayer(videoId, cameraId, pathName, serverIp, videoElement) {{
            console.log(`Initializing WebRTC for ${{videoId}}`);
            try {{
                const pc = new RTCPeerConnection({{
                    iceServers: [{{ urls: 'stun:stun.l.google.com:19302' }}]
                }});
                
                webrtcConnections.set(videoId, pc);
                
                pc.addTransceiver('video', {{ direction: 'recvonly' }});
                pc.addTransceiver('audio', {{ direction: 'recvonly' }});
                
                pc.ontrack = (event) => {{
                    if (videoElement.srcObject !== event.streams[0]) {{
                        videoElement.srcObject = event.streams[0];
                    }}
                }};
                
                const offer = await pc.createOffer();
                await pc.setLocalDescription(offer);
                
                let suffix = '_sub';
                if (videoId.startsWith('matrix-player-')) {{
                    const profile = (settings.matrixForceHighStream === true) ? 'main' : (matrixStreamProfiles[cameraId] || 'sub');
                    suffix = profile === 'main' ? '_main' : '_sub';
                }}
                const whepUrl = `http://${{serverIp}}:8889/${{pathName}}${{suffix}}/whep`;
                
                const response = await fetch(whepUrl, {{
                    method: 'POST',
                    body: offer.sdp,
                    headers: {{ 'Content-Type': 'application/sdp' }}
                }});
                
                if (!response.ok) throw new Error(`WHEP server responded with ${{response.status}}`);
                
                const answerSdp = await response.text();
                await pc.setRemoteDescription(new RTCSessionDescription({{
                    type: 'answer',
                    sdp: answerSdp
                }}));
                
                pc.onconnectionstatechange = () => {{
                    if (pc.connectionState === 'failed' || pc.connectionState === 'disconnected') {{
                        console.log(`WebRTC Disconnected for ${{videoId}}`);
                        showVideoError(cameraId, 'WebRTC Disconnected');
                        // Remove from tracking so it can be re-initialized
                        if (webrtcConnections.get(videoId) === pc) {{
                            webrtcConnections.delete(videoId);
                        }}
                    }}
                }};

            }} catch (err) {{
                console.error(`WebRTC Error [${{videoId}}]:`, err);
                showVideoError(cameraId, 'Low Latency failed. Try disabling Low Latency.');
                if (webrtcConnections.has(videoId)) {{
                    webrtcConnections.get(videoId).close();
                    webrtcConnections.delete(videoId);
                }}
            }}
        }}
        
        function initVideoPlayer(cameraId, pathName, explicitId = null) {{
            const videoId = explicitId || `player-${{cameraId}}`;
            
            // If a player for this videoId already exists, do not re-initialize it.
            if (hlsPlayers.has(videoId) || webrtcConnections.has(videoId)) {{
                return;
            }}

            const videoElement = document.getElementById(videoId);
            if (!videoElement) return;
            
            let serverIp = settings.serverIp || window.location.hostname || 'localhost';
            
            // Smart IP Override: If server settings are local but browser is remote, use browser IP
            if (serverIp === 'localhost' && window.location.hostname && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {{
                serverIp = window.location.hostname;
            }}
            
            if (useLowLatency) {{
                initWebRTCPlayer(videoId, cameraId, pathName, serverIp, videoElement);
                return;
            }}

            // Get credentials if RTSP auth is enabled
            let credentials = '';
            if (settings.rtspAuthEnabled && settings.globalUsername && settings.globalPassword) {{
                // Ensure credentials are URL encoded
                const u = encodeURIComponent(settings.globalUsername);
                const p = encodeURIComponent(settings.globalPassword);
                credentials = `?user=${{u}}&pass=${{p}}`;
            }}
            
            let suffix = '_sub';
            if (videoId.startsWith('matrix-player-')) {{
                const profile = (settings.matrixForceHighStream === true) ? 'main' : (matrixStreamProfiles[cameraId] || 'sub');
                suffix = profile === 'main' ? '_main' : '_sub';
            }}
            
            // Construct stream URL - Use current protocol if possible to support reverse proxies
            const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
            const streamUrl = `http://${{serverIp}}:8888/${{pathName}}${{suffix}}/index.m3u8${{credentials}}`;
            
            if (typeof Hls !== 'undefined' && Hls.isSupported()) {{
                // Prefer HLS.js if available and supported (Chrome, Firefox, Edge, Android, etc.)
                const hlsConfig = {{
                    debug: false,
                    enableWorker: true,
                    lowLatencyMode: true,
                    backBufferLength: 30,
                    liveSyncDurationCount: 3,
                    liveMaxLatencyDurationCount: 5,
                    maxLiveSyncPlaybackRate: 1.25
                }};

                // Hook to inject credentials into every segment request
                if (settings.rtspAuthEnabled && settings.globalUsername && settings.globalPassword) {{
                    hlsConfig.xhrSetup = function(xhr, url) {{
                        let accessUrl = url;
                        if (url.indexOf('user=') === -1) {{
                            const separator = url.indexOf('?') === -1 ? '?' : '&';
                            accessUrl = url + separator + `user=${{encodeURIComponent(settings.globalUsername)}}&pass=${{encodeURIComponent(settings.globalPassword)}}`;
                        }}
                        xhr.open('GET', accessUrl, true);
                    }};
                }}

                const hls = new Hls(hlsConfig);
                
                // Store player reference
                hlsPlayers.set(videoId, hls);
                recoveryAttempts.set(videoId, 0);
                
                hls.loadSource(streamUrl);
                hls.attachMedia(videoElement);

                // Play video as soon as manifest is parsed
                hls.on(Hls.Events.MANIFEST_PARSED, function() {{
                    videoElement.play().catch(e => console.warn("HLS autoplay failed:", e));
                }});
                
                // Enhanced error handling with exponential backoff
                hls.on(Hls.Events.ERROR, function(event, data) {{
                    console.log(`HLS Error [${{videoId}}]:`, data.type, data.details, data.fatal);
                    
                    if (data.fatal) {{
                        const attempts = recoveryAttempts.get(videoId) || 0;
                        const maxAttempts = 5;
                        
                        switch(data.type) {{
                            case Hls.ErrorTypes.NETWORK_ERROR:
                                console.log(`Network error on ${{videoId}}, attempt ${{attempts + 1}}/${{maxAttempts}}`);
                                if (attempts < maxAttempts) {{
                                    recoveryAttempts.set(videoId, attempts + 1);
                                    // Exponential backoff: 1s, 2s, 4s, 8s, 16s
                                    const delay = Math.min(1000 * Math.pow(2, attempts), 16000);
                                    setTimeout(() => {{
                                        console.log(`Retrying network connection for ${{videoId}}...`);
                                        hls.loadSource(streamUrl);
                                        hls.startLoad();
                                    }}, delay);
                                }} else {{
                                    console.error(`Max recovery attempts reached for ${{videoId}}`);
                                    showVideoError(cameraId, 'Network connection failed');
                                    hls.destroy();
                                    hlsPlayers.delete(videoId);
                                }}
                                break;
                                
                            case Hls.ErrorTypes.MEDIA_ERROR:
                                console.log(`Media error on ${{videoId}}, attempting recovery...`);
                                if (attempts < maxAttempts) {{
                                    recoveryAttempts.set(videoId, attempts + 1);
                                    hls.recoverMediaError();
                                }} else {{
                                    console.error(`Max media recovery attempts reached for ${{videoId}}`);
                                    showVideoError(cameraId, 'Media playback error');
                                    hls.destroy();
                                    hlsPlayers.delete(videoId);
                                }}
                                break;
                                
                            default:
                                console.error(`Unrecoverable error on ${{videoId}}:`, data.details);
                                showVideoError(cameraId, 'Playback error: ' + data.details);
                                hls.destroy();
                                hlsPlayers.delete(videoId);
                                break;
                        }}
                    }}
                }});
                
                // Reset recovery counter on successful manifest load
                hls.on(Hls.Events.MANIFEST_LOADED, function() {{
                    recoveryAttempts.set(videoId, 0);
                    console.log(`Stream loaded successfully for ${{videoId}}`);
                }});
                
                // Monitor buffer health
                hls.on(Hls.Events.BUFFER_APPENDING, function() {{
                    // Buffer is healthy, reset recovery attempts
                    recoveryAttempts.set(videoId, 0);
                }});

            }} else if (videoElement.canPlayType('application/vnd.apple.mpegurl')) {{
                // Fallback: Native HLS support (Safari / iOS)
                videoElement.src = streamUrl;
                videoElement.play().catch(e => console.warn("Native HLS autoplay failed:", e));
            }} else {{
                if (typeof Hls === 'undefined') {{
                    showVideoError(cameraId, 'Failed to load HLS player library (offline mode?)');
                }} else {{
                    showVideoError(cameraId, 'HLS not supported in this browser');
                }}
            }}
        }}
        
        function showVideoError(cameraId, message = 'Unable to load video') {{
            const container = document.getElementById(`video-${{cameraId}}`);
            if (container) {{
                container.innerHTML = `
                    <div class="video-placeholder">
                        <div style="font-size: 48px;"></div>
                        <div>${{message}}</div>
                        <div style="font-size: 12px; color: #a0aec0;">Check camera connection</div>
                    </div>
                `;
            }}
        }}
        
        
        function copyCameraSettings(id) {{
            if (!id) return;
            
            const camera = cameras.find(c => c.id === parseInt(id));
            if (!camera) return;
            
            // Parse the RTSP URL to extract credentials and paths
            try {{
                const mainUrl = new URL(camera.mainStreamUrl.replace('rtsp://', 'http://'));
                const subUrl = new URL(camera.subStreamUrl.replace('rtsp://', 'http://'));
                
                // Don't copy the name, let user choose a new one
                // document.getElementById('name').value = camera.name + ' (Copy)';
                
                document.getElementById('host').value = mainUrl.hostname;
                document.getElementById('rtspPort').value = mainUrl.port || '554';
                document.getElementById('username').value = decodeURIComponent(mainUrl.username || '');
                document.getElementById('password').value = decodeURIComponent(mainUrl.password || '');
                document.getElementById('mainPath').value = mainUrl.pathname + mainUrl.search;
                document.getElementById('subPath').value = subUrl.pathname + subUrl.search;
                document.getElementById('autoStart').checked = camera.autoStart || false;
                document.getElementById('enableEventForwarding').checked = camera.enableEventForwarding || false;
                document.getElementById('physicalOnvifPort').value = camera.physicalOnvifPort || '80';
                const hasFwdCreds = !!(camera.onvifForwardingUsername);
                document.getElementById('onvifUseAboveCredentials').checked = !hasFwdCreds;
                document.getElementById('onvifForwardingUsername').value = camera.onvifForwardingUsername || '';
                document.getElementById('onvifForwardingPassword').value = camera.onvifForwardingPassword || '';
                
                const eventSource = camera.eventSource || 'onvif';
                document.getElementById('eventSource').value = eventSource;
                document.getElementById('aiModel').value = camera.aiModel || 'yolov8n.pt';
                const aiTargets = camera.aiTargets || ['person', 'vehicle'];
                document.getElementById('aiTargetPerson').checked = aiTargets.includes('person');
                document.getElementById('aiTargetVehicle').checked = aiTargets.includes('vehicle');
                document.getElementById('aiTargetAnimal').checked = aiTargets.includes('animal');
                document.getElementById('aiTargetPackage').checked = aiTargets.includes('package');
                document.getElementById('sendSmartOnvifTopics').checked = camera.sendSmartOnvifTopics !== false;
                
                const copySens = camera.aiMotionSensitivity || 50;
                document.getElementById('aiMotionSensitivity').value = copySens;
                updateAiSensitivityDisplay(copySens);
                
                toggleOnvifCredFields();
                toggleEventForwardingFields();
                document.getElementById('enableAudio').checked = camera.enableAudio || false;
                document.getElementById('transcodeMainAudio').checked = camera.transcodeMainAudio || false;
                document.getElementById('transcodeSubAudio').checked = camera.transcodeSubAudio || false;
                
                // Copy audio transcoding settings
                document.getElementById('audioEncodingMain').value = camera.audioEncodingMain || 'aac';
                document.getElementById('audioSampleRateMain').value = camera.audioSampleRateMain || '44100';
                document.getElementById('audioBitrateMain').value = camera.audioBitrateMain || '128k';
                document.getElementById('audioEncodingSub').value = camera.audioEncodingSub || 'aac';
                document.getElementById('audioSampleRateSub').value = camera.audioSampleRateSub || '44100';
                document.getElementById('audioBitrateSub').value = camera.audioBitrateSub || '64k';
                
                toggleAudioSettings('main');
                toggleAudioSettings('sub');
                toggleTranscodeNotice('main');
                toggleTranscodeNotice('sub');
                
                // Populate resolution and frame rate fields
                document.getElementById('mainWidth').value = camera.mainWidth || 1920;
                document.getElementById('mainHeight').value = camera.mainHeight || 1080;
                document.getElementById('subWidth').value = camera.subWidth || 640;
                document.getElementById('subHeight').value = camera.subHeight || 480;
                document.getElementById('mainFramerate').value = camera.mainFramerate || 30;
                document.getElementById('subFramerate').value = camera.subFramerate || 15;

                
                // Don't copy ONVIF port or UUID (they need to be unique)
                document.getElementById('onvifPort').value = ''; 
                document.getElementById('cameraUuid').value = ''; 
                
                alert('Settings copied from ' + camera.name);
            }} catch (e) {{
                console.error('Error copying settings:', e);
                alert('Error copying settings: ' + e.message);
            }}
        }}

        async function detectNetworkInterfaces() {{
            if (!isLinux) return;
            const select = document.getElementById('parentInterface');
            if (!select) return;
            
            const currentValue = select.value;
            const container = document.getElementById('manual-interface-container');
            const manualInput = document.getElementById('parentInterfaceManual');
            
            try {{
                const response = await fetch('/api/network/interfaces');
                const interfaces = await response.json();
                
                select.innerHTML = '<option value="">-- Select Interface --</option>';
                if (interfaces && interfaces.length > 0) {{
                    interfaces.forEach(iface => {{
                        const option = document.createElement('option');
                        option.value = iface;
                        option.textContent = iface;
                        select.appendChild(option);
                    }});
                }}
                
                // Always add manual option
                const manualOption = document.createElement('option');
                manualOption.value = "__manual__";
                manualOption.textContent = "Manual Entry...";
                select.appendChild(manualOption);
                
                // Restore value logic
                if (currentValue && currentValue !== "__manual__") {{
                    if (interfaces.includes(currentValue)) {{
                        select.value = currentValue;
                        container.style.display = 'none';
                    }} else {{
                        select.value = "__manual__";
                        manualInput.value = currentValue;
                        container.style.display = 'block';
                    }}
                }}
            }} catch (error) {{
                console.error('Error detecting interfaces:', error);
                // Fallback if API fails
                select.innerHTML = '<option value="">-- Error detecting --</option><option value="__manual__">Manual Entry...</option>';
            }}
        }}

        function toggleManualInterface() {{
            const select = document.getElementById('parentInterface');
            const container = document.getElementById('manual-interface-container');
            if (select.value === "__manual__") {{
                container.style.display = 'block';
            }} else {{
                container.style.display = 'none';
            }}
        }}

        function randomizeMac() {{
            const hex = '0123456789ABCDEF';
            let mac = '02:'; // Locally administered unicast
            for (let i = 0; i < 5; i++) {{
                mac += hex.charAt(Math.floor(Math.random() * 16));
                mac += hex.charAt(Math.floor(Math.random() * 16));
                if (i < 4) mac += ':';
            }}
            document.getElementById('nicMac').value = mac;
        }}

        function generateNewUuid() {{
            try {{
                if (crypto && crypto.randomUUID) {{
                    document.getElementById('cameraUuid').value = crypto.randomUUID();
                }} else {{
                    // Fallback for non-secure contexts (http) or older browsers
                    document.getElementById('cameraUuid').value = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {{
                        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
                        return v.toString(16);
                    }});
                }}
            }} catch (e) {{
                console.error("UUID generation failed", e);
            }}
        }}

        function toggleNetworkFields() {{
            const useVnic = document.getElementById('useVirtualNic').checked;
            const fields = document.getElementById('vnic-fields');
            if (fields) fields.style.display = useVnic ? 'block' : 'none';
            if (useVnic && !document.getElementById('nicMac').value) {{
                randomizeMac();
            }}
            toggleStaticFields();
        }}

        function toggleStaticFields() {{
            const ipMode = document.getElementById('ipMode').value;
            const useVnicElement = document.getElementById('useVirtualNic');
            const useVnic = useVnicElement ? useVnicElement.checked : false;
            const fields = document.getElementById('static-ip-fields');
            if (fields) fields.style.display = (useVnic && ipMode === 'static') ? 'block' : 'none';
        }}

        async function openAddModal() {{
            switchFormTab('camera');
            document.getElementById('modal-title').textContent = 'Add New Camera';
            document.getElementById('camera-id').value = '';
            document.getElementById('camera-form').reset();
            
            document.getElementById('enableEventForwarding').checked = false;
            document.getElementById('physicalOnvifPort').value = '80';
            document.getElementById('onvifUseAboveCredentials').checked = true;
            document.getElementById('onvifForwardingUsername').value = '';
            document.getElementById('onvifForwardingPassword').value = '';
            
            document.getElementById('eventSource').value = 'onvif';
            document.getElementById('aiModel').value = 'yolov8n.pt';
            document.getElementById('aiTargetPerson').checked = true;
            document.getElementById('aiTargetVehicle').checked = true;
            document.getElementById('aiTargetAnimal').checked = false;
            document.getElementById('aiTargetPackage').checked = false;
            document.getElementById('sendSmartOnvifTopics').checked = true;
            document.getElementById('aiMotionSensitivity').value = 50;
            updateAiSensitivityDisplay(50);
            document.getElementById('aiConfidenceThreshold').value = 50;
            updateAiConfidenceDisplay(50);
            currentZonePoints = [];
            zoneSnapshotLoaded = false;
            
            toggleOnvifCredFields();
            toggleEventForwardingFields();
            toggleSmartOnvifWarning();
            
            document.getElementById('transcodeSub').checked = false;
            document.getElementById('transcodeMain').checked = false;
            document.getElementById('enableAudio').checked = false;
            document.getElementById('transcodeMainAudio').checked = false;
            document.getElementById('transcodeSubAudio').checked = false;
            
            // Audio settings reset
            document.getElementById('audioEncodingMain').value = 'aac';
            document.getElementById('audioSampleRateMain').value = '44100';
            document.getElementById('audioBitrateMain').value = '128k';
            document.getElementById('audioEncodingSub').value = 'aac';
            document.getElementById('audioSampleRateSub').value = '44100';
            document.getElementById('audioBitrateSub').value = '64k';
            toggleAudioSettings('main');
            toggleAudioSettings('sub');
            toggleTranscodeNotice('main');
            toggleTranscodeNotice('sub');
            
            // Network reset
            document.getElementById('useVirtualNic').checked = false;
            document.getElementById('vnicKeepalive').checked = false;
            document.getElementById('parentInterface').value = '';
            document.getElementById('nicMac').value = '';
            document.getElementById('ipMode').value = 'dhcp';
            document.getElementById('staticIp').value = '';
            generateNewUuid();

            
            document.getElementById('netmask').value = '24';
            document.getElementById('gateway').value = '';
            
            if (isLinux) {{
                await detectNetworkInterfaces();
                document.getElementById('parentInterfaceManual').value = '';
                document.getElementById('manual-interface-container').style.display = 'none';
            }}
            
            toggleNetworkFields();
            
            // Show copy dropdown
            document.getElementById('copy-from-group').style.display = 'block';
            
            // Populate copy dropdown
            const copySelect = document.getElementById('copyFrom');
            copySelect.innerHTML = '<option value="">Select a camera to copy...</option>';
            
            cameras.forEach(cam => {{
                const option = document.createElement('option');
                option.value = cam.id;
                option.textContent = cam.name;
                copySelect.appendChild(option);
            }});
            
            toggleSubStreamFields();
            document.getElementById('camera-modal').classList.add('active');
        }}
        
        async function openEditModal(id) {{
            switchFormTab('camera');
            document.getElementById('copy-from-group').style.display = 'none';
            const camera = cameras.find(c => c.id === id);
            if (!camera) return;
            
            document.getElementById('modal-title').textContent = 'Edit Camera';
            document.getElementById('camera-id').value = camera.id;
            
            // Parse the RTSP URL to extract credentials and paths
            const mainUrl = new URL(camera.mainStreamUrl.replace('rtsp://', 'http://'));
            const subUrl = new URL(camera.subStreamUrl.replace('rtsp://', 'http://'));
            
            document.getElementById('name').value = camera.name;
            document.getElementById('host').value = mainUrl.hostname;
            document.getElementById('rtspPort').value = mainUrl.port || '554';
            document.getElementById('username').value = decodeURIComponent(mainUrl.username || '');
            document.getElementById('password').value = decodeURIComponent(mainUrl.password || '');
            document.getElementById('mainPath').value = mainUrl.pathname + mainUrl.search;
            document.getElementById('subPath').value = subUrl.pathname + subUrl.search;
            document.getElementById('autoStart').checked = camera.autoStart || false;
            document.getElementById('enableEventForwarding').checked = camera.enableEventForwarding || false;
            document.getElementById('physicalOnvifPort').value = camera.physicalOnvifPort || '80';
            const hasFwdCreds2 = !!(camera.onvifForwardingUsername);
            document.getElementById('onvifUseAboveCredentials').checked = !hasFwdCreds2;
            document.getElementById('onvifForwardingUsername').value = camera.onvifForwardingUsername || '';
            document.getElementById('onvifForwardingPassword').value = camera.onvifForwardingPassword || '';
            
            const eventSource = camera.eventSource || 'onvif';
            document.getElementById('eventSource').value = eventSource;
            document.getElementById('aiModel').value = camera.aiModel || 'yolov8n.pt';
            const aiTargets = camera.aiTargets || ['person', 'vehicle'];
            document.getElementById('aiTargetPerson').checked = aiTargets.includes('person');
            document.getElementById('aiTargetVehicle').checked = aiTargets.includes('vehicle');
            document.getElementById('aiTargetAnimal').checked = aiTargets.includes('animal');
            document.getElementById('aiTargetPackage').checked = aiTargets.includes('package');
            document.getElementById('sendSmartOnvifTopics').checked = camera.sendSmartOnvifTopics !== false;
            
            const sens = camera.aiMotionSensitivity || 50;
            document.getElementById('aiMotionSensitivity').value = sens;
            updateAiSensitivityDisplay(sens);
            const conf = camera.aiConfidenceThreshold || 50;
            document.getElementById('aiConfidenceThreshold').value = conf;
            updateAiConfidenceDisplay(conf);
            currentZonePoints = camera.aiZone || [];
            zoneSnapshotLoaded = false;
            
            toggleOnvifCredFields();
            toggleEventForwardingFields();
            toggleSmartOnvifWarning();
            
            // Populate resolution and frame rate fields
            document.getElementById('mainWidth').value = camera.mainWidth || 1920;
            document.getElementById('mainHeight').value = camera.mainHeight || 1080;
            document.getElementById('subWidth').value = camera.subWidth || 640;
            document.getElementById('subHeight').value = camera.subHeight || 480;
            document.getElementById('mainFramerate').value = camera.mainFramerate || 30;
            document.getElementById('subFramerate').value = camera.subFramerate || 15;
            document.getElementById('transcodeSub').checked = camera.transcodeSub || false;
            document.getElementById('transcodeMain').checked = camera.transcodeMain || false;
            document.getElementById('disableSubstream').checked = camera.disableSubstream || false;
            document.getElementById('useMainAsSubstream').checked = camera.useMainAsSubstream || false;
            document.getElementById('enableAudio').checked = camera.enableAudio || false;
            document.getElementById('transcodeMainAudio').checked = camera.transcodeMainAudio || false;
            document.getElementById('transcodeSubAudio').checked = camera.transcodeSubAudio || false;
            
            // Populate audio transcoding settings
            document.getElementById('audioEncodingMain').value = camera.audioEncodingMain || 'aac';
            document.getElementById('audioSampleRateMain').value = camera.audioSampleRateMain || '44100';
            document.getElementById('audioBitrateMain').value = camera.audioBitrateMain || '128k';
            document.getElementById('audioEncodingSub').value = camera.audioEncodingSub || 'aac';
            document.getElementById('audioSampleRateSub').value = camera.audioSampleRateSub || '44100';
            document.getElementById('audioBitrateSub').value = camera.audioBitrateSub || '64k';
            
            toggleAudioSettings('main');
            toggleAudioSettings('sub');
            toggleTranscodeNotice('main');
            toggleTranscodeNotice('sub');
            document.getElementById('onvifPort').value = camera.onvifPort || '';
            document.getElementById('cameraUuid').value = camera.uuid || '';
            
            // Populate Network fields
            document.getElementById('useVirtualNic').checked = camera.useVirtualNic || false;
            document.getElementById('vnicKeepalive').checked = camera.vnicKeepalive || false;
            document.getElementById('parentInterface').value = camera.parentInterface || '';
            document.getElementById('nicMac').value = camera.nicMac || '';
            document.getElementById('ipMode').value = camera.ipMode || 'dhcp';
            document.getElementById('staticIp').value = camera.staticIp || '';
            document.getElementById('netmask').value = camera.netmask || '24';
            document.getElementById('gateway').value = camera.gateway || '';
            
            if (isLinux) {{
                await detectNetworkInterfaces();
                const select = document.getElementById('parentInterface');
                const manualInput = document.getElementById('parentInterfaceManual');
                const container = document.getElementById('manual-interface-container');
                
                const val = camera.parentInterface || '';
                let found = false;
                for (let i = 0; i < select.options.length; i++) {{
                    if (select.options[i].value === val) {{
                        select.value = val;
                        found = true;
                        break;
                    }}
                }}
                
                if (!found && val) {{
                    select.value = "__manual__";
                    manualInput.value = val;
                    container.style.display = 'block';
                }} else {{
                    container.style.display = 'none';
                }}
            }}
            
            toggleNetworkFields();
            toggleSubStreamFields();
            
            document.getElementById('camera-modal').classList.add('active');
        }}
        
        let isAiInstalled = false;
        let aiInstallInterval = null;

        async function checkAiStatus() {{
            try {{
                const response = await fetch('/api/ai/status');
                const data = await response.json();
                isAiInstalled = data.installed;
                updateAiUiState();
            }} catch (err) {{
                console.error("Failed to check AI status:", err);
            }}
        }}

        function updateAiUiState() {{
            const source = document.getElementById('eventSource').value;
            const checked = document.getElementById('enableEventForwarding').checked;
            
            const aiTargetGroup = document.getElementById('aiTargetClassesGroup');
            const aiModelGroup = document.getElementById('aiModelGroup');
            const aiInstallGroup = document.getElementById('aiInstallGroup');
            const smartGroup = document.getElementById('sendSmartOnvifTopicsGroup');
            const aiHwInfoGroup = document.getElementById('aiHardwareInfoGroup');
            const aiUninstallGroup = document.getElementById('aiUninstallGroup');
            
            if (checked && source === 'ai') {{
                if (isAiInstalled) {{
                    if (aiTargetGroup) aiTargetGroup.style.display = 'block';
                    if (aiModelGroup) {{
                        aiModelGroup.style.display = 'block';
                        updateModelDescription();
                    }}
                    if (aiHwInfoGroup) aiHwInfoGroup.style.display = 'block';
                    if (smartGroup) smartGroup.style.display = 'block';
                    if (aiInstallGroup) aiInstallGroup.style.display = 'none';
                    if (aiUninstallGroup) aiUninstallGroup.style.display = 'block';
                }} else {{
                    if (aiTargetGroup) aiTargetGroup.style.display = 'none';
                    if (aiModelGroup) aiModelGroup.style.display = 'none';
                    if (aiHwInfoGroup) aiHwInfoGroup.style.display = 'none';
                    if (smartGroup) smartGroup.style.display = 'none';
                    if (aiInstallGroup) aiInstallGroup.style.display = 'block';
                    if (aiUninstallGroup) aiUninstallGroup.style.display = 'none';
                }}
            }} else {{
                if (aiModelGroup) aiModelGroup.style.display = 'none';
                if (aiHwInfoGroup) aiHwInfoGroup.style.display = 'none';
                if (smartGroup) smartGroup.style.display = 'none';
                if (aiInstallGroup) aiInstallGroup.style.display = 'none';
                if (aiUninstallGroup) aiUninstallGroup.style.display = 'none';
            }}
        }}

        function updateModelDescription() {{
            const model = document.getElementById('aiModel').value;
            const desc = document.getElementById('aiModelDescription');
            if (!desc) return;
            
            let html = "";
            if (model === "yolov8n.pt") {{
                html = "<strong>YOLOv8 Nano (6.2 MB)</strong><br>" +
                       "• <strong>CPU Cost:</strong> Low (ideal for most servers).<br>" +
                       "• <strong>Accuracy:</strong> Standard.<br>" +
                       "• <strong>Drawbacks:</strong> Might miss small or distant objects in high-resolution streams.";
            }} else if (model === "yolo11n.pt") {{
                html = "<strong>YOLO11 Nano (5.6 MB) [Recommended]</strong><br>" +
                       "• <strong>CPU Cost:</strong> Low/Medium.<br>" +
                       "• <strong>Accuracy:</strong> High (newer architecture with optimized features).<br>" +
                       "• <strong>Drawbacks:</strong> Marginally higher CPU initialization load, but faster inference speed.";
            }} else if (model === "yolo11s.pt") {{
                html = "<strong>YOLO11 Small (19.0 MB)</strong><br>" +
                       "• <strong>CPU Cost:</strong> Medium (requires multi-core CPU).<br>" +
                       "• <strong>Accuracy:</strong> Very High (detects smaller/farther details).<br>" +
                       "• <strong>Drawbacks:</strong> Higher steady CPU usage; might cause framerate lag on slow systems.";
            }} else if (model === "yolov8s.pt") {{
                html = "<strong>YOLOv8 Small (22.5 MB)</strong><br>" +
                       "• <strong>CPU Cost:</strong> Medium (requires multi-core CPU).<br>" +
                       "• <strong>Accuracy:</strong> High.<br>" +
                       "• <strong>Drawbacks:</strong> Higher power consumption and slower inference speed than YOLO11 Small.";
            }} else if (model === "yolov8m.pt") {{
                html = "<strong>YOLOv8 Medium (52.0 MB)</strong><br>" +
                       "• <strong>CPU Cost:</strong> Very High (GPU recommended).<br>" +
                       "• <strong>Accuracy:</strong> Excellent.<br>" +
                       "• <strong>Drawbacks:</strong> Slow processing on CPU, which can lead to high latency and frame buildup.";
            }} else if (model === "yolo11l.pt") {{
                html = "<strong>YOLO11 Large (51.5 MB)</strong><br>" +
                       "• <strong>CPU Cost:</strong> Extremely High (GPU highly recommended).<br>" +
                       "• <strong>Accuracy:</strong> Outstanding (precise detection of tiny/far objects).<br>" +
                       "• <strong>Drawbacks:</strong> Heavy model; will struggle or cause lag on CPU inference.";
            }} else if (model === "yolo11x.pt") {{
                html = "<strong>YOLO11 Extra-Large (114.0 MB)</strong><br>" +
                       "• <strong>CPU Cost:</strong> Maximum (GPU required for real-time).<br>" +
                       "• <strong>Accuracy:</strong> Peak detection capability.<br>" +
                       "• <strong>Drawbacks:</strong> High memory footprint and slow speed unless run on hardware acceleration.";
            }} else if (model === "yolov8l.pt") {{
                html = "<strong>YOLOv8 Large (87.5 MB)</strong><br>" +
                       "• <strong>CPU Cost:</strong> Extremely High (GPU highly recommended).<br>" +
                       "• <strong>Accuracy:</strong> Very High.<br>" +
                       "• <strong>Drawbacks:</strong> Slower and uses more parameters than YOLO11 Large.";
            }} else if (model === "yolov8x.pt") {{
                html = "<strong>YOLOv8 Extra-Large (130.5 MB)</strong><br>" +
                       "• <strong>CPU Cost:</strong> Maximum (GPU required).<br>" +
                       "• <strong>Accuracy:</strong> Outstanding.<br>" +
                       "• <strong>Drawbacks:</strong> Very resource intensive.";
            }}
            desc.innerHTML = html;
        }}

        async function startAiInstallation() {{
            const btn = document.getElementById('installAiBtn');
            const selectedBackend = document.querySelector('input[name="aiBackend"]:checked');
            const mode = selectedBackend ? selectedBackend.value : 'cpu';
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Initializing Installer...';
            
            try {{
                const response = await fetch('/api/ai/install', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{mode: mode}})
                }});
                const data = await response.json();
                
                document.getElementById('aiInstallProgressContainer').style.display = 'block';
                pollAiInstallProgress();
                aiInstallInterval = setInterval(pollAiInstallProgress, 1000);
            }} catch (err) {{
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-download"></i> Install AI Dependencies';
                alert("Failed to start installation: " + err);
            }}
        }}

        async function startAiUninstall() {{
            if (!confirm("Are you sure you want to uninstall all AI dependencies (PyTorch, YOLO framework, OpenCV Headless)? This will disable local AI object detection until reinstalled.")) return;
            const btn = document.getElementById('uninstallAiBtn');
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Initializing Uninstaller...';
            
            try {{
                const response = await fetch('/api/ai/uninstall', {{ method: 'POST' }});
                const data = await response.json();
                
                document.getElementById('aiInstallProgressContainer').style.display = 'block';
                pollAiInstallProgress();
                aiInstallInterval = setInterval(pollAiInstallProgress, 1000);
            }} catch (err) {{
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-trash-alt"></i> Uninstall AI Dependencies';
                alert("Failed to start uninstallation: " + err);
            }}
        }}

        async function pollAiInstallProgress() {{
            try {{
                const response = await fetch('/api/ai/install/progress');
                const data = await response.json();
                
                const logBox = document.getElementById('aiInstallLogs');
                if (logBox && data.log) {{
                    logBox.textContent = data.log.join('\\n');
                    logBox.scrollTop = logBox.scrollHeight;
                }}
                
                const statusText = document.getElementById('aiInstallStatusText');
                const spinner = document.getElementById('aiInstallSpinner');
                const installBtn = document.getElementById('installAiBtn');
                const uninstallBtn = document.getElementById('uninstallAiBtn');
                
                if (data.status === 'success') {{
                    clearInterval(aiInstallInterval);
                    statusText.textContent = "Installation Completed Successfully!";
                    statusText.style.color = "#48bb78";
                    if (spinner) spinner.innerHTML = '<i class="fas fa-check-circle" style="color: #48bb78;"></i>';
                    isAiInstalled = true;
                    setTimeout(() => {{
                        updateAiUiState();
                    }}, 2000);
                }} else if (data.status === 'failed') {{
                    clearInterval(aiInstallInterval);
                    statusText.textContent = "Operation Failed!";
                    statusText.style.color = "#f56565";
                    if (spinner) spinner.innerHTML = '<i class="fas fa-times-circle" style="color: #f56565;"></i>';
                    if (installBtn) {{
                        installBtn.disabled = false;
                        installBtn.innerHTML = '<i class="fas fa-redo"></i> Retry Installation';
                    }}
                    if (uninstallBtn) {{
                        uninstallBtn.disabled = false;
                        uninstallBtn.innerHTML = '<i class="fas fa-trash-alt"></i> Uninstall AI Dependencies';
                    }}
                }} else if (data.status === 'uninstalling') {{
                    statusText.textContent = "Uninstalling AI Dependencies (this may take a minute)...";
                    statusText.style.color = "#3182ce";
                    if (spinner) spinner.innerHTML = '<i class="fas fa-spinner fa-spin" style="color: #3182ce;"></i>';
                }} else if (data.status === 'idle') {{
                    clearInterval(aiInstallInterval);
                    statusText.textContent = "Uninstall Completed Successfully!";
                    statusText.style.color = "#48bb78";
                    if (spinner) spinner.innerHTML = '<i class="fas fa-check-circle" style="color: #48bb78;"></i>';
                    isAiInstalled = false;
                    setTimeout(() => {{
                        updateAiUiState();
                    }}, 2000);
                }} else {{
                    statusText.textContent = "Installing AI Dependencies (this may take a few minutes)...";
                    statusText.style.color = "#3182ce";
                    if (spinner) spinner.innerHTML = '<i class="fas fa-spinner fa-spin" style="color: #3182ce;"></i>';
                }}
            }} catch (err) {{
                console.error("Error polling progress:", err);
            }}
        }}

        function closeModal() {{
            if (aiInstallInterval) {{
                clearInterval(aiInstallInterval);
                aiInstallInterval = null;
            }}
            document.getElementById('camera-modal').classList.remove('active');
            document.getElementById('camera-form').reset();
            const progress = document.getElementById('aiInstallProgressContainer');
            if (progress) progress.style.display = 'none';
            const logs = document.getElementById('aiInstallLogs');
            if (logs) logs.textContent = '';
            const btn = document.getElementById('installAiBtn');
            if (btn) {{
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-download"></i> Install AI Dependencies';
            }}
            const feedback = document.getElementById('aiTestEventFeedback');
            if (feedback) feedback.textContent = '';
        }}

        function switchFormTab(tabName) {{
            document.querySelectorAll('.form-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.form-section').forEach(s => s.classList.remove('active'));
            
            const selectedTab = document.getElementById(`form-tab-${{tabName}}`);
            const selectedSec = document.getElementById(`form-sec-${{tabName}}`);
            if (selectedTab) selectedTab.classList.add('active');
            if (selectedSec) selectedSec.classList.add('active');
        }}

        function toggleAudioSettings(type) {{
            const checked = document.getElementById(`transcode${{type.charAt(0).toUpperCase() + type.slice(1)}}Audio`).checked;
            const settings = document.getElementById(`${{type}}AudioSettings`);
            if (settings) {{
                settings.style.display = checked ? 'block' : 'none';
            }}
        }}

        function toggleTranscodeNotice(type) {{
            const checked = document.getElementById(`transcode${{type.charAt(0).toUpperCase() + type.slice(1)}}`).checked;
            const notice = document.getElementById(`${{type}}TranscodeNotice`);
            if (notice) {{
                notice.style.display = checked ? 'block' : 'none';
            }}
        }}
        
        function toggleEventForwardingFields() {{
            const checked = document.getElementById('enableEventForwarding').checked;
            const esGroup = document.getElementById('eventSourceGroup');
            if (esGroup) esGroup.style.display = checked ? 'block' : 'none';
            
            const cameraId = document.getElementById('camera-id').value;
            const isEdit = cameraId !== '';
            const testGroup = document.getElementById('aiTestEventGroup');
            if (testGroup) testGroup.style.display = (checked && isEdit) ? 'block' : 'none';
            
            if (checked) {{
                toggleEventSourceFields();
            }} else {{
                const portGroup = document.getElementById('physicalOnvifPortGroup');
                const credGroup = document.getElementById('onvifForwardingCredGroup');
                const aiGroup = document.getElementById('aiTargetClassesGroup');
                const aiModelGroup = document.getElementById('aiModelGroup');
                const aiInstallGroup = document.getElementById('aiInstallGroup');
                const testGroup = document.getElementById('aiTestEventGroup');
                const aiSensGroup = document.getElementById('aiSensitivityGroup');
                const aiConfidenceGroup = document.getElementById('aiConfidenceGroup');
                const aiZoneGroup = document.getElementById('aiZoneGroup');
                const aiCopyGroup = document.getElementById('aiCopySettingsGroup');
                const smartGroup = document.getElementById('sendSmartOnvifTopicsGroup');
                if (portGroup) portGroup.style.display = 'none';
                if (credGroup) credGroup.style.display = 'none';
                if (aiGroup) aiGroup.style.display = 'none';
                if (aiModelGroup) aiModelGroup.style.display = 'none';
                if (aiInstallGroup) aiInstallGroup.style.display = 'none';
                if (testGroup) testGroup.style.display = 'none';
                if (aiSensGroup) aiSensGroup.style.display = 'none';
                if (aiConfidenceGroup) aiConfidenceGroup.style.display = 'none';
                if (aiZoneGroup) aiZoneGroup.style.display = 'none';
                if (aiCopyGroup) aiCopyGroup.style.display = 'none';
                if (smartGroup) smartGroup.style.display = 'none';
            }}
        }}

        async function sendTestOnvifEvent(tag) {{
            const cameraId = document.getElementById('camera-id').value;
            if (!cameraId) return;
            
            const buttons = [
                'btnTestOnvifEvent',
                'btnTestPersonEvent',
                'btnTestVehicleEvent',
                'btnTestAnimalEvent',
                'btnTestPackageEvent'
            ];
            
            let clickedButtonId = 'btnTestOnvifEvent';
            if (tag === 'person') clickedButtonId = 'btnTestPersonEvent';
            else if (tag === 'vehicle') clickedButtonId = 'btnTestVehicleEvent';
            else if (tag === 'animal') clickedButtonId = 'btnTestAnimalEvent';
            else if (tag === 'package') clickedButtonId = 'btnTestPackageEvent';
            
            const clickedBtn = document.getElementById(clickedButtonId);
            if (!clickedBtn) return;
            
            const feedback = document.getElementById('aiTestEventFeedback');
            const originalHTML = clickedBtn.innerHTML;
            
            const camera = cameras.find(c => c.id === parseInt(cameraId));
            if (camera && camera.status !== 'running') {{
                feedback.textContent = 'Warning: Camera must be running to test events!';
                feedback.style.color = '#dd6b20';
                return;
            }}
            
            try {{
                // Disable all buttons
                buttons.forEach(btnId => {{
                    const b = document.getElementById(btnId);
                    if (b) b.disabled = true;
                }});
                
                clickedBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Triggering...';
                feedback.textContent = '';
                feedback.style.color = '#a0aec0';
                
                let url = `/api/cameras/${{cameraId}}/test-event`;
                if (tag) {{
                    url += `?tag=${{encodeURIComponent(tag)}}`;
                }}
                
                const response = await fetch(url, {{
                    method: 'POST'
                }});
                
                if (response.ok) {{
                    feedback.textContent = `Event (${{tag || 'all'}}) triggered successfully! Check Protect.`;
                    feedback.style.color = '#10b981';
                }} else {{
                    const err = await response.json();
                    feedback.textContent = 'Failed: ' + (err.error || 'Unknown error');
                    feedback.style.color = '#f56565';
                }}
            }} catch (error) {{
                console.error('Error sending test event:', error);
                feedback.textContent = 'Error triggering event.';
                feedback.style.color = '#f56565';
            }} finally {{
                setTimeout(() => {{
                    // Enable all buttons
                    buttons.forEach(btnId => {{
                        const b = document.getElementById(btnId);
                        if (b) b.disabled = false;
                    }});
                    clickedBtn.innerHTML = originalHTML;
                }}, 1000);
            }}
        }}

        function toggleEventSourceFields() {{
            const checked = document.getElementById('enableEventForwarding').checked;
            if (!checked) return;
            
            const source = document.getElementById('eventSource').value;
            const portGroup = document.getElementById('physicalOnvifPortGroup');
            const credGroup = document.getElementById('onvifForwardingCredGroup');
            const aiGroup = document.getElementById('aiTargetClassesGroup');
            const aiModelGroup = document.getElementById('aiModelGroup');
            const aiSensGroup = document.getElementById('aiSensitivityGroup');
            const aiConfidenceGroup = document.getElementById('aiConfidenceGroup');
            const aiZoneGroup = document.getElementById('aiZoneGroup');
            const aiCopyGroup = document.getElementById('aiCopySettingsGroup');
            
            const cameraId = document.getElementById('camera-id').value;
            const isEdit = cameraId !== '';
            
            if (source === 'onvif') {{
                if (portGroup) portGroup.style.display = 'block';
                if (credGroup) credGroup.style.display = 'block';
                if (aiGroup) aiGroup.style.display = 'none';
                if (aiModelGroup) aiModelGroup.style.display = 'none';
                if (aiSensGroup) aiSensGroup.style.display = 'none';
                if (aiConfidenceGroup) aiConfidenceGroup.style.display = 'none';
                if (aiZoneGroup) aiZoneGroup.style.display = 'none';
                if (aiCopyGroup) aiCopyGroup.style.display = 'none';
                if (document.getElementById('sendSmartOnvifTopicsGroup')) document.getElementById('sendSmartOnvifTopicsGroup').style.display = 'none';
                if (document.getElementById('aiHardwareInfoGroup')) document.getElementById('aiHardwareInfoGroup').style.display = 'none';
                document.getElementById('aiInstallGroup').style.display = 'none';
            }} else {{
                if (portGroup) portGroup.style.display = 'none';
                if (credGroup) credGroup.style.display = 'none';
                if (aiSensGroup) aiSensGroup.style.display = 'block';
                if (aiConfidenceGroup) aiConfidenceGroup.style.display = 'block';
                if (aiZoneGroup && isEdit) aiZoneGroup.style.display = 'block';
                if (aiCopyGroup && isEdit) aiCopyGroup.style.display = 'block';
                checkAiStatus();
            }}
        }}

        function toggleOnvifCredFields() {{
            const useAbove = document.getElementById('onvifUseAboveCredentials').checked;
            const customFields = document.getElementById('onvifCustomCredFields');
            if (customFields) customFields.style.display = useAbove ? 'none' : 'block';
        }}

        function toggleSmartOnvifWarning() {{
            const warningEl = document.getElementById('smartOnvifWarning');
            const checkbox = document.getElementById('sendSmartOnvifTopics');
            if (warningEl && checkbox) {{
                warningEl.style.display = checkbox.checked ? 'block' : 'none';
            }}
        }}

        // ========== Zone Drawing ==========
        let currentZonePoints = [];
        let zoneSnapshotLoaded = false;
        let zoneSnapshotImage = null;
        let zoneDragIndex = -1;
        let zoneIsDragging = false;
        let zoneMouseDownPos = null;

        async function loadZoneSnapshot() {{
            const cameraId = document.getElementById('camera-id').value;
            if (!cameraId) {{
                showToast('Save the camera first before loading a snapshot.', 'warning');
                return;
            }}
            const btn = document.getElementById('btnLoadZoneSnapshot');
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
            btn.disabled = true;
            try {{
                const resp = await fetch(`/api/cameras/${{cameraId}}/snapshot`);
                if (!resp.ok) throw new Error('Failed to capture snapshot');
                const blob = await resp.blob();
                const img = new Image();
                img.onload = function() {{
                    zoneSnapshotImage = img;
                    zoneSnapshotLoaded = true;
                    document.getElementById('zoneEmptyState').style.display = 'none';
                    drawZoneCanvas();
                }};
                img.src = URL.createObjectURL(blob);
            }} catch (e) {{
                console.error('Snapshot error:', e);
                showToast('Failed to load snapshot. Is the camera running?', 'error');
            }} finally {{
                btn.innerHTML = '<i class="fas fa-camera"></i> Load Snapshot';
                btn.disabled = false;
            }}
        }}

        function getZonePointAtPos(nx, ny, canvas) {{
            const hitRadius = 20;
            for (let i = 0; i < currentZonePoints.length; i++) {{
                const pt = currentZonePoints[i];
                const dx = (nx - pt.x) * canvas.width;
                const dy = (ny - pt.y) * canvas.height;
                if (Math.sqrt(dx * dx + dy * dy) < hitRadius) return i;
            }}
            return -1;
        }}

        function drawZoneCanvas(hoveredIdx) {{
            const canvas = document.getElementById('zoneCanvas');
            const container = document.getElementById('zoneCanvasContainer');
            if (!canvas || !container) return;
            
            const rect = container.getBoundingClientRect();
            canvas.width = rect.width;
            canvas.height = rect.height;
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            if (zoneSnapshotImage) {{
                ctx.drawImage(zoneSnapshotImage, 0, 0, canvas.width, canvas.height);
                // Darken areas outside zone
                if (currentZonePoints.length >= 3) {{
                    ctx.save();
                    ctx.fillStyle = 'rgba(0, 0, 0, 0.55)';
                    ctx.fillRect(0, 0, canvas.width, canvas.height);
                    ctx.globalCompositeOperation = 'destination-out';
                    ctx.beginPath();
                    ctx.moveTo(currentZonePoints[0].x * canvas.width, currentZonePoints[0].y * canvas.height);
                    for (let i = 1; i < currentZonePoints.length; i++) {{
                        ctx.lineTo(currentZonePoints[i].x * canvas.width, currentZonePoints[i].y * canvas.height);
                    }}
                    ctx.closePath();
                    ctx.fill();
                    ctx.restore();
                }}
            }}
            
            // Draw zone polygon
            if (currentZonePoints.length > 0) {{
                ctx.strokeStyle = '#10b981';
                ctx.lineWidth = 2;
                ctx.setLineDash([]);
                ctx.beginPath();
                ctx.moveTo(currentZonePoints[0].x * canvas.width, currentZonePoints[0].y * canvas.height);
                for (let i = 1; i < currentZonePoints.length; i++) {{
                    ctx.lineTo(currentZonePoints[i].x * canvas.width, currentZonePoints[i].y * canvas.height);
                }}
                if (currentZonePoints.length >= 3) ctx.closePath();
                ctx.stroke();
                
                // Fill zone area with transparent green
                if (currentZonePoints.length >= 3) {{
                    ctx.fillStyle = 'rgba(16, 185, 129, 0.15)';
                    ctx.fill();
                }}
                
                // Draw points
                currentZonePoints.forEach((pt, idx) => {{
                    const isHovered = (hoveredIdx !== undefined && hoveredIdx === idx);
                    const radius = isHovered ? 8 : 5;
                    ctx.beginPath();
                    ctx.arc(pt.x * canvas.width, pt.y * canvas.height, radius, 0, Math.PI * 2);
                    ctx.fillStyle = idx === 0 ? '#f59e0b' : (isHovered ? '#34d399' : '#10b981');
                    ctx.fill();
                    ctx.strokeStyle = '#fff';
                    ctx.lineWidth = isHovered ? 2.5 : 1.5;
                    ctx.stroke();
                }});
            }}
        }}

        // Mouse events for zone canvas: drag points + add new points
        document.addEventListener('mousedown', function(e) {{
            const canvas = document.getElementById('zoneCanvas');
            if (!canvas || e.target !== canvas || !zoneSnapshotLoaded) return;
            
            const rect = canvas.getBoundingClientRect();
            const nx = (e.clientX - rect.left) / rect.width;
            const ny = (e.clientY - rect.top) / rect.height;
            
            const hitIdx = getZonePointAtPos(nx, ny, canvas);
            if (hitIdx >= 0) {{
                // Start dragging an existing point
                zoneDragIndex = hitIdx;
                zoneIsDragging = false;
                zoneMouseDownPos = {{ x: nx, y: ny }};
                e.preventDefault();
            }} else {{
                zoneDragIndex = -1;
                zoneMouseDownPos = {{ x: nx, y: ny }};
            }}
        }});

        document.addEventListener('mousemove', function(e) {{
            const canvas = document.getElementById('zoneCanvas');
            if (!canvas || !zoneSnapshotLoaded) return;
            
            const rect = canvas.getBoundingClientRect();
            const nx = (e.clientX - rect.left) / rect.width;
            const ny = (e.clientY - rect.top) / rect.height;
            
            if (zoneDragIndex >= 0) {{
                // Dragging a point
                zoneIsDragging = true;
                currentZonePoints[zoneDragIndex].x = parseFloat(Math.max(0, Math.min(1, nx)).toFixed(4));
                currentZonePoints[zoneDragIndex].y = parseFloat(Math.max(0, Math.min(1, ny)).toFixed(4));
                drawZoneCanvas(zoneDragIndex);
                canvas.style.cursor = 'grabbing';
                return;
            }}
            
            // Hover detection for cursor change
            if (e.target === canvas) {{
                const hitIdx = getZonePointAtPos(nx, ny, canvas);
                if (hitIdx >= 0) {{
                    canvas.style.cursor = 'grab';
                    drawZoneCanvas(hitIdx);
                }} else {{
                    canvas.style.cursor = 'crosshair';
                    drawZoneCanvas();
                }}
            }}
        }});

        document.addEventListener('mouseup', function(e) {{
            const canvas = document.getElementById('zoneCanvas');
            if (!canvas || !zoneSnapshotLoaded) return;
            
            if (zoneDragIndex >= 0 && zoneIsDragging) {{
                // Finished dragging
                zoneDragIndex = -1;
                zoneIsDragging = false;
                zoneMouseDownPos = null;
                canvas.style.cursor = 'crosshair';
                drawZoneCanvas();
                return;
            }}
            
            // If not dragging, treat as a click to add a new point
            if (e.target === canvas && zoneDragIndex < 0 && zoneMouseDownPos) {{
                const rect = canvas.getBoundingClientRect();
                const nx = (e.clientX - rect.left) / rect.width;
                const ny = (e.clientY - rect.top) / rect.height;
                
                // Check we didn't move much (it's a click, not a drag)
                const dx = Math.abs(nx - zoneMouseDownPos.x) * rect.width;
                const dy = Math.abs(ny - zoneMouseDownPos.y) * rect.height;
                if (dx < 5 && dy < 5) {{
                    currentZonePoints.push({{ x: parseFloat(nx.toFixed(4)), y: parseFloat(ny.toFixed(4)) }});
                    drawZoneCanvas();
                }}
            }}
            
            zoneDragIndex = -1;
            zoneIsDragging = false;
            zoneMouseDownPos = null;
        }});

        // Right-click to delete a point
        document.addEventListener('contextmenu', function(e) {{
            const canvas = document.getElementById('zoneCanvas');
            if (!canvas || e.target !== canvas || !zoneSnapshotLoaded) return;
            
            const rect = canvas.getBoundingClientRect();
            const nx = (e.clientX - rect.left) / rect.width;
            const ny = (e.clientY - rect.top) / rect.height;
            const hitIdx = getZonePointAtPos(nx, ny, canvas);
            if (hitIdx >= 0) {{
                e.preventDefault();
                currentZonePoints.splice(hitIdx, 1);
                drawZoneCanvas();
            }}
        }});

        function clearZone() {{
            currentZonePoints = [];
            drawZoneCanvas();
        }}

        // ========== Copy AI Settings ==========
        function openCopyAiSettingsModal() {{
            const cameraId = document.getElementById('camera-id').value;
            if (!cameraId) return;
            
            const list = document.getElementById('copyAiCameraList');
            list.innerHTML = '';
            document.getElementById('copyAiSelectAll').checked = false;
            document.getElementById('copyAiFeedback').textContent = '';
            
            cameras.forEach(cam => {{
                if (cam.id === parseInt(cameraId)) return;
                const hasAi = cam.eventSource === 'ai' && cam.enableEventForwarding;
                const aiBadge = hasAi 
                    ? `<span style="font-size: 9px; background-color: #d69e2e; color: #1a202c; padding: 1px 5px; border-radius: 3px; font-weight: bold; text-transform: uppercase; margin-left: 6px;">AI</span>` 
                    : '';
                const item = document.createElement('label');
                item.style.cssText = 'display: flex; align-items: center; gap: 10px; padding: 10px 14px; border-bottom: 1px solid #2d3748; cursor: pointer; transition: background 0.15s;';
                item.onmouseover = () => item.style.background = 'rgba(99, 102, 241, 0.08)';
                item.onmouseout = () => item.style.background = 'transparent';
                item.innerHTML = `
                    <input type="checkbox" class="copy-ai-cb" value="${{cam.id}}" style="width: auto; cursor: pointer;">
                    <div style="flex: 1;">
                        <div style="font-size: 13px; color: #e2e8f0; font-weight: 500; display: flex; align-items: center;">
                            <span>${{cam.name}}</span>
                            ${{aiBadge}}
                        </div>
                        <div style="font-size: 10px; color: #718096;">ID: ${{cam.id}} &mdash; ${{cam.status}}</div>
                    </div>
                `;
                list.appendChild(item);
            }});
            
            document.getElementById('copy-ai-modal').classList.add('active');
        }}

        function closeCopyAiModal() {{
            document.getElementById('copy-ai-modal').classList.remove('active');
        }}

        function toggleCopyAiSelectAll() {{
            const checked = document.getElementById('copyAiSelectAll').checked;
            document.querySelectorAll('.copy-ai-cb').forEach(cb => cb.checked = checked);
        }}

        async function applyCopyAiSettings() {{
            const cameraId = document.getElementById('camera-id').value;
            const selected = Array.from(document.querySelectorAll('.copy-ai-cb:checked')).map(cb => parseInt(cb.value));
            
            if (selected.length === 0) {{
                document.getElementById('copyAiFeedback').textContent = 'Please select at least one camera.';
                document.getElementById('copyAiFeedback').style.color = '#f6ad55';
                return;
            }}
            
            const btn = document.getElementById('btnApplyCopyAi');
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Applying...';
            
            try {{
                const resp = await fetch(`/api/cameras/${{cameraId}}/copy-ai-settings`, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ targetCameraIds: selected }})
                }});
                
                if (resp.ok) {{
                    const result = await resp.json();
                    document.getElementById('copyAiFeedback').textContent = `Settings copied to ${{result.updated.length}} camera(s) successfully!`;
                    document.getElementById('copyAiFeedback').style.color = '#10b981';
                    setTimeout(() => closeCopyAiModal(), 1500);
                    loadData();
                }} else {{
                    document.getElementById('copyAiFeedback').textContent = 'Failed to copy settings.';
                    document.getElementById('copyAiFeedback').style.color = '#f56565';
                }}
            }} catch (err) {{
                console.error('Copy AI settings error:', err);
                document.getElementById('copyAiFeedback').textContent = 'Error copying settings.';
                document.getElementById('copyAiFeedback').style.color = '#f56565';
            }} finally {{
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-check"></i> Apply to Selected';
            }}
        }}

        let onvifViewActive = false;
        let onvifPollInterval = null;
        let onvifEvents = [];

        function toggleONVIFView(active, initialCameraId = null, initialEventType = null) {{
            onvifViewActive = active;
            const overlay = document.getElementById('onvif-overlay');
            if (active) {{
                overlay.classList.add('active');
                populateCameraFilter();
                document.getElementById('onvif-camera-filter').value = initialCameraId !== null ? initialCameraId : 'all';
                document.getElementById('onvif-type-filter').value = initialEventType !== null ? initialEventType : 'all';
                refreshONVIFEvents();
                onvifPollInterval = setInterval(refreshONVIFEvents, 2000);
            }} else {{
                overlay.classList.remove('active');
                if (onvifPollInterval) {{
                    clearInterval(onvifPollInterval);
                    onvifPollInterval = null;
                }}
            }}
        }}

        function populateCameraFilter() {{
            const select = document.getElementById('onvif-camera-filter');
            const currentValue = select.value;
            select.innerHTML = '<option value="all">All Cameras</option>';
            cameras.forEach(cam => {{
                select.innerHTML += `<option value="${{cam.id}}">${{cam.name}}</option>`;
            }});
            select.value = currentValue || 'all';
        }}

        async function refreshONVIFEvents() {{
            try {{
                const response = await fetch('/api/onvif/events');
                if (response.ok) {{
                    onvifEvents = await response.json();
                    renderONVIFEvents();
                }}
                
                const camResp = await fetch('/api/cameras');
                if (camResp.ok) {{
                    const latestCams = await camResp.json();
                    renderAiThreadDiagnostics(latestCams);
                }}
            }} catch (err) {{
                console.error("Error refreshing ONVIF events:", err);
            }}
        }}

        function renderAiThreadDiagnostics(latestCams) {{
            const panel = document.getElementById('ai-diagnostics-panel');
            const summary = document.getElementById('ai-diagnostics-summary');
            const body = document.getElementById('ai-diagnostics-body');
            if (!panel || !summary || !body) return;
            
            const aiCams = latestCams.filter(c => c.eventSource === 'ai' && c.enableEventForwarding);
            
            if (aiCams.length === 0) {{
                panel.style.display = 'none';
                return;
            }}
            
            panel.style.display = 'block';
            const activeCount = aiCams.filter(c => c.status === 'running').length;
            summary.innerHTML = `<span style="color: #4ade80;">${{activeCount}} active</span> / ${{aiCams.length}} configured`;
            
            let html = '';
            aiCams.forEach(cam => {{
                const isRunning = cam.status === 'running';
                const statusBadge = isRunning 
                    ? `<span style="background: rgba(74, 222, 128, 0.1); color: #4ade80; padding: 2px 6px; border-radius: 4px; font-weight: 600; font-size: 11px;">Active</span>`
                    : `<span style="background: rgba(239, 68, 68, 0.1); color: #f87171; padding: 2px 6px; border-radius: 4px; font-weight: 600; font-size: 11px;">Stopped</span>`;
                
                const fps = isRunning ? (cam.aiFpsMeasurement || 0.0).toFixed(1) : '0.0';
                const latency = isRunning ? `${{Math.round(cam.aiAvgInferenceLatency * 1000)}}ms` : '-';
                const queue = isRunning ? `${{Math.round(cam.aiQueueTime * 1000)}}ms` : '-';
                const count = cam.aiInferenceCount || 0;
                
                let detectionStr = 'None';
                if (isRunning && cam.aiLastDetection && cam.aiLastDetection.length > 0) {{
                    detectionStr = cam.aiLastDetection.map(d => 
                        `<span style="background: rgba(236, 201, 75, 0.1); color: #ecc94b; border: 1px solid rgba(236, 201, 75, 0.3); padding: 1px 4px; border-radius: 3px; font-size: 10px; margin-right: 4px; text-transform: uppercase; font-weight: bold;">${{d}}</span>`
                    ).join('');
                }}
                
                html += `
                    <tr style="border-bottom: 1px solid #1e293b;">
                        <td style="padding: 8px 12px; font-weight: 600;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                ${{statusBadge}}
                                <span>${{cam.name}}</span>
                            </div>
                        </td>
                        <td style="padding: 8px 12px; color: #94a3b8; font-size: 11px;">${{cam.aiModel || 'yolov8n.pt'}}</td>
                        <td style="padding: 8px 12px; text-align: center; font-weight: bold; color: ${{fps > 0 ? '#4ade80' : '#64748b'}}">${{fps}}</td>
                        <td style="padding: 8px 12px; text-align: center; color: #f59e0b;">${{latency}}</td>
                        <td style="padding: 8px 12px; text-align: center; color: #a855f7;">${{queue}}</td>
                        <td style="padding: 8px 12px;">${{detectionStr}}</td>
                        <td style="padding: 8px 12px; text-align: right; color: #64748b;">${{count.toLocaleString()}}</td>
                    </tr>
                `;
            }});
            
            body.innerHTML = html;
        }}

        function renderONVIFEvents() {{
            const filterVal = document.getElementById('onvif-camera-filter').value;
            const typeFilterVal = document.getElementById('onvif-type-filter').value;
            const searchQuery = (document.getElementById('onvif-event-search')?.value || '').trim().toLowerCase();
            const tbody = document.getElementById('onvif-events-body');
            tbody.innerHTML = '';
            
            const filtered = onvifEvents.filter(evt => {{
                // Camera filter
                if (filterVal !== 'all' && String(evt.camera_id) !== String(filterVal)) {{
                    return false;
                }}
                
                // Type filter
                const evtType = evt.type || 'onvif';
                if (typeFilterVal !== 'all' && evtType !== typeFilterVal) {{
                    return false;
                }}
                
                // Target/State filter
                const targetFilterVal = document.getElementById('onvif-target-filter')?.value || 'all';
                if (targetFilterVal !== 'all') {{
                    const valLower = String(evt.value).toLowerCase();
                    const isActive = valLower === 'true' || valLower === 'on' || valLower === '1' || valLower === 'active';
                    
                    if (targetFilterVal === 'active') {{
                        if (!isActive) return false;
                    }} else if (targetFilterVal === 'clear') {{
                        if (isActive) return false;
                    }} else {{
                        const tags = evt.tags || [];
                        if (!tags.includes(targetFilterVal)) return false;
                    }}
                }}
                
                // Search query filter
                if (searchQuery) {{
                    const cameraName = String(evt.camera_name || '').toLowerCase();
                    const topic = String(evt.topic || '').toLowerCase();
                    const val = String(evt.value || '').toLowerCase();
                    const property = String(evt.data_name || 'IsMotion').toLowerCase();
                    const tags = (evt.tags || []).join(' ').toLowerCase();
                    
                    return cameraName.includes(searchQuery) ||
                           topic.includes(searchQuery) ||
                           val.includes(searchQuery) ||
                           property.includes(searchQuery) ||
                           tags.includes(searchQuery);
                }}
                return true;
            }});
            
            if (filtered.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #4a5568; padding: 40px;">No events matching filters logged yet.</td></tr>';
                return;
            }}
            
            const sorted = [...filtered].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
            
            sorted.forEach(evt => {{
                let localTime = evt.timestamp;
                try {{
                    const d = new Date(evt.timestamp);
                    localTime = d.toLocaleDateString() + ' ' + d.toLocaleTimeString();
                }} catch (e) {{}}
                
                const isAi = (evt.type === 'ai');
                const typeBadge = isAi 
                    ? `<span style="background: rgba(147, 51, 234, 0.15); color: #c084fc; border: 1px solid rgba(147, 51, 234, 0.3); padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase; display: inline-flex; align-items: center; gap: 4px;">AI Engine</span>`
                    : `<span style="background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase; display: inline-flex; align-items: center; gap: 4px;">ONVIF Fwd</span>`;

                const valLower = String(evt.value).toLowerCase();
                const isActive = valLower === 'true' || valLower === 'on' || valLower === '1' || valLower === 'active';
                const stateBadge = isActive 
                    ? `<span class="badge-event-active">ACTIVE</span>` 
                    : `<span class="badge-event-inactive">CLEAR</span>`;
                
                let tagsHtml = '';
                if (evt.tags && Array.isArray(evt.tags)) {{
                    evt.tags.forEach(tag => {{
                        const pctStr = (evt.confidences && evt.confidences[tag] !== undefined) ? ' (' + evt.confidences[tag] + '%)' : '';
                        if (tag === 'person') {{
                            tagsHtml += ` <span style="background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; display: inline-flex; align-items: center; gap: 4px; margin-left: 5px;">Person` + pctStr + `</span>`;
                        }} else if (tag === 'vehicle') {{
                            tagsHtml += ` <span style="background: rgba(139, 92, 246, 0.15); color: #a78bfa; border: 1px solid rgba(139, 92, 246, 0.3); padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; display: inline-flex; align-items: center; gap: 4px; margin-left: 5px;">Vehicle` + pctStr + `</span>`;
                        }} else if (tag === 'animal') {{
                            tagsHtml += ` <span style="background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; display: inline-flex; align-items: center; gap: 4px; margin-left: 5px;">Animal` + pctStr + `</span>`;
                        }} else if (tag === 'package') {{
                            tagsHtml += ` <span style="background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; display: inline-flex; align-items: center; gap: 4px; margin-left: 5px;">Package` + pctStr + `</span>`;
                        }}
                    }});
                }}

                tbody.innerHTML += `
                    <tr style="border-bottom: 1px solid var(--border-color);">
                        <td style="padding: 10px; color: var(--text-muted);">${{localTime}}</td>
                        <td style="padding: 10px; font-weight: 600; color: var(--btn-primary);">${{evt.camera_name}}</td>
                        <td style="padding: 10px;">${{typeBadge}}</td>
                        <td style="padding: 10px; color: var(--text-body);">${{evt.topic}}</td>
                        <td style="padding: 10px; display: flex; align-items: center; flex-wrap: wrap; gap: 6px;">${{stateBadge}}${{tagsHtml}}</td>
                    </tr>
                `;
            }});
        }}

        async function clearONVIFEvents() {{
            if (!confirm("Are you sure you want to clear all ONVIF event logs?")) return;
            try {{
                const response = await fetch('/api/onvif/events/clear', {{ method: 'POST' }});
                if (response.ok) {{
                    onvifEvents = [];
                    renderONVIFEvents();
                }}
            }} catch (err) {{
                console.error("Error clearing ONVIF events:", err);
            }}
        }}

        async function saveCamera(event) {{
            event.preventDefault();
            
            const btn = event.submitter || event.target.querySelector('button[type="submit"]');
            const originalText = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving Please Wait';
            
            const cameraId = document.getElementById('camera-id').value;
            const isEdit = cameraId !== '';
            
            const data = {{
                name: document.getElementById('name').value,
                host: document.getElementById('host').value,
                rtspPort: document.getElementById('rtspPort').value,
                username: document.getElementById('username').value,
                password: document.getElementById('password').value,
                mainPath: document.getElementById('mainPath').value,
                subPath: document.getElementById('subPath').value,
                autoStart: document.getElementById('autoStart').checked,
                enableEventForwarding: document.getElementById('enableEventForwarding').checked,
                physicalOnvifPort: parseInt(document.getElementById('physicalOnvifPort').value || '80'),
                onvifForwardingUsername: document.getElementById('onvifUseAboveCredentials').checked ? '' : (document.getElementById('onvifForwardingUsername').value || ''),
                onvifForwardingPassword: document.getElementById('onvifUseAboveCredentials').checked ? '' : (document.getElementById('onvifForwardingPassword').value || ''),
                mainWidth: parseInt(document.getElementById('mainWidth').value),
                mainHeight: parseInt(document.getElementById('mainHeight').value),
                subWidth: parseInt(document.getElementById('subWidth').value),
                subHeight: parseInt(document.getElementById('subHeight').value),
                mainFramerate: parseInt(document.getElementById('mainFramerate').value),
                subFramerate: parseInt(document.getElementById('subFramerate').value),
                transcodeSub: document.getElementById('transcodeSub').checked,
                transcodeMain: document.getElementById('transcodeMain').checked,
                disableSubstream: document.getElementById('disableSubstream').checked,
                useMainAsSubstream: document.getElementById('useMainAsSubstream').checked,
                enableAudio: document.getElementById('enableAudio').checked,
                transcodeMainAudio: document.getElementById('transcodeMainAudio').checked,
                transcodeSubAudio: document.getElementById('transcodeSubAudio').checked,
                audioEncodingMain: document.getElementById('audioEncodingMain').value,
                audioSampleRateMain: document.getElementById('audioSampleRateMain').value,
                audioBitrateMain: document.getElementById('audioBitrateMain').value,
                audioEncodingSub: document.getElementById('audioEncodingSub').value,
                audioSampleRateSub: document.getElementById('audioSampleRateSub').value,
                audioBitrateSub: document.getElementById('audioBitrateSub').value,
                useVirtualNic: document.getElementById('useVirtualNic').checked,
                vnicKeepalive: document.getElementById('vnicKeepalive').checked,
                parentInterface: document.getElementById('parentInterface').value === "__manual__" 
                    ? document.getElementById('parentInterfaceManual').value 
                    : document.getElementById('parentInterface').value,
                nicMac: document.getElementById('nicMac').value,
                ipMode: document.getElementById('ipMode').value,
                staticIp: document.getElementById('staticIp').value,
                netmask: document.getElementById('netmask').value,
                gateway: document.getElementById('gateway').value,
                uuid: document.getElementById('cameraUuid').value || null,
                eventSource: document.getElementById('eventSource').value,
                aiModel: document.getElementById('aiModel').value,
                aiTargets: (function() {{
                    const targets = [];
                    if (document.getElementById('aiTargetPerson').checked) targets.push('person');
                    if (document.getElementById('aiTargetVehicle').checked) targets.push('vehicle');
                    if (document.getElementById('aiTargetAnimal').checked) targets.push('animal');
                    if (document.getElementById('aiTargetPackage').checked) targets.push('package');
                    return targets;
                }})(),
                aiMotionSensitivity: parseInt(document.getElementById('aiMotionSensitivity').value) || 50,
                aiConfidenceThreshold: parseInt(document.getElementById('aiConfidenceThreshold').value) || 50,
                aiZone: currentZonePoints || [],
                sendSmartOnvifTopics: document.getElementById('sendSmartOnvifTopics').checked
            }};
            // Add ONVIF port if specified
            const onvifPort = document.getElementById('onvifPort').value;
            if (onvifPort) {{
                data.onvifPort = parseInt(onvifPort);
            }}
            
            const url = isEdit ? `/api/cameras/${{cameraId}}` : '/api/cameras';
            const method = isEdit ? 'PUT' : 'POST';

            try {{
                console.log(`[SaveCamera] Initiating ${{method}} to ${{url}}...`);
                const response = await fetch(url, {{
                    method: method,
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify(data)
                }});
                
                console.log(`[SaveCamera] Response status: ${{response.status}}`);
                
                if (response.ok) {{
                    console.log('[SaveCamera] Save successful, closing modal and reloading data...');
                    closeModal();
                    
                    // Reset button state immediately after closing modal so it's ready for next time
                    btn.disabled = false;
                    btn.innerHTML = originalText;
                    
                    // Now reload data in the background (no need to await it for the UI to be responsive)
                    loadData(); 
                }} else {{
                    const error = await response.json();
                    console.error('[SaveCamera] Save failed:', error);
                    alert('Error saving camera: ' + (error.error || 'Unknown error'));
                    
                    // Reset button state on error
                    btn.disabled = false;
                    btn.innerHTML = originalText;
                }}
            }} catch (error) {{
                console.error('[SaveCamera] Network/execution error:', error);
                alert('An error occurred while saving the camera. Check console for details.');
            }} finally {{
                // Ensure button is always reset if not already done
                if (btn.disabled) {{
                    btn.disabled = false;
                    btn.innerHTML = originalText;
                }}
            }}
        }}
        
        async function deleteCamera(id) {{
            if (!confirm('Are you sure you want to delete this camera?')) return;
            try {{
                await fetch(`/api/cameras/${{id}}`, {{method: 'DELETE'}});
                await loadData();
            }} catch (error) {{
                console.error('Error deleting camera:', error);
            }}
        }}
        
        async function startCamera(id) {{
            try {{
                await fetch(`/api/cameras/${{id}}/start`, {{method: 'POST'}});
                await loadData();
            }} catch (error) {{
                console.error('Error starting camera:', error);
            }}
        }}
        
        async function stopCamera(id) {{
            try {{
                await fetch(`/api/cameras/${{id}}/stop`, {{method: 'POST'}});
                await loadData();
            }} catch (error) {{
                console.error('Error stopping camera:', error);
            }}
        }}
        
        async function startAll() {{
            try {{
                await fetch('/api/cameras/start-all', {{method: 'POST'}});
                await loadData();
            }} catch (error) {{
                console.error('Error starting all cameras:', error);
            }}
        }}
        
        async function stopAll() {{
            try {{
                await fetch('/api/cameras/stop-all', {{method: 'POST'}});
                await loadData();
            }} catch (error) {{
                console.error('Error stopping all cameras:', error);
            }}
        }}
        
        function switchSettingsTab(tabId) {{
            // Hide all tab content
            document.querySelectorAll('.settings-tab-content').forEach(el => {{
                el.classList.remove('active');
            }});
            // Remove active class from all buttons
            document.querySelectorAll('.settings-tab-btn').forEach(el => {{
                el.classList.remove('active');
            }});
            
            // Show selected tab content
            document.getElementById(tabId).classList.add('active');
            
            // Find active button and make it active
            const btn = Array.from(document.querySelectorAll('.settings-tab-btn')).find(b => {{
                return b.getAttribute('onclick') && b.getAttribute('onclick').includes(tabId);
            }});
            if (btn) btn.classList.add('active');
            
            // Toggle Save Settings button visibility based on tab
            const saveBtn = document.getElementById('settings-save-btn');
            if (saveBtn) {{
                if (tabId === 'settings-maintenance') {{
                    saveBtn.style.display = 'none';
                }} else {{
                    saveBtn.style.display = 'block';
                }}
            }}
        }}
        
        function toggleAuthFields() {{
            const enabled = document.getElementById('authEnabled').checked;
            document.getElementById('auth-settings-fields').style.display = enabled ? 'block' : 'none';
        }}
        
        function toggleSubStreamFields() {{
            const disabled = document.getElementById('disableSubstream').checked;
            const useMain = document.getElementById('useMainAsSubstream').checked;
            
            const container = document.getElementById('sub-stream-fields-container');
            const pathContainer = document.getElementById('subPathContainer');
            const subPathInput = document.getElementById('subPath');
            
            if (disabled) {{
                container.style.display = 'none';
            }} else {{
                container.style.display = 'block';
                if (useMain) {{
                    pathContainer.style.display = 'none';
                    subPathInput.required = false;
                }} else {{
                    pathContainer.style.display = 'block';
                    subPathInput.required = true;
                }}
            }}
        }}
        
        async function toggleAutoStart(id, autoStart) {{
            console.log(`[v2025-12-23] Toggling auto-start for camera ${{id}} to ${{autoStart}}`);
            
            try {{
                // Use the dedicated endpoint for toggling auto-start
                const response = await fetch(`/api/cameras/${{id}}/auto-start`, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                        'Cache-Control': 'no-cache'
                    }},
                    body: JSON.stringify({{
                        autoStart: autoStart
                    }})
                }});
                
                if (response.ok) {{
                    console.log('Auto-start updated successfully');
                    await loadData();
                }} else {{
                    let errorMsg = 'Unknown error';
                    try {{
                        const error = await response.json();
                        errorMsg = error.error || errorMsg;
                    }} catch (e) {{
                        errorMsg = response.statusText;
                    }}
                    console.error('Failed to update auto-start:', errorMsg);
                    alert('Failed to update auto-start setting: ' + errorMsg);
                    // Revert the toggle if it failed
                    await loadData();
                }}
            }} catch (error) {{
                console.error('Error toggling auto-start:', error);
                alert('Error updating auto-start setting: ' + error.message);
                await loadData();
            }}
        }}
        
        async function restartServer() {{
            if (!confirm('Are you sure you want to restart the server application?')) return;
            try {{
                const response = await fetch('/api/server/restart', {{method: 'POST'}});
                if (response.ok) {{
                    if (typeof showToast === 'function') {{
                        showToast('Server is restarting...', 'info');
                    }} else {{
                        alert('Server is restarting... Please wait a few seconds.');
                    }}
                    // Reload page after 5 seconds to reconnect
                    setTimeout(() => window.location.reload(), 5000);
                }} else {{
                    alert('Failed to restart server');
                }}
            }} catch (error) {{
                console.error('Error restarting server:', error);
                alert('Error restarting server');
            }}
        }}
        
        async function stopServer() {{
            if (!confirm('Are you sure you want to stop the server? This will shut down all camera streams and the web interface.')) {{
                return;
            }}
            
            try {{
                if (typeof showToast === 'function') {{
                    showToast('Server is stopping...', 'warning');
                }}
                
                const response = await fetch('/api/server/stop', {{method: 'POST'}});
                if (response.ok) {{
                    setTimeout(() => {{
                        document.body.innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 100vh; font-family: sans-serif; flex-direction: column; background: #1a202c; color: #fff; text-align: center; padding: 20px;">' +
                            '<i class="fas fa-power-off" style="font-size: 64px; color: #f56565; margin-bottom: 20px;"></i>' +
                            '<h1>Server Stopped</h1>' +
                            '<p style="font-size: 18px; color: #a0aec0;">The ONVIF server has been shut down successfully.</p>' +
                            '<p style="color: #718096; margin-top: 30px; font-size: 14px;">You can safely close this browser tab.</p>' +
                            '</div>';
                    }}, 1500);
                }} else {{
                    alert('Failed to stop server');
                }}
            }} catch (error) {{
                // Expected error since server is shutting down
                document.body.innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 100vh; font-family: sans-serif; flex-direction: column; background: #1a202c; color: #fff; text-align: center; padding: 20px;">' +
                    '<i class="fas fa-power-off" style="font-size: 64px; color: #f56565; margin-bottom: 20px;"></i>' +
                    '<h1>Server Stopped</h1>' +
                    '<p style="font-size: 18px; color: #a0aec0;">The ONVIF server has been shut down successfully.</p>' +
                    '<p style="color: #718096; margin-top: 30px; font-size: 14px;">You can safely close this browser tab.</p>' +
                    '</div>';
            }}
        }}
        
        async function fetchStreamInfo(streamType) {{
            const cameraId = document.getElementById('camera-id').value;
            
            // Build a temporary camera object to fetch stream info
            const tempCamera = {{
                host: document.getElementById('host').value,
                rtspPort: document.getElementById('rtspPort').value,
                username: document.getElementById('username').value,
                password: document.getElementById('password').value,
                mainPath: document.getElementById('mainPath').value,
                subPath: document.getElementById('subPath').value
            }};
            
            // Validate required fields
            if (!tempCamera.host || !tempCamera.mainPath || !tempCamera.subPath) {{
                alert('Please fill in camera host and stream paths first');
                return;
            }}
            
            // Show loading state
            const button = event.target;
            const originalText = button.textContent;
            button.disabled = true;
            button.textContent = 'Fetching...';
            
            try {{
                // If editing existing camera, use its ID
                let url, method, body;
                
                if (cameraId) {{
                    // Editing existing camera
                    url = `/api/cameras/${{cameraId}}/fetch-stream-info`;
                    method = 'POST';
                    body = JSON.stringify({{ streamType }});
                }} else {{
                    // New camera - need to create temp camera first or use direct URL
                    // For simplicity, we'll require saving the camera first
                    alert('Please save the camera first, then use the fetch button when editing');
                    button.disabled = false;
                    button.textContent = originalText;
                    return;
                }}
                
                const response = await fetch(url, {{
                    method: method,
                    headers: {{'Content-Type': 'application/json'}},
                    body: body
                }});
                
                if (response.ok) {{
                    const data = await response.json();
                    
                    // Populate the appropriate fields
                    if (streamType === 'main') {{
                        document.getElementById('mainWidth').value = data.width;
                        document.getElementById('mainHeight').value = data.height;
                        document.getElementById('mainFramerate').value = data.framerate;
                        alert(`Main stream info fetched: ${{data.width}}x${{data.height}} @ ${{data.framerate}}fps`);
                    }} else {{
                        document.getElementById('subWidth').value = data.width;
                        document.getElementById('subHeight').value = data.height;
                        document.getElementById('subFramerate').value = data.framerate;
                        alert(`Sub stream info fetched: ${{data.width}}x${{data.height}} @ ${{data.framerate}}fps`);
                    }}
                }} else {{
                    const error = await response.json();
                    let errorMsg = 'Failed to fetch stream info: ' + (error.error || 'Unknown error');
                    if (error.details) {{
                        errorMsg += '\\n\\nDetails: ' + error.details;
                    }}
                    if (error.troubleshooting && error.troubleshooting.length > 0) {{
                        errorMsg += '\\n\\nTroubleshooting tips:\\n' + error.troubleshooting.join('\\n');
                    }}
                    alert(errorMsg);
                }}
            }} catch (error) {{
                console.error('Error fetching stream info:', error);
                alert('Error fetching stream info: ' + error.message);
            }} finally {{
                button.disabled = false;
                button.textContent = originalText;
            }}
        }}
        
        function resetAdvancedSettings() {{
            if (confirm('Are you sure you want to reset all MediaMTX and FFmpeg settings to their factory defaults?')) {{
                document.getElementById('mediamtx_id').value = 4096;
                document.getElementById('mediamtx_writeQueueSize').value = 16384;
                document.getElementById('mediamtx_readTimeout').value = '30s';
                document.getElementById('mediamtx_writeTimeout').value = '30s';
                document.getElementById('mediamtx_udpMaxPayloadSize').value = 1472;
                document.getElementById('mediamtx_hlsSegmentCount').value = 3;
                document.getElementById('mediamtx_hlsSegmentDuration').value = '1s';
                document.getElementById('mediamtx_hlsPartDuration').value = '200ms';
                
                // FFmpeg Defaults
                document.getElementById('ffmpeg_globalArgs').value = '-hide_banner -loglevel error';
                document.getElementById('ffmpeg_inputArgs').value = '-rtsp_transport tcp -reconnect 1 -reconnect_at_eof 1 -reconnect_streamed 1 -reconnect_delay_max 2';
                document.getElementById('ffmpeg_processArgs').value = '-c:v libx264 -preset ultrafast -tune zerolatency -g 30';
                document.getElementById('ffmpeg_hardwareEncoding').checked = false;
                
                showToast('Settings reset to defaults. Click "Save Settings" to apply.');
            }}
        }}

        function toggleAdvancedSettings() {{
            const section = document.getElementById('advancedSettingsSection');
            const chevron = document.getElementById('advancedChevron');
            if (section.style.display === 'none') {{
                section.style.display = 'block';
                if (chevron) chevron.style.transform = 'rotate(180deg)';
            }} else {{
                section.style.display = 'none';
                if (chevron) chevron.style.transform = 'rotate(0deg)';
            }}
        }}

        async function loadSettings() {{
            try {{
                const response = await fetch('/api/settings?t=' + new Date().getTime());
                if (response.ok) {{
                    settings = await response.json();
                    // Update form fields if modal is open
                    const ipField = document.getElementById('serverIp');
                    if (ipField) ipField.value = settings.serverIp || 'localhost';
                    
                    const browserField = document.getElementById('openBrowser');
                    if (browserField) browserField.checked = settings.openBrowser === true;
                    const themeField = document.getElementById('themeSelect');
                    if (themeField) themeField.value = settings.theme || 'dracula';
                    
                    const gridField = document.getElementById('gridColumnsSelect');
                    if (gridField) gridField.value = settings.gridColumns || 3;
                    
                    const rtspPortField = document.getElementById('rtspPortSettings');
                    if (rtspPortField) rtspPortField.value = settings.rtspPort || 8554;

                    const autoBootField = document.getElementById('autoBoot');
                    if (autoBootField) autoBootField.checked = settings.autoBoot === true;
                    
                    
                    const globalUserField = document.getElementById('globalUsername');
                    if (globalUserField) globalUserField.value = settings.globalUsername || 'admin';
                    
                    const globalPassField = document.getElementById('globalPassword');
                    if (globalPassField) globalPassField.value = settings.globalPassword || 'admin';
                    
                    const rtspAuthField = document.getElementById('rtspAuthEnabled');
                    if (rtspAuthField) rtspAuthField.checked = settings.rtspAuthEnabled === true;

                    const debugModeField = document.getElementById('debugMode');
                    if (debugModeField) debugModeField.checked = settings.debugMode === true;

                    const watchdogField = document.getElementById('watchdogEnabled');
                    if (watchdogField) watchdogField.checked = settings.watchdogEnabled === true;

                    // Load Advanced Settings
                    if (settings.advancedSettings) {{
                        const adv = settings.advancedSettings;
                        if (adv.mediamtx) {{
                            document.getElementById('mediamtx_writeQueueSize').value = adv.mediamtx.writeQueueSize || 32768;
                            document.getElementById('mediamtx_readTimeout').value = adv.mediamtx.readTimeout || '30s';
                            document.getElementById('mediamtx_writeTimeout').value = adv.mediamtx.writeTimeout || '30s';
                            document.getElementById('mediamtx_udpMaxPayloadSize').value = adv.mediamtx.udpMaxPayloadSize || 1472;
                            document.getElementById('mediamtx_hlsSegmentCount').value = adv.mediamtx.hlsSegmentCount || 10;
                            document.getElementById('mediamtx_hlsSegmentDuration').value = adv.mediamtx.hlsSegmentDuration || '1s';
                            document.getElementById('mediamtx_hlsPartDuration').value = adv.mediamtx.hlsPartDuration || '200ms';
                        }}
                        if (adv.ffmpeg) {{
                            document.getElementById('ffmpeg_globalArgs').value = adv.ffmpeg.globalArgs || '-hide_banner -loglevel error';
                            document.getElementById('ffmpeg_inputArgs').value = adv.ffmpeg.inputArgs || '-rtsp_transport tcp -timeout 10000000';
                            document.getElementById('ffmpeg_processArgs').value = adv.ffmpeg.processArgs || '-c:v libx264 -preset ultrafast -tune zerolatency -g 30';
                            document.getElementById('ffmpeg_hardwareEncoding').checked = adv.ffmpeg.hardwareEncoding === true;
                        }}
                    }}
                    
                    const authEnabledField = document.getElementById('authEnabled');
                    if (authEnabledField) authEnabledField.checked = settings.authEnabled === true;
                    
                    toggleAuthFields();
                    
                    applyTheme(settings.theme);
                    applyGridLayout(settings.gridColumns || 3);
                }}
            }} catch (error) {{
                console.error('Error loading settings:', error);
            }}
        }}
        
        function openAboutModal() {{
            // Fetch system versions
            fetchSystemVersions();
            document.getElementById('about-modal').classList.add('active');
        }}
        
        function closeAboutModal() {{
            document.getElementById('about-modal').classList.remove('active');
        }}
        
        function openSettingsModal() {{
            loadSettings();
            
            // Auto-detect server IP if not set
            const serverIpField = document.getElementById('serverIp');
            if (!serverIpField.value || serverIpField.value === 'localhost') {{
                // Use the current hostname from the browser
                const detectedIp = window.location.hostname;
                if (detectedIp && detectedIp !== 'localhost' && detectedIp !== '127.0.0.1') {{
                    serverIpField.placeholder = `Auto-detected: ${{detectedIp}}`;
                }}
            }}
            
            document.getElementById('settings-modal').classList.add('active');
            switchSettingsTab('settings-general');
        }}
        
        async function fetchSystemVersions() {{
            try {{
                const response = await fetch('/api/system/versions');
                if (response.ok) {{
                    const data = await response.json();
                    document.getElementById('about-mediamtx-version').textContent = data.mediamtx || 'Unknown';
                    document.getElementById('about-ffmpeg-version').textContent = data.ffmpeg || 'Not installed';
                    
                    const aiDev = data.ai_device || 'Unknown';
                    document.getElementById('about-ai-device').textContent = aiDev;
                    const settingsAi = document.getElementById('settings-ai-device');
                    if (settingsAi) settingsAi.textContent = aiDev;
                }} else {{
                    document.getElementById('about-mediamtx-version').textContent = 'Error';
                    document.getElementById('about-ffmpeg-version').textContent = 'Error';
                    document.getElementById('about-ai-device').textContent = 'Error';
                }}
            }} catch (error) {{
                console.error('Failed to fetch system versions:', error);
                document.getElementById('about-mediamtx-version').textContent = 'Error';
                document.getElementById('about-ffmpeg-version').textContent = 'Error';
                document.getElementById('about-ai-device').textContent = 'Error';
            }}
        }}
        
        function closeSettingsModal() {{
            document.getElementById('settings-modal').classList.remove('active');
        }}
        
        async function resetAllUUIDs() {{
            if (!confirm("Are you sure you want to reset ALL camera UUIDs? This will make them appear as new devices to your NVR/Ubiquiti.")) return;
            try {{
                const response = await fetch('/api/cameras/reset-uuids', {{ method: 'POST' }});
                const result = await response.json();
                if (response.ok) {{
                    alert("Camera UUIDs have been reset successfully.\\n\\nA server restart is required to apply these changes to the ONVIF service.");
                    showToast(result.message, "success");
                    loadData();
                }} else {{
                    showToast(result.error || "Failed to reset UUIDs", "danger");
                }}
            }} catch (e) {{
                showToast("Error: " + e.message, "danger");
            }}
        }}

        async function resetAllMACs() {{
            if (!confirm("Are you sure you want to reset ALL camera MAC addresses? This may cause IP changes if you use DHCP reservations.")) return;
            try {{
                const response = await fetch('/api/cameras/reset-macs', {{ method: 'POST' }});
                const result = await response.json();
                if (response.ok) {{
                    alert("Camera MAC addresses have been reset successfully.\\n\\nA server restart is required to apply these changes to the Virtual NICs.");
                    showToast(result.message, "success");
                    loadData();
                }} else {{
                    showToast(result.error || "Failed to reset MACs", "danger");
                }}
            }} catch (e) {{
                showToast("Error: " + e.message, "danger");
            }}
        }}

        async function saveSettings(event) {{
            event.preventDefault();
            
            const btn = event.submitter || event.target.querySelector('button[type="submit"]');
            const originalText = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving Please Wait';
            
            const data = {{
                serverIp: document.getElementById('serverIp').value || 'localhost',
                openBrowser: document.getElementById('openBrowser').checked,
                theme: document.getElementById('themeSelect').value,
                gridColumns: parseInt(document.getElementById('gridColumnsSelect').value),
                rtspPort: parseInt(document.getElementById('rtspPortSettings').value || 8554),
                autoBoot: document.getElementById('autoBoot') ? document.getElementById('autoBoot').checked : false,
                globalUsername: document.getElementById('globalUsername').value,
                globalPassword: document.getElementById('globalPassword').value,
                rtspAuthEnabled: document.getElementById('rtspAuthEnabled').checked,
                debugMode: document.getElementById('debugMode').checked,
                watchdogEnabled: document.getElementById('watchdogEnabled') ? document.getElementById('watchdogEnabled').checked : false,
                matrixStretchFill: settings.matrixStretchFill === true,
                matrixHideNames: settings.matrixHideNames === true,
                matrixAiFlash: settings.matrixAiFlash === true,
                matrixAudioHover: settings.matrixAudioHover === true,
                matrixCarousel: settings.matrixCarousel === true,
                carouselSize: parseInt(settings.carouselSize) || 4,
                carouselInterval: parseInt(settings.carouselInterval) || 10000,
                advancedSettings: {{
                    mediamtx: {{
                        writeQueueSize: parseInt(document.getElementById('mediamtx_writeQueueSize').value) || 32768,
                        readTimeout: document.getElementById('mediamtx_readTimeout').value || '30s',
                        writeTimeout: document.getElementById('mediamtx_writeTimeout').value || '30s',
                        udpMaxPayloadSize: parseInt(document.getElementById('mediamtx_udpMaxPayloadSize').value) || 1472,
                        hlsSegmentCount: parseInt(document.getElementById('mediamtx_hlsSegmentCount').value) || 10,
                        hlsSegmentDuration: document.getElementById('mediamtx_hlsSegmentDuration').value || '1s',
                        hlsPartDuration: document.getElementById('mediamtx_hlsPartDuration').value || '200ms'
                    }},
                    ffmpeg: {{
                        globalArgs: document.getElementById('ffmpeg_globalArgs').value || '-hide_banner -loglevel error',
                        inputArgs: document.getElementById('ffmpeg_inputArgs').value || '-rtsp_transport tcp -timeout 10000000',
                        processArgs: document.getElementById('ffmpeg_processArgs').value || '-c:v libx264 -preset ultrafast -tune zerolatency -g 30',
                        hardwareEncoding: document.getElementById('ffmpeg_hardwareEncoding').checked
                    }}
                }},
                authEnabled: document.getElementById('authEnabled').checked,
                username: document.getElementById('authUsername').value,
                password: document.getElementById('authPassword').value
            }};
            
            try {{
                const response = await fetch('/api/settings', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify(data)
                }});
                
                if (response.ok) {{
                    closeSettingsModal();
                    await loadData(); // Reload everything
                }} else {{
                    const error = await response.json();
                    alert('Error saving settings: ' + (error.error || 'Unknown error'));
                }}
            }} catch (error) {{
                console.error('Error saving settings:', error);
                alert('Error saving settings: ' + error.message);
            }} finally {{
                btn.disabled = false;
                btn.innerHTML = originalText;
            }}
        }}
        
        function showToast(message, type = 'info') {{
            const toast = document.createElement('div');
            toast.className = `toast toast-${{type}}`;
            
            if (type === 'info') toast.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
            else if (type === 'success') toast.style.background = '#48bb78';
            else if (type === 'warning') toast.style.background = '#ed8936';
            else if (type === 'error') toast.style.background = '#f56565';
            else toast.style.background = '#2d3748';
            
            toast.textContent = message;
            document.body.appendChild(toast);
            
            setTimeout(() => {{
                if (toast) {{
                    toast.style.animation = 'slideOut 0.3s ease-in forwards';
                    setTimeout(() => toast.remove(), 300);
                }}
            }}, 3000);
        }}

        async function rebootServer() {{
            if (!confirm('This will reboot the entire server. The system will be unavailable for a few minutes. Continue?')) {{
                return;
            }}
            
            try {{
                const response = await fetch('/api/server/reboot', {{method: 'POST'}});
                if (response.ok) {{
                    alert('Server is rebooting... The system will be back online in a few minutes.');
                    if (typeof closeSettingsModal === 'function') closeSettingsModal();
                }} else {{
                    alert('Failed to reboot server. This feature only works on Linux.');
                }}
            }} catch (error) {{
                console.error('Error rebooting server:', error);
                alert('Error rebooting server');
            }}
        }}
        
        // Update System Functions
        let updateInfo = null;
        let updateProgressInterval = null;
        
        async function checkForUpdates() {{
            // Open modal and show checking state
            document.getElementById('update-modal').classList.add('active');
            showUpdateState('checking');
            
            try {{
                const response = await fetch('/api/updates/check');
                if (response.ok) {{
                    updateInfo = await response.json();
                    
                    // Handle Docker warnings and button visibility
                    const warningEl = document.getElementById('docker-update-warning');
                    const reinstallBtns = document.querySelectorAll('.reinstall-btn');
                    const downloadBtn = document.getElementById('download-update-btn');
                    
                    if (updateInfo.is_docker) {{
                        if (warningEl) warningEl.style.display = 'block';
                        if (downloadBtn) downloadBtn.style.display = 'none';
                        reinstallBtns.forEach(btn => btn.style.display = 'none');
                    }} else {{
                        if (warningEl) warningEl.style.display = 'none';
                        if (downloadBtn) downloadBtn.style.display = 'block';
                        reinstallBtns.forEach(btn => btn.style.display = 'inline-block');
                    }}
                    
                    if (updateInfo.update_available) {{
                        // Show update info
                        document.getElementById('current-version').textContent = 'v' + updateInfo.current_version;
                        document.getElementById('latest-version').textContent = 'v' + updateInfo.latest_version;
                        
                        // Format release date
                        const releaseDate = new Date(updateInfo.published_at);
                        document.getElementById('release-date').textContent = releaseDate.toLocaleDateString('en-US', {{
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric'
                        }});
                        
                        document.getElementById('release-notes').textContent = updateInfo.release_notes || 'No release notes available.';
                        showUpdateState('info');
                    }} else {{
                        // No updates available
                        document.getElementById('no-update-version').textContent = 'Current version: v' + updateInfo.current_version;
                        showUpdateState('no-updates');
                    }}
                }} else {{
                    showUpdateState('error');
                    document.getElementById('error-message').textContent = 'Failed to check for updates. Please try again later.';
                }}
            }} catch (error) {{
                console.error('Error checking for updates:', error);
                showUpdateState('error');
                document.getElementById('error-message').textContent = 'Network error. Please check your connection.';
            }}
        }}
        
        function showUpdateState(state) {{
            // Hide all states
            document.getElementById('update-checking').style.display = 'none';
            document.getElementById('update-info').style.display = 'none';
            document.getElementById('update-progress').style.display = 'none';
            document.getElementById('update-no-updates').style.display = 'none';
            document.getElementById('update-error').style.display = 'none';
            
            // Show requested state
            if (state === 'checking') {{
                document.getElementById('update-checking').style.display = 'block';
            }} else if (state === 'info') {{
                document.getElementById('update-info').style.display = 'block';
            }} else if (state === 'progress') {{
                document.getElementById('update-progress').style.display = 'block';
            }} else if (state === 'no-updates') {{
                document.getElementById('update-no-updates').style.display = 'block';
            }} else if (state === 'error') {{
                document.getElementById('update-error').style.display = 'block';
            }}
        }}
        
        async function downloadAndInstallUpdate() {{
            if (!updateInfo || !updateInfo.download_url) {{
                alert('Update information not available');
                return;
            }}
            
            if (!confirm('This will download and install the update. The server will restart automatically. Continue?')) {{
                return;
            }}
            
            // Show progress
            showUpdateState('progress');
            
            try {{
                // Start the update
                const response = await fetch('/api/updates/apply', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        download_url: updateInfo.download_url
                    }})
                }});
                
                if (response.ok) {{
                    // Start polling for progress
                    startUpdateProgressPolling();
                }} else {{
                    showUpdateState('error');
                    document.getElementById('error-message').textContent = 'Failed to start update. Please try again.';
                }}
            }} catch (error) {{
                console.error('Error starting update:', error);
                showUpdateState('error');
                document.getElementById('error-message').textContent = 'Failed to start update: ' + error.message;
            }}
        }}
        
        function startUpdateProgressPolling() {{
            if (updateProgressInterval) {{
                clearInterval(updateProgressInterval);
            }}
            
            updateProgressInterval = setInterval(async () => {{
                try {{
                    const response = await fetch('/api/updates/status');
                    if (response.ok) {{
                        const status = await response.json();
                        
                        // Update progress bar
                        document.getElementById('progress-bar').style.width = status.progress + '%';
                        document.getElementById('progress-percent').textContent = Math.round(status.progress) + '%';
                        document.getElementById('progress-message').textContent = status.message;
                        
                        // Check if complete or error
                        if (status.status === 'complete') {{
                            clearInterval(updateProgressInterval);
                            document.getElementById('progress-message').textContent = 'Update complete! Server restarting...';
                            // Server will restart, page will disconnect
                            setTimeout(() => {{
                                window.location.reload();
                            }}, 5000);
                        }} else if (status.status === 'error') {{
                            clearInterval(updateProgressInterval);
                            showUpdateState('error');
                            document.getElementById('error-message').textContent = status.message;
                        }}
                    }}
                }} catch (error) {{
                    // Server might have restarted, try to reload
                    console.log('Update progress check failed, server may be restarting...');
                }}
            }}, 1000); // Poll every second
        }}
        
        async function reinstallCurrentVersion() {{
            if (!confirm('This will download and reinstall the current version (v{CURRENT_VERSION}) from GitHub. This is useful for repairing corrupted files. The server will restart automatically. Continue?')) {{
                return;
            }}
            
            // Show progress
            showUpdateState('progress');
            
            try {{
                // We need to get the download URL for the current version
                // First, check if we have it from the update check
                let downloadUrl = null;
                
                if (updateInfo && updateInfo.current_version === '{CURRENT_VERSION}') {{
                    // If we just checked and we're on the latest version, use that URL
                    downloadUrl = updateInfo.download_url;
                }} else {{
                    // Otherwise, fetch the latest release (which should be our current version if we're up to date)
                    const response = await fetch('/api/updates/check');
                    if (response.ok) {{
                        const info = await response.json();
                        downloadUrl = info.download_url;
                    }}
                }}
                
                if (!downloadUrl) {{
                    showUpdateState('error');
                    document.getElementById('error-message').textContent = 'Failed to get download URL. Please try again.';
                    return;
                }}
                
                // Start the reinstall (same as update, just different messaging)
                const applyResponse = await fetch('/api/updates/apply', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        download_url: downloadUrl
                    }})
                }});
                
                if (applyResponse.ok) {{
                    // Start polling for progress
                    startUpdateProgressPolling();
                }} else {{
                    showUpdateState('error');
                    document.getElementById('error-message').textContent = 'Failed to start reinstall. Please try again.';
                }}
            }} catch (error) {{
                console.error('Error reinstalling version:', error);
                showUpdateState('error');
                document.getElementById('error-message').textContent = 'Failed to reinstall: ' + error.message;
            }}
        }}
        
        function closeUpdateModal() {{
            document.getElementById('update-modal').classList.remove('active');
            if (updateProgressInterval) {{
                clearInterval(updateProgressInterval);
                updateProgressInterval = null;
            }}
            // Reset to checking state for next time
            showUpdateState('checking');
        }}
        
        async function updateStats() {{
            try {{
                // Parallel fetch for speed
                const [statsResp, analyticsResp] = await Promise.all([
                    fetch('/api/stats'),
                    fetch('/api/analytics')
                ]);
                
                const stats = await statsResp.json();
                const analytics = await analyticsResp.json();
                cachedAnalytics = analytics;
                
                if (matrixActive) {{
                    renderMatrix();
                }}
                
                // Update global server stats
                if (stats.cpu_percent !== undefined) {{
                    let totalBitrate = 0;
                    Object.values(analytics).forEach(a => totalBitrate += (a.bitrate || 0));
                    
                    document.getElementById('server-stats').innerHTML = 
                        `<i class="fa-solid fa-microchip" style="opacity: 0.75; color: var(--btn-primary);"></i> CPU: ${{stats.cpu_percent}}% &nbsp;&nbsp;•&nbsp;&nbsp; <i class="fa-solid fa-memory" style="opacity: 0.75; color: var(--btn-primary);"></i> MEM: ${{stats.memory_mb}}MB &nbsp;&nbsp;•&nbsp;&nbsp; <i class="fa-solid fa-network-wired" style="opacity: 0.75; color: var(--btn-primary);"></i> NET: ${{totalBitrate.toFixed(1)}} kbps`;
                }}
                
                // Update per-camera metrics
                cameras.forEach(cam => {{
                    const metricsEl = document.getElementById(`metrics-${{cam.id}}`);
                    if (!metricsEl) return;
                    
                    if (cam.status !== 'running') {{
                        metricsEl.innerHTML = '';
                        return;
                    }}
                    
                    // We check both main and sub streams
                    const pName = cam.pathName || cam.path_name;
                    const mainStats = analytics[pName + '_main'];
                    const subStats = analytics[pName + '_sub'];
                    
                    let html = '';
                    
                    if (mainStats) {{
                        const stats = mainStats;
                        const statusClass = stats.stale ? 'warn' : (stats.online || stats.ready ? 'live' : 'error');
                        html += `
                            <div class="metric-badge ${{statusClass}}" title="${{stats.stale ? 'Stream Stalled' : 'Main Stream Status'}}" style="min-width: 95px; justify-content: center;">
                                MAIN: ${{stats.bitrate.toFixed(0)}}
                            </div>
                        `;
                    }}
                    
                    if (subStats) {{
                        const stats = subStats;
                        const statusClass = stats.stale ? 'warn' : (stats.online || stats.ready ? 'live' : 'error');
                        const viewers = stats.readers || 0;
                        html += `
                            <div class="metric-badge ${{statusClass}}" title="${{stats.stale ? 'Stream Stalled' : 'Sub Stream Status'}}" style="min-width: 85px; justify-content: center;">
                                SUB: ${{stats.bitrate.toFixed(0)}}
                            </div>
                            <div class="metric-badge ${{viewers > 0 ? 'live' : ''}}" title="Active Viewers" style="min-width: 40px; justify-content: center;">
                                <i class="fas fa-users"></i> ${{viewers}}
                            </div>
                        `;
                    }}
                    
                    metricsEl.innerHTML = html;
                    
                    // Check for H265/HEVC codec on main or sub stream and display warning
                    const warningEl = document.getElementById(`codec-warning-${{cam.id}}`);
                    if (warningEl) {{
                        let isH265 = false;
                        
                        const checkTracksForH265 = (stats) => {{
                            if (stats && stats.tracks && Array.isArray(stats.tracks)) {{
                                return stats.tracks.some(track => {{
                                    const trackStr = typeof track === 'string' ? track : JSON.stringify(track);
                                    const t = trackStr.toLowerCase();
                                    return t.includes('h265') || t.includes('hevc');
                                }});
                            }}
                            return false;
                        }};
                        
                        isH265 = checkTracksForH265(mainStats) || checkTracksForH265(subStats);
                        
                        if (isH265) {{
                            warningEl.innerHTML = '<div style="background: rgba(237, 137, 54, 0.1); padding: 10px; margin-bottom: 15px; border-radius: 4px; font-size: 13px; color: #ed8936; display: flex; align-items: flex-start; gap: 8px; line-height: 1.4;"><i class="fas fa-exclamation-triangle" style="margin-top: 2px;"></i><span><strong>Performance Warning:</strong> H.265 / HEVC stream detected. For optimal performance and compatibility, it is recommended to set your camera to use <strong>H.264</strong> encoding instead.</span></div>';
                        }} else {{
                            warningEl.innerHTML = '';
                        }}
                    }}
                }});
                
            }} catch (e) {{
                console.error("Stats fetch failed:", e);
            }}
        }}
        
        function applyTheme(theme) {{
            // Remove all possible theme classes
            const themes = ['dark', 'nord', 'dracula', 'solar-light', 'midnight', 'emerald', 'sunset', 'matrix', 'slate', 'cyberpunk', 'amoled', 'ui'];
            themes.forEach(t => document.body.classList.remove(`theme-${{t}}`));
            
            // Add the selected one
            if (theme && theme !== 'classic') {{
                document.body.classList.add(`theme-${{theme}}`);
            }}

            // Sync dropdowns
            const s1 = document.getElementById('themeSwitcher');
            const s2 = document.getElementById('themeSelect');
            if (s1) s1.value = theme || 'dracula';
            if (s2) s2.value = theme || 'dracula';
        }}

        async function changeTheme(theme) {{
            applyTheme(theme);
            settings.theme = theme;
            
            try {{
                await fetch('/api/settings', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify(settings)
                }});
                console.log('Theme saved:', theme);
            }} catch (e) {{
                console.error('Failed to save theme:', e);
            }}
        }}

        function applyGridLayout(cols) {{
            const root = document.documentElement;
            const columns = parseInt(cols) || 3;
            root.style.setProperty('--grid-cols', columns);
            
            // Significantly increased widths to satisfy card content and alignment
            if (columns >= 6) {{
                root.style.setProperty('--container-width', '3500px');
            }} else if (columns >= 5) {{
                root.style.setProperty('--container-width', '2800px');
            }} else if (columns >= 4) {{
                root.style.setProperty('--container-width', '2200px');
            }} else if (columns >= 3) {{
                root.style.setProperty('--container-width', '1800px');
            }} else if (columns >= 2) {{
                root.style.setProperty('--container-width', '1400px');
            }} else {{
                root.style.setProperty('--container-width', '1200px');
            }}
            console.log(`Grid layout applied: ${{columns}} columns`);
        }}

        // Initialize on load
        async function init() {{
            await loadSettings();
            await loadData();
            if (settings.theme) applyTheme(settings.theme);
            if (settings.gridColumns) applyGridLayout(settings.gridColumns);
            await updateStats();
            fetchSystemVersions();
            
            // Check if matrix view is requested via URL search param or hash
            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.get('view') === 'matrix' || window.location.hash === '#matrix') {{
                toggleMatrixView(true);
            }}
            
            // Auto-refresh data and stats
            setInterval(loadData, 5000);
            setInterval(updateStats, 3000);
        }}
        
        init();
    </script>
    <script>
        function switchAddMode(mode) {{
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.getElementById('tab-' + mode).classList.add('active');
            
            if (mode === 'manual') {{
                document.getElementById('camera-form').style.display = 'block';
                document.getElementById('onvif-probe-form').style.display = 'none';
            }} else {{
                document.getElementById('camera-form').style.display = 'none';
                document.getElementById('onvif-probe-form').style.display = 'block';
            }}
        }}

        async function probeOnvif() {{
            const host = document.getElementById('probeHost').value;
            const port = document.getElementById('probePort').value;
            const user = document.getElementById('probeUser').value;
            const pass = document.getElementById('probePass').value;
            const btn = document.getElementById('btnProbe');
            const resultsDiv = document.getElementById('probe-results');
            
            if (!host) {{ alert('Host IP is required'); return; }}
            
            btn.disabled = true;
            btn.textContent = 'Scanning...';
            resultsDiv.innerHTML = '<div style="text-align:center">Connecting to camera...</div>';
            
            try {{
                const resp = await fetch('/api/onvif/probe', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{ host, port, username: user, password: pass }})
                }});
                
                const data = await resp.json();
                
                if (resp.ok) {{
                    let html = '<h4>Found Profiles:</h4><p style="font-size:12px;color:#718096;margin-bottom:10px">Click to use profile</p>';
                    if (data.profiles.length === 0) {{
                        html += '<p>No profiles found.</p>';
                    }} else {{
                        data.profiles.forEach(p => {{
                            html += `<div class="result-item" style="cursor:default">
                                <div style="margin-bottom:8px">
                                    <strong>${{p.name}}</strong> (${{p.width}}x${{p.height}} @ ${{p.framerate}}fps)<br>
                                    <span style="font-size:10px;color:#718096;word-break:break-all">${{p.streamUrl}}</span>
                                </div>
                                <div style="display:flex;gap:10px">
                                    <button type="button" class="btn" style="padding:5px 10px;font-size:12px;background:#667eea;color:white" onclick='applyProfile(${{JSON.stringify(p).replace(/'/g, "&#39;")}}, "${{data.device_info.host}}", "${{data.device_info.port}}", "main", this)'>Set as Main</button>
                                    <button type="button" class="btn" style="padding:5px 10px;font-size:12px;background:#718096;color:white" onclick='applyProfile(${{JSON.stringify(p).replace(/'/g, "&#39;")}}, "${{data.device_info.host}}", "${{data.device_info.port}}", "sub", this)'>Set as Sub</button>
                                </div>
                            </div>`;
                        }});
                    }}
                    resultsDiv.innerHTML = html;
                }} else {{
                    resultsDiv.innerHTML = `<div class="alert alert-danger">Error: ${{data.error || 'Unknown error'}}</div>`;
                }}
            }} catch (e) {{
                resultsDiv.innerHTML = `<div class="alert alert-danger">Connection Error: ${{e.message}}</div>`;
            }} finally {{
                btn.disabled = false;
                btn.textContent = 'Scan Camera';
            }}
        }}
        
        function applyProfile(profile, host, port, target, btn) {{
            // Always update credentials and host
            document.getElementById('host').value = host;
            document.getElementById('username').value = document.getElementById('probeUser').value;
            document.getElementById('password').value = document.getElementById('probePass').value;
            
            // Extract path logic
            let path = profile.streamUrl;
            try {{
                // Remove rtsp://.../ part intelligent parsing
                const url = new URL(profile.streamUrl);
                path = url.pathname + url.search;
            }} catch (e) {{
                // Fallback string manipulation
                if (path.includes(host)) {{
                    path = path.substring(path.indexOf(host) + host.length);
                    if (path.startsWith(':')) {{
                       path = path.substring(path.indexOf('/') );
                    }}
                }}
            }}
            
            if (target === 'main') {{
                document.getElementById('mainPath').value = path;
                document.getElementById('mainWidth').value = profile.width;
                document.getElementById('mainHeight').value = profile.height;
                document.getElementById('mainFramerate').value = profile.framerate;
                
                // Visual feedback
                if (btn) {{
                    const originalText = btn.textContent;
                    btn.textContent = 'Set!';
                    btn.style.background = '#48bb78';
                    setTimeout(() => {{ btn.textContent = originalText; btn.style.background = '#667eea'; }}, 2000);
                }}
                
            }} else {{
                document.getElementById('subPath').value = path;
                document.getElementById('subWidth').value = profile.width;
                document.getElementById('subHeight').value = profile.height;
                document.getElementById('subFramerate').value = profile.framerate;
                
                // Visual feedback
                if (btn) {{
                    const originalText = btn.textContent;
                    btn.textContent = 'Set!';
                    btn.style.background = '#48bb78';
                    setTimeout(() => {{ btn.textContent = originalText; btn.style.background = '#718096'; }}, 2000);
                }}
            }}
        }}


        function copyTextToClipboard(id) {{
            const el = document.getElementById(id);
            const text = el.textContent || el.value;
            navigator.clipboard.writeText(text).then(() => {{
                const btn = event.target;
                const originalText = btn.textContent;
                const originalBg = btn.style.backgroundColor;
                
                btn.textContent = 'Copied!';
                btn.style.backgroundColor = '#48bb78'; // Green
                btn.style.color = '#ffffff';
                
                setTimeout(() => {{ 
                    btn.textContent = originalText;
                    btn.style.backgroundColor = originalBg;
                    btn.style.color = '';
                }}, 2000);
            }});
        }}
        async function downloadBackup() {{
            window.location.href = '/api/config/backup';
        }}

        async function restoreBackup() {{
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.json';
            
            input.onchange = async (e) => {{
                const file = e.target.files[0];
                if (!file) return;
                
                if (!confirm('This will overwrite your current configuration and restart the server. Are you sure?')) return;
                
                const formData = new FormData();
                formData.append('file', file);
                
                try {{
                    const btn = document.getElementById('restoreBtn');
                    const originalText = btn.textContent;
                    btn.textContent = 'Restoring...';
                    btn.disabled = true;
                    
                    const response = await fetch('/api/config/restore', {{
                        method: 'POST',
                        body: formData
                    }});
                    
                    const result = await response.json();
                    
                    if (response.ok) {{
                        alert(result.message);
                        window.location.reload();
                    }} else {{
                        alert('Restore failed: ' + result.error);
                        btn.textContent = originalText;
                        btn.disabled = false;
                    }}
                }} catch (error) {{
                    console.error('Error restoring config:', error);
                    alert('Error restoring configuration');
                    document.getElementById('restoreBtn').textContent = 'Restore Config';
                    document.getElementById('restoreBtn').disabled = false;
                }}
            }};
            
            input.click();
        }}

        // Tab visibility change handler to reconnect streams
        document.addEventListener('visibilitychange', () => {{
            if (document.visibilityState === 'visible') {{
                console.log('Tab became visible, checking connections...');
                reconnectAllStreams();
            }}
        }});

        function reconnectAllStreams() {{
            // Re-initialize players for all running cameras
            cameras.forEach(cam => {{
                if (cam.status === 'running') {{
                    // initVideoPlayer has a guard to prevent double-init
                    initVideoPlayer(cam.id, cam.pathName);
                }}
            }});
            
            // Also handle matrix view if active
            if (matrixActive) {{
                renderMatrix();
            }}
        }}

        // Global Custom Tooltip System
        (function() {{
            let tooltipEl = null;
            let activeElement = null;
            let showTimeout = null;

            function getTooltipEl() {{
                if (!tooltipEl) {{
                    tooltipEl = document.createElement('div');
                    tooltipEl.className = 'custom-tooltip';
                    document.body.appendChild(tooltipEl);
                }}
                return tooltipEl;
            }}

            document.addEventListener('mouseover', function(e) {{
                const el = e.target.closest('[title]');
                if (!el) return;

                clearTimeout(showTimeout);

                activeElement = el;
                const titleText = el.getAttribute('title');
                
                el.setAttribute('data-title', titleText);
                el.removeAttribute('title');

                showTimeout = setTimeout(() => {{
                    if (activeElement !== el) return;
                    
                    const tooltip = getTooltipEl();
                    tooltip.textContent = titleText;
                    tooltip.classList.add('visible');

                    positionTooltip(el, tooltip);
                }}, 120);
            }});

            document.addEventListener('mouseout', function(e) {{
                const el = e.target.closest('[data-title]');
                if (!el || activeElement !== el) return;

                clearTimeout(showTimeout);
                activeElement = null;

                const titleText = el.getAttribute('data-title');
                el.setAttribute('title', titleText);
                el.removeAttribute('data-title');

                if (tooltipEl) {{
                    tooltipEl.classList.remove('visible');
                }}
            }});

            function positionTooltip(target, tooltip) {{
                const targetRect = target.getBoundingClientRect();
                const tooltipRect = tooltip.getBoundingClientRect();

                let top = window.scrollY + targetRect.top - tooltipRect.height - 8;
                let left = window.scrollX + targetRect.left + (targetRect.width - tooltipRect.width) / 2;

                if (targetRect.top - tooltipRect.height - 8 < 0) {{
                    top = window.scrollY + targetRect.bottom + 8;
                }}

                if (left < 10) {{
                    left = 10;
                }}
                if (left + tooltipRect.width > window.innerWidth - 10) {{
                    left = window.innerWidth - tooltipRect.width - 10;
                }}

                tooltip.style.top = top + 'px';
                tooltip.style.left = left + 'px';
            }}
        }})();

    </script>
</body>
</html>
"""

def get_login_html():
    """Generate Login Page HTML"""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Tonys Onvif-RTSP Server v{CURRENT_VERSION}</title>
    <style>
        :root {{
            --primary-bg: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --card-bg: #ffffff;
            --text-title: #2d3748;
            --text-body: #718096;
            --btn-primary: #667eea;
            --btn-hover: #5a67d8;
            --border: #e2e8f0;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--primary-bg);
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-title);
        }}
        .login-card {{
            background: var(--card-bg);
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            width: 100%;
            max-width: 400px;
            text-align: center;
        }}
        h1 {{ font-size: 24px; margin-bottom: 8px; }}
        p {{ color: var(--text-body); font-size: 14px; margin-bottom: 30px; }}
        .form-group {{ margin-bottom: 20px; text-align: left; }}
        label {{ display: block; font-size: 12px; font-weight: 700; text-transform: uppercase; margin-bottom: 8px; color: var(--text-body); }}
        input[type="text"], input[type="password"] {{
            width: 100%;
            padding: 12px;
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }}
        input:focus {{ border-color: var(--btn-primary); }}
        .checkbox-group {{ display: flex; align-items: center; gap: 8px; margin-bottom: 25px; cursor: pointer; }}
        .btn {{
            width: 100%;
            padding: 14px;
            background: var(--btn-primary);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }}
        .btn:hover {{ background: var(--btn-hover); }}
        .error {{ color: #e53e3e; font-size: 13px; margin-top: 15px; display: none; }}
    </style>
</head>
<body>
    <div class="login-card">
        <h1>Welcome Back</h1>
        <p>Login to manage your ONVIF cameras</p>
        
        <form id="loginForm">
            <div class="form-group">
                <label>Username</label>
                <input type="text" name="username" required>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" required>
            </div>
            <div class="checkbox-group" onclick="document.getElementById('remember').click()">
                <input type="checkbox" id="remember" name="remember">
                <label style="margin-bottom: 0; text-transform: none; cursor: pointer;">Stay logged in for 30 days</label>
            </div>
            <button type="submit" class="btn">Login</button>
        </form>
        <div id="error" class="error"></div>
    </div>

    <script>
        document.getElementById('loginForm').onsubmit = async (e) => {{
            e.preventDefault();
            const formData = new FormData(e.target);
            formData.append('remember', document.getElementById('remember').checked);
            
            const errorDiv = document.getElementById('error');
            errorDiv.style.display = 'none';
            
            try {{
                const res = await fetch('/login', {{
                    method: 'POST',
                    body: formData
                }});
                const data = await res.json();
                if (data.success) {{
                    window.location.href = '/';
                }} else {{
                    errorDiv.textContent = data.error || 'Login failed';
                    errorDiv.style.display = 'block';
                }}
            }} catch (err) {{
                errorDiv.textContent = 'Connection error';
                errorDiv.style.display = 'block';
            }}
        }};
    </script>
</body>
</html>
"""

def get_setup_html():
    """Generate Setup Page HTML"""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Initial Setup - Tonys Onvif-RTSP Server v{CURRENT_VERSION}</title>
    <style>
        :root {{
            --primary-bg: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            --card-bg: #ffffff;
            --text-title: #2d3748;
            --text-body: #718096;
            --btn-primary: #38a169;
            --btn-hover: #2f855a;
            --border: #e2e8f0;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--primary-bg);
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-title);
        }}
        .setup-card {{
            background: var(--card-bg);
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            width: 100%;
            max-width: 450px;
            text-align: center;
        }}
        h1 {{ font-size: 24px; margin-bottom: 8px; }}
        p {{ color: var(--text-body); font-size: 14px; margin-bottom: 30px; }}
        .form-group {{ margin-bottom: 20px; text-align: left; }}
        label {{ display: block; font-size: 12px; font-weight: 700; text-transform: uppercase; margin-bottom: 8px; color: var(--text-body); }}
        input[type="text"], input[type="password"] {{
            width: 100%;
            padding: 12px;
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }}
        input:focus {{ border-color: var(--btn-primary); }}
        .btn {{
            width: 100%;
            padding: 14px;
            background: var(--btn-primary);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }}
        .btn:hover {{ background: var(--btn-hover); }}
        .error {{ color: #e53e3e; font-size: 13px; margin-top: 15px; display: none; }}
        .info-box {{
            background: #f0fff4;
            border: 1px solid #c6f6d5;
            padding: 15px;
            border-radius: 8px;
            font-size: 14px;
            color: #276749;
            margin-bottom: 25px;
            text-align: left;
        }}
    </style>
</head>
<body>
    <div class="setup-card">
        <h1>First-Time Setup</h1>
        <p>Create your administrator account</p>
        
        <div class="info-box">
            This account will be used to access the web interface and manage your cameras.
        </div>

        <form id="setupForm">
            <div class="form-group">
                <label>Admin Username</label>
                <input type="text" name="username" required placeholder="e.g. admin">
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" required placeholder="Choose a strong password">
            </div>
            <div class="form-group">
                <label>Confirm Password</label>
                <input type="password" id="confirm" required placeholder="Re-enter password">
            </div>
            <button type="submit" class="btn">Complete Setup</button>
            <button type="button" onclick="skipSetup()" class="btn" style="background: transparent; color: var(--btn-primary); margin-top: 10px; border: 1px solid var(--btn-primary);">Use Without Login</button>
        </form>
        <div id="error" class="error"></div>
    </div>

    <script>
        async function skipSetup() {{
            if (!confirm('Are you sure? You can always enable login later in the Settings menu.')) return;
            
            try {{
                const res = await fetch('/setup/skip', {{ method: 'POST' }});
                const data = await res.json();
                if (data.success) {{
                    window.location.href = '/';
                }}
            }} catch (err) {{
                alert('Connection error');
            }}
        }}

        document.getElementById('setupForm').onsubmit = async (e) => {{
            e.preventDefault();
            const password = e.target.password.value;
            const confirm = document.getElementById('confirm').value;
            const errorDiv = document.getElementById('error');
            
            errorDiv.style.display = 'none';
            
            if (password !== confirm) {{
                errorDiv.textContent = 'Passwords do not match';
                errorDiv.style.display = 'block';
                return;
            }}
            
            const formData = new FormData(e.target);
            try {{
                const res = await fetch('/setup', {{
                    method: 'POST',
                    body: formData
                }});
                const data = await res.json();
                if (data.success) {{
                    window.location.href = '/';
                }} else {{
                    errorDiv.textContent = data.error || 'Setup failed';
                    errorDiv.style.display = 'block';
                }}
            }} catch (err) {{
                errorDiv.textContent = 'Connection error';
                errorDiv.style.display = 'block';
            }}
        }};
    </script>
</body>
</html>
"""
