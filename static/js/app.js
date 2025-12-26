/**
 * Tonys Onvif-RTSP Server - Web UI Application
 * Main application logic for camera management dashboard
 */

// ============================================================================
// Global State
// ============================================================================

let cameras = [];
let settings = {};
let matrixActive = false;
let isLinux = false;

// HLS player management
const hlsPlayers = new Map();
const recoveryAttempts = new Map();

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', async () => {
    await init();
});

async function init() {
    try {
        // Detect platform
        await detectPlatform();

        // Load initial data
        await loadData();

        // Apply saved theme
        applyTheme(settings.theme || 'light');

        // Apply grid layout
        applyGridLayout(settings.gridColumns || 3);

        // Update stats
        await updateStats();

        // Setup auto-refresh
        setInterval(loadData, 5000);
        setInterval(updateStats, 3000);

        // Setup theme toggle
        setupThemeToggle();

        // Setup keyboard shortcuts
        setupKeyboardShortcuts();

        console.log('Tonys Onvif-RTSP Server UI initialized');
    } catch (error) {
        console.error('Initialization error:', error);
        showToast('Failed to initialize application', 'error');
    }
}

async function detectPlatform() {
    try {
        const response = await fetch('/api/settings');
        if (response.ok) {
            const data = await response.json();
            // Check if Linux-specific features should be shown
            // This is determined by checking if network interfaces endpoint works
            try {
                const netResponse = await fetch('/api/network/interfaces');
                const interfaces = await netResponse.json();
                isLinux = Array.isArray(interfaces) && interfaces.length > 0;
            } catch {
                isLinux = false;
            }
        }
    } catch (error) {
        console.error('Platform detection failed:', error);
    }

    // Hide Linux-only sections if not on Linux
    if (!isLinux) {
        const linuxSections = document.querySelectorAll('.linux-only, #linux-network-section');
        linuxSections.forEach(section => section.style.display = 'none');
    }
}

// ============================================================================
// Data Loading
// ============================================================================

async function loadData() {
    try {
        // Fetch settings
        const settingsResp = await fetch('/api/settings?t=' + Date.now());
        if (settingsResp.ok) {
            const newSettings = await settingsResp.json();
            if (newSettings && typeof newSettings === 'object') {
                // Preserve server IP logic
                const newIp = newSettings.serverIp;
                const storedIp = localStorage.getItem('onvif_last_good_ip');

                if (newIp && newIp !== 'localhost') {
                    localStorage.setItem('onvif_last_good_ip', newIp);
                } else if (storedIp && storedIp !== 'localhost' && (!newIp || newIp === 'localhost')) {
                    newSettings.serverIp = storedIp;
                }

                settings = newSettings;
            }
        }

        // Fetch cameras
        const camerasResp = await fetch('/api/cameras?t=' + Date.now());
        if (camerasResp.ok) {
            const newCameras = await camerasResp.json();
            if (Array.isArray(newCameras)) {
                cameras = newCameras;
            }
        }

        // Render UI
        renderCameras();
        if (matrixActive) {
            renderMatrix();
        }
    } catch (error) {
        console.error('Error loading data:', error);
    }
}

// ============================================================================
// Camera Rendering
// ============================================================================

function renderCameras() {
    const list = document.getElementById('camera-list');
    const empty = document.getElementById('empty-state');

    if (cameras.length === 0) {
        list.style.display = 'none';
        empty.classList.remove('hidden');
        list.innerHTML = '';
        return;
    }

    list.style.display = 'grid';
    empty.classList.add('hidden');

    // Determine server IP
    const serverIp = getServerIp();

    // Track existing camera IDs
    const currentIds = new Set(cameras.map(c => c.id.toString()));

    // Remove deleted cameras
    Array.from(list.children).forEach(card => {
        if (!currentIds.has(card.dataset.id)) {
            card.remove();
        }
    });

    // Render each camera
    cameras.forEach(cam => {
        let card = list.querySelector(`.camera-card[data-id="${cam.id}"]`);
        const content = getCameraCardContent(cam, serverIp);

        if (!card) {
            // New camera
            card = document.createElement('div');
            card.className = `camera-card ${cam.status === 'running' ? 'running' : ''}`;
            card.dataset.id = cam.id;
            card.dataset.status = cam.status;
            card.innerHTML = content;
            list.appendChild(card);

            if (cam.status === 'running') {
                initVideoPlayer(cam.id, cam.pathName);
            }
        } else {
            // Existing camera - check for status change
            if (card.dataset.status !== cam.status) {
                card.className = `camera-card ${cam.status === 'running' ? 'running' : ''}`;
                card.dataset.status = cam.status;
                card.innerHTML = content;

                if (cam.status === 'running') {
                    initVideoPlayer(cam.id, cam.pathName);
                }
            } else {
                // Update text elements without touching video
                const nameEl = card.querySelector('.camera-name');
                if (nameEl && nameEl.textContent !== cam.name) {
                    nameEl.textContent = cam.name;
                }

                const autoStartEl = card.querySelector('.toggle-switch input');
                if (autoStartEl && autoStartEl.checked !== cam.autoStart) {
                    autoStartEl.checked = cam.autoStart;
                }

                // Update info section
                const infoSection = card.querySelector('.info-section');
                if (infoSection) {
                    const tempDiv = document.createElement('div');
                    tempDiv.innerHTML = content;
                    const newInfoSection = tempDiv.querySelector('.info-section');
                    if (newInfoSection) {
                        infoSection.innerHTML = newInfoSection.innerHTML;
                    }
                }
            }
        }
    });
}

