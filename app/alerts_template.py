"""
Standalone AI Detection Alerts page (gallery view) served at /alerts
"""


def get_alerts_html():
    return r'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Detection Alerts - Tonys Onvif Server</title>
    <style>
        :root {
            --bg-color: #0f1012;
            --header-bg: #151619;
            --card-bg: #1a1b1e;
            --text-main: #f0f2f5;
            --text-muted: #888e99;
            --accent: #3b82f6;
            --accent-violet: #8b5cf6;
            --accent-red: #ef4444;
            --accent-green: #10b981;
            --border-color: #24262b;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: var(--bg-color);
            color: var(--text-main);
            min-height: 100vh;
        }
        .header {
            position: sticky; top: 0; z-index: 50;
            background: var(--header-bg);
            padding: 14px 28px;
            display: flex; justify-content: space-between; align-items: center;
            border-bottom: 1px solid var(--border-color);
        }
        .header h1 { font-size: 18px; font-weight: 700; }
        .header h1 span { color: var(--text-muted); font-weight: 500; font-size: 13px; margin-left: 10px; }
        .header-actions { display: flex; gap: 10px; align-items: center; }
        .btn {
            background: #24262b; color: var(--text-main);
            border: 1px solid #333742; padding: 7px 14px; border-radius: 6px;
            cursor: pointer; font-size: 12.5px; font-weight: 600; transition: all 0.15s ease;
        }
        .btn:hover { background: #2f333e; border-color: #454b59; }
        .btn-danger { color: #fca5a5; }
        .btn-danger:hover { background: rgba(239,68,68,0.12); border-color: var(--accent-red); }
        .btn-primary { background: var(--accent); border-color: var(--accent); color: #fff; }
        .btn-primary:hover { background: #2563eb; }
        .btn.live-on { background: rgba(16,185,129,0.12); border-color: var(--accent-green); color: var(--accent-green); }

        /* Toolbar */
        .toolbar {
            position: sticky; top: 57px; z-index: 40;
            background: var(--bg-color);
            padding: 14px 28px 12px 28px;
            display: flex; align-items: center; gap: 14px; flex-wrap: wrap;
            border-bottom: 1px solid var(--border-color);
        }
        .toolbar label { font-size: 11px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }
        .toolbar select {
            background: var(--card-bg); color: var(--text-main);
            border: 1px solid var(--border-color); border-radius: 6px;
            padding: 6px 10px; font-size: 12.5px; cursor: pointer;
        }
        .pill-group { display: flex; gap: 3px; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 8px; padding: 3px; }
        .pill {
            padding: 5px 12px; border: none; border-radius: 6px; cursor: pointer;
            font-size: 12px; font-weight: 600; background: transparent; color: var(--text-muted);
            transition: all 0.15s ease;
        }
        .pill:hover { color: var(--text-main); }
        .pill.active { background: #2f333e; color: var(--text-main); }
        .pill.active[data-tag="person"]  { color: #90cdf4; }
        .pill.active[data-tag="vehicle"] { color: #c4b5fd; }
        .pill.active[data-tag="animal"]  { color: #9ae6b4; }
        .pill.active[data-tag="package"] { color: #fbd38d; }
        .size-slider { display: flex; align-items: center; gap: 8px; }
        .size-slider input { width: 110px; accent-color: var(--accent); cursor: pointer; }
        .count-label { margin-left: auto; font-size: 12px; color: var(--text-muted); }

        /* Selection bar */
        .selection-bar {
            position: sticky; top: 118px; z-index: 39;
            display: none; align-items: center; gap: 12px;
            background: rgba(59,130,246,0.1);
            border-bottom: 1px solid rgba(59,130,246,0.35);
            padding: 9px 28px; font-size: 12.5px;
            backdrop-filter: blur(6px);
        }
        .selection-bar.visible { display: flex; }
        .selection-bar .sel-count { font-weight: 700; color: var(--accent); }

        /* Gallery */
        .gallery { padding: 18px 28px 50px 28px; }
        .day-header {
            font-size: 13px; font-weight: 700; color: var(--text-main);
            margin: 22px 0 10px 0; display: flex; align-items: center; gap: 12px;
        }
        .day-header:first-child { margin-top: 0; }
        .day-header .day-count { font-size: 11px; font-weight: 600; color: var(--text-muted); background: var(--card-bg); padding: 2px 9px; border-radius: 9px; }
        .day-header .day-select { font-size: 11px; color: var(--text-muted); cursor: pointer; border: none; background: none; font-weight: 600; }
        .day-header .day-select:hover { color: var(--accent); text-decoration: underline; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(var(--thumb-size, 220px), 1fr)); gap: 10px; }
        .thumb {
            position: relative; border-radius: 8px; overflow: hidden;
            background: var(--card-bg); border: 1px solid var(--border-color);
            cursor: pointer; aspect-ratio: 16/9;
            transition: border-color 0.15s ease, transform 0.1s ease;
        }
        .thumb:hover { border-color: #454b59; }
        .thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
        .thumb .meta {
            position: absolute; bottom: 0; left: 0; right: 0;
            background: linear-gradient(transparent, rgba(0,0,0,0.85));
            padding: 18px 8px 6px 8px;
            display: flex; justify-content: space-between; align-items: flex-end; gap: 6px;
            pointer-events: none;
        }
        .thumb .meta .cam { font-size: 11px; font-weight: 600; color: #e2e8f0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .thumb .meta .time { font-size: 10px; color: #a0aec0; white-space: nowrap; }
        .thumb .tags { position: absolute; top: 6px; right: 6px; display: flex; gap: 4px; pointer-events: none; }
        .tag-chip { font-size: 9.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.4px; padding: 2px 7px; border-radius: 8px; background: rgba(0,0,0,0.65); }
        .tag-person  { color: #90cdf4; } .tag-vehicle { color: #c4b5fd; }
        .tag-animal  { color: #9ae6b4; } .tag-package { color: #fbd38d; }
        .tag-chip.tag-other { color: #cbd5e0; }
        .thumb .check {
            position: absolute; top: 6px; left: 6px;
            width: 20px; height: 20px; border-radius: 5px;
            border: 2px solid rgba(255,255,255,0.75); background: rgba(0,0,0,0.45);
            display: flex; align-items: center; justify-content: center;
            opacity: 0; transition: opacity 0.12s ease;
            font-size: 12px; color: #fff;
        }
        .thumb:hover .check { opacity: 1; }
        body.has-selection .thumb .check { opacity: 1; }
        .thumb.selected { border-color: var(--accent); box-shadow: 0 0 0 2px rgba(59,130,246,0.55); }
        .thumb.selected .check { opacity: 1; background: var(--accent); border-color: var(--accent); }

        /* Hover preview popup */
        .hover-preview {
            position: fixed; z-index: 150; pointer-events: none;
            display: none; flex-direction: column;
            background: var(--card-bg); border: 1px solid #333742; border-radius: 10px;
            padding: 6px; box-shadow: 0 14px 40px rgba(0,0,0,0.65);
        }
        .hover-preview.visible { display: flex; }
        .hover-preview img { width: 560px; max-width: 46vw; border-radius: 6px; display: block; }
        .hover-preview .hp-caption {
            display: flex; justify-content: space-between; gap: 12px;
            padding: 7px 4px 2px 4px; font-size: 11.5px;
        }
        .hover-preview .hp-cam { font-weight: 700; color: var(--text-main); }
        .hover-preview .hp-time { color: var(--text-muted); }

        /* Storage cap control */
        .storage-ctl { display: flex; align-items: center; gap: 7px; font-size: 12px; color: var(--text-muted); }
        .storage-ctl input {
            width: 64px; background: var(--card-bg); color: var(--text-main);
            border: 1px solid var(--border-color); border-radius: 6px;
            padding: 5px 8px; font-size: 12.5px; text-align: center;
        }
        .storage-ctl input:focus { outline: none; border-color: var(--accent); }
        .storage-saved { color: var(--accent-green); font-weight: 600; opacity: 0; transition: opacity 0.3s ease; }
        .storage-saved.flash { opacity: 1; }

        .empty-state { text-align: center; padding: 90px 20px; color: var(--text-muted); }
        .empty-state .big { font-size: 15px; margin-bottom: 8px; color: var(--text-main); }

        /* Lightbox */
        .lightbox {
            position: fixed; inset: 0; z-index: 200;
            background: rgba(8,9,11,0.94);
            display: none; flex-direction: column;
        }
        .lightbox.open { display: flex; }
        .lb-top {
            display: flex; justify-content: space-between; align-items: center;
            padding: 14px 24px; flex-shrink: 0;
        }
        .lb-info { display: flex; align-items: baseline; gap: 14px; }
        .lb-cam { font-size: 15px; font-weight: 700; }
        .lb-time { font-size: 12.5px; color: var(--text-muted); }
        .lb-counter { font-size: 12px; color: var(--text-muted); background: rgba(255,255,255,0.07); padding: 3px 11px; border-radius: 10px; }
        .lb-actions { display: flex; gap: 9px; }
        .lb-stage { flex: 1; display: flex; align-items: center; justify-content: center; position: relative; min-height: 0; padding: 0 70px; }
        .lb-stage img { width: 100%; height: 100%; max-width: 100%; max-height: calc(100vh - 130px); object-fit: contain; border-radius: 6px; }
        .lb-nav {
            position: absolute; top: 50%; transform: translateY(-50%);
            background: rgba(255,255,255,0.08); color: #fff; border: none;
            border-radius: 50%; width: 46px; height: 46px; cursor: pointer; font-size: 18px;
            transition: background 0.15s ease;
        }
        .lb-nav:hover { background: rgba(255,255,255,0.18); }
        .lb-prev { left: 16px; } .lb-next { right: 16px; }
        .lb-bottom { padding: 10px 24px 16px 24px; display: flex; justify-content: center; gap: 6px; flex-shrink: 0; }
        .lb-bottom .tag-chip { font-size: 11px; padding: 3px 11px; background: rgba(255,255,255,0.07); }
        .lb-filmstrip {
            display: flex; gap: 6px; overflow-x: auto; padding: 4px 24px 14px 24px;
            flex-shrink: 0; scrollbar-width: thin;
        }
        .lb-filmstrip img {
            height: 52px; border-radius: 4px; cursor: pointer; opacity: 0.45;
            border: 2px solid transparent; transition: opacity 0.12s ease; flex-shrink: 0;
        }
        .lb-filmstrip img:hover { opacity: 0.85; }
        .lb-filmstrip img.current { opacity: 1; border-color: var(--accent); }

        @media (max-width: 700px) {
            .header, .toolbar, .selection-bar { padding-left: 14px; padding-right: 14px; }
            .gallery { padding: 14px 14px 40px 14px; }
            .lb-stage { padding: 0 8px; }
            .lb-nav { width: 38px; height: 38px; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>AI Detection Alerts<span id="hdr-summary"></span></h1>
        <div class="header-actions">
            <button class="btn" id="btn-live" onclick="toggleLive()">Live: Off</button>
            <button class="btn" onclick="loadAlerts()">Refresh</button>
            <button class="btn btn-danger" onclick="clearAll()">Clear All</button>
            <button class="btn" onclick="window.location.href='/'">&#8592; Dashboard</button>
        </div>
    </div>

    <div class="toolbar">
        <label>Camera</label>
        <select id="filter-cam" onchange="applyFilters()">
            <option value="">All cameras</option>
        </select>
        <label>Type</label>
        <div class="pill-group" id="tag-pills">
            <button class="pill active" data-tag="" onclick="setTag(this)">All</button>
            <button class="pill" data-tag="person" onclick="setTag(this)">Person</button>
            <button class="pill" data-tag="vehicle" onclick="setTag(this)">Vehicle</button>
            <button class="pill" data-tag="animal" onclick="setTag(this)">Animal</button>
            <button class="pill" data-tag="package" onclick="setTag(this)">Package</button>
        </div>
        <label>When</label>
        <div class="pill-group" id="time-pills">
            <button class="pill active" data-hours="" onclick="setRange(this)">All</button>
            <button class="pill" data-hours="1" onclick="setRange(this)">1h</button>
            <button class="pill" data-hours="24" onclick="setRange(this)">24h</button>
            <button class="pill" data-hours="168" onclick="setRange(this)">7d</button>
        </div>
        <div class="size-slider">
            <label>Size</label>
            <input type="range" min="120" max="600" value="220" id="thumb-size" oninput="setThumbSize(this.value)" onchange="saveThumbSize(this.value)">
        </div>
        <div class="storage-ctl" style="margin-left: auto;" title="Oldest images are deleted automatically once this many are stored (10 - 10,000)">
            <span>Keep last</span>
            <input type="number" id="max-alerts-input" min="10" max="10000" step="10" onchange="saveMaxAlerts(this.value)">
            <span>images</span>
            <span class="storage-saved" id="storage-saved">saved</span>
        </div>
        <span class="count-label" id="count-label" style="margin-left: 0;"></span>
    </div>

    <div class="selection-bar" id="selection-bar">
        <span class="sel-count" id="sel-count">0 selected</span>
        <button class="btn" onclick="selectAllVisible()">Select All Visible</button>
        <button class="btn" onclick="clearSelection()">Clear Selection</button>
        <button class="btn btn-primary" onclick="downloadSelected()">Download ZIP</button>
        <button class="btn btn-danger" onclick="deleteSelected()">Delete Selected</button>
    </div>

    <div class="gallery" id="gallery"></div>

    <!-- Large preview shown while hovering a thumbnail -->
    <div class="hover-preview" id="hover-preview">
        <img id="hp-img" src="" alt="">
        <div class="hp-caption">
            <span class="hp-cam" id="hp-cam"></span>
            <span class="hp-time" id="hp-time"></span>
        </div>
    </div>

    <!-- Lightbox -->
    <div class="lightbox" id="lightbox">
        <div class="lb-top">
            <div class="lb-info">
                <span class="lb-cam" id="lb-cam"></span>
                <span class="lb-time" id="lb-time"></span>
                <span class="lb-counter" id="lb-counter"></span>
            </div>
            <div class="lb-actions">
                <button class="btn" onclick="downloadCurrent()">Download</button>
                <button class="btn btn-danger" onclick="deleteCurrent()">Delete</button>
                <button class="btn" onclick="closeLightbox()">Close &times;</button>
            </div>
        </div>
        <div class="lb-stage">
            <button class="lb-nav lb-prev" onclick="stepLightbox(-1)">&#10094;</button>
            <img id="lb-img" src="" alt="AI Detection">
            <button class="lb-nav lb-next" onclick="stepLightbox(1)">&#10095;</button>
        </div>
        <div class="lb-bottom" id="lb-tags"></div>
        <div class="lb-filmstrip" id="lb-filmstrip"></div>
    </div>

    <script>
        let allAlerts = [];
        let filtered = [];
        let camMap = {};
        let curTag = '';
        let curHours = '';
        let selected = new Set();
        let lbIndex = -1;
        let liveTimer = null;
        let maxAlerts = null;

        const tagClass = t => ['person','vehicle','animal','package'].includes(t) ? 'tag-' + t : 'tag-other';
        const imgUrl = f => '/api/ai-alerts/image/' + encodeURIComponent(f);
        const camName = id => camMap[id] || ('Camera ' + id);

        async function loadCameras() {
            try {
                const cams = await (await fetch('/api/cameras')).json();
                camMap = {};
                const sel = document.getElementById('filter-cam');
                const prev = sel.value;
                sel.innerHTML = '<option value="">All cameras</option>';
                cams.forEach(c => {
                    camMap[c.id] = c.name;
                    const o = document.createElement('option');
                    o.value = c.id; o.textContent = c.name;
                    sel.appendChild(o);
                });
                sel.value = prev;
            } catch (e) { /* camera names fall back to "Camera N" */ }
        }

        async function loadAlerts() {
            try {
                const data = await (await fetch('/api/ai-alerts')).json();
                allAlerts = data.alerts || [];
                if (data.max_alerts) {
                    maxAlerts = data.max_alerts;
                    const inp = document.getElementById('max-alerts-input');
                    if (document.activeElement !== inp) inp.value = maxAlerts;
                }
                applyFilters();
            } catch (e) {
                document.getElementById('gallery').innerHTML =
                    '<div class="empty-state"><div class="big">Failed to load alerts</div><div>' + e + '</div></div>';
            }
        }

        function setTag(btn) {
            curTag = btn.dataset.tag;
            document.querySelectorAll('#tag-pills .pill').forEach(b => b.classList.toggle('active', b === btn));
            applyFilters();
        }

        function setRange(btn) {
            curHours = btn.dataset.hours;
            document.querySelectorAll('#time-pills .pill').forEach(b => b.classList.toggle('active', b === btn));
            applyFilters();
        }

        function setThumbSize(px) {
            document.documentElement.style.setProperty('--thumb-size', px + 'px');
            localStorage.setItem('alerts-thumb-size', px);
        }

        async function saveThumbSize(px) {
            try {
                const settings = await (await fetch('/api/settings')).json();
                settings.alertsThumbSize = parseInt(px);
                await fetch('/api/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(settings)
                });
            } catch (e) {
                console.error('Failed to save alertsThumbSize setting:', e);
            }
        }

        function applyFilters() {
            const camId = document.getElementById('filter-cam').value;
            const cutoff = curHours ? Date.now() - parseFloat(curHours) * 3600 * 1000 : 0;
            filtered = allAlerts.filter(a =>
                (!camId || String(a.camera_id) === camId) &&
                (!curTag || (a.tags || []).includes(curTag)) &&
                (a.ts >= cutoff)
            );
            // Drop selections that are no longer visible on disk
            const known = new Set(allAlerts.map(a => a.file));
            selected.forEach(f => { if (!known.has(f)) selected.delete(f); });
            renderGallery();
        }

        function renderGallery() {
            const g = document.getElementById('gallery');
            document.getElementById('count-label').textContent = filtered.length + ' of ' + allAlerts.length + ' alerts';
            const capNote = maxAlerts ? ' · saving the last ' + maxAlerts.toLocaleString() + ' images' : '';
            document.getElementById('hdr-summary').textContent =
                (allAlerts.length ? allAlerts.length + ' stored' : '') + (allAlerts.length ? capNote : '');
            if (!filtered.length) {
                g.innerHTML = '<div class="empty-state"><div class="big">No detection alerts' +
                    (allAlerts.length ? ' match these filters' : ' yet') + '</div>' +
                    '<div>Snapshots appear here automatically when AI detects people, vehicles, animals or packages.</div></div>';
                updateSelectionBar();
                return;
            }
            // Group by calendar day
            const groups = [];
            let last = null;
            filtered.forEach((a, i) => {
                const d = new Date(a.ts);
                const key = d.toDateString();
                if (key !== last) { groups.push({ key, label: dayLabel(d), items: [] }); last = key; }
                groups[groups.length - 1].items.push(i);
            });
            let html = '';
            groups.forEach(grp => {
                html += '<div class="day-header">' + grp.label +
                    '<span class="day-count">' + grp.items.length + '</span>' +
                    '<button class="day-select" onclick="selectDay(\'' + grp.key + '\')">select day</button></div>';
                html += '<div class="grid">';
                grp.items.forEach(i => {
                    const a = filtered[i];
                    const t = new Date(a.ts);
                    html += '<div class="thumb' + (selected.has(a.file) ? ' selected' : '') + '" data-idx="' + i + '" data-file="' + a.file + '">' +
                        '<img src="' + imgUrl(a.file) + '" loading="lazy" alt="">' +
                        '<div class="check" onclick="toggleSelect(event, \'' + a.file + '\')">' + (selected.has(a.file) ? '&#10003;' : '') + '</div>' +
                        '<div class="tags">' + (a.tags || []).map(tg => '<span class="tag-chip ' + tagClass(tg) + '">' + tg + '</span>').join('') + '</div>' +
                        '<div class="meta"><span class="cam">' + camName(a.camera_id) + '</span>' +
                        '<span class="time">' + t.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + '</span></div></div>';
                });
                html += '</div>';
            });
            g.innerHTML = html;
            g.querySelectorAll('.thumb').forEach(el => {
                el.addEventListener('click', e => {
                    if (e.target.classList.contains('check')) return;
                    const idx = parseInt(el.dataset.idx);
                    // While selecting, plain click toggles; otherwise opens viewer
                    if (selected.size > 0 && !e.ctrlKey && !e.metaKey) { toggleSelect(e, el.dataset.file); return; }
                    if (e.ctrlKey || e.metaKey) { toggleSelect(e, el.dataset.file); return; }
                    openLightbox(idx);
                });
            });
            updateSelectionBar();
        }

        function dayLabel(d) {
            const today = new Date(); today.setHours(0,0,0,0);
            const that = new Date(d); that.setHours(0,0,0,0);
            const diff = Math.round((today - that) / 86400000);
            if (diff === 0) return 'Today';
            if (diff === 1) return 'Yesterday';
            return d.toLocaleDateString([], { weekday: 'long', month: 'short', day: 'numeric', year: d.getFullYear() !== today.getFullYear() ? 'numeric' : undefined });
        }

        // ---------- Selection ----------
        function toggleSelect(e, file) {
            e.stopPropagation();
            if (selected.has(file)) selected.delete(file); else selected.add(file);
            const el = document.querySelector('.thumb[data-file="' + CSS.escape(file) + '"]');
            if (el) {
                el.classList.toggle('selected', selected.has(file));
                el.querySelector('.check').innerHTML = selected.has(file) ? '&#10003;' : '';
            }
            updateSelectionBar();
        }

        function selectAllVisible() {
            filtered.forEach(a => selected.add(a.file));
            renderGallery();
        }

        function selectDay(key) {
            filtered.forEach(a => { if (new Date(a.ts).toDateString() === key) selected.add(a.file); });
            renderGallery();
        }

        function clearSelection() {
            selected.clear();
            renderGallery();
        }

        function updateSelectionBar() {
            const bar = document.getElementById('selection-bar');
            bar.classList.toggle('visible', selected.size > 0);
            document.body.classList.toggle('has-selection', selected.size > 0);
            document.getElementById('sel-count').textContent = selected.size + ' selected';
        }

        async function deleteSelected() {
            if (!selected.size) return;
            if (!confirm('Delete ' + selected.size + ' selected alert image(s)? This cannot be undone.')) return;
            await fetch('/api/ai-alerts/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ files: [...selected] })
            });
            selected.clear();
            loadAlerts();
        }

        function downloadSelected() {
            if (!selected.size) return;
            postDownload([...selected]);
        }

        function postDownload(files) {
            // Submit a throwaway form so the browser handles the zip as a download
            const form = document.createElement('form');
            form.method = 'POST'; form.action = '/api/ai-alerts/download';
            const inp = document.createElement('input');
            inp.type = 'hidden'; inp.name = 'files'; inp.value = JSON.stringify(files);
            form.appendChild(inp);
            document.body.appendChild(form);
            form.submit();
            form.remove();
        }

        async function clearAll() {
            if (!confirm('Delete ALL stored AI detection alert images? This cannot be undone.')) return;
            await fetch('/api/ai-alerts', { method: 'DELETE' });
            selected.clear();
            loadAlerts();
        }

        // ---------- Lightbox ----------
        function openLightbox(idx) {
            lbIndex = idx;
            document.getElementById('lightbox').classList.add('open');
            buildFilmstrip();
            showLightbox();
        }

        function closeLightbox() {
            document.getElementById('lightbox').classList.remove('open');
            lbIndex = -1;
        }

        function stepLightbox(dir) {
            if (!filtered.length) return;
            lbIndex = (lbIndex + dir + filtered.length) % filtered.length;
            showLightbox();
        }

        function showLightbox() {
            const a = filtered[lbIndex];
            if (!a) { closeLightbox(); return; }
            document.getElementById('lb-img').src = imgUrl(a.file);
            document.getElementById('lb-cam').textContent = camName(a.camera_id);
            document.getElementById('lb-time').textContent = new Date(a.ts).toLocaleString();
            document.getElementById('lb-counter').textContent = (lbIndex + 1) + ' / ' + filtered.length;
            document.getElementById('lb-tags').innerHTML = (a.tags || []).map(tg =>
                '<span class="tag-chip ' + tagClass(tg) + '">' + tg + '</span>').join('');
            document.querySelectorAll('#lb-filmstrip img').forEach((im, i) => {
                im.classList.toggle('current', i === lbIndex);
                if (i === lbIndex) im.scrollIntoView({ block: 'nearest', inline: 'center', behavior: 'smooth' });
            });
            // Preload neighbours for instant arrow keys
            [lbIndex - 1, lbIndex + 1].forEach(i => {
                const n = filtered[(i + filtered.length) % filtered.length];
                if (n) { const pre = new Image(); pre.src = imgUrl(n.file); }
            });
        }

        function buildFilmstrip() {
            const fs = document.getElementById('lb-filmstrip');
            fs.innerHTML = '';
            filtered.forEach((a, i) => {
                const im = document.createElement('img');
                im.src = imgUrl(a.file);
                im.loading = 'lazy';
                im.onclick = () => { lbIndex = i; showLightbox(); };
                fs.appendChild(im);
            });
        }

        function downloadCurrent() {
            const a = filtered[lbIndex];
            if (!a) return;
            const link = document.createElement('a');
            link.href = imgUrl(a.file);
            link.download = a.file;
            link.click();
        }

        async function deleteCurrent() {
            const a = filtered[lbIndex];
            if (!a) return;
            if (!confirm('Delete this alert image?')) return;
            await fetch('/api/ai-alerts/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ files: [a.file] })
            });
            selected.delete(a.file);
            const keepIndex = lbIndex;
            await loadAlertsKeepLightbox(keepIndex);
        }

        async function loadAlertsKeepLightbox(idx) {
            const data = await (await fetch('/api/ai-alerts')).json();
            allAlerts = data.alerts || [];
            applyFilters();
            if (!filtered.length) { closeLightbox(); return; }
            lbIndex = Math.min(idx, filtered.length - 1);
            buildFilmstrip();
            showLightbox();
        }

        document.addEventListener('keydown', e => {
            if (!document.getElementById('lightbox').classList.contains('open')) {
                if (e.key === 'Escape' && selected.size) clearSelection();
                return;
            }
            if (e.key === 'Escape') closeLightbox();
            else if (e.key === 'ArrowLeft') stepLightbox(-1);
            else if (e.key === 'ArrowRight') stepLightbox(1);
            else if (e.key === 'Delete') deleteCurrent();
        });

        // ---------- Storage cap ----------
        async function saveMaxAlerts(value) {
            try {
                const res = await fetch('/api/ai-alerts/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ max_alerts: parseInt(value) })
                });
                const data = await res.json();
                if (data.max_alerts) {
                    maxAlerts = data.max_alerts;
                    document.getElementById('max-alerts-input').value = maxAlerts;
                    const tick = document.getElementById('storage-saved');
                    tick.classList.add('flash');
                    setTimeout(() => tick.classList.remove('flash'), 1600);
                    loadAlerts(); // lowering the cap prunes immediately
                }
            } catch (e) { /* leave the field as typed; next load re-syncs */ }
        }

        // ---------- Hover preview ----------
        const hp = document.getElementById('hover-preview');
        let hpTimer = null;
        const touchDevice = window.matchMedia('(hover: none)').matches;

        function positionPreview(e) {
            const pad = 18;
            const w = hp.offsetWidth, h = hp.offsetHeight;
            let x = e.clientX + pad, y = e.clientY + pad;
            if (x + w > window.innerWidth - 8) x = e.clientX - w - pad;
            if (y + h > window.innerHeight - 8) y = Math.max(8, window.innerHeight - h - 8);
            if (x < 8) x = 8;
            hp.style.left = x + 'px';
            hp.style.top = y + 'px';
        }

        function hidePreview() {
            clearTimeout(hpTimer); hpTimer = null;
            hp.classList.remove('visible');
        }

        if (!touchDevice) {
            const gallery = document.getElementById('gallery');
            gallery.addEventListener('mouseover', e => {
                const thumb = e.target.closest('.thumb');
                if (!thumb) return;
                clearTimeout(hpTimer);
                hpTimer = setTimeout(() => {
                    const a = filtered[parseInt(thumb.dataset.idx)];
                    if (!a || document.getElementById('lightbox').classList.contains('open')) return;
                    document.getElementById('hp-img').src = imgUrl(a.file);
                    document.getElementById('hp-cam').textContent = camName(a.camera_id);
                    document.getElementById('hp-time').textContent = new Date(a.ts).toLocaleString();
                    hp.classList.add('visible');
                    positionPreview(e);
                }, 280);
            });
            gallery.addEventListener('mousemove', e => {
                if (hp.classList.contains('visible')) positionPreview(e);
            });
            gallery.addEventListener('mouseout', e => {
                if (!e.relatedTarget || !e.relatedTarget.closest || !e.relatedTarget.closest('.thumb')) hidePreview();
            });
            gallery.addEventListener('click', hidePreview);
            window.addEventListener('scroll', hidePreview, { passive: true });
        }

        // ---------- Live refresh ----------
        function toggleLive() {
            const btn = document.getElementById('btn-live');
            if (liveTimer) {
                clearInterval(liveTimer); liveTimer = null;
                btn.textContent = 'Live: Off'; btn.classList.remove('live-on');
            } else {
                liveTimer = setInterval(loadAlerts, 10000);
                btn.textContent = 'Live: On'; btn.classList.add('live-on');
                loadAlerts();
            }
        }

        // ---------- Init ----------
        async function initSize() {
            let size = 220;
            try {
                const settings = await (await fetch('/api/settings')).json();
                if (settings.alertsThumbSize) {
                    size = settings.alertsThumbSize;
                } else {
                    const localSize = localStorage.getItem('alerts-thumb-size');
                    if (localSize) size = localSize;
                }
            } catch (e) {
                const localSize = localStorage.getItem('alerts-thumb-size');
                if (localSize) size = localSize;
            }
            document.getElementById('thumb-size').value = size;
            setThumbSize(size);
        }
        initSize();
        loadCameras().then(loadAlerts);
    </script>
</body>
</html>
'''
