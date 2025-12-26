#!/bin/bash
#
# Tonys Onvif-RTSP Server - Linux Installation Script
#
# One-command installation for Linux systems.
# Supports: Ubuntu, Debian, Fedora, CentOS, RHEL, Arch Linux, Manjaro
#
# Usage: ./install.sh [OPTIONS]
#   --no-systemd      Skip systemd service setup
#   --no-binaries     Skip MediaMTX and FFmpeg download
#   --uninstall       Remove systemd service
#   --help            Show this help message
#
# Quick install:
#   curl -fsSL https://raw.githubusercontent.com/YOUR_REPO/install.sh | bash
#

# =============================================================================
# CONFIGURATION
# =============================================================================

set -e
set -o pipefail

# Script version
SCRIPT_VERSION="1.0.0"

# Installation directory (current directory or specified)
INSTALL_DIR="$(pwd)"

# Minimum Python version
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=10

# Virtual environment directory
VENV_DIR="venv"

# Systemd service name
SERVICE_NAME="tonys-onvif-server"

# MediaMTX version (locked for compatibility)
MEDIAMTX_VERSION="v1.15.5"

# =============================================================================
# COLOR DEFINITIONS
# =============================================================================

if [ -t 1 ] && command -v tput &>/dev/null && [ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]; then
    RED=$(tput setaf 1)
    GREEN=$(tput setaf 2)
    YELLOW=$(tput setaf 3)
    BLUE=$(tput setaf 4)
    MAGENTA=$(tput setaf 5)
    CYAN=$(tput setaf 6)
    WHITE=$(tput setaf 7)
    BOLD=$(tput bold)
    RESET=$(tput sgr0)
else
    RED=""
    GREEN=""
    YELLOW=""
    BLUE=""
    MAGENTA=""
    CYAN=""
    WHITE=""
    BOLD=""
    RESET=""
fi

# =============================================================================
# LOGGING FUNCTIONS
# =============================================================================

log_info() {
    echo "${BLUE}[INFO]${RESET} $1"
}

log_success() {
    echo "${GREEN}[OK]${RESET} $1"
}

log_warning() {
    echo "${YELLOW}[WARN]${RESET} $1"
}

log_error() {
    echo "${RED}[ERROR]${RESET} $1" >&2
}

log_step() {
    echo ""
    echo "${CYAN}${BOLD}=== $1 ===${RESET}"
}

# Progress indicator
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    while ps -p "$pid" > /dev/null 2>&1; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "      \b\b\b\b\b\b"
}

# =============================================================================
# ARGUMENT PARSING
# =============================================================================

SKIP_SYSTEMD=0
SKIP_BINARIES=0
DO_UNINSTALL=0

show_help() {
    cat << EOF
${BOLD}Tonys Onvif-RTSP Server - Linux Installation Script${RESET}
Version: ${SCRIPT_VERSION}

${CYAN}USAGE:${RESET}
    $0 [OPTIONS]

${CYAN}OPTIONS:${RESET}
    ${GREEN}--no-systemd${RESET}      Skip systemd service setup
    ${GREEN}--no-binaries${RESET}     Skip MediaMTX and FFmpeg download
    ${GREEN}--uninstall${RESET}       Remove systemd service
    ${GREEN}--help, -h${RESET}        Show this help message

${CYAN}WHAT THIS SCRIPT DOES:${RESET}
    1. Detects your Linux distribution
    2. Installs required system packages (Python, etc.)
    3. Creates a Python virtual environment
    4. Installs Python dependencies
    5. Downloads MediaMTX and FFmpeg binaries
    6. Optionally sets up a systemd service

${CYAN}SUPPORTED DISTRIBUTIONS:${RESET}
    - Ubuntu / Debian / Linux Mint
    - Fedora / CentOS / RHEL
    - Arch Linux / Manjaro
    - Other systemd-based distributions

${CYAN}EXAMPLES:${RESET}
    $0                          # Full installation
    $0 --no-systemd             # Install without systemd service
    $0 --uninstall              # Remove systemd service

EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-systemd)
            SKIP_SYSTEMD=1
            shift
            ;;
        --no-binaries)
            SKIP_BINARIES=1
            shift
            ;;
        --uninstall)
            DO_UNINSTALL=1
            shift
            ;;
        --help|-h)
            show_help
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# =============================================================================
# BANNER
# =============================================================================

