# Shared client-side streaming helpers.
#
# Returned as a plain JavaScript string (NOT an f-string) so it can be embedded
# verbatim into any page template without brace-escaping. Depends on hls.js
# being loaded globally on the page. Used by the standalone mobile viewer
# (mobile_template.py) so the HLS bootstrap lives in exactly one place.


def get_streaming_js():
    """Return shared HLS streaming helper functions as a JS string."""
    return r"""
    // ===== Shared streaming helpers (app/streaming_js.py) =====

    // Resolve the server IP the browser should use for HLS, mirroring the
    // dashboard's "smart override" so remote browsers don't try localhost.
    function resolveServerIp(settings) {
        let serverIp = (settings && settings.serverIp) || window.location.hostname || 'localhost';
        if (serverIp === 'localhost' && window.location.hostname
            && window.location.hostname !== 'localhost'
            && window.location.hostname !== '127.0.0.1') {
            serverIp = window.location.hostname;
        }
        return serverIp;
    }

    // Build the MediaMTX HLS playlist URL for a camera path + profile ('sub'/'main').
    function buildStreamUrl(serverIp, pathName, profile, settings) {
        const suffix = profile === 'main' ? '_main' : '_sub';
        let credentials = '';
        if (settings && settings.rtspAuthEnabled && settings.globalUsername && settings.globalPassword) {
            const u = encodeURIComponent(settings.globalUsername);
            const p = encodeURIComponent(settings.globalPassword);
            credentials = `?user=${u}&pass=${p}`;
        }
        return `http://${serverIp}:8888/${pathName}${suffix}/index.m3u8${credentials}`;
    }

    // Attach an HLS (or native-HLS for Safari/iOS) player to a <video> element.
    // Includes the dashboard's network/media error recovery with backoff.
    // Returns a handle exposing destroy(); safe to call when hls.js is missing.
    function createHlsPlayer(videoEl, streamUrl, settings, onError) {
        if (!videoEl) return null;

        if (typeof Hls !== 'undefined' && Hls.isSupported()) {
            const config = {
                enableWorker: true,
                lowLatencyMode: true,
                backBufferLength: 30,
                liveSyncDurationCount: 3,
                liveMaxLatencyDurationCount: 5,
                maxLiveSyncPlaybackRate: 1.25
            };
            if (settings && settings.rtspAuthEnabled && settings.globalUsername && settings.globalPassword) {
                config.xhrSetup = function(xhr, url) {
                    let accessUrl = url;
                    if (url.indexOf('user=') === -1) {
                        const sep = url.indexOf('?') === -1 ? '?' : '&';
                        accessUrl = url + sep + `user=${encodeURIComponent(settings.globalUsername)}&pass=${encodeURIComponent(settings.globalPassword)}`;
                    }
                    xhr.open('GET', accessUrl, true);
                };
            }

            const hls = new Hls(config);
            let attempts = 0;
            const maxAttempts = 5;

            hls.loadSource(streamUrl);
            hls.attachMedia(videoEl);
            hls.on(Hls.Events.MANIFEST_PARSED, function() {
                videoEl.play().catch(function() {});
            });
            hls.on(Hls.Events.ERROR, function(event, data) {
                if (!data.fatal) return;
                if (data.type === Hls.ErrorTypes.NETWORK_ERROR && attempts < maxAttempts) {
                    attempts++;
                    const delay = Math.min(1000 * Math.pow(2, attempts), 16000);
                    setTimeout(function() { hls.loadSource(streamUrl); hls.startLoad(); }, delay);
                } else if (data.type === Hls.ErrorTypes.MEDIA_ERROR && attempts < maxAttempts) {
                    attempts++;
                    hls.recoverMediaError();
                } else {
                    try { hls.destroy(); } catch (e) {}
                    if (typeof onError === 'function') onError(data);
                }
            });
            return { type: 'hls', hls: hls, destroy: function() { try { hls.destroy(); } catch (e) {} } };
        }

        if (videoEl.canPlayType('application/vnd.apple.mpegurl')) {
            videoEl.src = streamUrl;
            videoEl.play().catch(function() {});
            return { type: 'native', destroy: function() { try { videoEl.removeAttribute('src'); videoEl.load(); } catch (e) {} } };
        }

        if (typeof onError === 'function') onError({ details: 'HLS not supported' });
        return null;
    }

    // Attach a low-latency WebRTC (WHEP) player to a <video> element, mirroring
    // the dashboard's default streaming path (MediaMTX :8889). Calls onFail() if
    // negotiation or the connection fails, so callers can fall back to HLS.
    // Returns a handle with destroy(); null if WebRTC is unavailable.
    function createWebRtcPlayer(videoEl, serverIp, pathName, profile, settings, onFail) {
        if (!videoEl || typeof RTCPeerConnection === 'undefined') {
            if (typeof onFail === 'function') onFail();
            return null;
        }

        let failed = false;
        let closed = false;
        const pc = new RTCPeerConnection({ iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] });

        function fail(reason) {
            if (failed || closed) return;
            failed = true;
            try { pc.close(); } catch (e) {}
            if (typeof onFail === 'function') onFail(reason);
        }

        pc.addTransceiver('video', { direction: 'recvonly' });
        pc.addTransceiver('audio', { direction: 'recvonly' });
        pc.ontrack = function(event) {
            if (videoEl.srcObject !== event.streams[0]) {
                videoEl.srcObject = event.streams[0];
                videoEl.play().catch(function() {});
            }
        };
        pc.onconnectionstatechange = function() {
            if (pc.connectionState === 'failed' || pc.connectionState === 'disconnected') {
                fail('connection ' + pc.connectionState);
            }
        };

        const suffix = profile === 'main' ? '_main' : '_sub';
        const whepUrl = `http://${serverIp}:8889/${pathName}${suffix}/whep`;

        (async function negotiate() {
            try {
                const offer = await pc.createOffer();
                await pc.setLocalDescription(offer);
                const resp = await fetch(whepUrl, {
                    method: 'POST',
                    body: offer.sdp,
                    headers: { 'Content-Type': 'application/sdp' }
                });
                if (!resp.ok) throw new Error('WHEP responded ' + resp.status);
                const answerSdp = await resp.text();
                if (closed) return;
                await pc.setRemoteDescription(new RTCSessionDescription({ type: 'answer', sdp: answerSdp }));
            } catch (err) {
                fail(err);
            }
        })();

        return {
            type: 'webrtc',
            destroy: function() {
                closed = true;
                try { videoEl.srcObject = null; } catch (e) {}
                try { pc.close(); } catch (e) {}
            }
        };
    }

    // High-level player factory used by the mobile viewer. Prefers low-latency
    // WebRTC (the dashboard default) and automatically falls back to HLS if
    // WebRTC isn't available or fails — so a camera whose HLS sub-stream is
    // flaky still plays, and vice-versa. Returns a handle with destroy().
    function createCameraPlayer(videoEl, opts) {
        opts = opts || {};
        const serverIp = opts.serverIp;
        const pathName = opts.pathName;
        const profile = opts.profile || 'sub';
        const settings = opts.settings || {};
        const lowLatency = opts.lowLatency !== false; // default: WebRTC first
        let active = null;
        let destroyed = false;
        let triedHls = false;

        function startHls() {
            if (destroyed || triedHls) return;
            triedHls = true;
            const url = buildStreamUrl(serverIp, pathName, profile, settings);
            active = createHlsPlayer(videoEl, url, settings, opts.onError);
        }

        if (lowLatency && typeof RTCPeerConnection !== 'undefined') {
            active = createWebRtcPlayer(videoEl, serverIp, pathName, profile, settings, function() {
                if (destroyed) return;
                if (active) { try { active.destroy(); } catch (e) {} active = null; }
                startHls();
            });
            if (!active) startHls();
        } else {
            startHls();
        }

        return {
            destroy: function() {
                destroyed = true;
                if (active) { try { active.destroy(); } catch (e) {} active = null; }
            }
        };
    }
    """
