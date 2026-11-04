"""
System Logs page: the captured terminal output on its own full page.
"""


def get_logs_html(theme=''):
    from .theme_css import APP_THEME_CSS, body_theme_class
    theme_class = body_theme_class(theme)

    html = r'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>System Logs - Tonys Onvif-RTSP-AI Server</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html, body { height: 100%; }
        body {
            font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--rf-bg, #111214);
            color: var(--rf-text, #f0f2f5);
            overflow: hidden;
        }

        /* The page fills everything below the top bar and right of the rail */
        .logs-page {
            position: fixed;
            top: var(--rf-top-h, 0px);
            left: var(--rf-rail-w, 0px);
            right: 0;
            bottom: 0;
            display: flex;
            flex-direction: column;
            gap: 10px;
            padding: 12px 18px 16px;
            background: var(--rf-bg, #111214);
        }

        .logs-toolbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            flex-wrap: wrap;
            flex-shrink: 0;
        }
        .logs-heading { display: flex; align-items: baseline; gap: 12px; min-width: 0; }
        .logs-heading h2 { font-size: 16px; font-weight: 600; color: var(--rf-text, #f0f2f5); white-space: nowrap; }
        .logs-heading .logs-sub { font-size: 12.5px; color: var(--rf-text-3, #888e99); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .logs-live-dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #22c55e; margin-right: 6px; vertical-align: 1px; }
        .logs-live-dot.paused { background: #f59e0b; }

        .logs-controls { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
        .logs-btn {
            display: inline-flex; align-items: center; gap: 6px;
            height: 30px; padding: 0 11px;
            font: inherit; font-size: 12.5px; font-weight: 500;
            color: var(--rf-text, #f0f2f5);
            background: var(--rf-surface, #18191b);
            border: 1px solid var(--rf-border-strong, rgba(255,255,255,0.14));
            border-radius: 6px;
            cursor: pointer;
            white-space: nowrap;
        }
        .logs-btn:hover { background: var(--rf-surface-2, #1e1f22); }
        .logs-btn i { font-size: 12px; color: var(--rf-text-2, #b6bac2); }
        .logs-check { display: inline-flex; align-items: center; gap: 7px; font-size: 12.5px; font-weight: 500; color: var(--rf-text-2, #b6bac2); cursor: pointer; user-select: none; }
        .logs-check input { width: 14px; height: 14px; cursor: pointer; accent-color: var(--rf-accent, #3b82f6); }
        .logs-size {
            display: inline-flex; align-items: center; height: 30px;
            border: 1px solid var(--rf-border-strong, rgba(255,255,255,0.14));
            border-radius: 6px; overflow: hidden; background: var(--rf-surface, #18191b);
        }
        .logs-size button { width: 28px; height: 100%; border: 0; background: transparent; color: var(--rf-text, #f0f2f5); font-size: 14px; cursor: pointer; }
        .logs-size button:hover { background: var(--rf-surface-2, #1e1f22); }
        .logs-size span { min-width: 44px; text-align: center; font-size: 12px; font-weight: 600; color: var(--rf-text-2, #b6bac2); }
        .logs-filter {
            height: 30px; width: 190px; padding: 0 10px;
            font: inherit; font-size: 12.5px;
            color: var(--rf-text, #f0f2f5);
            background: var(--rf-surface, #18191b);
            border: 1px solid var(--rf-border-strong, rgba(255,255,255,0.14));
            border-radius: 6px; outline: none;
        }
        .logs-filter:focus { border-color: var(--rf-accent, #3b82f6); }

        /* "Hide AI" menu */
        .logs-hide { position: relative; }
        .logs-hide .logs-btn.on { border-color: var(--rf-accent, #3b82f6); }
        .logs-hide-count { display: none; min-width: 17px; height: 17px; padding: 0 5px; border-radius: 9px; background: var(--rf-accent, #3b82f6); color: #fff; font-size: 10.5px; font-weight: 700; line-height: 17px; text-align: center; }
        .logs-hide .logs-btn.on .logs-hide-count { display: inline-block; }
        .logs-hide-menu {
            display: none; position: absolute; top: calc(100% + 6px); right: 0; z-index: 50;
            width: 290px; padding: 6px;
            background: var(--rf-surface, #18191b);
            border: 1px solid var(--rf-border-strong, rgba(255,255,255,0.14));
            border-radius: 8px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.18);
        }
        .logs-hide.open .logs-hide-menu { display: block; }
        .logs-hide-head { display: flex; justify-content: space-between; align-items: center; padding: 6px 8px 8px; font-size: 11.5px; font-weight: 600; color: var(--rf-text-3, #888e99); text-transform: uppercase; letter-spacing: 0.04em; }
        .logs-hide-head button { border: 0; background: none; color: var(--rf-accent, #3b82f6); font: inherit; font-size: 12px; text-transform: none; letter-spacing: 0; cursor: pointer; padding: 0; }
        .logs-hide-item { display: flex; align-items: flex-start; gap: 10px; padding: 7px 8px; border-radius: 6px; cursor: pointer; }
        .logs-hide-item:hover { background: var(--rf-surface-2, #1e1f22); }
        .logs-hide-item input { margin-top: 2px; width: 14px; height: 14px; accent-color: var(--rf-accent, #3b82f6); cursor: pointer; flex-shrink: 0; }
        .logs-hide-item b { display: block; font-size: 13px; font-weight: 500; color: var(--rf-text, #f0f2f5); }
        .logs-hide-item small { display: block; font-size: 11.5px; color: var(--rf-text-3, #888e99); margin-top: 1px; }

        /* The black terminal takes the rest of the page */
        #logs-container {
            flex: 1 1 auto;
            min-height: 0;
            overflow: auto;
            background: #0a0c10;
            color: #e6edf3;
            border: 1px solid #1f242c;
            border-radius: 8px;
            padding: 16px 20px;
            font-family: 'Cascadia Mono', Consolas, 'SF Mono', Monaco, 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.55;
            white-space: pre-wrap;
            overflow-wrap: anywhere;
            box-shadow: 0 1px 2px rgba(0,0,0,0.12);
        }
        #logs-container::-webkit-scrollbar { width: 12px; height: 12px; }
        #logs-container::-webkit-scrollbar-thumb { background: #2b313b; border-radius: 6px; border: 3px solid #0a0c10; }
        #logs-container::-webkit-scrollbar-track { background: transparent; }
        #logs-container mark { background: #f1fa8c; color: #0a0c10; border-radius: 2px; }
        .logs-footer { display: flex; justify-content: space-between; gap: 12px; flex-shrink: 0; font-size: 12px; color: var(--rf-text-3, #888e99); }

        @media (max-width: 760px) {
            .logs-page { left: 0; bottom: 70px; padding: 10px 10px 10px; }
            .logs-heading .logs-sub, .logs-footer span:last-child { display: none; }
            .logs-filter { width: 130px; }
            .logs-hide-menu { position: fixed; top: auto; left: 10px; right: 10px; bottom: 78px; width: auto; }
        }
    </style>
</head>
<body>
    <main class="logs-page">
        <div class="logs-toolbar">
            <div class="logs-heading">
                <h2>System Logs</h2>
                <span class="logs-sub"><span class="logs-live-dot" id="logsLiveDot"></span><span id="logsLiveText">Live, refreshing every 3 seconds</span></span>
            </div>
            <div class="logs-controls">
                <input type="search" class="logs-filter" id="logsFilter" placeholder="Filter lines..." autocomplete="off">
                <div class="logs-hide" id="logsHide">
                    <button type="button" class="logs-btn" id="logsHideBtn" aria-haspopup="true" aria-expanded="false"><i class="fa-solid fa-eye-slash"></i><span>Hide AI</span><span class="logs-hide-count" id="logsHideCount"></span></button>
                    <div class="logs-hide-menu" id="logsHideMenu">
                        <div class="logs-hide-head"><span>Hide these lines</span><button type="button" id="logsHideAll">Hide all</button></div>
                    </div>
                </div>
                <label class="logs-check"><input type="checkbox" id="autoScrollLogs"> Auto-scroll</label>
                <div class="logs-size" title="Font size">
                    <button type="button" onclick="adjustLogFontSize(-1)" aria-label="Smaller text">&minus;</button>
                    <span id="logFontSizeDisplay">14px</span>
                    <button type="button" onclick="adjustLogFontSize(1)" aria-label="Bigger text">+</button>
                </div>
                <button type="button" class="logs-btn" id="logsPauseBtn" onclick="togglePause()"><i class="fa-solid fa-pause"></i><span>Pause</span></button>
                <button type="button" class="logs-btn" onclick="copyLogs()"><i class="fa-regular fa-copy"></i><span id="logsCopyLabel">Copy</span></button>
                <button type="button" class="logs-btn" onclick="downloadLogs()"><i class="fa-solid fa-download"></i><span>Download</span></button>
                <button type="button" class="logs-btn" onclick="refreshLogs()"><i class="fa-solid fa-rotate"></i><span>Refresh</span></button>
            </div>
        </div>
        <div id="logs-container">Loading logs...</div>
        <div class="logs-footer">
            <span id="logsLineCount"></span>
            <span id="logsKeepNote">The server keeps the newest <b id="logsKeepN">10,000</b> lines. <a href="/#settings" style="color: inherit;">Change in Settings</a></span>
        </div>
    </main>

    <script>
        var logInterval = null;
        var paused = false;
        var lastRaw = null;
        var logFontSize = parseInt(safeGet('logFontSize'), 10) || 14;
        var autoScroll = document.getElementById('autoScrollLogs');
        var container = document.getElementById('logs-container');
        var filterBox = document.getElementById('logsFilter');

        function safeGet(k) { try { return localStorage.getItem(k); } catch (_) { return null; } }
        function safeSet(k, v) { try { localStorage.setItem(k, v); } catch (_) {} }

        autoScroll.checked = safeGet('logAutoScroll') !== '0';
        autoScroll.addEventListener('change', function () {
            safeSet('logAutoScroll', autoScroll.checked ? '1' : '0');
            if (autoScroll.checked) container.scrollTop = container.scrollHeight;
        });

        function applyLogFontSize() {
            container.style.fontSize = logFontSize + 'px';
            document.getElementById('logFontSizeDisplay').textContent = logFontSize + 'px';
        }
        function adjustLogFontSize(direction) {
            logFontSize = Math.max(10, Math.min(32, logFontSize + direction));
            safeSet('logFontSize', logFontSize);
            applyLogFontSize();
        }

        // Groups of AI messages that can be hidden from the "Hide AI" menu.
        // A line goes in the first group that matches it.
        var AI_GROUPS = [
            { id: 'errors',  label: 'AI errors',            hint: 'Model load, inference and plate-reading failures',
              re: /\[AI[^\]]*Error\]|\[AI Camera \([^)]*\)\] (Error in inference|AI disabled|.*\berror:)/ },
            { id: 'events',  label: 'AI detections',        hint: '"AI Event" lines for every person, car, etc.',
              re: /\[AI Camera \([^)]*\)\] (AI Event:|User triggered test)/ },
            { id: 'lpr',     label: 'License plate reading', hint: 'EasyOCR / LPR messages',
              re: /\[AI LPR/ },
            { id: 'alerts',  label: 'AI Alerts',            hint: 'Alert snapshots and alert settings',
              re: /\[AI Alerts\]/ },
            { id: 'onvif',   label: 'ONVIF event forwarding', hint: 'Events sent to or read from ONVIF cameras and NVRs',
              re: /\[ONVIF Event/ },
            { id: 'status',  label: 'AI status and setup',  hint: 'Model loading, threads, zones, stream connects',
              re: /\[AI Camera|\[AI\]|\[Camera \([^)]*\)\] Local AI|AI dependencies/ }
        ];
        var hiddenGroups = {};
        try { (JSON.parse(safeGet('logHiddenAi') || '[]') || []).forEach(function (id) { hiddenGroups[id] = true; }); } catch (_) {}

        function aiGroupOf(line) {
            for (var i = 0; i < AI_GROUPS.length; i++) if (AI_GROUPS[i].re.test(line)) return AI_GROUPS[i].id;
            return null;
        }

        (function buildHideMenu() {
            var wrap = document.getElementById('logsHide');
            var btn = document.getElementById('logsHideBtn');
            var menu = document.getElementById('logsHideMenu');
            var allBtn = document.getElementById('logsHideAll');
            AI_GROUPS.forEach(function (g) {
                var row = document.createElement('label');
                row.className = 'logs-hide-item';
                row.innerHTML = '<input type="checkbox"><span><b></b><small></small></span>';
                row.querySelector('b').textContent = g.label;
                row.querySelector('small').textContent = g.hint;
                var cb = row.querySelector('input');
                cb.checked = !!hiddenGroups[g.id];
                cb.dataset.group = g.id;
                cb.addEventListener('change', function () {
                    if (cb.checked) hiddenGroups[g.id] = true; else delete hiddenGroups[g.id];
                    saveHidden();
                });
                menu.appendChild(row);
            });
            allBtn.addEventListener('click', function () {
                var hideAll = Object.keys(hiddenGroups).length < AI_GROUPS.length;
                hiddenGroups = {};
                if (hideAll) AI_GROUPS.forEach(function (g) { hiddenGroups[g.id] = true; });
                menu.querySelectorAll('input[data-group]').forEach(function (cb) { cb.checked = hideAll; });
                saveHidden();
            });
            function saveHidden() {
                safeSet('logHiddenAi', JSON.stringify(Object.keys(hiddenGroups)));
                syncHideButton();
                render();
            }
            btn.addEventListener('click', function (e) {
                e.stopPropagation();
                var on = !wrap.classList.contains('open');
                wrap.classList.toggle('open', on);
                btn.setAttribute('aria-expanded', on ? 'true' : 'false');
            });
            document.addEventListener('click', function (e) { if (!wrap.contains(e.target)) { wrap.classList.remove('open'); btn.setAttribute('aria-expanded', 'false'); } });
            document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { wrap.classList.remove('open'); btn.setAttribute('aria-expanded', 'false'); } });
            syncHideButton();
        })();

        function syncHideButton() {
            var n = Object.keys(hiddenGroups).length;
            document.getElementById('logsHideBtn').classList.toggle('on', n > 0);
            document.getElementById('logsHideCount').textContent = n;
            document.getElementById('logsHideAll').textContent = n < AI_GROUPS.length ? 'Hide all' : 'Show all';
        }

        function escapeHtml(s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

        function formatLogText(text) {
            if (!text) return 'No logs available.';
            var html = escapeHtml(text);
            ['Starting Web UI', 'SERVER RUNNING', 'Web Interface:', 'RTSP Server:', '\\* Serving Flask app'].forEach(function (phrase) {
                html = html.replace(new RegExp('(' + phrase + ')', 'g'), '<span style="color: #8be9fd;">$1</span>');
            });
            html = html.replace(/\b(successfully)\b/gi, '<span style="color: #50fa7b;">$&</span>');
            html = html.replace(/\b(Shutdown|stopped|Warning)\b/gi, '<span style="color: #f1fa8c;">$&</span>');
            html = html.replace(/\b(failed|Error|Exception|faile)\b/gi, '<span style="color: #ff5555;">$&</span>');
            html = html.replace(/(\[rtsp @ 0x[0-9a-f]+\])/gi, '<span style="color: #ff79c6;">$1</span>');
            html = html.replace(/(\[([^\]]+)\])/g, function (match) {
                if (match.indexOf('rtsp @') !== -1 || match.indexOf('<span') !== -1) return match;
                return '<span style="color: #8be9fd;">' + match + '</span>';
            });
            html = html.replace(/\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b/g, '<span style="color: #ff79c6;">$1</span>');
            return html;
        }

        // Each line is its own row so a refresh only adds the new lines and drops
        // the oldest ones, instead of redrawing all 10,000 every 3 seconds.
        var drawn = [];
        function lineEl(line) {
            var d = document.createElement('div');
            d.innerHTML = line ? formatLogText(line) : '&#8203;';
            return d;
        }
        function drawLines(shown, msg) {
            if (msg !== null) {
                drawn = [];
                container.textContent = msg;
                return;
            }
            var start = -1;
            if (drawn.length && shown.length) {
                // Find where the new list picks up the old one (old lines may have dropped off the top)
                var from = 0;
                while (true) {
                    var d = drawn.indexOf(shown[0], from);
                    if (d === -1) break;
                    var n = drawn.length - d, ok = n <= shown.length;
                    for (var i = 1; ok && i < n; i++) if (drawn[d + i] !== shown[i]) ok = false;
                    if (ok) { start = d; break; }
                    from = d + 1;
                }
            }
            if (start === -1 || container.childElementCount !== drawn.length) {
                var frag = document.createDocumentFragment();
                shown.forEach(function (l) { frag.appendChild(lineEl(l)); });
                container.textContent = '';
                container.appendChild(frag);
            } else {
                for (var k = 0; k < start; k++) container.firstElementChild.remove();
                var add = document.createDocumentFragment();
                for (var j = drawn.length - start; j < shown.length; j++) add.appendChild(lineEl(shown[j]));
                container.appendChild(add);
            }
            drawn = shown.slice();
        }

        function render() {
            if (lastRaw === null) return;
            var clean = lastRaw.replace(/\u001b\[[0-9;]*[a-zA-Z]/g, '');
            var q = filterBox.value.trim().toLowerCase();
            var lines = clean.split('\n');
            if (lines.length && lines[lines.length - 1] === '') lines.pop();
            var anyHidden = Object.keys(hiddenGroups).length > 0;
            var visible = anyHidden ? lines.filter(function (l) { var g = aiGroupOf(l); return !(g && hiddenGroups[g]); }) : lines;
            var hiddenCount = lines.length - visible.length;
            var shown = q ? visible.filter(function (l) { return l.toLowerCase().indexOf(q) !== -1; }) : visible;
            var msg = null;
            if (!shown.length) {
                if (q) msg = 'No lines match "' + filterBox.value.trim() + '".';
                else if (hiddenCount) msg = 'All ' + hiddenCount.toLocaleString() + ' lines are hidden by the Hide AI menu.';
                else msg = 'No logs available.';
            }
            drawLines(msg ? null : shown, msg);
            var total = lines.length;
            var countText = q
                ? shown.length.toLocaleString() + ' of ' + total.toLocaleString() + ' lines match'
                : total.toLocaleString() + ' lines';
            if (hiddenCount) countText += ' \u00b7 ' + hiddenCount.toLocaleString() + ' AI lines hidden';
            document.getElementById('logsLineCount').textContent = countText;
            if (autoScroll.checked) container.scrollTop = container.scrollHeight;
        }

        async function refreshLogs() {
            try {
                var response = await fetch('/api/logs', { credentials: 'same-origin' });
                if (!response.ok) return;
                var data = await response.json();
                var raw = data.logs || '';
                if (raw === lastRaw) return;   // nothing new: keep the reader's selection and scroll
                // Don't redraw while the user is selecting text
                var sel = window.getSelection && window.getSelection();
                if (sel && !sel.isCollapsed && container.contains(sel.anchorNode)) return;
                lastRaw = raw;
                render();
            } catch (error) {
                console.error('Error fetching logs:', error);
            }
        }

        function startTimer() {
            if (logInterval) clearInterval(logInterval);
            logInterval = setInterval(function () { if (!paused && !document.hidden) refreshLogs(); }, 3000);
        }

        function togglePause() {
            paused = !paused;
            var btn = document.getElementById('logsPauseBtn');
            btn.querySelector('i').className = paused ? 'fa-solid fa-play' : 'fa-solid fa-pause';
            btn.querySelector('span').textContent = paused ? 'Resume' : 'Pause';
            document.getElementById('logsLiveDot').classList.toggle('paused', paused);
            document.getElementById('logsLiveText').textContent = paused ? 'Paused' : 'Live, refreshing every 3 seconds';
            if (!paused) refreshLogs();
        }

        function plainText() { return container.innerText || container.textContent || ''; }

        function copyLogs() {
            var label = document.getElementById('logsCopyLabel');
            var done = function () { label.textContent = 'Copied'; setTimeout(function () { label.textContent = 'Copy'; }, 1500); };
            var text = plainText();
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(text).then(done).catch(fallbackCopy);
            } else fallbackCopy();
            function fallbackCopy() {
                var ta = document.createElement('textarea');
                ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
                document.body.appendChild(ta); ta.select();
                try { document.execCommand('copy'); done(); } catch (_) {}
                ta.remove();
            }
        }

        function downloadLogs() {
            var blob = new Blob([plainText()], { type: 'text/plain' });
            var a = document.createElement('a');
            var d = new Date(), p = function (n) { return String(n).padStart(2, '0'); };
            a.href = URL.createObjectURL(blob);
            a.download = 'system-logs-' + d.getFullYear() + p(d.getMonth() + 1) + p(d.getDate()) + '-' + p(d.getHours()) + p(d.getMinutes()) + '.txt';
            document.body.appendChild(a); a.click(); a.remove();
            setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
        }

        var filterTimer = null;
        filterBox.addEventListener('input', function () { clearTimeout(filterTimer); filterTimer = setTimeout(render, 120); });

        fetch('/api/settings', { credentials: 'same-origin' }).then(function (r) { return r.ok ? r.json() : null; }).then(function (st) {
            if (st && st.logMaxLines) document.getElementById('logsKeepN').textContent = Number(st.logMaxLines).toLocaleString();
        }).catch(function () {});

        applyLogFontSize();
        refreshLogs();
        startTimer();
        document.addEventListener('visibilitychange', function () { if (!document.hidden && !paused) refreshLogs(); });
    </script>
</body>
</html>
'''

    themed_style = """
        /* Dashboard theme palette (only active when body has a theme class) */
""" + APP_THEME_CSS + """
    """
    html = html.replace('</style>', themed_style + '\n    </style>', 1)
    html = html.replace('<body>', f'<body class="{theme_class}">', 1)
    return html
