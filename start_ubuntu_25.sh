#!/bin/bash

# Tonys Onvif Server - Ubuntu 25.04 Startup Script
# This script installs dependencies, sets up a virtual environment, and starts the server.

# 0. Check for sudo privileges
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run with sudo."
    echo "Please use: sudo ./start_ubuntu_25.sh"
    exit 1
fi

echo "============================================================"
echo "Tonys Onvif-RTSP Server v5.5.3 - Ubuntu Development Setup"
echo "============================================================"

# 1. Install system-level Python dependencies (only if missing)
echo "Checking system dependencies..."
if ! python3 -c "import venv" &> /dev/null; then
    echo "  Missing system dependencies: python3-full, python3-venv"
    echo "  These are required to create a Python virtual environment."
    read -p "  Would you like to install them now via apt? (y/n): " confirm
    if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
        sudo apt update
        sudo apt install -y python3-full python3-venv
    else
        echo "  Installation skipped. Please install them manually to continue."
        exit 1
    fi
else
    echo "  System dependencies already installed."
fi

# 2. Create Virtual Environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment (venv)..."
    python3 -m venv venv
else
    echo "Virtual environment already exists."
fi

# 3. Activate Virtual Environment
echo "Activating virtual environment..."
source venv/bin/activate

# 4. Install initial required Python packages
echo "Checking Python packages..."
if ! python3 -c "import flask" &> /dev/null; then
    echo "  Missing core Python packages: flask, flask-cors, requests, pyyaml, psutil, onvif-zeep"
    read -p "  Would you like to install them now via pip? (y/n): " confirm
    if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
        echo "  Installing packages..."
        pip install flask flask-cors requests pyyaml psutil onvif-zeep
    else
        echo "  Installation skipped. Please install dependencies manually."
        exit 1
    fi
else
    echo "  Core Python packages already installed."
fi

# 4b. Check specifically for onvif-zeep (added later, may be missing in existing installations)
if ! python3 -c "from onvif import ONVIFCamera" &> /dev/null; then
    echo "  Missing onvif-zeep package"
    read -p "  Would you like to install onvif-zeep now via pip? (y/n): " confirm
    if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
        echo "  Installing onvif-zeep..."
        pip install onvif-zeep
        if [ $? -eq 0 ]; then
            echo "  onvif-zeep installed successfully."
        else
            echo "  Warning: Failed to install onvif-zeep. You may need to install it manually."
        fi
    else
        echo "  Installation skipped. Note: ONVIF camera discovery will not work without onvif-zeep."
    fi
fi

# 5. Provide permissions to MediaMTX and FFmpeg if they exist locally
if [ -f "mediamtx" ]; then
    chmod +x mediamtx
fi
if [ -f "ffmpeg" ]; then
    chmod +x ffmpeg
fi

# 6. Increase file descriptor limit
# This is crucial when running many virtual cameras as each uses multiple sockets and files
echo "Increasing file descriptor limit..."
ulimit -n 65535

# 7. Start the application with auto-restart support
echo ""
echo "============================================================"
echo "Starting Tonys Onvif Server v5.5.3..."
echo "============================================================"

# Loop to handle restart requests (exit code 42)
while true; do
    python run.py
    EXIT_CODE=$?
    
    # Check if exit code is 42 (restart requested)
    if [ $EXIT_CODE -eq 42 ]; then
        echo ""
        echo "============================================================"
        echo "Restart requested, restarting server..."
        echo "============================================================"
        sleep 1
        continue
    else
        # Any other exit code means intentional shutdown
        echo ""
        echo "Server stopped."
        break
    fi
done
