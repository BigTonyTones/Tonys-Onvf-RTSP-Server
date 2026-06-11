# Use a slim Python base image
FROM python:3.11-slim

# Install system dependencies needed for FFmpeg, macvlan creation, DHCP, and PyTorch (libgomp1)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    iproute2 \
    isc-dhcp-client \
    procps \
    sudo \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Detect host architecture at build time and download the correct MediaMTX v1.18.2.
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
    curl -L -o mediamtx.tar.gz "https://github.com/bluenviron/mediamtx/releases/download/v1.18.2/mediamtx_v1.18.2_linux_${MEDIAMTX_ARCH}.tar.gz" && \
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
    apprise

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

# Expose default Web UI port
EXPOSE 5552

# Run the app
CMD ["python", "run.py"]