function getCameraCardContent(cam, serverIp) {
    const displayIp = cam.assignedIp || serverIp;
    const rtspPort = settings.rtspPort || 8554;

    return `
        <div class="p-6">
            <div class="flex items-start justify-between mb-4">
                <div class="flex-1">
                    <div class="flex items-center gap-3 mb-2">
                        <div class="status-badge ${cam.status === 'running' ? 'running' : ''}"></div>
                        <h3 class="camera-name text-lg font-bold text-slate-800 dark:text-white">${escapeHtml(cam.name)}</h3>
                    </div>
                    <div class="flex flex-wrap gap-2">
                        ${cam.assignedIp ? `<span class="text-xs bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-300 px-2 py-1 rounded-full">&#127760; ${cam.assignedIp}</span>` : ''}
                        ${cam.useVirtualNic && cam.nicMac ? `<span class="text-xs bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400 px-2 py-1 rounded-full">&#127380; ${cam.nicMac}</span>` : ''}
                    </div>
                </div>
                <div class="flex gap-1">
                    ${cam.status === 'running'
                        ? `<button class="icon-btn" onclick="stopCamera(${cam.id})" title="Stop">&#9209;</button>`
                        : `<button class="icon-btn" onclick="startCamera(${cam.id})" title="Start">&#9654;</button>`
                    }
                    <button class="icon-btn" onclick="openEditModal(${cam.id})" title="Edit">&#9998;</button>
                    <button class="icon-btn" onclick="deleteCamera(${cam.id})" title="Delete">&#128465;</button>
                </div>
            </div>

            <div class="video-preview mb-4" id="video-${cam.id}">
                ${cam.status === 'running'
                    ? `<video id="player-${cam.id}" autoplay muted playsinline></video>
                       <button class="fullscreen-btn" onclick="toggleFullScreenPlayer(${cam.id})">&#9974; Full Screen</button>`
                    : `<div class="video-placeholder">
                        <div class="text-4xl mb-2">&#128249;</div>
                        <div class="text-sm">Camera Stopped</div>
                       </div>`
                }
            </div>

            <div class="info-section">
                <div class="mb-3">
                    <div class="info-label">&#127916; RTSP Main Stream</div>
                    <div class="info-value">
                        <span class="truncate">rtsp://${displayIp}:${rtspPort}/${cam.pathName}_main</span>
                        <button class="copy-btn" onclick="copyToClipboard('rtsp://${displayIp}:${rtspPort}/${cam.pathName}_main')">&#128203;</button>
                    </div>
                </div>

                <div class="mb-3">
                    <div class="info-label">&#128241; RTSP Sub Stream</div>
                    <div class="info-value">
                        <span class="truncate">rtsp://${displayIp}:${rtspPort}/${cam.pathName}_sub</span>
                        <button class="copy-btn" onclick="copyToClipboard('rtsp://${displayIp}:${rtspPort}/${cam.pathName}_sub')">&#128203;</button>
                    </div>
                </div>

                <div>
                    <div class="info-label">&#128268; ONVIF Service</div>
                    <div class="info-value">
                        <span class="flex items-center gap-2">
                            ${displayIp}:${cam.onvifPort}
                            <span class="text-xs text-slate-500">&#128100; ${cam.onvifUsername} / &#128273; ${cam.onvifPassword}</span>
                        </span>
                        <button class="copy-btn" onclick="copyToClipboard('${displayIp}:${cam.onvifPort}')">&#128203;</button>
                    </div>
                </div>
            </div>

            <div class="auto-start-row">
                <span class="text-sm text-slate-600 dark:text-slate-300 font-medium">&#128640; Auto-start on server startup</span>
                <label class="toggle-switch">
                    <input type="checkbox" ${cam.autoStart ? 'checked' : ''} onchange="toggleAutoStart(${cam.id}, this.checked)">
                    <span class="toggle-slider"></span>
                </label>
            </div>
        </div>
    `;
}

function getServerIp() {
    const configIp = settings.serverIp;
    const storedIp = localStorage.getItem('onvif_last_good_ip');
    const browserIp = window.location.hostname;

    if (configIp && configIp !== 'localhost' && configIp !== '127.0.0.1') {
        return configIp;
    } else if (storedIp && storedIp !== 'localhost') {
        return storedIp;
    } else if (browserIp && browserIp !== 'localhost' && browserIp !== '127.0.0.1') {
        return browserIp;
    }
    return configIp || 'localhost';
}

// ============================================================================
// Video Player
// ============================================================================

function initVideoPlayer(cameraId, pathName, explicitId = null) {
    const videoId = explicitId || `player-${cameraId}`;
    const videoElement = document.getElementById(videoId);
    if (!videoElement) return;

    // Clean up existing player
    const existingPlayer = hlsPlayers.get(videoId);
    if (existingPlayer) {
        try {
            existingPlayer.destroy();
        } catch (e) {
            console.warn('Error destroying existing player:', e);
        }
        hlsPlayers.delete(videoId);
    }

    let serverIp = settings.serverIp || window.location.hostname || 'localhost';

    // Smart IP override
    if (serverIp === 'localhost' && window.location.hostname &&
        window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
        serverIp = window.location.hostname;
    }

    const streamUrl = `http://${serverIp}:8888/${pathName}_sub/index.m3u8`;

    if (videoElement.canPlayType('application/vnd.apple.mpegurl')) {
        // Native HLS support (Safari)
        videoElement.src = streamUrl;
    } else if (typeof Hls !== 'undefined') {
        const hls = new Hls({
            debug: false,
            enableWorker: true,
            maxBufferLength: 10,
            maxMaxBufferLength: 20,
            maxBufferSize: 20 * 1000 * 1000,
            maxBufferHole: 0.3,
            backBufferLength: 5,
            liveSyncDurationCount: 2,
            liveMaxLatencyDurationCount: 6,
            manifestLoadingTimeOut: 15000,
            manifestLoadingMaxRetry: 4,
            manifestLoadingRetryDelay: 1000,
            levelLoadingTimeOut: 15000,
            levelLoadingMaxRetry: 4,
            fragLoadingTimeOut: 20000,
            fragLoadingMaxRetry: 4,
            lowLatencyMode: false,
            progressive: true,
            abrEwmaDefaultEstimate: 500000,
            abrBandWidthFactor: 0.95,
            abrBandWidthUpFactor: 0.7,
        });

        hlsPlayers.set(videoId, hls);
        recoveryAttempts.set(videoId, 0);

        hls.loadSource(streamUrl);
        hls.attachMedia(videoElement);

        // Error handling
        hls.on(Hls.Events.ERROR, function(event, data) {
            console.log(`HLS Error [${videoId}]:`, data.type, data.details, data.fatal);

            if (data.fatal) {
                const attempts = recoveryAttempts.get(videoId) || 0;
                const maxAttempts = 5;

                switch(data.type) {
                    case Hls.ErrorTypes.NETWORK_ERROR:
                        if (attempts < maxAttempts) {
                            recoveryAttempts.set(videoId, attempts + 1);
                            const delay = Math.min(1000 * Math.pow(2, attempts), 16000);
                            setTimeout(() => hls.startLoad(), delay);
                        } else {
                            showVideoError(cameraId, 'Network connection failed');
                            hls.destroy();
                            hlsPlayers.delete(videoId);
                        }
                        break;

                    case Hls.ErrorTypes.MEDIA_ERROR:
                        if (attempts < maxAttempts) {
                            recoveryAttempts.set(videoId, attempts + 1);
                            hls.recoverMediaError();
                        } else {
                            showVideoError(cameraId, 'Media playback error');
                            hls.destroy();
                            hlsPlayers.delete(videoId);
                        }
                        break;

                    default:
                        showVideoError(cameraId, 'Playback error');
                        hls.destroy();
                        hlsPlayers.delete(videoId);
                        break;
                }
            }
        });

        hls.on(Hls.Events.MANIFEST_LOADED, () => {
            recoveryAttempts.set(videoId, 0);
        });
    } else {
        showVideoError(cameraId, 'HLS not supported');
    }
}

