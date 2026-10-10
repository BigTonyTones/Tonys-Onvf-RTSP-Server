# RTSPS and Wyze camera support

This server can now pull cameras over **RTSPS** (RTSP inside TLS), such as Wyze
cameras on the official RTSP firmware (`rtsps://<ip>:322/stream0`), and re-serve
them as ordinary virtual ONVIF cameras to UniFi Protect and other NVRs.

Existing RTSP cameras are unaffected: RTSP stays the default, and saved configs
load unchanged.

## How it works

```
camera --rtsps (TLS, verified)--> MediaMTX --rtsp (loopback/LAN)--> Protect / dashboard / FFmpeg
```

* **MediaMTX is the single TLS endpoint.** It pulls the camera natively over
  RTSPS and checks the certificate according to the camera's TLS mode.
* **No transcoding by default.** Video and audio are passed through as-is,
  keeping the camera's resolution, frame rate and audio. The optional
  per-camera "transcode" settings still work; FFmpeg then reads the camera
  through a hidden, already-verified MediaMTX path (`<cam>_main_src`) on
  loopback, so it never talks TLS to the camera itself. No GPU is needed.
* **The encrypted upstream connection is never silently downgraded.** An
  `rtsps://` camera is only ever contacted over TLS.

## Adding a Wyze camera

1. In the Wyze app, enable RTSP for the camera. Note its IP, user name and password.
2. In the dashboard, add a camera and set:
   * **Protocol:** `RTSPS (TLS)` (the port changes to 322)
   * **Host:** the camera IP, **Main path:** `/stream0`, **Sub path:** `/stream1`
   * **User name / password:** as set in the Wyze app. Any characters are fine
     (`! @ : # &` …); they are URL-encoded for you.
3. **TLS mode:** choose **Pinned certificate**, click **Fetch certificate from
   camera**, check the details shown, then click **Trust this certificate**.
4. Save and start the camera. The card shows **Streaming** once video is
   actually arriving.

## TLS modes

| Mode | What is checked | Use for |
|---|---|---|
| **Verify with trusted CAs** (default) | Chain to a trusted CA and the host name/IP | Cameras with a CA-issued cert, or your own CA |
| **Pinned certificate** | The exact SHA-256 fingerprint of the camera's certificate | Self-signed cameras such as Wyze |
| **Do not verify** (insecure) | Nothing (traffic is still encrypted) | Short-term diagnostics only. The card shows a warning |

* **Your own CA:** put the CA certificate (PEM, `.pem` or `.crt`) in
  `data/tls/ca/` and restart the container. It is added to the system trust
  store for MediaMTX. `GET /api/tls/status` lists the CAs that were loaded.
* **Certificate changed?** A camera reset or firmware update can create a new
  certificate. The camera then shows **TLS verification failed** with
  "fingerprint does not match". Fetch and trust the new certificate if you
  expected the change.
* Pinned mode with no fingerprint saved never means "trust anything". It falls
  back to full CA verification, which a self-signed camera fails (closed).

## Substream handling

If the sub stream can't be opened (missing path, 404, etc.) while the main stream
works, the camera stays online. The card reports "Main stream OK. Sub stream: …".
After two failed checks the server serves the main stream on the sub path, and
the ONVIF sub profile reports the main stream's resolution. You can turn this off
per camera with **Fall back to main stream if the sub stream fails**. **Use Main as Substream** still works and re-uses MediaMTX's single connection to the camera.

## Status states

The camera card shows a status that comes from what MediaMTX actually receives,
not from "process is running".

| State | Meaning |
|---|---|
| Starting / Connecting | MediaMTX is (re)starting, or the first connection is in progress |
| Streaming (green) | A video track was seen and bytes are increasing, or a probe through MediaMTX returned video within the last 5 minutes |
| Reconnecting | The stream was working and dropped. MediaMTX is retrying on its own |
| Authentication failed | The camera answered 401/403. Check the user name and password |
| TLS verification failed | Untrusted cert, fingerprint mismatch, expired cert, or IP missing from the cert's SANs |
| Source unavailable | Connection refused, timed out, path not found, or plain RTSP sent to a TLS port |
| Error | MediaMTX not running, port conflict, audio-only source, etc. |

Messages never include credentials. URLs in logs, API errors, and diagnostics
output are shown as `rtsps://***@host:port/path`.

## MediaMTX process handling

* One MediaMTX instance per server. Starts and restarts are serialized, and bursts
  of restart requests (several cameras saved at once) are merged into one.
