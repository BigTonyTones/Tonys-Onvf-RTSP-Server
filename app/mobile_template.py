# Standalone mobile / kiosk camera viewer.
#
# A deliberately lightweight page (separate from the full dashboard) for quickly
# watching live cameras on a phone or kiosk display. Features:
#   - Swipeable pages of cameras (native CSS scroll-snap, touch-friendly)
#   - Selectable cameras-per-page (1 / 2 / 4 / 6 / 9)
#   - Tap a camera to enlarge it to a full-screen HD view
#
# Built as a plain string with __TOKEN__ placeholders (no f-string / .format) so
# the embedded CSS/JS braces need no escaping. Streaming logic is pulled from the
# shared app/streaming_js.py module rather than duplicated here.

from .version import CURRENT_VERSION
from .streaming_js import get_streaming_js


_MOBILE_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="theme-color" content="#000000">
    <title>Cameras</title>
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
        html, body {
            height: 100%;
            background: #000;
            color: #e8e8e8;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            overflow: hidden;
            overscroll-behavior: none;
        }
        body { display: flex; flex-direction: column; height: 100vh; height: 100dvh; }

        /* ---- Top bar ---- */
        .topbar {
            flex: 0 0 auto;
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 0 12px;
            background: #0d0d0f;
            border-bottom: 1px solid #1e1e22;
            padding-top: env(safe-area-inset-top, 0);
            height: calc(52px + env(safe-area-inset-top, 0));
            overflow-x: auto;
            overflow-y: hidden;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: none;
        }
        .topbar::-webkit-scrollbar { display: none; }
        .topbar > * { flex: 0 0 auto; }
        .topbar .title {
            font-size: 15px;
            font-weight: 700;
            letter-spacing: 0.3px;
            display: flex;
            align-items: center;
            gap: 8px;
            margin-right: auto;
        }
        .topbar .title .dot-live {
            width: 8px; height: 8px; border-radius: 50%;
            background: #22c55e; box-shadow: 0 0 8px #22c55e;
        }
        .topbar select {
            background: #1a1a1f;
            color: #e8e8e8;
            border: 1px solid #2a2a30;
            border-radius: 8px;
            padding: 7px 8px;
            font-size: 13px;
            font-weight: 600;
        }
        .topbar .link-btn {
            background: #1a1a1f;
            color: #b9b9c2;
            border: 1px solid #2a2a30;
            border-radius: 8px;
            padding: 7px 10px;
            font-size: 12px;
            font-weight: 600;
            text-decoration: none;
        }
        .topbar .toggle-btn {
            background: #1a1a1f;
            color: #b9b9c2;
            border: 1px solid #2a2a30;
            border-radius: 8px;
            padding: 7px 11px;
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
            white-space: nowrap;
        }
        .topbar .toggle-btn.active {
            background: #2563eb;
            color: #fff;
            border-color: #2563eb;
        }

        /* Stretch Fill: edge-to-edge video wall — no gaps, borders, or letterboxing. */
        body.stretch .page { padding: 0; }
        body.stretch .tiles { gap: 0; }
        body.stretch .tile { border: none; border-radius: 0; }
        body.stretch .tile video { object-fit: cover; }

        /* Hide Names: clean wall, no labels or tap hints. */
        body.hide-names .tile-name,
        body.hide-names .tap-hint { display: none; }

        /* ---- Swipeable pager ---- */
        .pager {
            flex: 1 1 auto;
            display: flex;
            overflow-x: auto;
            overflow-y: hidden;
            scroll-snap-type: x mandatory;
            scroll-behavior: smooth;
            overscroll-behavior: contain;
            -webkit-overflow-scrolling: touch;
        }
        .pager::-webkit-scrollbar { display: none; }
        .pager { scrollbar-width: none; }

        .page {
            flex: 0 0 100%;
            width: 100%;
            height: 100%;
            scroll-snap-align: start;
            scroll-snap-stop: always;
            padding: 6px;
        }
        .tiles {
            display: grid;
            gap: 6px;
            width: 100%;
            height: 100%;
            grid-auto-rows: 1fr;
        }
        .tile {
            position: relative;
            background: #0a0a0c;
            border: 1px solid #1c1c20;
            border-radius: 10px;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
        }
        .tile video {
            width: 100%;
            height: 100%;
            object-fit: contain;
            background: #000;
        }
        .tile.disabled { flex-direction: column; gap: 8px; color: #6b7280; }
        .tile.disabled .icon { font-size: 26px; }
        .tile-name {
            position: absolute;
            top: 7px; left: 7px;
            background: rgba(0,0,0,0.62);
            color: #fff;
            font-size: 12px;
            font-weight: 600;
            padding: 3px 9px;
            border-radius: 6px;
            max-width: calc(100% - 14px);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            pointer-events: none;
        }
        .tile .tap-hint {
            position: absolute;
            bottom: 7px; right: 7px;
            background: rgba(0,0,0,0.55);
            color: #cbd5e1;
            font-size: 11px;
            padding: 3px 7px;
            border-radius: 6px;
            pointer-events: none;
        }
        .tile.disabled .tile-msg { font-size: 12px; }

        .empty {
            margin: auto;
            text-align: center;
            color: #6b7280;
            font-size: 15px;
            padding: 40px;
        }

        /* ---- Page dots ---- */
        .dots {
            flex: 0 0 auto;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 7px;
            min-height: 26px;
            padding: 4px 0 calc(4px + env(safe-area-inset-bottom, 0));
            background: #0d0d0f;
            border-top: 1px solid #1e1e22;
        }
        .dot {
            width: 7px; height: 7px;
            border-radius: 50%;
            background: #3a3a42;
            transition: all 0.2s ease;
        }
        .dot.active { background: #e8e8e8; width: 22px; border-radius: 4px; }

        /* ---- Enlarge overlay ---- */
        .enlarge {
            display: none;
            position: fixed;
            inset: 0;
            z-index: 50;
            background: #000;
            flex-direction: column;
        }
        .enlarge.active { display: flex; }
        .enlarge-bar {
            flex: 0 0 auto;
            display: flex;
            align-items: center;
            gap: 12px;
            height: calc(52px + env(safe-area-inset-top, 0));
            padding: env(safe-area-inset-top, 0) 14px 0;
            background: rgba(13,13,15,0.92);
        }
        .enlarge-bar .back {
            background: #1a1a1f;
            color: #e8e8e8;
            border: 1px solid #2a2a30;
            border-radius: 8px;
            padding: 8px 14px;
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
        }
        .enlarge-bar .enlarge-name { font-size: 15px; font-weight: 600; }
        .enlarge video {
            flex: 1 1 auto;
            width: 100%;
            height: 100%;
            object-fit: contain;
            background: #000;
        }
    </style>
</head>
<body>
    <div class="topbar">
        <div class="title"><span class="dot-live"></span> Cameras</div>
        <select id="perPage" aria-label="Cameras per page">
            <option value="all">Show All</option>
            <option value="1">1 / page</option>
            <option value="2">2 / page</option>
            <option value="4">4 / page</option>
            <option value="6">6 / page</option>
            <option value="9">9 / page</option>
        </select>
        <button class="toggle-btn" id="btnStretch" title="Stretch video to fill — no borders">Fill</button>
        <button class="toggle-btn" id="btnNames" title="Hide camera name labels">Names</button>
        <a class="link-btn" href="/?desktop=1">Desktop</a>
    </div>

    <div id="pager" class="pager"></div>
    <div id="dots" class="dots"></div>

    <div id="enlarge" class="enlarge">
        <div class="enlarge-bar">
            <button class="back" id="enlargeBack">&larr; Back</button>
            <span class="enlarge-name" id="enlargeName"></span>
        </div>
        <video id="enlargeVideo" muted autoplay playsinline></video>
    </div>

    <script>
    __STREAMING_JS__
    </script>

    <script>
        // ===== Mobile viewer state =====
        let settings = {};
        let cameras = [];
        let perPage = localStorage.getItem('mobilePerPage') || '4';   // number-as-string or 'all'
        let stretchFill = localStorage.getItem('mobileStretchFill') === '1';
        let hideNames = localStorage.getItem('mobileHideNames') === '1';
        // Match the dashboard: prefer low-latency WebRTC, fall back to HLS.
        // Shares the dashboard's 'useWebRTC' preference (default on).
        let useLowLatency = (localStorage.getItem('useWebRTC') === null)
            ? true : (localStorage.getItem('useWebRTC') === 'true');
        let currentPage = 0;
        const players = new Map();   // videoId -> player handle
        let enlargePlayer = null;
        let scrollTimer = null;
        let resizeTimer = null;
        let lastSignature = '';

        function esc(s) {
            return String(s == null ? '' : s)
                .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
        }

        // Effective cameras-per-page ('all' => every running camera on one page).
        function pageSize() {
            if (perPage === 'all') return Math.max(1, runningCameras().length);
            const n = parseInt(perPage, 10);
            return (n && n > 0) ? n : 4;
        }

        // Columns for a page of `size` tiles, tuned for phone orientation.
        function colsFor(size, landscape) {
            if (size <= 1) return 1;
            const portrait = { 2: 1, 4: 2, 6: 2, 9: 3 };
            const land = { 2: 2, 4: 2, 6: 3, 9: 3 };
            const map = landscape ? land : portrait;
            if (perPage !== 'all' && map[size]) return map[size];
            return Math.ceil(Math.sqrt(size)); // 'all' / custom counts: balanced grid
        }

        function applyDisplayModes() {
            document.body.classList.toggle('stretch', stretchFill);
            document.body.classList.toggle('hide-names', hideNames);
            const bs = document.getElementById('btnStretch');
            const bn = document.getElementById('btnNames');
            if (bs) bs.classList.toggle('active', stretchFill);
            if (bn) bn.classList.toggle('active', hideNames);
        }

        function chunk(arr, size) {
            const out = [];
            for (let i = 0; i < arr.length; i += size) out.push(arr.slice(i, i + size));
            return out;
        }

        function runningCameras() {
            return cameras.filter(c => c.status === 'running');
        }

        function tileHtml(cam) {
            if (cam.disableSubstream) {
                return `<div class="tile disabled" data-cam="${cam.id}" data-path="${esc(cam.pathName)}" data-name="${esc(cam.name)}">
                    <div class="tile-name">${esc(cam.name)}</div>
                    <div class="icon">&#128247;</div>
                    <div class="tile-msg">Substream off &middot; tap for HD</div>
                </div>`;
            }
            return `<div class="tile" data-cam="${cam.id}" data-path="${esc(cam.pathName)}" data-name="${esc(cam.name)}">
                <video id="m-vid-${cam.id}" data-path="${esc(cam.pathName)}" muted autoplay playsinline></video>
                <div class="tile-name">${esc(cam.name)}</div>
                <div class="tap-hint">tap to enlarge</div>
            </div>`;
        }

        function startPlayer(video) {
            if (players.has(video.id)) return;
            const handle = createCameraPlayer(video, {
                serverIp: resolveServerIp(settings),
                pathName: video.dataset.path,
                profile: 'sub',
                settings: settings,
                lowLatency: useLowLatency
            });
            if (handle) players.set(video.id, handle);
        }

        function stopPlayer(video) {
            const handle = players.get(video.id);
            if (handle) { handle.destroy(); players.delete(video.id); }
        }

        // Only the visible page streams; off-screen pages are torn down so a
        // kiosk / phone never holds more connections than it is showing.
        function activatePage(idx) {
            document.querySelectorAll('.page').forEach((pageEl, i) => {
                const vids = pageEl.querySelectorAll('video[data-path]');
                if (i === idx) {
                    // Stagger startup so many streams don't all negotiate at once
                    // (a common cause of some feeds failing to come up).
                    vids.forEach((v, k) => {
                        setTimeout(() => {
                            if (currentPage === idx) startPlayer(v);
                        }, k * 200);
                    });
                } else {
                    vids.forEach(v => stopPlayer(v));
                }
            });
        }

        function updateDots() {
            document.querySelectorAll('.dot').forEach((d, i) => {
                d.classList.toggle('active', i === currentPage);
            });
        }

        function render() {
            const pager = document.getElementById('pager');
            const dots = document.getElementById('dots');

            // Tear down all existing players before rebuilding the DOM.
            players.forEach(h => h.destroy());
            players.clear();

            const running = runningCameras();
            if (running.length === 0) {
                pager.innerHTML = '<div class="empty">No cameras are currently running.</div>';
                dots.innerHTML = '';
                return;
            }

            const landscape = window.innerWidth > window.innerHeight;
            const size = pageSize();
            const cols = colsFor(size, landscape);
            const pages = chunk(running, size);
            if (currentPage >= pages.length) currentPage = pages.length - 1;
            if (currentPage < 0) currentPage = 0;

            pager.innerHTML = pages.map(page => `
                <div class="page">
                    <div class="tiles" style="grid-template-columns: repeat(${cols}, 1fr);">
                        ${page.map(tileHtml).join('')}
                    </div>
                </div>`).join('');

            dots.innerHTML = pages.length > 1
                ? pages.map((_, i) => `<span class="dot ${i === currentPage ? 'active' : ''}"></span>`).join('')
                : '';

            // Restore scroll position to the current page, then stream it.
            requestAnimationFrame(() => {
                pager.scrollLeft = currentPage * pager.clientWidth;
                activatePage(currentPage);
            });
        }

        function enlarge(camId, pathName, name) {
            const ov = document.getElementById('enlarge');
            document.getElementById('enlargeName').textContent = name || '';
            const video = document.getElementById('enlargeVideo');
            if (enlargePlayer) { enlargePlayer.destroy(); enlargePlayer = null; }
            // Use the main (HD) profile for the enlarged single-camera view.
            enlargePlayer = createCameraPlayer(video, {
                serverIp: resolveServerIp(settings),
                pathName: pathName,
                profile: 'main',
                settings: settings,
                lowLatency: useLowLatency
            });
            ov.classList.add('active');
        }

        function closeEnlarge() {
            const ov = document.getElementById('enlarge');
            ov.classList.remove('active');
            if (enlargePlayer) { enlargePlayer.destroy(); enlargePlayer = null; }
            const video = document.getElementById('enlargeVideo');
            try { video.removeAttribute('src'); video.load(); } catch (e) {}
        }

        async function loadAll() {
            try {
                const sResp = await fetch('/api/settings?t=' + Date.now());
                if (sResp.ok) {
                    const s = await sResp.json();
                    if (s && typeof s === 'object') settings = s;
                }
            } catch (e) { console.warn('settings load failed', e); }

            try {
                const cResp = await fetch('/api/cameras?t=' + Date.now());
                if (cResp.ok) {
                    const c = await cResp.json();
                    if (Array.isArray(c)) cameras = c;
                }
            } catch (e) { console.warn('cameras load failed', e); }
        }

        // Re-render only when the set of running cameras actually changes, so a
        // routine refresh doesn't tear down healthy streams.
        function signatureOf() {
            return runningCameras().map(c => c.id + ':' + c.pathName + ':' + (c.disableSubstream ? 1 : 0)).join(',');
        }

        async function refresh() {
            await loadAll();
            const sig = signatureOf();
            if (sig !== lastSignature) {
                lastSignature = sig;
                render();
            }
        }

        function initEvents() {
            const pager = document.getElementById('pager');

            // Detect the settled page after a swipe and activate its streams.
            pager.addEventListener('scroll', () => {
                clearTimeout(scrollTimer);
                scrollTimer = setTimeout(() => {
                    const w = pager.clientWidth || 1;
                    const idx = Math.round(pager.scrollLeft / w);
                    if (idx !== currentPage) {
                        currentPage = idx;
                        activatePage(currentPage);
                        updateDots();
                    }
                }, 130);
            });

            // Tap a tile to enlarge (event delegation handles re-rendered tiles).
            pager.addEventListener('click', (e) => {
                const tile = e.target.closest('.tile');
                if (!tile) return;
                enlarge(parseInt(tile.dataset.cam, 10), tile.dataset.path, tile.dataset.name);
            });

            document.getElementById('enlargeBack').addEventListener('click', closeEnlarge);

            document.getElementById('perPage').addEventListener('change', (e) => {
                perPage = e.target.value;
                localStorage.setItem('mobilePerPage', perPage);
                currentPage = 0;
                render();
            });

            // Stretch Fill / Hide Names are pure CSS toggles — no stream teardown.
            document.getElementById('btnStretch').addEventListener('click', () => {
                stretchFill = !stretchFill;
                localStorage.setItem('mobileStretchFill', stretchFill ? '1' : '0');
                applyDisplayModes();
            });
            document.getElementById('btnNames').addEventListener('click', () => {
                hideNames = !hideNames;
                localStorage.setItem('mobileHideNames', hideNames ? '1' : '0');
                applyDisplayModes();
            });

            // Re-flow on rotate / resize (debounced so streams aren't thrashed).
            window.addEventListener('resize', () => {
                clearTimeout(resizeTimer);
                resizeTimer = setTimeout(render, 250);
            });

            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') closeEnlarge();
            });
        }

        async function init() {
            // Reflect the saved per-page choice in the selector.
            const sel = document.getElementById('perPage');
            if (!['all', '1', '2', '4', '6', '9'].includes(perPage)) perPage = '4';
            sel.value = perPage;
            applyDisplayModes();

            initEvents();
            await loadAll();
            lastSignature = signatureOf();
            render();

            // Keep the camera list fresh (picks up start/stop, new cameras).
            setInterval(refresh, 5000);
        }

        init();
    </script>
</body>
</html>
"""


def get_mobile_html(settings=None):
    """Generate the standalone mobile/kiosk viewer HTML."""
    html = _MOBILE_PAGE
    html = html.replace('__STREAMING_JS__', get_streaming_js())
    html = html.replace('__VERSION__', CURRENT_VERSION)
    return html