print_banner() {
    echo ""
    echo "${CYAN}${BOLD}============================================================${RESET}"
    echo "${CYAN}${BOLD}     Tonys Onvif-RTSP Server - Linux Installer v${SCRIPT_VERSION}${RESET}"
    echo "${CYAN}${BOLD}============================================================${RESET}"
    echo ""
}

# =============================================================================
# UNINSTALL FUNCTION
# =============================================================================

do_uninstall() {
    log_step "Uninstalling Tonys Onvif-RTSP Server"

    # Stop and disable systemd service
    if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        log_info "Stopping service..."
        sudo systemctl stop "$SERVICE_NAME"
    fi

    if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
        log_info "Disabling service..."
        sudo systemctl disable "$SERVICE_NAME"
    fi

    # Remove service file
    if [ -f "/etc/systemd/system/${SERVICE_NAME}.service" ]; then
        log_info "Removing service file..."
        sudo rm -f "/etc/systemd/system/${SERVICE_NAME}.service"
        sudo systemctl daemon-reload
        log_success "Systemd service removed"
    else
        log_info "No systemd service found"
    fi

    echo ""
    log_success "Uninstall complete!"
    echo ""
    echo "Note: The application files were not removed."
    echo "To completely remove, delete the installation directory:"
    echo "  rm -rf $INSTALL_DIR"
    echo ""

    exit 0
}

# Run uninstall if requested
if [ "$DO_UNINSTALL" -eq 1 ]; then
    print_banner
    do_uninstall
fi

# =============================================================================
# DISTRIBUTION DETECTION
# =============================================================================

detect_distro() {
    log_step "Detecting Linux Distribution"

    DISTRO=""
    DISTRO_FAMILY=""
    PKG_MANAGER=""
    PKG_UPDATE=""
    PKG_INSTALL=""

    # Try to detect from /etc/os-release
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO="$ID"
        DISTRO_VERSION="$VERSION_ID"
        DISTRO_NAME="$PRETTY_NAME"
    elif [ -f /etc/lsb-release ]; then
        . /etc/lsb-release
        DISTRO="$DISTRIB_ID"
        DISTRO_VERSION="$DISTRIB_RELEASE"
        DISTRO_NAME="$DISTRIB_DESCRIPTION"
    else
        log_error "Could not detect Linux distribution"
        exit 1
    fi

    # Convert to lowercase
    DISTRO=$(echo "$DISTRO" | tr '[:upper:]' '[:lower:]')

    log_info "Detected: ${BOLD}${DISTRO_NAME:-$DISTRO}${RESET}"

    # Determine package manager and family
    case "$DISTRO" in
        ubuntu|debian|linuxmint|pop|elementary|zorin|kali)
            DISTRO_FAMILY="debian"
            PKG_MANAGER="apt-get"
            PKG_UPDATE="sudo apt-get update"
            PKG_INSTALL="sudo apt-get install -y"
            PYTHON_PACKAGES="python3 python3-venv python3-pip python3-dev"
            EXTRA_PACKAGES="curl wget isc-dhcp-client"
            ;;
        fedora|centos|rhel|rocky|almalinux)
            DISTRO_FAMILY="redhat"
            if command -v dnf &>/dev/null; then
                PKG_MANAGER="dnf"
                PKG_UPDATE="sudo dnf check-update || true"
                PKG_INSTALL="sudo dnf install -y"
            else
                PKG_MANAGER="yum"
                PKG_UPDATE="sudo yum check-update || true"
                PKG_INSTALL="sudo yum install -y"
            fi
            PYTHON_PACKAGES="python3 python3-pip python3-devel"
            EXTRA_PACKAGES="curl wget dhcp-client"
            ;;
        arch|manjaro|endeavouros|garuda)
            DISTRO_FAMILY="arch"
            PKG_MANAGER="pacman"
            PKG_UPDATE="sudo pacman -Sy"
            PKG_INSTALL="sudo pacman -S --noconfirm"
            PYTHON_PACKAGES="python python-pip"
            EXTRA_PACKAGES="curl wget dhclient"
            ;;
        opensuse*|suse*)
            DISTRO_FAMILY="suse"
            PKG_MANAGER="zypper"
            PKG_UPDATE="sudo zypper refresh"
            PKG_INSTALL="sudo zypper install -y"
            PYTHON_PACKAGES="python3 python3-pip python3-devel"
            EXTRA_PACKAGES="curl wget dhcp-client"
            ;;
        *)
            log_warning "Unknown distribution: $DISTRO"
            log_info "Attempting to detect package manager..."

            if command -v apt-get &>/dev/null; then
                DISTRO_FAMILY="debian"
                PKG_MANAGER="apt-get"
                PKG_UPDATE="sudo apt-get update"
                PKG_INSTALL="sudo apt-get install -y"
                PYTHON_PACKAGES="python3 python3-venv python3-pip"
                EXTRA_PACKAGES="curl wget"
            elif command -v dnf &>/dev/null; then
                DISTRO_FAMILY="redhat"
                PKG_MANAGER="dnf"
                PKG_UPDATE="sudo dnf check-update || true"
                PKG_INSTALL="sudo dnf install -y"
                PYTHON_PACKAGES="python3 python3-pip"
                EXTRA_PACKAGES="curl wget"
            elif command -v pacman &>/dev/null; then
                DISTRO_FAMILY="arch"
                PKG_MANAGER="pacman"
                PKG_UPDATE="sudo pacman -Sy"
                PKG_INSTALL="sudo pacman -S --noconfirm"
                PYTHON_PACKAGES="python python-pip"
                EXTRA_PACKAGES="curl wget"
            else
                log_error "Could not detect package manager"
                log_error "Please install Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ manually"
                exit 1
            fi
            ;;
    esac

    log_success "Package manager: $PKG_MANAGER ($DISTRO_FAMILY family)"
}

