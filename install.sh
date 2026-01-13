#!/bin/bash

# Tonys Onvif-RTSP Server - One-Line Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/BigTonyTones/Tonys-Onvf-RTSP-Server/main/install.sh | sudo bash
# Or:    wget -qO- https://raw.githubusercontent.com/BigTonyTones/Tonys-Onvf-RTSP-Server/main/install.sh | sudo bash

set -e

# Define colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Installation directory - use current directory or default if running from curl pipe
# If script is piped via curl, use a default directory, otherwise use current directory
if [ -t 0 ]; then
    # Running interactively (not piped), use current directory
    INSTALL_DIR="$(pwd)"
else
    # Piped from curl, use default directory
    INSTALL_DIR="/opt/tonys-onvif-server"
fi
REPO_URL="https://github.com/BigTonyTones/Tonys-Onvf-RTSP-Server.git"

print_banner() {
    echo ""
    echo -e "${CYAN}==============================================================${NC}"
    echo -e "${YELLOW}     Tonys Onvif-RTSP Server - Automated Installer${NC}"
    echo -e "${CYAN}==============================================================${NC}"
    echo ""
    echo -e "  ${CYAN}Installation Directory:${NC} $INSTALL_DIR"
    echo ""
}

print_step() {
    echo ""
    echo -e "${BLUE}==>${NC} ${1}"
}

print_info() {
    echo -e "    ${1}"
}

print_success() {
    echo -e "    ${GREEN}[OK]${NC} ${1}"
}

print_warning() {
    echo -e "    ${YELLOW}[WARN]${NC} ${1}"
}

print_error() {
    echo -e "    ${RED}[ERROR]${NC} ${1}"
}

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This installer must be run with sudo!"
        echo ""
        echo "Usage:"
        echo "  curl -fsSL https://raw.githubusercontent.com/BigTonyTones/Tonys-Onvf-RTSP-Server/main/install.sh | sudo bash"
        exit 1
    fi
}

# Detect OS
detect_os() {
    print_step "STEP 1: Detecting Operating System"
    
    # Check for macOS first
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        OS_VERSION=$(sw_vers -productVersion 2>/dev/null || echo "unknown")
        print_info "Operating System: macOS"
        print_info "Version: $OS_VERSION"
        print_info "Architecture: $(uname -m)"
        print_success "OS detection complete"
        return
    fi
    
    # Check for Linux distributions
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
        print_info "Operating System: $PRETTY_NAME"
        print_info "ID: $OS"
        print_info "Version: $OS_VERSION"
        print_info "Architecture: $(uname -m)"
        print_success "OS detection complete"
    else
        print_error "Cannot detect OS"
        print_info "This installer requires macOS or a modern Linux distribution"
        exit 1
    fi
}

# Install system dependencies
install_dependencies() {
    print_step "STEP 2: Installing System Dependencies"
    
    print_info "Detected OS: $OS"
    
    case $OS in
        macos)
            print_info "Using Homebrew package manager..."
            if ! command -v brew &> /dev/null; then
                print_warning "Homebrew not found. Installing Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            print_info "Installing: python3, git, curl, wget"
            brew install python3 git curl wget 2>/dev/null || true
            ;;
        ubuntu|debian|raspbian)
            print_info "Using apt package manager..."
            print_info "Running apt-get update..."
            apt-get update -qq
            print_info "Installing: git, python3, python3-venv, python3-pip, curl, wget"
            apt-get install -y -qq git python3-full python3-venv python3-pip curl wget > /dev/null 2>&1 || \
            apt-get install -y -qq git python3 python3-venv python3-pip curl wget > /dev/null 2>&1
            ;;
        fedora)
            print_info "Using dnf package manager..."
            print_info "Installing: git, python3, python3-pip, curl, wget"
            dnf install -y -q git python3 python3-pip curl wget > /dev/null 2>&1
            ;;
        centos|rhel|rocky|alma)
            print_info "Using yum package manager..."
            print_info "Installing: git, python3, python3-pip, curl, wget"
            yum install -y -q git python3 python3-pip curl wget > /dev/null 2>&1
            ;;
        arch|manjaro)
            print_info "Using pacman package manager..."
            print_info "Installing: git, python, python-pip, curl, wget"
            pacman -Sy --noconfirm --quiet git python python-pip curl wget > /dev/null 2>&1
            ;;
        *)
            print_warning "Unsupported OS: $OS"
            print_info "Attempting to continue with existing packages..."
            ;;
    esac
    
    print_success "System dependencies installed"
}