function showVideoError(cameraId, message) {
    const container = document.getElementById(`video-${cameraId}`);
    if (container) {
        container.innerHTML = `
            <div class="video-placeholder">
                <div class="text-4xl mb-2">&#9888;</div>
                <div class="text-sm">${message}</div>
                <div class="text-xs text-slate-400 mt-1">Check camera connection</div>
            </div>
        `;
    }
}

function toggleFullScreenPlayer(cameraId) {
    const video = document.getElementById(`player-${cameraId}`);
    if (!video) return;

    if (video.requestFullscreen) {
        video.requestFullscreen();
    } else if (video.webkitRequestFullscreen) {
        video.webkitRequestFullscreen();
    } else if (video.webkitEnterFullscreen) {
        video.webkitEnterFullscreen();
    }
}

// ============================================================================
// Matrix View
// ============================================================================

function toggleMatrixView(active) {
    matrixActive = active;
    const overlay = document.getElementById('matrix-overlay');

    if (active) {
        overlay.classList.remove('hidden');
        overlay.classList.add('flex');
        renderMatrix();
    } else {
        overlay.classList.add('hidden');
        overlay.classList.remove('flex');
        document.getElementById('matrix-grid').innerHTML = '';
    }
}

function renderMatrix() {
    const grid = document.getElementById('matrix-grid');
    const runningCameras = cameras.filter(c => c.status === 'running');

    if (runningCameras.length === 0) {
        grid.innerHTML = '<div class="text-white col-span-full text-center pt-20">No cameras are currently running.</div>';
        return;
    }

    const count = runningCameras.length;
    let cols = 1;
    if (count > 9) cols = 4;
    else if (count > 4) cols = 3;
    else if (count > 1) cols = 2;

    grid.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;

    // Check if re-render is needed
    const currentIds = Array.from(grid.querySelectorAll('.matrix-item')).map(el => el.dataset.id).join(',');
    const newIds = runningCameras.map(c => c.id).join(',');

    if (currentIds === newIds) return;

    grid.innerHTML = runningCameras.map(cam => `
        <div class="matrix-item" data-id="${cam.id}">
            <div class="matrix-label">${escapeHtml(cam.name)}</div>
            <video id="matrix-player-${cam.id}" autoplay muted playsinline></video>
        </div>
    `).join('');

    runningCameras.forEach(cam => {
        initVideoPlayer(cam.id, cam.pathName, `matrix-player-${cam.id}`);
    });
}