* The server records its MediaMTX PID in `data/mediamtx.pid`. On startup it only
  stops a leftover MediaMTX if that process is running **this** server's binary
  with **this** server's config file.
* If something else is listening on the RTSP (8554) or API (9997) port, the
  server **does not kill it**. It logs which process holds the port, shows
  Error on the cameras, and waits for you to free the port or change it in
  Settings.

## FFmpeg versions

FFmpeg's RTSPS behaviour depends on the build. FFmpeg 7+ verifies certificates
and accepts `-tls_verify 0`. FFmpeg 6.x never verifies over RTSPS and rejects
that option. The server detects which kind it has (`ffmpeg -h demuxer=rtsp`) and
only passes `-tls_verify 0` for cameras explicitly set to insecure mode. In the
verified modes FFmpeg never connects to an RTSPS camera directly, so the TLS
policy does not depend on the FFmpeg build.

## Changelog

* RTSP/RTSPS protocol selector per camera. Ports default to 554 and 322.
  Credentials are URL-encoded and IPv6 hosts are bracketed.
* RTSPS via MediaMTX, with three TLS modes (verify by default, pinned
  fingerprint, explicit insecure). Custom CAs load from `data/tls/ca/`.
  "Fetch certificate from camera" and "Trust this certificate" in the editor.
* Passthrough by default. Optional transcoding reads RTSPS cameras through a
  verified loopback path.
* Missing-substream detection with automatic fallback to the main stream
  (can be turned off).
* Real stream health states with actionable, redacted messages, and a
  "running-degraded" card indicator.
* MediaMTX lifecycle: lock, PID file, ownership checks, and no killing of
  foreign processes on 8554. Removed the blanket `pkill -9 mediamtx`.
* Credential redaction in the app log, the MediaMTX log, FFprobe and FFmpeg
  errors, API errors, and diagnostics.
* Docker: `ca-certificates`, `init: true`, `stop_grace_period`, and a
  documented port list and trust directory.
* Tests: `tests/` (unit) and `tests/integration/` (a lab that runs real MediaMTX
  and fake RTSPS cameras).

## Running the tests

```bash
pip install pytest pyyaml psutil requests flask flask-cors
python -m pytest -q tests --ignore=tests/integration          # unit tests, no network
MEDIAMTX_BIN=/path/to/mediamtx python -m pytest -q tests/integration   # lab, needs ffmpeg + mediamtx v1.18
```

The lab tests generate throwaway self-signed and CA-signed certificates and
fake cameras with dummy credentials. No real camera or Wyze account is needed.

## Upgrading a Docker Compose install

```bash
cd <your checkout>
cp -a data "data.bak-$(date +%Y%m%d-%H%M)"         # 1. back up config + trust
git rev-parse HEAD > data/.previous-commit          # 2. remember the current version
git pull
docker compose build --pull                        # 3. rebuild the image
docker compose up -d                               # 4. restart with the new image
docker compose logs -f --tail=200                  # 5. watch startup
```

The container still needs only `NET_ADMIN` and host networking. Privileged mode
is not required.

### Rollback

```bash
docker compose down
git checkout "$(cat data/.previous-commit)"
rm -rf data && cp -a data.bak-<timestamp> data     # restore the config saved in step 1
docker compose build && docker compose up -d
```

Restoring `data/` matters if you saved RTSPS cameras: older versions don't
know the `rtsps` protocol fields.

## Hardware test checklist

- [ ] Container starts, and the logs show exactly one "MediaMTX running on RTSP port 8554".
- [ ] Existing RTSP cameras still stream in the dashboard and in the NVR.
- [ ] A Wyze camera added as RTSPS + Pinned shows **Streaming**, with the right resolution and fps on the card.
- [ ] Sub stream `/stream1` works. If not, the card shows "Sub stream: …" and switches to main as sub, while the camera stays green.
- [ ] A wrong password shows **Authentication failed**. Fix it and the camera recovers.
- [ ] A wrong pin shows **TLS verification failed**.
- [ ] Unplugging the camera shows **Reconnecting** or **Source unavailable**, and plugging it back returns to **Streaming** without a restart.
- [ ] Logs and the dashboard log viewer show no camera passwords.
- [ ] The NVR adopts the virtual camera, shows live video, records, and plays back.
- [ ] CPU stays low with passthrough (no `ffmpeg` processes per camera unless transcoding is on).

## Tested with

Three Wyze cameras (`rtsps://<ip>:322/stream0`, self-signed certificates, Pinned
mode) adopted by UniFi Protect through the virtual ONVIF cameras, running in
Docker with host networking and `NET_ADMIN`.
