# Use a slim Python base image
FROM python:3.15-slim

# Install system dependencies needed for FFmpeg, macvlan creation, DHCP, and PyTorch (libgomp1)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    iproute2 \
    isc-dhcp-client \
    procps \
    sudo \
    curl \
    libgomp1 \
    avahi-daemon \
    && rm -rf /var/lib/apt/lists/*

# VAAPI hardware video drivers for GridFusion encoding (issue #73): Intel (iHD for
# Broadwell and newer, i965 for older) and AMD (Mesa). vainfo is for troubleshooting.
# These are only used when the GPU is passed in (see docker-compose.yml "devices").
# Installed best-effort so ARM builds without these packages still succeed.
RUN apt-get update && \
    (apt-get install -y --no-install-recommends vainfo mesa-va-drivers || true) && \
    (apt-get install -y --no-install-recommends intel-media-va-driver i965-va-driver || true) && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Detect host architecture at build time and download the correct MediaMTX v1.21.3.
# This places it directly in the working directory so MediaMTXManager skips downloading it at runtime.
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "amd64" ]; then \
        MEDIAMTX_ARCH="amd64"; \
    elif [ "$ARCH" = "arm64" ]; then \
        MEDIAMTX_ARCH="arm64"; \
    elif [ "$ARCH" = "armhf" ]; then \
        MEDIAMTX_ARCH="armv7"; \
    else \
        MEDIAMTX_ARCH="amd64"; \
    fi && \
    curl -L -o mediamtx.tar.gz "https://github.com/bluenviron/mediamtx/releases/download/v1.21.3/mediamtx_v1.21.3_linux_${MEDIAMTX_ARCH}.tar.gz" && \
    tar -xzf mediamtx.tar.gz mediamtx && \
    rm mediamtx.tar.gz && \
    chmod +x mediamtx

# Install core Python dependencies
RUN pip install --no-cache-dir \
    flask \
    flask-cors \
    requests \
    pyyaml \
    psutil \
    onvif-zeep \
    apprise \
    paramiko \
    cryptography \
    "HAP-python[Camera]" \
    qrcode

# Install CPU-only PyTorch first (keeps the image small, ~200MB vs ~2GB for GPU)
RUN pip install --no-cache-dir \
    torch \
    torchvision \
    --index-url https://download.pytorch.org/whl/cpu

# Install AI dependencies (ultralytics / YOLO + headless OpenCV)
RUN pip install --no-cache-dir \
    ultralytics \
    opencv-python-headless

# Pre-download the default YOLO model so it's available immediately at runtime
RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# Copy the rest of the application
COPY . .

# Default Web UI port. Override at build/run time with the WEB_UI_PORT env var.
# (With network_mode: host this is informational; the app binds this port on the host.)
ENV WEB_UI_PORT=5552
EXPOSE ${WEB_UI_PORT}

# Run the app
CMD ["python", "run.py"]
