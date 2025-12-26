# =============================================================================
# Tonys Onvif-RTSP Server - Dockerfile
# Multi-stage build for optimized production image
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies and prepare the application
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS builder

# Set build-time labels
LABEL stage=builder

# Install build dependencies
# - gcc and python3-dev are needed for compiling some Python packages
# - We install these only in the builder stage to keep the final image small
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment for clean dependency isolation
# This allows us to copy just the venv to the final stage
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies first (layer caching optimization)
# Changes to requirements.txt will invalidate this cache, but code changes won't
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: Runtime - Final minimal production image
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

# =============================================================================
# OCI Image Labels (org.opencontainers.image.*)
# These provide metadata about the image following OCI standards
# =============================================================================
LABEL org.opencontainers.image.title="Tonys Onvif-RTSP Server" \
      org.opencontainers.image.description="Virtual ONVIF-RTSP Gateway for bridging incompatible cameras into NVRs like UniFi Protect" \
      org.opencontainers.image.version="4.0" \
      org.opencontainers.image.vendor="BigTonyTones" \
      org.opencontainers.image.authors="BigTonyTones" \
      org.opencontainers.image.url="https://github.com/BigTonyTones/Tonys-Onvf-RTSP-Server" \
      org.opencontainers.image.source="https://github.com/BigTonyTones/Tonys-Onvf-RTSP-Server" \
      org.opencontainers.image.documentation="https://github.com/BigTonyTones/Tonys-Onvf-RTSP-Server#readme" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.base.name="python:3.12-slim"

# =============================================================================
# Install System Dependencies
# =============================================================================
# - ffmpeg: Required for stream transcoding and probing (ffprobe)
# - isc-dhcp-client: Required for Virtual NIC DHCP support (dhclient)
# - iproute2: Required for macvlan network interface management (ip command)
# - procps: Provides 'ps' command needed for process management
# - curl: Used for healthcheck and downloading binaries
# - net-tools: Provides network utilities (ifconfig, etc.)
# =============================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    isc-dhcp-client \
    iproute2 \
    procps \
    curl \
    net-tools \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# =============================================================================
# Download and Install MediaMTX at Build Time (Security Best Practice)
# =============================================================================
# Installing at build time rather than runtime:
# - Avoids downloading binaries at runtime (security concern)
# - Makes builds reproducible with a known version
# - Faster container startup
# =============================================================================
ARG MEDIAMTX_VERSION=v1.15.5
RUN ARCH=$(dpkg --print-architecture) && \
    case "$ARCH" in \
        amd64) MEDIAMTX_ARCH="linux_amd64" ;; \
        arm64) MEDIAMTX_ARCH="linux_arm64v8" ;; \
        armhf) MEDIAMTX_ARCH="linux_armv7" ;; \
        *) echo "Unsupported architecture: $ARCH" && exit 1 ;; \
    esac && \
    curl -L "https://github.com/bluenviron/mediamtx/releases/download/${MEDIAMTX_VERSION}/mediamtx_${MEDIAMTX_VERSION}_${MEDIAMTX_ARCH}.tar.gz" \
        -o /tmp/mediamtx.tar.gz && \
    tar -xzf /tmp/mediamtx.tar.gz -C /usr/local/bin mediamtx && \
    chmod +x /usr/local/bin/mediamtx && \
    rm /tmp/mediamtx.tar.gz && \
    mediamtx --version

# =============================================================================
# Create Non-Root User
# =============================================================================
# Running as non-root is a security best practice
# However, some features (macvlan, dhclient) require root privileges
# We create the user but may need to run as root for full functionality
# =============================================================================
RUN groupadd --gid 1000 onvif && \
    useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home onvif

# =============================================================================
# Application Setup
# =============================================================================
# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
# This contains all installed Python packages
COPY --from=builder /opt/venv /opt/venv

# Ensure the virtual environment is used
ENV PATH="/opt/venv/bin:$PATH"

# Set Python environment variables for better container behavior
# - PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files
# - PYTHONUNBUFFERED: Ensures logs are sent to stdout immediately
# - PYTHONFAULTHANDLER: Better error reporting for segfaults
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

# =============================================================================
# Create Directories for Persistent Data
# =============================================================================
# - /app/config: For camera_config.json persistence
# Note: ffmpeg and mediamtx are now installed at build time in /usr/bin and
#       /usr/local/bin respectively, eliminating runtime binary downloads.
# =============================================================================
RUN mkdir -p /app/config && \
    chown -R onvif:onvif /app

# =============================================================================
# Copy Application Code
# =============================================================================
# Copy the application code last to maximize layer caching
# Code changes don't invalidate dependency layers
COPY --chown=onvif:onvif . /app/

# Ensure the config directory has correct permissions
RUN chown -R onvif:onvif /app/config

# =============================================================================
# Port Exposure Documentation
# =============================================================================
# - 5552: Web UI (Flask application)
# - 8554: RTSP streaming port (MediaMTX)
# - 9997: MediaMTX API port
# - 8001-8100: ONVIF service ports (one per camera)
# =============================================================================
EXPOSE 5552 8554 9997
EXPOSE 8001-8100

# =============================================================================
# Health Check
# =============================================================================
# Check if the web UI is responding
# - interval: Check every 30 seconds
# - timeout: Wait up to 10 seconds for response
# - start-period: Give container 60 seconds to start up
# - retries: Mark unhealthy after 3 consecutive failures
# =============================================================================
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl --fail http://localhost:5552/ || exit 1

# =============================================================================
# Runtime Configuration
# =============================================================================
# Note: We run as root by default because macvlan and dhclient require
# elevated privileges. For deployments not using Virtual NIC features,
# you can override with: --user onvif
# =============================================================================

# Default command - run the main application
CMD ["python", "run.py"]