# =============================================================================
# SYSTEM DEPENDENCIES
# =============================================================================

install_system_dependencies() {
    log_step "Installing System Dependencies"

    log_info "Updating package lists..."
    eval "$PKG_UPDATE" &>/dev/null || true

    log_info "Installing required packages..."
    echo "  Packages: $PYTHON_PACKAGES $EXTRA_PACKAGES"

    # Install packages
    eval "$PKG_INSTALL $PYTHON_PACKAGES $EXTRA_PACKAGES" || {
        log_error "Failed to install system packages"
        log_info "Please install these manually: $PYTHON_PACKAGES $EXTRA_PACKAGES"
        exit 1
    }

    log_success "System dependencies installed"
}

# =============================================================================
# PYTHON VERSION CHECK
# =============================================================================

check_python_version() {
    log_step "Checking Python Version"

    # Find Python executable
    PYTHON_CMD=""
    for cmd in python3 python; do
        if command -v "$cmd" &>/dev/null; then
            PYTHON_CMD="$cmd"
            break
        fi
    done

    if [ -z "$PYTHON_CMD" ]; then
        log_error "Python not found after installation"
        exit 1
    fi

    # Get version
    PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PYTHON_MAJOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.major)')
    PYTHON_MINOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.minor)')

    log_info "Found Python $PYTHON_VERSION at $(which $PYTHON_CMD)"

    # Version check
    if [ "$PYTHON_MAJOR" -lt "$MIN_PYTHON_MAJOR" ] || \
       { [ "$PYTHON_MAJOR" -eq "$MIN_PYTHON_MAJOR" ] && [ "$PYTHON_MINOR" -lt "$MIN_PYTHON_MINOR" ]; }; then
        log_error "Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ required, but found $PYTHON_VERSION"
        log_info "Please upgrade Python or use a newer distribution"
        exit 1
    fi

    log_success "Python version $PYTHON_VERSION meets requirements"
}

# =============================================================================
# VIRTUAL ENVIRONMENT
# =============================================================================

setup_virtual_environment() {
    log_step "Setting Up Python Virtual Environment"

    cd "$INSTALL_DIR"

    if [ -d "$VENV_DIR" ]; then
        log_info "Removing existing virtual environment..."
        rm -rf "$VENV_DIR"
    fi

    log_info "Creating virtual environment..."
    $PYTHON_CMD -m venv "$VENV_DIR"

    # Activate
    source "$VENV_DIR/bin/activate"

    # Upgrade pip
    log_info "Upgrading pip..."
    pip install --upgrade pip --quiet

    log_success "Virtual environment created at $INSTALL_DIR/$VENV_DIR"
}

# =============================================================================
# PYTHON DEPENDENCIES
# =============================================================================