# Clone or update repository
clone_repository() {
    print_step "STEP 3: Setting Up Repository"
    
    print_info "Target directory: $INSTALL_DIR"
    
    cd "$INSTALL_DIR" 2>/dev/null || mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # Check if we're already in the repository (run.py exists)
    if [ -f "run.py" ]; then
        print_success "Repository already exists in this directory"
        if [ -d ".git" ]; then
            print_info "Checking for updates from GitHub..."
            git fetch --quiet origin 2>/dev/null || true
            git reset --quiet --hard origin/main 2>/dev/null || true
            print_info "Repository updated to latest version"
        fi
        return
    fi
    
    # Check if this is a git repo that needs updating
    if [ -d ".git" ]; then
        print_warning "Git repository found but incomplete"
        print_info "Pulling latest changes..."
        git fetch --quiet origin 2>/dev/null || true
        git reset --quiet --hard origin/main 2>/dev/null || true
        print_success "Repository updated"
        return
    fi
    
    # Directory exists but is not a git repo - clone to temp and copy
    print_info "Cloning repository from GitHub..."
    print_info "URL: $REPO_URL"
    TEMP_CLONE="/tmp/tonys-onvif-clone-$$"
    rm -rf "$TEMP_CLONE" 2>/dev/null || true
    
    if git clone --quiet "$REPO_URL" "$TEMP_CLONE" 2>/dev/null; then
        print_info "Clone complete, copying files..."
        cp -rf "$TEMP_CLONE"/* "$INSTALL_DIR"/ 2>/dev/null || true
        cp -rf "$TEMP_CLONE"/.git "$INSTALL_DIR"/ 2>/dev/null || true
        cp -rf "$TEMP_CLONE"/.gitignore "$INSTALL_DIR"/ 2>/dev/null || true
        print_info "Cleaning up temporary files..."
        rm -rf "$TEMP_CLONE"
        print_success "Repository ready"
    else
        print_error "Failed to clone repository"
        rm -rf "$TEMP_CLONE" 2>/dev/null || true
        exit 1
    fi
}

# Setup Python virtual environment
setup_venv() {
    print_step "STEP 4: Setting Up Python Environment"
    
    cd "$INSTALL_DIR"
    
    if [ ! -d "venv" ]; then
        print_info "Creating Python virtual environment..."
        python3 -m venv venv
        print_info "Virtual environment created: $INSTALL_DIR/venv"
    else
        print_info "Virtual environment already exists"
    fi
    
    source venv/bin/activate
    
    print_info "Upgrading pip..."
    pip install --quiet --upgrade pip 2>/dev/null
    
    print_info "Installing Python packages:"
    print_info "  - flask (web framework)"
    print_info "  - flask-cors (CORS support)"
    print_info "  - requests (HTTP client)"
    print_info "  - pyyaml (YAML parsing)"
    print_info "  - psutil (system utilities)"
    print_info "  - onvif-zeep (ONVIF protocol)"
    pip install --quiet flask flask-cors requests pyyaml psutil onvif-zeep 2>/dev/null
    
    deactivate
    
    print_success "Python environment configured"
}

# Detect system architecture
detect_arch() {
    ARCH=$(uname -m)
    case $ARCH in
        x86_64|amd64)
            ARCH="amd64"
            ;;
        aarch64|arm64)
            ARCH="arm64"
            ;;
        armv7l|armhf)
            ARCH="armv7"
            ;;
        armv6l)
            ARCH="armv6"
            ;;
        *)
            print_warning "Unknown architecture: $ARCH. Defaulting to amd64."
            ARCH="amd64"
            ;;
    esac
}

# Install MediaMTX
install_mediamtx() {
    print_step "STEP 5: Installing MediaMTX (RTSP Server)"
    
    cd "$INSTALL_DIR"
    
    # Skip if already exists and is executable
    if [ -f "mediamtx" ] && [ -x "mediamtx" ]; then
        print_success "MediaMTX already installed"
        print_info "Location: $INSTALL_DIR/mediamtx"
        return
    fi
    
    detect_arch
    
    # Determine OS type for download
    if [ "$OS" == "macos" ]; then
        MEDIAMTX_OS="darwin"
    else
        MEDIAMTX_OS="linux"
    fi
    
    # MediaMTX version and download URL
    MEDIAMTX_VERSION="1.15.6"
    MEDIAMTX_URL="https://github.com/bluenviron/mediamtx/releases/download/v${MEDIAMTX_VERSION}/mediamtx_v${MEDIAMTX_VERSION}_${MEDIAMTX_OS}_${ARCH}.tar.gz"
    
    print_info "Downloading MediaMTX v${MEDIAMTX_VERSION}..."
    print_info "Platform: ${MEDIAMTX_OS}/${ARCH}"
    print_info "URL: $MEDIAMTX_URL"
    
    # Download and extract
    curl -fsSL "$MEDIAMTX_URL" -o /tmp/mediamtx.tar.gz 2>/dev/null || {
        print_warning "Failed to download MediaMTX"
        print_info "You can install it manually later"
        return
    }
    
    print_info "Extracting MediaMTX..."
    tar -xzf /tmp/mediamtx.tar.gz -C "$INSTALL_DIR" mediamtx 2>/dev/null || {
        tar -xzf /tmp/mediamtx.tar.gz -C "$INSTALL_DIR" 2>/dev/null
    }
    
    print_info "Cleaning up..."
    rm -f /tmp/mediamtx.tar.gz
    chmod +x "$INSTALL_DIR/mediamtx" 2>/dev/null || true
    
    print_success "MediaMTX v${MEDIAMTX_VERSION} installed"
}

# Install FFmpeg
install_ffmpeg() {
    print_step "STEP 6: Installing FFmpeg (Video Processing)"
    
    cd "$INSTALL_DIR"
    
    # Check if FFmpeg is already in the system PATH
    if command -v ffmpeg &> /dev/null; then
        FFMPEG_VERSION=$(ffmpeg -version 2>&1 | head -n1)
        print_success "FFmpeg already available in PATH"
        print_info "$FFMPEG_VERSION"
        return
    fi
    
    # Check if local ffmpeg exists in ffmpeg subdirectory
    if [ -f "ffmpeg/ffmpeg" ] && [ -x "ffmpeg/ffmpeg" ]; then
        print_success "FFmpeg already installed locally"
        print_info "Location: $INSTALL_DIR/ffmpeg/ffmpeg"
        return
    fi
    
    detect_arch
    
    if [ "$OS" == "macos" ]; then
        # Install via Homebrew on macOS
        print_info "Installing FFmpeg via Homebrew..."
        if ! command -v brew &> /dev/null; then
            print_warning "Homebrew not found. Installing Homebrew first..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        
        brew install ffmpeg 2>/dev/null || {
            print_error "Failed to install FFmpeg via Homebrew"
            print_info "Please install manually: brew install ffmpeg"
            exit 1
        }
        print_success "FFmpeg installed via Homebrew"
    else
        # Linux: Try package manager first, then fallback to static build
        FFMPEG_INSTALLED=false
        
        print_info "Attempting to install FFmpeg via package manager..."
        case $OS in
            ubuntu|debian|raspbian)
                print_info "Running: apt-get install -y ffmpeg"
                if apt-get install -y -qq ffmpeg > /dev/null 2>&1; then
                    print_success "FFmpeg installed via apt"
                    FFMPEG_INSTALLED=true
                fi
                ;;
            fedora)
                print_info "Running: dnf install -y ffmpeg"
                if dnf install -y -q ffmpeg > /dev/null 2>&1; then
                    print_success "FFmpeg installed via dnf"
                    FFMPEG_INSTALLED=true
                fi
                ;;
            centos|rhel|rocky|alma)
                print_info "Running: yum install -y ffmpeg"
                if yum install -y -q ffmpeg > /dev/null 2>&1; then
                    print_success "FFmpeg installed via yum"
                    FFMPEG_INSTALLED=true
                fi
                ;;
            arch|manjaro)
                print_info "Running: pacman -S --noconfirm ffmpeg"
                if pacman -Sy --noconfirm --quiet ffmpeg > /dev/null 2>&1; then
                    print_success "FFmpeg installed via pacman"
                    FFMPEG_INSTALLED=true
                fi
                ;;
        esac
        
        # If package manager install succeeded, verify and return
        if [ "$FFMPEG_INSTALLED" = true ]; then
            if command -v ffmpeg &> /dev/null; then
                FFMPEG_VERSION=$(ffmpeg -version 2>&1 | head -n1)
                print_info "Verified: $FFMPEG_VERSION"
                return
            fi
        fi
        
        # Fallback: Download static build
        print_warning "Package manager install failed or FFmpeg not available in repos"
        print_info "Downloading static FFmpeg build as fallback..."
        
        # Create ffmpeg subdirectory
        mkdir -p "$INSTALL_DIR/ffmpeg"
        
        # Determine download URL based on architecture
        if [ "$ARCH" == "amd64" ]; then
            FFMPEG_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
        elif [ "$ARCH" == "arm64" ]; then
            FFMPEG_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz"
        elif [ "$ARCH" == "armv7" ] || [ "$ARCH" == "armv6" ]; then
            FFMPEG_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-armhf-static.tar.xz"
        else
            print_error "No static FFmpeg build available for architecture: $ARCH"
            print_info "Please install FFmpeg manually for your system"
            exit 1
        fi
        
        print_info "Architecture: $ARCH"
        print_info "Download URL: $FFMPEG_URL"
        
        # Download FFmpeg
        if ! curl -fsSL "$FFMPEG_URL" -o /tmp/ffmpeg.tar.xz 2>/dev/null; then
            print_error "Failed to download FFmpeg from $FFMPEG_URL"
            print_info "Please check your internet connection and try again"
            exit 1
        fi
        
        print_info "Download complete. Extracting FFmpeg..."
        
        # Extract FFmpeg
        mkdir -p /tmp/ffmpeg-extract
        if ! tar -xJf /tmp/ffmpeg.tar.xz -C /tmp/ffmpeg-extract 2>/dev/null; then
            print_error "Failed to extract FFmpeg archive"
            rm -rf /tmp/ffmpeg.tar.xz /tmp/ffmpeg-extract
            exit 1
        fi
        
        # Copy binaries
        print_info "Installing FFmpeg binaries to $INSTALL_DIR/ffmpeg/..."
        if ! find /tmp/ffmpeg-extract -name "ffmpeg" -type f -exec cp {} "$INSTALL_DIR/ffmpeg/ffmpeg" \;; then
            print_error "Failed to copy ffmpeg binary"
            rm -rf /tmp/ffmpeg.tar.xz /tmp/ffmpeg-extract
            exit 1
        fi
        
        if ! find /tmp/ffmpeg-extract -name "ffprobe" -type f -exec cp {} "$INSTALL_DIR/ffmpeg/ffprobe" \;; then
            print_warning "Failed to copy ffprobe binary (non-critical)"
        fi
        
        # Set permissions
        chmod +x "$INSTALL_DIR/ffmpeg/ffmpeg" 2>/dev/null || true
        chmod +x "$INSTALL_DIR/ffmpeg/ffprobe" 2>/dev/null || true
        
        # Cleanup
        print_info "Cleaning up temporary files..."
        rm -rf /tmp/ffmpeg.tar.xz /tmp/ffmpeg-extract
        
        # Verify installation
        if [ -x "$INSTALL_DIR/ffmpeg/ffmpeg" ]; then
            FFMPEG_VERSION=$("$INSTALL_DIR/ffmpeg/ffmpeg" -version 2>&1 | head -n1)
            print_success "FFmpeg installed successfully to $INSTALL_DIR/ffmpeg/"
            print_info "$FFMPEG_VERSION"
        else
            print_error "FFmpeg installation verification failed"
            exit 1
        fi
    fi
}

# Set permissions
set_permissions() {
    print_step "Setting permissions..."
    
    cd "$INSTALL_DIR"
    
    chmod +x start_ubuntu_25.sh 2>/dev/null || true
    
    if [ -f "mediamtx" ]; then
        chmod +x mediamtx
    fi
    
    if [ -f "ffmpeg" ]; then
        chmod +x ffmpeg
    fi
    
    print_success "Permissions configured"
}

# Create system service (systemd for Linux, launchd for macOS)
create_system_service() {
    if [ "$OS" == "macos" ]; then
        print_step "Creating launchd service..."
        
        cat > /Library/LaunchDaemons/com.tonys.onvif-server.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.tonys.onvif-server</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/tonys-onvif-server/venv/bin/python</string>
        <string>/opt/tonys-onvif-server/run.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/opt/tonys-onvif-server</string>
    <key>RunAtLoad</key>
    <false/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    <key>StandardOutPath</key>
    <string>/opt/tonys-onvif-server/logs/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/opt/tonys-onvif-server/logs/stderr.log</string>
</dict>
</plist>
EOF
        mkdir -p /opt/tonys-onvif-server/logs 2>/dev/null || true
        print_success "Launchd service created (com.tonys.onvif-server)"
    else
        print_step "Creating systemd service..."
        
        cat > /etc/systemd/system/tonys-onvif.service << 'EOF'
[Unit]
Description=Tonys Onvif-RTSP Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/tonys-onvif-server
ExecStart=/opt/tonys-onvif-server/venv/bin/python /opt/tonys-onvif-server/run.py
Restart=on-failure
RestartSec=5
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF

        systemctl daemon-reload 2>/dev/null || true
        print_success "Systemd service created (tonys-onvif.service)"
    fi
}

# Create convenience commands
create_commands() {
    print_step "Creating convenience commands..."
    
    # Create a 'tonys-onvif' command
    cat > /usr/local/bin/tonys-onvif << 'EOF'
#!/bin/bash
cd /opt/tonys-onvif-server
sudo ./start_ubuntu_25.sh
EOF
    chmod +x /usr/local/bin/tonys-onvif
    
    print_success "Command 'tonys-onvif' created"
}

# Print completion message
print_completion() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}          ${GREEN}Installation Complete!${NC}                              ${GREEN}║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  ${CYAN}Installation Path:${NC} $INSTALL_DIR"
    echo ""
    echo -e "  ${YELLOW}To start the server:${NC}"
    echo "    sudo tonys-onvif"
    echo ""
    echo -e "  ${YELLOW}Or manually:${NC}"
    echo "    cd $INSTALL_DIR && sudo ./start_ubuntu_25.sh"
    echo ""
    
    if [ "$OS" == "macos" ]; then
        echo -e "  ${YELLOW}To enable auto-start on boot:${NC}"
        echo "    sudo launchctl load /Library/LaunchDaemons/com.tonys.onvif-server.plist"
        echo ""
        echo -e "  ${YELLOW}To stop the service:${NC}"
        echo "    sudo launchctl unload /Library/LaunchDaemons/com.tonys.onvif-server.plist"
    else
        echo -e "  ${YELLOW}To enable auto-start on boot:${NC}"
        echo "    sudo systemctl enable tonys-onvif"
        echo "    sudo systemctl start tonys-onvif"
    fi
    
    echo ""
    echo -e "  ${YELLOW}Web UI:${NC} http://localhost:5552"
    echo ""
    echo -e "  ${CYAN}Thank you for using Tonys Onvif-RTSP Server!${NC}"
    echo ""
}

# Main installation flow
main() {
    print_banner
    check_root
    detect_os
    install_dependencies
    clone_repository
    setup_venv
    install_mediamtx
    install_ffmpeg
    set_permissions
    create_system_service
    create_commands
    print_completion
    
    # Ask if user wants to start the server now
    echo ""
    echo -e "${YELLOW}Would you like to start the server now? (y/n):${NC} "
    read -r start_now
    
    if [[ $start_now == [yY] || $start_now == [yY][eE][sS] ]]; then
        echo ""
        echo -e "${GREEN}Starting Tonys Onvif-RTSP Server...${NC}"
        echo ""
        cd "$INSTALL_DIR"
        exec ./start_ubuntu_25.sh
    else
        echo ""
        echo -e "${CYAN}Server not started. You can start it later with:${NC}"
        echo "  sudo tonys-onvif"
        echo ""
    fi
}

# Run main function
main