function toggleFullScreen() {
    const elem = document.getElementById('matrix-overlay');
    if (!document.fullscreenElement) {
        elem.requestFullscreen().catch(err => {
            showToast(`Fullscreen error: ${err.message}`, 'error');
        });
    } else {
        document.exitFullscreen();
    }
}

// ============================================================================
// Camera Operations
// ============================================================================

async function startCamera(id) {
    showLoading('Starting camera...');
    try {
        await fetch(`/api/cameras/${id}/start`, { method: 'POST' });
        await loadData();
        showToast('Camera started', 'success');
    } catch (error) {
        console.error('Error starting camera:', error);
        showToast('Failed to start camera', 'error');
    } finally {
        hideLoading();
    }
}

async function stopCamera(id) {
    showLoading('Stopping camera...');
    try {
        await fetch(`/api/cameras/${id}/stop`, { method: 'POST' });
        await loadData();
        showToast('Camera stopped', 'success');
    } catch (error) {
        console.error('Error stopping camera:', error);
        showToast('Failed to stop camera', 'error');
    } finally {
        hideLoading();
    }
}

async function deleteCamera(id) {
    if (!confirm('Are you sure you want to delete this camera?')) return;

    showLoading('Deleting camera...');
    try {
        await fetch(`/api/cameras/${id}`, { method: 'DELETE' });
        await loadData();
        showToast('Camera deleted', 'success');
    } catch (error) {
        console.error('Error deleting camera:', error);
        showToast('Failed to delete camera', 'error');
    } finally {
        hideLoading();
    }
}

async function startAll() {
    showLoading('Starting all cameras...');
    try {
        await fetch('/api/cameras/start-all', { method: 'POST' });
        await loadData();
        showToast('All cameras started', 'success');
    } catch (error) {
        console.error('Error starting all cameras:', error);
        showToast('Failed to start cameras', 'error');
    } finally {
        hideLoading();
    }
}

async function stopAll() {
    showLoading('Stopping all cameras...');
    try {
        await fetch('/api/cameras/stop-all', { method: 'POST' });
        await loadData();
        showToast('All cameras stopped', 'success');
    } catch (error) {
        console.error('Error stopping all cameras:', error);
        showToast('Failed to stop cameras', 'error');
    } finally {
        hideLoading();
    }
}