install_python_dependencies() {
    log_step "Installing Python Dependencies"

    # Ensure we're in venv
    source "$INSTALL_DIR/$VENV_DIR/bin/activate"

    PACKAGES="flask flask-cors requests pyyaml psutil"

    log_info "Installing packages: $PACKAGES"
    pip install $PACKAGES --quiet

    # Check for tzdata (Python 3.9+)
    if [ "$PYTHON_MINOR" -ge 9 ]; then
        pip install tzdata --quiet
    fi

    log_success "Python dependencies installed"
}

# =============================================================================
# DOWNLOAD BINARIES
# =============================================================================

download_mediamtx() {
    log_step "Downloading MediaMTX"

    cd "$INSTALL_DIR"

    # Check if already exists and is correct version
    if [ -f "mediamtx" ]; then
        CURRENT_VERSION=$(./mediamtx --version 2>/dev/null | head -1 || echo "unknown")
        if [ "$CURRENT_VERSION" = "$MEDIAMTX_VERSION" ] || [ "$CURRENT_VERSION" = "${MEDIAMTX_VERSION#v}" ]; then
            log_success "MediaMTX $MEDIAMTX_VERSION already installed"
            return 0
        fi
        log_info "Updating MediaMTX from $CURRENT_VERSION to $MEDIAMTX_VERSION"
    fi

    # Determine architecture
    ARCH=$(uname -m)
    case "$ARCH" in
        x86_64|amd64)
            ARCH_SUFFIX="linux_amd64"
            ;;
        aarch64|arm64)
            ARCH_SUFFIX="linux_arm64v8"
            ;;
        armv7l|armhf)
            ARCH_SUFFIX="linux_armv7"
            ;;
        i386|i686)
            ARCH_SUFFIX="linux_386"
            ;;
        *)
            log_error "Unsupported architecture: $ARCH"
            return 1
            ;;
    esac

    URL="https://github.com/bluenviron/mediamtx/releases/download/${MEDIAMTX_VERSION}/mediamtx_${MEDIAMTX_VERSION}_${ARCH_SUFFIX}.tar.gz"
    ARCHIVE="mediamtx_${MEDIAMTX_VERSION}_${ARCH_SUFFIX}.tar.gz"

    log_info "Architecture: $ARCH ($ARCH_SUFFIX)"
    log_info "Downloading from: $URL"

    # Download
    if command -v curl &>/dev/null; then
        curl -L -o "$ARCHIVE" "$URL" --progress-bar
    elif command -v wget &>/dev/null; then
        wget -O "$ARCHIVE" "$URL" --show-progress
    else
        log_error "Neither curl nor wget found"
        return 1
    fi

    # Extract
    log_info "Extracting..."
    tar -xzf "$ARCHIVE"
    rm -f "$ARCHIVE"

    # Set permissions
    chmod +x mediamtx

    log_success "MediaMTX $MEDIAMTX_VERSION installed"
}

download_ffmpeg() {
    log_step "Downloading FFmpeg"

    cd "$INSTALL_DIR"

    # Check if already exists
    if [ -f "ffmpeg/ffmpeg" ] && [ -f "ffmpeg/ffprobe" ]; then
        log_success "FFmpeg already installed"
        return 0
    fi

    mkdir -p ffmpeg

    # Determine architecture
    ARCH=$(uname -m)
    case "$ARCH" in
        x86_64|amd64)
            ARCH_SUFFIX="amd64"
            ;;
        aarch64|arm64)
            ARCH_SUFFIX="arm64"
            ;;
        *)
            log_warning "FFmpeg static builds not available for: $ARCH"
            log_info "Please install FFmpeg from your package manager"
            return 0
            ;;
    esac

    URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-${ARCH_SUFFIX}-static.tar.xz"
    ARCHIVE="ffmpeg-static.tar.xz"

    log_info "Architecture: $ARCH ($ARCH_SUFFIX)"
    log_info "Downloading from: $URL"

    # Download
    if command -v curl &>/dev/null; then
        curl -L -o "$ARCHIVE" "$URL" --progress-bar
    elif command -v wget &>/dev/null; then
        wget -O "$ARCHIVE" "$URL" --show-progress
    else
        log_error "Neither curl nor wget found"
        return 1
    fi

    # Extract
    log_info "Extracting..."
    mkdir -p ffmpeg_temp
    tar -xJf "$ARCHIVE" -C ffmpeg_temp

    # Move binaries
    find ffmpeg_temp -name 'ffmpeg' -type f -exec mv {} ffmpeg/ \;
    find ffmpeg_temp -name 'ffprobe' -type f -exec mv {} ffmpeg/ \;

    # Cleanup
    rm -rf ffmpeg_temp "$ARCHIVE"

    # Set permissions
    chmod +x ffmpeg/ffmpeg ffmpeg/ffprobe

    log_success "FFmpeg installed"
}

