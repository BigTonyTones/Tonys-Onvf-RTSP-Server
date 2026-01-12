import json
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
    <title>Tonys Onvif-RTSP Server v{CURRENT_VERSION}</title>
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
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: var(--shadow);
            position: relative;
            width: 100%;
            display: block;
        }}
        .header h1 {{ color: var(--text-title); margin-bottom: 10px; }}
        .header p {{ color: var(--text-body); font-size: 14px; }}
        .actions {{ display: flex; gap: 10px; margin-top: 20px; flex-wrap: wrap; }}
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
            background: #e2e8f0;
            color: #718096;
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
            background: #000;
            z-index: 3000;
            padding: 10px;
            overflow: hidden;
        }}
        .matrix-overlay.active {{ display: flex; flex-direction: column; }}
        
        .matrix-grid {{
            display: grid;
            gap: 8px;
            flex: 1;
            width: 100%;
            height: 100%;
        }}
        
        .matrix-item {{
            position: relative;
            background: #111;
            border: 1px solid #333;
            border-radius: 4px;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
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
            gap: 12px;
            padding: 10px 0;
            background: #000;
        }}
        
        .btn-matrix {{
            background: #4a5568;
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 14px;
            border: none;
            cursor: pointer;
        }}
        .btn-matrix:hover {{ background: #2d3748; }}
        
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div style="position: absolute; top: 15px; right: 15px; display: flex; align-items: center; gap: 15px;">
                <span id="server-stats" style="padding: 6px 10px; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 6px; font-weight: 600; color: var(--text-muted); font-family: monospace; font-size: 11px; white-space: nowrap; box-shadow: var(--shadow-sm);">CPU: ... | MEM: ...</span>
                <div style="display: flex; align-items: center; gap: 8px; padding-left: 15px; border-left: 1px solid var(--card-border);">
                    <span style="font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase;">Theme</span>
                    <select id="themeSwitcher" class="form-input" style="width: auto; padding: 4px 8px; font-size: 13px; cursor: pointer; border-color: var(--card-border);" onchange="changeTheme(this.value)">
                        <option value="classic">Classic</option>
                        <option value="dark">Modern Dark</option>
                        <option value="nord">Nordic</option>
                        <option value="dracula">Dracula (Pro Dark)</option>
                        <option value="solar-light">Solarized</option>
                        <option value="midnight">Midnight</option>
                        <option value="emerald">Emerald</option>
                        <option value="sunset">Sunset</option>
                        <option value="matrix">Matrix</option>
                        <option value="slate">Slate</option>
                        <option value="cyberpunk">Cyberpunk</option>
                        <option value="amoled">Amoled</option>
                    </select>
                </div>
            </div>
            <h1>Tonys Onvif-RTSP Server v{CURRENT_VERSION}</h1>
            <div class="actions">
                <button class="btn btn-primary" onclick="openAddModal()">Add Camera</button>
                <button class="btn btn-primary" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);" onclick="window.location.href='/gridfusion'">GridFusion</button>
                <button class="btn" onclick="startAll()">Start All</button>
                <button class="btn" onclick="stopAll()">Stop All</button>
                <button class="btn" onclick="toggleMatrixView(true)">Matrix View</button>
                <button class="btn" onclick="openSettingsModal()">Settings</button>
                <button class="btn" onclick="restartServer()">Restart Server</button>
                <button class="btn" onclick="openAboutModal()">About</button>
                <button class="btn" onclick="openLogsModal()">Logs</button>
                <button class="btn btn-danger" onclick="stopServer()">Stop Server</button>
                <div style="display: flex; align-items: center; margin-left: 15px; margin-right: 15px; background: rgba(0,0,0,0.2); padding: 5px 12px; border-radius: 20px; border: 1px solid var(--border-color);" title="Use WebRTC for sub-second latency (recommended for PTZ and real-time viewing)">
                    <span style="font-size: 12px; font-weight: 600; margin-right: 8px; color: var(--text-title);">Low Latency</span>
                    <label class="toggle-switch" style="margin: 0; transform: scale(0.8);">
                        <input type="checkbox" id="latencyToggle" onchange="toggleLatencyMode(this.checked)">
                        <span class="toggle-slider"></span>
                    </label>
                </div>
                <div style="display: flex; align-items: center; margin-right: 15px; background: rgba(0,0,0,0.2); padding: 5px 12px; border-radius: 20px; border: 1px solid var(--border-color);" title="Display real-time bitrate, stream status, and active viewer count on camera previews">
                    <span style="font-size: 12px; font-weight: 600; margin-right: 8px; color: var(--text-title);">Bandwidth</span>
                    <label class="toggle-switch" style="margin: 0; transform: scale(0.8);">
                        <input type="checkbox" id="bandwidthToggle" onchange="toggleBandwidth(this.checked)">
                        <span class="toggle-slider"></span>
                    </label>
                </div>
                <a href="/logout" id="logoutBtn" class="btn btn-danger" style="text-decoration: none; display: none;">Logout</a>
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
            <p>© 2026 <a href="https://github.com/BigTonyTones/Tonys-Onvf-RTSP-Server" target="_blank" style="color: inherit; text-decoration: none; font-weight: 600;">Tonys Onvif-RTSP Server v{CURRENT_VERSION}</a> • Created by <a href="https://github.com/BigTonyTones" target="_blank" style="color: inherit; text-decoration: none; font-weight: 600;">Tony</a></p>
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
            <button class="btn-matrix" onclick="toggleFullScreen()">Full Screen</button>
            <button class="btn-matrix" onclick="toggleMatrixView(false)" style="background: #f56565;">Close Matrix</button>
        </div>
        <div id="matrix-grid" class="matrix-grid"></div>
    </div>
    
    <div id="logs-modal" class="modal">
        <div class="modal-content" style="max-width: 1200px; width: 95%;">
            <div class="modal-header">
                <div class="modal-title">Terminal Logs</div>
                <div style="display: flex; gap: 10px;">
                    <button class="btn" onclick="refreshLogs()">Refresh</button>
                    <button class="close-btn" onclick="closeLogsModal()">×</button>
                </div>
            </div>
            <div id="logs-container" style="background: #0d1117; color: #e6f1ff; padding: 20px; border-radius: 8px; font-family: 'Consolas', 'Monaco', 'Courier New', monospace; font-size: 13px; line-height: 1.5; max-height: 600px; overflow-y: auto; white-space: pre-wrap; word-break: break-all; border: 1px solid #30363d;">
                Loading logs...
            </div>
            <div style="margin-top: 15px; display: flex; justify-content: space-between; align-items: center; color: var(--text-muted); font-size: 12px;">
                <span>Total 2,000 lines captured in memory</span>
                <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                    <input type="checkbox" id="autoScrollLogs" checked style="width: auto; cursor: pointer;">
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
            
            <div class="alert alert-warning">
                <strong>Special Characters:</strong><br>
                Passwords with # @ : / etc. are automatically URL-encoded
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
                
                <div class="form-row" style="align-items: flex-start; gap: 24px; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; padding: 24px 0; margin: 24px 0;">
                    <!-- Main Stream Column -->
                    <div class="form-col" style="flex: 1; padding-right: 12px; border-right: 1px solid #e2e8f0;">
                        <h3 style="margin-top: 0; margin-bottom: 16px; color: var(--text-title); font-size: 16px;">Main Stream Settings</h3>
                        
                        <div class="form-group">
                            <label class="form-label">Main Stream Path</label>
                            <input type="text" class="form-input" id="mainPath" placeholder="/stream1" value="/stream1" required>
                        </div>
                        
                        <div class="form-group" style="background: rgba(0,0,0,0.03); padding: 15px; border-radius: 8px;">
                            <div class="auto-start-row" style="margin-bottom: 15px;">
                                <span class="auto-start-label" style="font-size: 13px;">Transcode Main Stream</span>
                                <label class="toggle-switch">
                                    <input type="checkbox" id="transcodeMain">
                                    <span class="toggle-slider"></span>
                                </label>
                            </div>
                            
                            <label class="form-label">Resolution & FPS</label>
                            <div class="form-row" style="margin-bottom: 10px;">
                                <div class="form-group" style="margin-bottom: 0;">
                                    <input type="number" class="form-input" id="mainWidth" placeholder="Width" value="1920" required>
                                </div>
                                <div class="form-group" style="margin-bottom: 0;">
                                    <input type="number" class="form-input" id="mainHeight" placeholder="Height" value="1080" required>
                                </div>
                            </div>
                            <input type="number" class="form-input" id="mainFramerate" placeholder="FPS" value="30" required>
                        </div>
                        
                        <button type="button" class="btn btn-secondary" onclick="fetchStreamInfo('main')" style="width:100%; margin-top: 12px; font-size: 13px;">
                            Fetch Main Stream Info
                        </button>
                    </div>

                    <!-- Sub Stream Column -->
                    <div class="form-col" style="flex: 1; padding-left: 12px;">
                        <h3 style="margin-top: 0; margin-bottom: 16px; color: var(--text-title); font-size: 16px;">Sub Stream Settings</h3>
                        
                        <div class="form-group">
                            <label class="form-label">Sub Stream Path</label>
                            <input type="text" class="form-input" id="subPath" placeholder="/stream2" value="/stream2" required>
                        </div>
                        
                        <div class="form-group" style="background: rgba(0,0,0,0.03); padding: 15px; border-radius: 8px;">
                            <div class="auto-start-row" style="margin-bottom: 15px;">
                                <span class="auto-start-label" style="font-size: 13px;">Transcode Substream</span>
                                <label class="toggle-switch">
                                    <input type="checkbox" id="transcodeSub">
                                    <span class="toggle-slider"></span>
                                </label>
                            </div>
                            
                            <label class="form-label">Resolution & FPS</label>
                            <div class="form-row" style="margin-bottom: 10px;">
                                <div class="form-group" style="margin-bottom: 0;">
                                    <input type="number" class="form-input" id="subWidth" placeholder="Width" value="640" required>
                                </div>
                                <div class="form-group" style="margin-bottom: 0;">
                                    <input type="number" class="form-input" id="subHeight" placeholder="Height" value="480" required>
                                </div>
                            </div>
                            <input type="number" class="form-input" id="subFramerate" placeholder="FPS" value="15" required>
                        </div>
                        
                        <button type="button" class="btn btn-secondary" onclick="fetchStreamInfo('sub')" style="width:100%; margin-top: 12px; font-size: 13px;">
                            Fetch Sub Stream Info
                        </button>
                    </div>
                </div>
                
                <div class="form-group">
                    <label class="form-label">ONVIF Port (leave empty for auto-assign)</label>
                    <input type="number" class="form-input" id="onvifPort" placeholder="Auto-assigned">
                    <small style="color: #718096; font-size: 12px; margin-top: 4px; display: block;">
                        Default: Auto-assigned starting from 8001
                    </small>
                </div>
                
                <div class="form-group">
                    <label class="form-label">Camera UUID (Unique Identifier)</label>
                    <div style="display: flex; gap: 8px;">
                        <input type="text" class="form-input" id="cameraUuid" placeholder="Auto-generated" style="flex: 1;">
                        <button type="button" class="btn btn-secondary" onclick="generateNewUuid()" style="padding: 0 15px;">Generate New</button>
                    </div>
                    <small style="color: #718096; font-size: 12px; margin-top: 4px; display: block;">
                        Used for WS-Discovery and Serial Number. Changing this will make NVRs see it as a new camera.
                    </small>
                </div>
                
                <div class="form-group">
                    <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                        <input type="checkbox" id="autoStart" style="width: auto; cursor: pointer;">
                        <span class="form-label" style="margin: 0;">Auto-start camera on server startup</span>
                    </label>
                </div>

                <!-- Network Settings (Linux only) -->
                <div id="linux-network-section" style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #2d3748;">
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
                            <label class="form-label">Virtual MAC Address</label>
                            <div style="display: flex; gap: 8px;">
                                <input type="text" class="form-input" id="nicMac" placeholder="00:00:00:00:00:00" style="flex: 1;">
                                <button type="button" class="btn btn-secondary" onclick="randomizeMac()" style="padding: 0 15px;">Randomize</button>
                            </div>
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
                
                <div class="alert alert-info">
                    <strong>Common formats:</strong><br>
                    Hikvision: /Streaming/Channels/101<br>
                    Reolink: /h264Preview_01_main<br>
                    Dahua: /cam/realmonitor?channel=1&subtype=0
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
            
            <form onsubmit="saveSettings(event)">
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

                <div class="form-group linux-only">
                    <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                        <input type="checkbox" id="autoBoot" style="width: auto; cursor: pointer;">
                        <span class="form-label" style="margin: 0;">Auto-start on System Boot (Ubuntu Service)</span>
                    </label>
                    <small style="color: #718096; font-size: 12px; margin-top: 4px; display: block;">
                        Creates and enables a systemd service to start this server automatically when the computer turns on.
                    </small>
                </div>

                <div class="form-group" style="margin-top: 15px;">
                    <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;" onclick="toggleAdvancedSettings()">
                        <span class="form-label" style="margin: 0; color: #ffffff; font-weight: 700; display: flex; align-items: center; gap: 5px;">
                            <i class="fas fa-tools"></i> Advanced Settings (MediaMTX & FFmpeg)
                            <i id="advancedChevron" class="fas fa-chevron-down" style="font-size: 12px; transition: transform 0.3s; margin-left: auto;"></i>
                        </span>
                    </label>
                </div>

                <div id="advancedSettingsSection" style="display: none; padding: 20px; background: rgba(0,0,0,0.35); border-radius: 10px; border: 1px solid rgba(255,255,255,0.2); margin-bottom: 25px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.5);">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div>
                            <h3 style="font-size: 14px; margin: 0 0 12px 0; color: #ffffff; border-bottom: 2px solid var(--primary-color); padding-bottom: 6px; display: flex; align-items: center; gap: 8px;">
                                <i class="fas fa-server" style="font-size: 12px; color: var(--primary-color);"></i> MediaMTX Core
                            </h3>
                            <div class="form-group" style="margin-bottom: 12px;">
                                <label class="form-label" style="font-size: 12px; margin-bottom: 4px; color: #ffffff;">Write Queue Size</label>
                                <input type="number" class="form-input" id="mediamtx_writeQueueSize" style="font-size: 13px; padding: 8px 10px; background: rgba(255,255,255,0.05); color: #ffffff;">
                            </div>
                            <div class="form-group" style="margin-bottom: 12px;">
                                <label class="form-label" style="font-size: 12px; margin-bottom: 4px; color: #ffffff;">Read Timeout (duration)</label>
                                <input type="text" class="form-input" id="mediamtx_readTimeout" style="font-size: 13px; padding: 8px 10px; background: rgba(255,255,255,0.05); color: #ffffff;">
                            </div>
                            <div class="form-group" style="margin-bottom: 12px;">
                                <label class="form-label" style="font-size: 12px; margin-bottom: 4px; color: #ffffff;">Write Timeout (duration)</label>
                                <input type="text" class="form-input" id="mediamtx_writeTimeout" style="font-size: 13px; padding: 8px 10px; background: rgba(255,255,255,0.05); color: #ffffff;">
                            </div>
                            <div class="form-group" style="margin-bottom: 12px;">
                                <label class="form-label" style="font-size: 12px; margin-bottom: 4px; color: #ffffff;">UDP Max Payload</label>
                                <input type="number" class="form-input" id="mediamtx_udpMaxPayloadSize" style="font-size: 13px; padding: 8px 10px; background: rgba(255,255,255,0.05); color: #ffffff;">
                            </div>
                        </div>
                        <div>
                            <h3 style="font-size: 14px; margin: 0 0 12px 0; color: #ffffff; border-bottom: 2px solid var(--primary-color); padding-bottom: 6px; display: flex; align-items: center; gap: 8px;">
                                <i class="fas fa-stream" style="font-size: 12px; color: var(--primary-color);"></i> HLS Optimized
                            </h3>
                            <div class="form-group" style="margin-bottom: 12px;">
                                <label class="form-label" style="font-size: 12px; margin-bottom: 4px; color: #ffffff;">Segment Count</label>
                                <input type="number" class="form-input" id="mediamtx_hlsSegmentCount" style="font-size: 13px; padding: 8px 10px; background: rgba(255,255,255,0.05); color: #ffffff;">
                            </div>
                            <div class="form-group" style="margin-bottom: 12px;">
                                <label class="form-label" style="font-size: 12px; margin-bottom: 4px; color: #ffffff;">Segment Duration</label>
                                <input type="text" class="form-input" id="mediamtx_hlsSegmentDuration" style="font-size: 13px; padding: 8px 10px; background: rgba(255,255,255,0.05); color: #ffffff;">
                            </div>
                            <div class="form-group" style="margin-bottom: 12px;">
                                <label class="form-label" style="font-size: 12px; margin-bottom: 4px; color: #ffffff;">Part Duration</label>
                                <input type="text" class="form-input" id="mediamtx_hlsPartDuration" style="font-size: 13px; padding: 8px 10px; background: rgba(255,255,255,0.05); color: #ffffff;">
                            </div>
                        </div>
                    </div>

                    <h3 style="font-size: 14px; margin: 20px 0 12px 0; color: #ffffff; border-bottom: 2px solid var(--primary-color); padding-bottom: 6px; display: flex; align-items: center; gap: 8px;">
                        <i class="fas fa-video" style="font-size: 12px; color: var(--primary-color);"></i> FFmpeg Transcoding Global
                    </h3>
                    <div class="form-group" style="margin-bottom: 12px;">
                        <label class="form-label" style="font-size: 12px; margin-bottom: 4px; color: #ffffff;">Global Arguments (Flags)</label>
                        <input type="text" class="form-input" id="ffmpeg_globalArgs" style="font-size: 13px; padding: 10px; font-family: 'Consolas', monospace; background: #1a202c; color: #ffffff;">
                    </div>
                    <div class="form-group" style="margin-bottom: 12px;">
                        <label class="form-label" style="font-size: 12px; margin-bottom: 4px; color: #ffffff;">Input Arguments (Before -i)</label>
                        <input type="text" class="form-input" id="ffmpeg_inputArgs" style="font-size: 13px; padding: 10px; font-family: 'Consolas', monospace; background: #1a202c; color: #ffffff;">
                    </div>
                    <div class="form-group" style="margin-bottom: 12px;">
                        <label class="form-label" style="font-size: 12px; margin-bottom: 4px; color: #ffffff;">Process & Codec Arguments</label>
                        <input type="text" class="form-input" id="ffmpeg_processArgs" style="font-size: 13px; padding: 10px; font-family: 'Consolas', monospace; background: #1a202c; color: #ffffff;">
                    </div>

                    <div style="background: rgba(237, 137, 54, 0.1); border-left: 3px solid #ed8936; padding: 10px; margin-top: 15px; border-radius: 4px;">
                        <small style="color: #f6ad55; font-size: 11px; font-weight: 600; display: block;">
                            <i class="fas fa-exclamation-triangle"></i> Note: MediaMTX will restart automatically to apply these changes. Incorrect FFmpeg arguments may cause camera streams to fail.
                        </small>
                    </div>
                    <div style="margin-top: 20px; display: flex; justify-content: flex-end;">
                        <button type="button" class="btn btn-primary" style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.3); font-size: 11px; padding: 6px 14px; color: #ffffff;" onclick="resetAdvancedSettings()">
                            <i class="fas fa-undo"></i> Reset to Defaults
                        </button>
                    </div>
                </div>

                <div style="margin: 20px 0; padding-top: 15px; border-top: 1px solid var(--border-color);">
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
                
                <!-- System Updates -->
                <div style="margin: 20px 0; padding-top: 15px; border-top: 1px solid var(--border-color);">
                    <div style="font-size: 14px; font-weight: 600; color: var(--text-title); margin-bottom: 10px;">System Updates</div>
                    <button type="button" class="btn btn-secondary" onclick="checkForUpdates()" style="width:100%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-color: #667eea; color: white; font-weight: 600;">
                        <i class="fas fa-sync-alt"></i> Check for Updates
                    </button>
                </div>
                
                <button type="submit" class="btn btn-success" style="width:100%">Save Settings</button>
                
                <!-- Reboot Server Button (Linux Only) -->
                <button type="button" class="btn linux-only" onclick="rebootServer()" style="width:100%; margin-top: 15px; background: linear-gradient(135deg, #e53e3e 0%, #c53030 100%); border-color: #c53030; color: white; font-weight: 600;">
                    <i class="fas fa-power-off"></i> Reboot Server
                </button>
            </form>
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
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 12px;">
                        <div style="background: rgba(0,0,0,0.2); padding: 10px; border-radius: 6px;">
                            <div style="color: var(--text-muted); margin-bottom: 4px;">MediaMTX Version</div>
                            <div id="about-mediamtx-version" style="color: var(--text-title); font-weight: 600; font-family: monospace;">Loading...</div>
                        </div>
                        <div style="background: rgba(0,0,0,0.2); padding: 10px; border-radius: 6px;">
                            <div style="color: var(--text-muted); margin-bottom: 4px;">FFmpeg Version</div>
                            <div id="about-ffmpeg-version" style="color: var(--text-title); font-weight: 600; font-family: monospace;">Loading...</div>
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
                    
                    <button class="btn btn-secondary" onclick="reinstallCurrentVersion()" style="width:100%; margin-top: 10px; background: var(--toggle-bg); border-color: var(--border-color); color: var(--text-body);">
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
                    
                    <button class="btn btn-secondary" onclick="reinstallCurrentVersion()" style="background: var(--toggle-bg); border-color: var(--border-color); color: var(--text-body);">
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
        window.addEventListener('DOMContentLoaded', () => {{
            if (!isLinux) {{
                const linuxSections = document.querySelectorAll('.linux-only');
                linuxSections.forEach(s => s.style.display = 'none');
                
                // Legacy support for specific ID
                const linuxSection = document.getElementById('linux-network-section');
                if (linuxSection) linuxSection.style.display = 'none';
            }}
        }});

        let logInterval = null;

        function openLogsModal() {{
            document.getElementById('logs-modal').classList.add('active');
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
                    const cleanLogs = data.logs.replace(/\u001b\\[[0-9;]*[a-zA-Z]/g, '');
                    
                    container.textContent = cleanLogs || "No logs available.";
                    
                    if (document.getElementById('autoScrollLogs').checked) {{
                        container.scrollTop = container.scrollHeight;
                    }}
                }}
            }} catch (error) {{
                console.error('Error fetching logs:', error);
            }}
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
                    // New camera
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

                        // Always update info section to ensure IP is correct
                        // This is safe because it doesn't affect the video player (video-preview div)
                        const newInfoContent = getCameraCardContent(cam, serverIp);
                        const tempDiv = document.createElement('div');
                        tempDiv.innerHTML = newInfoContent;
                        card.querySelector('.info-section').innerHTML = tempDiv.querySelector('.info-section').innerHTML;
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

        function toggleMatrixView(active) {{
            matrixActive = active;
            const overlay = document.getElementById('matrix-overlay');
            if (active) {{
                overlay.classList.add('active');
                renderMatrix();
            }} else {{
                overlay.classList.remove('active');
                // Stop any video players in matrix
                const grid = document.getElementById('matrix-grid');
                if (grid) {{
                    const players = grid.querySelectorAll('video');
                    players.forEach(el => destroyPlayer(el.id));
                    grid.innerHTML = '';
                }}
            }}
        }}

        function renderMatrix() {{
            const grid = document.getElementById('matrix-grid');
            const runningCameras = cameras.filter(c => c.status === 'running');
            
            if (runningCameras.length === 0) {{
                grid.innerHTML = '<div style="color: white; grid-column: 1/-1; text-align: center; padding-top: 100px;">No cameras are currently running.</div>';
                return;
            }}
            
            const count = runningCameras.length;
            let cols = 1;
            if (count > 9) cols = 4;
            else if (count > 4) cols = 3;
            else if (count > 1) cols = 2;
            
            grid.style.gridTemplateColumns = `repeat(${{cols}}, 1fr)`;
            
            // Check if we need to re-render
            const currentMatrixIds = Array.from(grid.querySelectorAll('.matrix-item')).map(el => el.dataset.id).join(',');
            const newMatrixIds = runningCameras.map(c => c.id).join(',');
            
            if (currentMatrixIds === newMatrixIds) return;
            
            // Cleanup existing players before re-rendering
            grid.querySelectorAll('video').forEach(el => destroyPlayer(el.id));
            
            grid.innerHTML = runningCameras.map(cam => `
                <div class="matrix-item" data-id="${{cam.id}}">
                    <div class="matrix-label">${{cam.name}}</div>
                    <video id="matrix-player-${{cam.id}}" autoplay muted playsinline></video>
                </div>
            `).join('');
            
            runningCameras.forEach(cam => {{
                initVideoPlayer(cam.id, cam.pathName, `matrix-player-${{cam.id}}`);
            }});
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
        }});

        function getCameraCardContent(cam, serverIp) {{
            const displayIp = cam.assignedIp || serverIp;
            return `
                <div class="camera-header">
                    <div class="camera-title" style="flex-direction: column; align-items: flex-start; gap: 4px;">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <div class="status-badge ${{cam.status === 'running' ? 'running' : ''}}"></div>
                            <div class="camera-name">${{cam.name}}</div>
                        </div>
                        <div style="display: flex; align-items: center; gap: 8px; margin-left: 24px;">
                            ${{cam.assignedIp ? `<div class="status-badge running" style="width: auto; height: auto; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600;">${{cam.assignedIp}}</div>` : ''}}
                            ${{cam.useVirtualNic && cam.nicMac ? `<div style="padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; background: var(--text-muted); color: white; white-space: nowrap;">${{cam.nicMac}}</div>` : ''}}
                        </div>
                        <div style="margin-left: 24px; margin-top: 4px;">
                            <div style="padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; background: #764ba2; color: white; width: fit-content; white-space: nowrap; font-family: monospace;" title="${{cam.uuid}}">UUID: ${{cam.uuid}}</div>
                        </div>
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
                
                <div class="video-preview" id="video-${{cam.id}}">
                    <div id="metrics-${{cam.id}}" class="metrics-overlay"></div>
                    ${{cam.status === 'running' 
                        ? `<video id="player-${{cam.id}}" autoplay muted playsinline></video>
                           <button class="fullscreen-btn" onclick="toggleFullScreenPlayer(${{cam.id}})" title="Maximize">Full Screen</button>`
                        : `<div class="video-placeholder">
                            <div style="font-size: 48px;"></div>
                            <div>Camera Stopped</div>
                           </div>`
                    }}

                </div>
                
                <div class="info-section">
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
                
                const whepUrl = `http://${{serverIp}}:8889/${{pathName}}_sub/whep`;
                
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
                        showVideoError(cameraId, 'WebRTC Disconnected');
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
            
            // Construct stream URL - Use current protocol if possible to support reverse proxies
            const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
            const streamUrl = `http://${{serverIp}}:8888/${{pathName}}_sub/index.m3u8${{credentials}}`;
            
            if (videoElement.canPlayType('application/vnd.apple.mpegurl')) {{
                // Native HLS support (Safari)
                videoElement.src = streamUrl;
            }} else if (typeof Hls !== 'undefined') {{
                // Optimized HLS.js configuration for multiple cameras
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
                
            }} else {{
                showVideoError(cameraId, 'HLS not supported in this browser');
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
                document.getElementById('onvifUsername').value = camera.onvifUsername || 'admin';
                document.getElementById('onvifPassword').value = camera.onvifPassword || 'admin';
                
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
            document.getElementById('modal-title').textContent = 'Add New Camera';
            document.getElementById('camera-id').value = '';
            document.getElementById('camera-form').reset();
            
            document.getElementById('transcodeSub').checked = false;
            document.getElementById('transcodeMain').checked = false;
            
            // Network reset
            document.getElementById('useVirtualNic').checked = false;
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
            document.getElementById('camera-modal').classList.add('active');
        }}
        
        async function openEditModal(id) {{
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
            
            // Populate resolution and frame rate fields
            document.getElementById('mainWidth').value = camera.mainWidth || 1920;
            document.getElementById('mainHeight').value = camera.mainHeight || 1080;
            document.getElementById('subWidth').value = camera.subWidth || 640;
            document.getElementById('subHeight').value = camera.subHeight || 480;
            document.getElementById('mainFramerate').value = camera.mainFramerate || 30;
            document.getElementById('subFramerate').value = camera.subFramerate || 15;
            document.getElementById('transcodeSub').checked = camera.transcodeSub || false;
            document.getElementById('transcodeMain').checked = camera.transcodeMain || false;
            document.getElementById('onvifPort').value = camera.onvifPort || '';
            document.getElementById('cameraUuid').value = camera.uuid || '';
            
            // Populate Network fields
            document.getElementById('useVirtualNic').checked = camera.useVirtualNic || false;
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
            
            document.getElementById('camera-modal').classList.add('active');
        }}
        
        function closeModal() {{
            document.getElementById('camera-modal').classList.remove('active');
            document.getElementById('camera-form').reset();
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
                mainWidth: parseInt(document.getElementById('mainWidth').value),
                mainHeight: parseInt(document.getElementById('mainHeight').value),
                subWidth: parseInt(document.getElementById('subWidth').value),
                subHeight: parseInt(document.getElementById('subHeight').value),
                mainFramerate: parseInt(document.getElementById('mainFramerate').value),
                subFramerate: parseInt(document.getElementById('subFramerate').value),
                transcodeSub: document.getElementById('transcodeSub').checked,
                transcodeMain: document.getElementById('transcodeMain').checked,
                useVirtualNic: document.getElementById('useVirtualNic').checked,
                parentInterface: document.getElementById('parentInterface').value === "__manual__" 
                    ? document.getElementById('parentInterfaceManual').value 
                    : document.getElementById('parentInterface').value,
                nicMac: document.getElementById('nicMac').value,
                ipMode: document.getElementById('ipMode').value,
                staticIp: document.getElementById('staticIp').value,
                netmask: document.getElementById('netmask').value,
                gateway: document.getElementById('gateway').value,
                uuid: document.getElementById('cameraUuid').value || null
            }};
            
            // Add ONVIF port if specified
            const onvifPort = document.getElementById('onvifPort').value;
            if (onvifPort) {{
                data.onvifPort = parseInt(onvifPort);
            }}
            
            try {{
                const url = isEdit ? `/api/cameras/${{cameraId}}` : '/api/cameras';
                const method = isEdit ? 'PUT' : 'POST';
                
                const response = await fetch(url, {{
                    method: method,
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify(data)
                }});
                
                if (response.ok) {{
                    closeModal();
                    await loadData();
                }} else {{
                    const error = await response.json();
                    alert('Error saving camera: ' + (error.error || 'Unknown error'));
                }}
            }} catch (error) {{
                console.error('Error saving camera:', error);
                alert('Error saving camera');
            }} finally {{
                btn.disabled = false;
                btn.innerHTML = originalText;
            }}
        }}
        
        async function deleteCamera(id) {{
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
        
        
        function toggleAuthFields() {{
            const enabled = document.getElementById('authEnabled').checked;
            document.getElementById('auth-settings-fields').style.display = enabled ? 'block' : 'none';
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
            try {{
                const response = await fetch('/api/server/restart', {{method: 'POST'}});
                if (response.ok) {{
                    alert('Server is restarting... The page will reload in 10 seconds.');
                    // Reload page after 10 seconds to reconnect
                    setTimeout(() => {{
                        window.location.reload();
                    }}, 10000);
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
                const response = await fetch('/api/server/stop', {{method: 'POST'}});
                if (response.ok) {{
                    // Show a message since the server will be down
                    document.body.innerHTML = '<div style=\"display: flex; align-items: center; justify-content: center; height: 100vh; font-family: sans-serif; flex-direction: column; background: #000; color: #fff;\"><h1>Server Stopped</h1><p>The ONVIF server has been shut down successfully.</p><p style=\"color: #718096; margin-top: 20px;\">You can safely close this browser tab.</p></div>';
                }} else {{
                    alert('Failed to stop server');
                }}
            }} catch (error) {{
                // Expected error since server is shutting down
                document.body.innerHTML = '<div style=\"display: flex; align-items: center; justify-content: center; height: 100vh; font-family: sans-serif; flex-direction: column; background: #000; color: #fff;\"><h1>Server Stopped</h1><p>The ONVIF server has been shut down successfully.</p><p style=\"color: #718096; margin-top: 20px;\">You can safely close this browser tab.</p></div>';
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
                    if (browserField) browserField.checked = settings.openBrowser !== false;
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

                    // Load Advanced Settings
                    if (settings.advancedSettings) {{
                        const adv = settings.advancedSettings;
                        if (adv.mediamtx) {{
                            document.getElementById('mediamtx_writeQueueSize').value = adv.mediamtx.writeQueueSize || 4096;
                            document.getElementById('mediamtx_readTimeout').value = adv.mediamtx.readTimeout || '30s';
                            document.getElementById('mediamtx_writeTimeout').value = adv.mediamtx.writeTimeout || '30s';
                            document.getElementById('mediamtx_udpMaxPayloadSize').value = adv.mediamtx.udpMaxPayloadSize || 1472;
                            document.getElementById('mediamtx_hlsSegmentCount').value = adv.mediamtx.hlsSegmentCount || 10;
                            document.getElementById('mediamtx_hlsSegmentDuration').value = adv.mediamtx.hlsSegmentDuration || '1s';
                            document.getElementById('mediamtx_hlsPartDuration').value = adv.mediamtx.hlsPartDuration || '200ms';
                        }}
                        if (adv.ffmpeg) {{
                            document.getElementById('ffmpeg_globalArgs').value = adv.ffmpeg.globalArgs || '';
                            document.getElementById('ffmpeg_inputArgs').value = adv.ffmpeg.inputArgs || '';
                            document.getElementById('ffmpeg_processArgs').value = adv.ffmpeg.processArgs || '';
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
        }}
        
        async function fetchSystemVersions() {{
            try {{
                const response = await fetch('/api/system/versions');
                if (response.ok) {{
                    const data = await response.json();
                    document.getElementById('about-mediamtx-version').textContent = data.mediamtx || 'Unknown';
                    document.getElementById('about-ffmpeg-version').textContent = data.ffmpeg || 'Not installed';
                }} else {{
                    document.getElementById('about-mediamtx-version').textContent = 'Error';
                    document.getElementById('about-ffmpeg-version').textContent = 'Error';
                }}
            }} catch (error) {{
                console.error('Failed to fetch system versions:', error);
                document.getElementById('about-mediamtx-version').textContent = 'Error';
                document.getElementById('about-ffmpeg-version').textContent = 'Error';
            }}
        }}
        
        function closeSettingsModal() {{
            document.getElementById('settings-modal').classList.remove('active');
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
                advancedSettings: {{
                    mediamtx: {{
                        writeQueueSize: parseInt(document.getElementById('mediamtx_writeQueueSize').value),
                        readTimeout: document.getElementById('mediamtx_readTimeout').value,
                        writeTimeout: document.getElementById('mediamtx_writeTimeout').value,
                        udpMaxPayloadSize: parseInt(document.getElementById('mediamtx_udpMaxPayloadSize').value),
                        hlsSegmentCount: parseInt(document.getElementById('mediamtx_hlsSegmentCount').value),
                        hlsSegmentDuration: document.getElementById('mediamtx_hlsSegmentDuration').value,
                        hlsPartDuration: document.getElementById('mediamtx_hlsPartDuration').value
                    }},
                    ffmpeg: {{
                        globalArgs: document.getElementById('ffmpeg_globalArgs').value,
                        inputArgs: document.getElementById('ffmpeg_inputArgs').value,
                        processArgs: document.getElementById('ffmpeg_processArgs').value,
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
        
        async function rebootServer() {{
            if (!confirm('This will reboot the entire server. The system will be unavailable for a few minutes. Continue?')) {{
                return;
            }}
            
            try {{
                const response = await fetch('/api/server/reboot', {{method: 'POST'}});
                if (response.ok) {{
                    alert('Server is rebooting... The system will be back online in a few minutes.');
                    closeSettingsModal();
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
                
                // Update global server stats
                if (stats.cpu_percent !== undefined) {{
                    let totalBitrate = 0;
                    Object.values(analytics).forEach(a => totalBitrate += (a.bitrate || 0));
                    
                    document.getElementById('server-stats').innerHTML = 
                        `CPU: ${{stats.cpu_percent}}% • MEM: ${{stats.memory_mb}}MB • NET: ${{totalBitrate.toFixed(1)}} kbps`;
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
                        const statusClass = mainStats.stale ? 'warn' : (mainStats.ready ? 'live' : 'error');
                        html += `
                            <div class="metric-badge ${{statusClass}}" title="${{mainStats.stale ? 'Stream Stalled' : 'Main Stream Status'}}" style="min-width: 95px; justify-content: center;">
                                MAIN: ${{mainStats.bitrate.toFixed(0)}}
                            </div>
                        `;
                    }}
                    
                    if (subStats) {{
                        const statusClass = subStats.stale ? 'warn' : (subStats.ready ? 'live' : 'error');
                        const viewers = subStats.readers || 0;
                        html += `
                            <div class="metric-badge ${{statusClass}}" title="${{subStats.stale ? 'Stream Stalled' : 'Sub Stream Status'}}" style="min-width: 85px; justify-content: center;">
                                SUB: ${{subStats.bitrate.toFixed(0)}}
                            </div>
                            <div class="metric-badge ${{viewers > 0 ? 'live' : ''}}" title="Active Viewers" style="min-width: 40px; justify-content: center;">
                                <i class="fas fa-users"></i> ${{viewers}}
                            </div>
                        `;
                    }}
                    
                    metricsEl.innerHTML = html;
                }});
                
            }} catch (e) {{
                console.error("Stats fetch failed:", e);
            }}
        }}
        
        function applyTheme(theme) {{
            // Remove all possible theme classes
            const themes = ['dark', 'nord', 'dracula', 'solar-light', 'midnight', 'emerald', 'sunset', 'matrix', 'slate', 'cyberpunk', 'amoled'];
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