async function toggleAutoStart(id, autoStart) {
    try {
        const response = await fetch(`/api/cameras/${id}/auto-start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ autoStart })
        });

        if (response.ok) {
            await loadData();
        } else {
            const error = await response.json();
            showToast(`Failed: ${error.error}`, 'error');
            await loadData();
        }
    } catch (error) {
        console.error('Error toggling auto-start:', error);
        showToast('Error updating auto-start', 'error');
        await loadData();
    }
}

// ============================================================================
// Modals
// ============================================================================

async function openAddModal() {
    document.getElementById('modal-title').textContent = 'Add New Camera';
    document.getElementById('camera-id').value = '';
    document.getElementById('camera-form').reset();

    // Reset checkboxes
    document.getElementById('transcodeSub').checked = false;
    document.getElementById('transcodeMain').checked = false;
    document.getElementById('useVirtualNic').checked = false;
    document.getElementById('ipMode').value = 'dhcp';

    if (isLinux) {
        await detectNetworkInterfaces();
        document.getElementById('manual-interface-container').classList.add('hidden');
    }

    toggleNetworkFields();

    // Show copy dropdown
    document.getElementById('copy-from-group').style.display = 'block';

    // Populate copy dropdown
    const copySelect = document.getElementById('copyFrom');
    copySelect.innerHTML = '<option value="">Select a camera to copy...</option>';
    cameras.forEach(cam => {
        const option = document.createElement('option');
        option.value = cam.id;
        option.textContent = cam.name;
        copySelect.appendChild(option);
    });

    // Switch to manual mode
    switchAddMode('manual');

    document.getElementById('camera-modal').classList.add('active');
}

async function openEditModal(id) {
    document.getElementById('copy-from-group').style.display = 'none';

    const camera = cameras.find(c => c.id === id);
    if (!camera) return;

    document.getElementById('modal-title').textContent = 'Edit Camera';
    document.getElementById('camera-id').value = camera.id;

    // Parse RTSP URL
    const mainUrl = new URL(camera.mainStreamUrl.replace('rtsp://', 'http://'));
    const subUrl = new URL(camera.subStreamUrl.replace('rtsp://', 'http://'));

    // Populate form fields
    document.getElementById('name').value = camera.name;
    document.getElementById('host').value = mainUrl.hostname;
    document.getElementById('rtspPort').value = mainUrl.port || '554';
    document.getElementById('username').value = decodeURIComponent(mainUrl.username || '');
    document.getElementById('password').value = decodeURIComponent(mainUrl.password || '');
    document.getElementById('mainPath').value = mainUrl.pathname + mainUrl.search;
    document.getElementById('subPath').value = subUrl.pathname + subUrl.search;
    document.getElementById('autoStart').checked = camera.autoStart || false;

    // Resolution fields
    document.getElementById('mainWidth').value = camera.mainWidth || 1920;
    document.getElementById('mainHeight').value = camera.mainHeight || 1080;
    document.getElementById('subWidth').value = camera.subWidth || 640;
    document.getElementById('subHeight').value = camera.subHeight || 480;
    document.getElementById('mainFramerate').value = camera.mainFramerate || 30;
    document.getElementById('subFramerate').value = camera.subFramerate || 15;
    document.getElementById('transcodeSub').checked = camera.transcodeSub || false;
    document.getElementById('transcodeMain').checked = camera.transcodeMain || false;

    // ONVIF fields
    document.getElementById('onvifPort').value = camera.onvifPort || '';
    document.getElementById('onvifUsername').value = camera.onvifUsername || 'admin';
    document.getElementById('onvifPassword').value = camera.onvifPassword || 'admin';

    // Network fields
    document.getElementById('useVirtualNic').checked = camera.useVirtualNic || false;
    document.getElementById('nicMac').value = camera.nicMac || '';
    document.getElementById('ipMode').value = camera.ipMode || 'dhcp';
    document.getElementById('staticIp').value = camera.staticIp || '';
    document.getElementById('netmask').value = camera.netmask || '24';
    document.getElementById('gateway').value = camera.gateway || '';

    if (isLinux) {
        await detectNetworkInterfaces();
        const select = document.getElementById('parentInterface');
        const val = camera.parentInterface || '';

        let found = false;
        for (let i = 0; i < select.options.length; i++) {
            if (select.options[i].value === val) {
                select.value = val;
                found = true;
                break;
            }
        }

        if (!found && val) {
            select.value = '__manual__';
            document.getElementById('parentInterfaceManual').value = val;
            document.getElementById('manual-interface-container').classList.remove('hidden');
        }
    }

    toggleNetworkFields();
    switchAddMode('manual');

    document.getElementById('camera-modal').classList.add('active');
}

function closeModal() {
    document.getElementById('camera-modal').classList.remove('active');
    document.getElementById('camera-form').reset();
}

async function saveCamera(event) {
    event.preventDefault();

    const cameraId = document.getElementById('camera-id').value;
    const isEdit = cameraId !== '';

    const data = {
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
        onvifUsername: document.getElementById('onvifUsername').value,
        onvifPassword: document.getElementById('onvifPassword').value,
        useVirtualNic: document.getElementById('useVirtualNic').checked,
        parentInterface: document.getElementById('parentInterface').value === '__manual__'
            ? document.getElementById('parentInterfaceManual').value
            : document.getElementById('parentInterface').value,
        nicMac: document.getElementById('nicMac').value,
        ipMode: document.getElementById('ipMode').value,
        staticIp: document.getElementById('staticIp').value,
        netmask: document.getElementById('netmask').value,
        gateway: document.getElementById('gateway').value
    };

    const onvifPort = document.getElementById('onvifPort').value;
    if (onvifPort) {
        data.onvifPort = parseInt(onvifPort);
    }

    showLoading(isEdit ? 'Updating camera...' : 'Adding camera...');

    try {
        const url = isEdit ? `/api/cameras/${cameraId}` : '/api/cameras';
        const method = isEdit ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            closeModal();
            await loadData();
            showToast(isEdit ? 'Camera updated' : 'Camera added', 'success');
        } else {
            const error = await response.json();
            showToast(`Error: ${error.error}`, 'error');
        }
    } catch (error) {
        console.error('Error saving camera:', error);
        showToast('Failed to save camera', 'error');
    } finally {
        hideLoading();
    }
}

function copyCameraSettings(id) {
    if (!id) return;

    const camera = cameras.find(c => c.id === parseInt(id));
    if (!camera) return;

    try {
        const mainUrl = new URL(camera.mainStreamUrl.replace('rtsp://', 'http://'));
        const subUrl = new URL(camera.subStreamUrl.replace('rtsp://', 'http://'));

        document.getElementById('host').value = mainUrl.hostname;
        document.getElementById('rtspPort').value = mainUrl.port || '554';
        document.getElementById('username').value = decodeURIComponent(mainUrl.username || '');
        document.getElementById('password').value = decodeURIComponent(mainUrl.password || '');
        document.getElementById('mainPath').value = mainUrl.pathname + mainUrl.search;
        document.getElementById('subPath').value = subUrl.pathname + subUrl.search;
        document.getElementById('autoStart').checked = camera.autoStart || false;
        document.getElementById('mainWidth').value = camera.mainWidth || 1920;
        document.getElementById('mainHeight').value = camera.mainHeight || 1080;
        document.getElementById('subWidth').value = camera.subWidth || 640;
        document.getElementById('subHeight').value = camera.subHeight || 480;
        document.getElementById('mainFramerate').value = camera.mainFramerate || 30;
        document.getElementById('subFramerate').value = camera.subFramerate || 15;
        document.getElementById('onvifPort').value = '';
        document.getElementById('onvifUsername').value = camera.onvifUsername || 'admin';
        document.getElementById('onvifPassword').value = camera.onvifPassword || 'admin';

        showToast(`Settings copied from ${camera.name}`, 'info');
    } catch (e) {
        console.error('Error copying settings:', e);
        showToast('Error copying settings', 'error');
    }
}

// ============================================================================
// Settings Modal
// ============================================================================

function openSettingsModal() {
    loadSettingsForm();
    document.getElementById('settings-modal').classList.add('active');
}

function closeSettingsModal() {
    document.getElementById('settings-modal').classList.remove('active');
}

function loadSettingsForm() {
    document.getElementById('serverIp').value = settings.serverIp || 'localhost';
    document.getElementById('rtspPortSettings').value = settings.rtspPort || 8554;
    document.getElementById('themeSelect').value = settings.theme || 'light';
    document.getElementById('gridColumnsSelect').value = settings.gridColumns || 3;
    document.getElementById('openBrowser').checked = settings.openBrowser !== false;

    const autoBootField = document.getElementById('autoBoot');
    if (autoBootField) {
        autoBootField.checked = settings.autoBoot === true;
    }

    // Auto-detect server IP
    const serverIpField = document.getElementById('serverIp');
    if (!serverIpField.value || serverIpField.value === 'localhost') {
        const detectedIp = window.location.hostname;
        if (detectedIp && detectedIp !== 'localhost' && detectedIp !== '127.0.0.1') {
            serverIpField.placeholder = `Auto-detected: ${detectedIp}`;
        }
    }
}

async function saveSettings(event) {
    event.preventDefault();

    const data = {
        serverIp: document.getElementById('serverIp').value || 'localhost',
        openBrowser: document.getElementById('openBrowser').checked,
        theme: document.getElementById('themeSelect').value,
        gridColumns: parseInt(document.getElementById('gridColumnsSelect').value),
        rtspPort: parseInt(document.getElementById('rtspPortSettings').value || 8554),
        autoBoot: document.getElementById('autoBoot')?.checked || false
    };

    showLoading('Saving settings...');

    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            closeSettingsModal();
            settings = data;
            applyTheme(data.theme);
            applyGridLayout(data.gridColumns);
            showToast('Settings saved', 'success');
        } else {
            const error = await response.json();
            showToast(`Error: ${error.error}`, 'error');
        }
    } catch (error) {
        console.error('Error saving settings:', error);
        showToast('Failed to save settings', 'error');
    } finally {
        hideLoading();
    }
}

// ============================================================================
// About Modal
// ============================================================================

function openAboutModal() {
    document.getElementById('about-modal').classList.add('active');
}

function closeAboutModal() {
    document.getElementById('about-modal').classList.remove('active');
}

// ============================================================================
// Server Operations
// ============================================================================

async function restartServer() {
    if (!confirm('Are you sure you want to restart the server?')) return;

    try {
        const response = await fetch('/api/server/restart', { method: 'POST' });
        if (response.ok) {
            showToast('Server restarting... Page will reload in 10 seconds', 'info');
            setTimeout(() => window.location.reload(), 10000);
        } else {
            showToast('Failed to restart server', 'error');
        }
    } catch (error) {
        console.error('Error restarting server:', error);
        showToast('Error restarting server', 'error');
    }
}

async function stopServer() {
    if (!confirm('Are you sure you want to stop the server? This will shut down all camera streams and the web interface.')) {
        return;
    }

    try {
        await fetch('/api/server/stop', { method: 'POST' });
        document.body.innerHTML = `
            <div class="min-h-screen bg-slate-900 flex flex-col items-center justify-center text-white">
                <h1 class="text-3xl font-bold mb-4">&#9209; Server Stopped</h1>
                <p class="text-slate-400">The ONVIF server has been shut down successfully.</p>
                <p class="text-slate-500 mt-4 text-sm">You can safely close this browser tab.</p>
            </div>
        `;
    } catch (error) {
        document.body.innerHTML = `
            <div class="min-h-screen bg-slate-900 flex flex-col items-center justify-center text-white">
                <h1 class="text-3xl font-bold mb-4">&#9209; Server Stopped</h1>
                <p class="text-slate-400">The ONVIF server has been shut down successfully.</p>
                <p class="text-slate-500 mt-4 text-sm">You can safely close this browser tab.</p>
            </div>
        `;
    }
}

// ============================================================================
// Stats
// ============================================================================

async function updateStats() {
    try {
        const resp = await fetch('/api/stats');
        const stats = await resp.json();
        if (stats.cpu_percent !== undefined) {
            const statsEl = document.getElementById('server-stats');
            if (statsEl) {
                statsEl.innerHTML = `
                    <span class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                    <span>CPU: ${stats.cpu_percent}% | MEM: ${stats.memory_mb}MB</span>
                `;
            }
        }
    } catch (e) {
        console.error('Stats fetch failed:', e);
    }
}

// ============================================================================
// ONVIF Probe
// ============================================================================

function switchAddMode(mode) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.getElementById('tab-' + mode).classList.add('active');

    if (mode === 'manual') {
        document.getElementById('camera-form').style.display = 'block';
        document.getElementById('onvif-probe-form').classList.add('hidden');
    } else {
        document.getElementById('camera-form').style.display = 'none';
        document.getElementById('onvif-probe-form').classList.remove('hidden');
    }
}

async function probeOnvif() {
    const host = document.getElementById('probeHost').value;
    const port = document.getElementById('probePort').value;
    const user = document.getElementById('probeUser').value;
    const pass = document.getElementById('probePass').value;
    const btn = document.getElementById('btnProbe');
    const resultsDiv = document.getElementById('probe-results');

    if (!host) {
        showToast('Host IP is required', 'error');
        return;
    }

    btn.disabled = true;
    btn.textContent = 'Scanning...';
    resultsDiv.innerHTML = '<div class="text-center text-slate-500 dark:text-slate-400 py-4">Connecting to camera...</div>';

    try {
        const resp = await fetch('/api/onvif/probe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ host, port, username: user, password: pass })
        });

        const data = await resp.json();

        if (resp.ok) {
            if (data.profiles.length === 0) {
                resultsDiv.innerHTML = '<p class="text-slate-500 dark:text-slate-400 py-4">No profiles found.</p>';
            } else {
                resultsDiv.innerHTML = `
                    <h4 class="font-semibold text-slate-800 dark:text-white mb-2">Found Profiles:</h4>
                    <p class="text-xs text-slate-500 dark:text-slate-400 mb-4">Click to use profile</p>
                    ${data.profiles.map(p => `
                        <div class="result-item">
                            <div class="mb-3">
                                <strong class="text-slate-800 dark:text-white">${escapeHtml(p.name)}</strong>
                                <span class="text-slate-500 dark:text-slate-400">(${p.width}x${p.height} @ ${p.framerate}fps)</span>
                                <div class="text-xs text-slate-400 dark:text-slate-500 break-all mt-1">${escapeHtml(p.streamUrl)}</div>
                            </div>
                            <div class="flex gap-2">
                                <button type="button" class="btn-primary text-sm py-1.5" onclick='applyProfile(${JSON.stringify(p).replace(/'/g, "&#39;")}, "${data.device_info.host}", "${data.device_info.port}", "main", this)'>Set as Main</button>
                                <button type="button" class="btn-secondary text-sm py-1.5" onclick='applyProfile(${JSON.stringify(p).replace(/'/g, "&#39;")}, "${data.device_info.host}", "${data.device_info.port}", "sub", this)'>Set as Sub</button>
                            </div>
                        </div>
                    `).join('')}
                `;
            }
        } else {
            resultsDiv.innerHTML = `<div class="alert-danger">${escapeHtml(data.error || 'Unknown error')}</div>`;
        }
    } catch (e) {
        resultsDiv.innerHTML = `<div class="alert-danger">Connection Error: ${escapeHtml(e.message)}</div>`;
    } finally {
        btn.disabled = false;
        btn.textContent = '&#128269; Scan Camera';
    }
}

function applyProfile(profile, host, port, target, btn) {
    document.getElementById('host').value = host;
    document.getElementById('username').value = document.getElementById('probeUser').value;
    document.getElementById('password').value = document.getElementById('probePass').value;

    let path = profile.streamUrl;
    try {
        const url = new URL(profile.streamUrl);
        path = url.pathname + url.search;
    } catch (e) {
        if (path.includes(host)) {
            path = path.substring(path.indexOf(host) + host.length);
            if (path.startsWith(':')) {
                path = path.substring(path.indexOf('/'));
            }
        }
    }

    if (target === 'main') {
        document.getElementById('mainPath').value = path;
        document.getElementById('mainWidth').value = profile.width;
        document.getElementById('mainHeight').value = profile.height;
        document.getElementById('mainFramerate').value = profile.framerate;
    } else {
        document.getElementById('subPath').value = path;
        document.getElementById('subWidth').value = profile.width;
        document.getElementById('subHeight').value = profile.height;
        document.getElementById('subFramerate').value = profile.framerate;
    }

    if (btn) {
        const originalText = btn.textContent;
        btn.textContent = '&#10003; Set!';
        btn.classList.add('bg-emerald-600');
        setTimeout(() => {
            btn.textContent = originalText;
            btn.classList.remove('bg-emerald-600');
        }, 2000);
    }

    showToast(`Profile applied to ${target} stream`, 'success');
}

// ============================================================================
// Stream Info
// ============================================================================

async function fetchStreamInfo(streamType) {
    const cameraId = document.getElementById('camera-id').value;

    if (!cameraId) {
        showToast('Please save the camera first, then use fetch button when editing', 'info');
        return;
    }

    showLoading('Fetching stream info...');

    try {
        const response = await fetch(`/api/cameras/${cameraId}/fetch-stream-info`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ streamType })
        });

        if (response.ok) {
            const data = await response.json();

            if (streamType === 'main') {
                document.getElementById('mainWidth').value = data.width;
                document.getElementById('mainHeight').value = data.height;
                document.getElementById('mainFramerate').value = data.framerate;
            } else {
                document.getElementById('subWidth').value = data.width;
                document.getElementById('subHeight').value = data.height;
                document.getElementById('subFramerate').value = data.framerate;
            }

            showToast(`${streamType} stream: ${data.width}x${data.height} @ ${data.framerate}fps`, 'success');
        } else {
            const error = await response.json();
            let msg = error.error || 'Unknown error';
            if (error.troubleshooting) {
                msg += '\n' + error.troubleshooting.join('\n');
            }
            showToast(msg, 'error');
        }
    } catch (error) {
        console.error('Error fetching stream info:', error);
        showToast('Failed to fetch stream info', 'error');
    } finally {
        hideLoading();
    }
}

// ============================================================================
// Network Settings
// ============================================================================

async function detectNetworkInterfaces() {
    if (!isLinux) return;

    const select = document.getElementById('parentInterface');
    if (!select) return;

    try {
        const response = await fetch('/api/network/interfaces');
        const interfaces = await response.json();

        select.innerHTML = '<option value="">-- Select Interface --</option>';
        if (interfaces && interfaces.length > 0) {
            interfaces.forEach(iface => {
                const option = document.createElement('option');
                option.value = iface;
                option.textContent = iface;
                select.appendChild(option);
            });
        }

        const manualOption = document.createElement('option');
        manualOption.value = '__manual__';
        manualOption.textContent = '+ Manual Entry...';
        select.appendChild(manualOption);
    } catch (error) {
        console.error('Error detecting interfaces:', error);
        select.innerHTML = '<option value="">-- Error detecting --</option><option value="__manual__">+ Manual Entry...</option>';
    }
}

function toggleManualInterface() {
    const select = document.getElementById('parentInterface');
    const container = document.getElementById('manual-interface-container');
    if (select.value === '__manual__') {
        container.classList.remove('hidden');
    } else {
        container.classList.add('hidden');
    }
}

function randomizeMac() {
    const hex = '0123456789ABCDEF';
    let mac = '02:';
    for (let i = 0; i < 5; i++) {
        mac += hex.charAt(Math.floor(Math.random() * 16));
        mac += hex.charAt(Math.floor(Math.random() * 16));
        if (i < 4) mac += ':';
    }
    document.getElementById('nicMac').value = mac;
}

function toggleNetworkFields() {
    const useVnic = document.getElementById('useVirtualNic').checked;
    const fields = document.getElementById('vnic-fields');

    if (fields) {
        if (useVnic) {
            fields.classList.remove('hidden');
            if (!document.getElementById('nicMac').value) {
                randomizeMac();
            }
        } else {
            fields.classList.add('hidden');
        }
    }

    toggleStaticFields();
}

function toggleStaticFields() {
    const ipMode = document.getElementById('ipMode').value;
    const useVnic = document.getElementById('useVirtualNic')?.checked || false;
    const fields = document.getElementById('static-ip-fields');

    if (fields) {
        if (useVnic && ipMode === 'static') {
            fields.classList.remove('hidden');
        } else {
            fields.classList.add('hidden');
        }
    }
}

// ============================================================================
// Theme
// ============================================================================

function setupThemeToggle() {
    const toggle = document.getElementById('theme-toggle');
    if (toggle) {
        toggle.addEventListener('click', () => {
            const currentTheme = document.documentElement.classList.contains('dark') ? 'dark' : 'light';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            applyTheme(newTheme);
            saveTheme(newTheme);
        });
    }
}

function applyTheme(theme) {
    if (theme === 'dark') {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }

    const themeSelect = document.getElementById('themeSelect');
    if (themeSelect) {
        themeSelect.value = theme || 'light';
    }
}

async function saveTheme(theme) {
    settings.theme = theme;
    try {
        await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
    } catch (e) {
        console.error('Failed to save theme:', e);
    }
}

function applyGridLayout(cols) {
    const columns = parseInt(cols) || 3;
    const grid = document.getElementById('camera-list');
    if (grid) {
        grid.className = `grid gap-6 grid-cols-1 ${columns >= 3 ? 'md:grid-cols-2 xl:grid-cols-3' : 'md:grid-cols-2'}`;
    }
}

// ============================================================================
// Keyboard Shortcuts
// ============================================================================

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (matrixActive) {
                toggleMatrixView(false);
            } else {
                closeModal();
                closeSettingsModal();
                closeAboutModal();
            }
        }
    });
}

// ============================================================================
// Utility Functions
// ============================================================================

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard', 'success');
    }).catch(() => {
        showToast('Failed to copy', 'error');
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showLoading(text = 'Loading...') {
    const overlay = document.getElementById('loading-overlay');
    const loadingText = document.getElementById('loading-text');
    if (overlay && loadingText) {
        loadingText.textContent = text;
        overlay.classList.remove('hidden');
        overlay.classList.add('flex');
    }
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.add('hidden');
        overlay.classList.remove('flex');
    }
}

function showToast(message, type = 'info') {
    // Remove existing toasts
    const existingToasts = document.querySelectorAll('.toast');
    existingToasts.forEach(t => t.remove());

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
        toast.style.transform = 'translateY(0)';
        toast.style.opacity = '1';
    });

    // Remove after delay
    setTimeout(() => {
        toast.style.transform = 'translateY(100%)';
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