# =============================================================================
# SYSTEMD SERVICE
# =============================================================================

setup_systemd_service() {
    log_step "Setting Up Systemd Service"

    # Check if systemd is available
    if ! command -v systemctl &>/dev/null; then
        log_warning "systemctl not found, skipping service setup"
        return 0
    fi

    # Get current user
    CURRENT_USER=$(whoami)

    # Create service file
    SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

    log_info "Creating systemd service file..."

    sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=Tonys Onvif-RTSP Server
Documentation=https://github.com/YOUR_REPO
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/$VENV_DIR/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$INSTALL_DIR/$VENV_DIR/bin/python $INSTALL_DIR/run.py --no-browser
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=$INSTALL_DIR
PrivateTmp=true

# Resource limits
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    sudo systemctl daemon-reload

    log_success "Systemd service created: $SERVICE_NAME"

    # Ask about enabling
    echo ""
    read -p "Would you like to enable the service to start on boot? [y/N] " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo systemctl enable "$SERVICE_NAME"
        log_success "Service enabled for auto-start"
    fi

    # Ask about starting now
    read -p "Would you like to start the service now? [y/N] " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo systemctl start "$SERVICE_NAME"
        sleep 2
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            log_success "Service started successfully"
        else
            log_warning "Service may have failed to start. Check: sudo journalctl -u $SERVICE_NAME"
        fi
    fi
}

# =============================================================================
# FINAL SUMMARY
# =============================================================================

print_summary() {
    echo ""
    echo "${GREEN}${BOLD}============================================================${RESET}"
    echo "${GREEN}${BOLD}              Installation Complete!${RESET}"
    echo "${GREEN}${BOLD}============================================================${RESET}"
    echo ""
    echo "${CYAN}Installation Directory:${RESET} $INSTALL_DIR"
    echo "${CYAN}Virtual Environment:${RESET} $INSTALL_DIR/$VENV_DIR"
    echo ""
    echo "${BOLD}To start the server manually:${RESET}"
    echo "  cd $INSTALL_DIR"
    echo "  ./start_ubuntu_25.sh"
    echo ""
    echo "${BOLD}Or with command line options:${RESET}"
    echo "  ./start_ubuntu_25.sh --port 8080 --no-browser"
    echo ""

    if [ "$SKIP_SYSTEMD" -eq 0 ] && command -v systemctl &>/dev/null; then
        echo "${BOLD}Systemd service commands:${RESET}"
        echo "  sudo systemctl start $SERVICE_NAME    # Start server"
        echo "  sudo systemctl stop $SERVICE_NAME     # Stop server"
        echo "  sudo systemctl status $SERVICE_NAME   # Check status"
        echo "  sudo journalctl -u $SERVICE_NAME -f   # View logs"
        echo ""
    fi

    echo "${BOLD}Web UI:${RESET} http://localhost:5552"
    echo "${BOLD}RTSP:${RESET}   rtsp://localhost:8554"
    echo ""
    echo "${YELLOW}Note:${RESET} Run ./install.sh --uninstall to remove the systemd service"
    echo ""
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    print_banner

    # Check if running as root (not recommended)
    if [ "$EUID" -eq 0 ]; then
        log_warning "Running as root is not recommended"
        log_info "The script will use sudo when needed"
        echo ""
    fi

    # Run installation steps
    detect_distro
    install_system_dependencies
    check_python_version
    setup_virtual_environment
    install_python_dependencies

    if [ "$SKIP_BINARIES" -eq 0 ]; then
        download_mediamtx
        download_ffmpeg
    fi

    if [ "$SKIP_SYSTEMD" -eq 0 ]; then
        setup_systemd_service
    fi

    print_summary
}

# Run main
main
