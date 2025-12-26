#!/bin/bash
#
# Tonys Onvif-RTSP Server - Ubuntu/Linux Startup Script
#
# This script sets up and starts the ONVIF-RTSP server with proper
# error handling, virtual environment management, and command line options.
#
# Usage: ./start_ubuntu_25.sh [OPTIONS]
#   --port PORT       Set the web UI port (default: 5552)
#   --no-browser      Don't open browser automatically
#   --debug           Enable debug mode
#   --config FILE     Use custom config file
#   --help            Show this help message
#

# =============================================================================
# CONFIGURATION
# =============================================================================

# Exit on error, undefined variables, and pipe failures
set -e
set -u
set -o pipefail

# Script directory (absolute path)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Minimum Python version required
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=10

# Virtual environment directory
VENV_DIR="venv"

# =============================================================================
# COLOR DEFINITIONS
# =============================================================================

# Check if terminal supports colors
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
    echo "${CYAN}${BOLD}>>> $1${RESET}"
}

# =============================================================================
# CLEANUP AND SIGNAL HANDLING
# =============================================================================

# Track if cleanup has run to prevent double execution
CLEANUP_DONE=0

cleanup() {
    if [ "$CLEANUP_DONE" -eq 1 ]; then
        return
    fi
    CLEANUP_DONE=1

    echo ""
    log_info "Shutting down gracefully..."

    # Kill any child processes
    if [ -n "${SERVER_PID:-}" ] && kill -0 "$SERVER_PID" 2>/dev/null; then
        log_info "Stopping server (PID: $SERVER_PID)..."
        kill -TERM "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
    fi

    # Kill any stale mediamtx processes
    if command -v pkill &>/dev/null; then
        pkill -9 mediamtx 2>/dev/null || true
    fi

    log_success "Cleanup complete. Goodbye!"
    exit 0
}

# Trap signals for clean shutdown
trap cleanup SIGINT SIGTERM SIGHUP EXIT

# =============================================================================
# ARGUMENT PARSING
# =============================================================================

# Default values
PORT=""
NO_BROWSER=""
DEBUG=""
CONFIG_FILE=""
SHOW_HELP=0

show_help() {
    cat << EOF
${BOLD}Tonys Onvif-RTSP Server - Startup Script${RESET}

${CYAN}USAGE:${RESET}
    $0 [OPTIONS]

${CYAN}OPTIONS:${RESET}
    ${GREEN}--port PORT${RESET}       Set the web UI port (default: 5552)
    ${GREEN}--no-browser${RESET}      Don't open browser automatically
    ${GREEN}--debug${RESET}           Enable debug mode with verbose output
    ${GREEN}--config FILE${RESET}     Use a custom configuration file
    ${GREEN}--help, -h${RESET}        Show this help message

${CYAN}EXAMPLES:${RESET}
    $0                          # Start with defaults
    $0 --port 8080              # Start on port 8080
    $0 --no-browser --debug     # Start without browser, debug mode

${CYAN}REQUIREMENTS:${RESET}
    - Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR} or higher
    - Internet connection (for first-time setup)

EOF
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --no-browser)
            NO_BROWSER="--no-browser"
            shift
            ;;
        --debug)
            DEBUG="--debug"
            shift
            ;;
        --config)
            CONFIG_FILE="--config $2"
            shift 2
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
    echo "${CYAN}${BOLD}        Tonys Onvif-RTSP Server - Linux Startup${RESET}"
    echo "${CYAN}${BOLD}============================================================${RESET}"
    echo ""
}

# =============================================================================
# PYTHON VERSION CHECK
# =============================================================================

check_python_version() {
    log_step "Checking Python version..."

    # Find Python executable
    PYTHON_CMD=""
    for cmd in python3 python; do
        if command -v "$cmd" &>/dev/null; then
            PYTHON_CMD="$cmd"
            break
        fi
    done

    if [ -z "$PYTHON_CMD" ]; then
        log_error "Python is not installed or not in PATH"
        echo ""
        echo "Please install Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ using:"
        echo "  ${YELLOW}sudo apt install python3 python3-venv python3-pip${RESET}  (Ubuntu/Debian)"
        echo "  ${YELLOW}sudo dnf install python3 python3-pip${RESET}               (Fedora)"
        echo "  ${YELLOW}sudo pacman -S python python-pip${RESET}                   (Arch)"
        exit 1
    fi

    # Get Python version
    PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PYTHON_MAJOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.major)')
    PYTHON_MINOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.minor)')

    log_info "Found Python $PYTHON_VERSION at $(which $PYTHON_CMD)"

    # Version check
    if [ "$PYTHON_MAJOR" -lt "$MIN_PYTHON_MAJOR" ] || \
       { [ "$PYTHON_MAJOR" -eq "$MIN_PYTHON_MAJOR" ] && [ "$PYTHON_MINOR" -lt "$MIN_PYTHON_MINOR" ]; }; then
        log_error "Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ required, but found $PYTHON_VERSION"
        exit 1
    fi

    log_success "Python version $PYTHON_VERSION meets requirements"
}

# =============================================================================
# SYSTEM DEPENDENCIES CHECK
# =============================================================================

check_system_dependencies() {
    log_step "Checking system dependencies..."

    MISSING_DEPS=()

    # Check for python3-venv
    if ! $PYTHON_CMD -c "import venv" &>/dev/null; then
        MISSING_DEPS+=("python3-venv")
    fi

    # Check for pip
    if ! $PYTHON_CMD -m pip --version &>/dev/null; then
        MISSING_DEPS+=("python3-pip")
    fi

    # Check for common utilities
    if ! command -v curl &>/dev/null && ! command -v wget &>/dev/null; then
        MISSING_DEPS+=("curl")
    fi

    if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
        log_warning "Missing system dependencies: ${MISSING_DEPS[*]}"
        echo ""

        # Detect package manager and suggest install command
        if command -v apt-get &>/dev/null; then
            echo "Install with: ${YELLOW}sudo apt-get install -y ${MISSING_DEPS[*]}${RESET}"

            read -p "Would you like to install them now? [y/N] " -n 1 -r
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                log_info "Installing system dependencies..."
                sudo apt-get update
                sudo apt-get install -y "${MISSING_DEPS[@]}"
                log_success "System dependencies installed"
            else
                log_error "Cannot continue without required dependencies"
                exit 1
            fi
        elif command -v dnf &>/dev/null; then
            echo "Install with: ${YELLOW}sudo dnf install -y ${MISSING_DEPS[*]}${RESET}"
            exit 1
        elif command -v pacman &>/dev/null; then
            echo "Install with: ${YELLOW}sudo pacman -S ${MISSING_DEPS[*]}${RESET}"
            exit 1
        else
            log_error "Please install the missing dependencies manually"
            exit 1
        fi
    else
        log_success "All system dependencies are installed"
    fi
}

# =============================================================================
# VIRTUAL ENVIRONMENT SETUP
# =============================================================================

setup_virtual_environment() {
    log_step "Setting up Python virtual environment..."

    if [ ! -d "$VENV_DIR" ]; then
        log_info "Creating virtual environment in ./$VENV_DIR..."
        $PYTHON_CMD -m venv "$VENV_DIR"
        log_success "Virtual environment created"
    else
        log_success "Virtual environment already exists"
    fi

    # Activate virtual environment
    log_info "Activating virtual environment..."
    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate"

    # Verify activation
    if [ "$VIRTUAL_ENV" != "" ]; then
        log_success "Virtual environment activated: $VIRTUAL_ENV"
    else
        log_error "Failed to activate virtual environment"
        exit 1
    fi

    # Upgrade pip if needed
    log_info "Ensuring pip is up to date..."
    pip install --upgrade pip --quiet
}

# =============================================================================
# PYTHON DEPENDENCIES
# =============================================================================

check_python_dependencies() {
    log_step "Checking Python dependencies..."

    REQUIRED_PACKAGES=("flask" "flask-cors" "requests" "pyyaml" "psutil")
    MISSING_PACKAGES=()

    for pkg in "${REQUIRED_PACKAGES[@]}"; do
        # Normalize package name for import (flask-cors -> flask_cors)
        import_name="${pkg//-/_}"
        if ! python -c "import $import_name" &>/dev/null; then
            MISSING_PACKAGES+=("$pkg")
        fi
    done

    if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
        log_warning "Missing Python packages: ${MISSING_PACKAGES[*]}"
        log_info "Installing missing packages..."
        pip install "${MISSING_PACKAGES[@]}" --quiet
        log_success "Python packages installed"
    else
        log_success "All Python dependencies are installed"
    fi
}

# =============================================================================
# BINARY PERMISSIONS
# =============================================================================

setup_binary_permissions() {
    log_step "Setting up binary permissions..."

    # MediaMTX
    if [ -f "mediamtx" ]; then
        chmod +x mediamtx
        log_success "MediaMTX executable permissions set"
    fi

    # FFmpeg binaries
    if [ -d "ffmpeg" ]; then
        for binary in ffmpeg/ffmpeg ffmpeg/ffprobe; do
            if [ -f "$binary" ]; then
                chmod +x "$binary"
                log_success "$(basename $binary) executable permissions set"
            fi
        done
    fi
}

# =============================================================================
# SYSTEM LIMITS
# =============================================================================

increase_file_limits() {
    log_step "Configuring system limits..."

    # Try to increase file descriptor limit
    CURRENT_LIMIT=$(ulimit -n)
    TARGET_LIMIT=65535

    if [ "$CURRENT_LIMIT" -lt "$TARGET_LIMIT" ]; then
        log_info "Current file descriptor limit: $CURRENT_LIMIT"
        log_info "Attempting to increase to: $TARGET_LIMIT"

        if ulimit -n "$TARGET_LIMIT" 2>/dev/null; then
            log_success "File descriptor limit increased to $TARGET_LIMIT"
        else
            log_warning "Could not increase file limit (may need root privileges)"
            log_info "Current limit ($CURRENT_LIMIT) should work for most setups"
        fi
    else
        log_success "File descriptor limit already sufficient: $CURRENT_LIMIT"
    fi
}

# =============================================================================
# START SERVER
# =============================================================================

start_server() {
    log_step "Starting Tonys Onvif-RTSP Server..."

    # Build command arguments
    CMD_ARGS=""

    if [ -n "$PORT" ]; then
        CMD_ARGS="$CMD_ARGS --port $PORT"
    fi

    if [ -n "$NO_BROWSER" ]; then
        CMD_ARGS="$CMD_ARGS $NO_BROWSER"
    fi

    if [ -n "$DEBUG" ]; then
        CMD_ARGS="$CMD_ARGS $DEBUG"
    fi

    if [ -n "$CONFIG_FILE" ]; then
        CMD_ARGS="$CMD_ARGS $CONFIG_FILE"
    fi

    echo ""
    echo "${GREEN}${BOLD}============================================================${RESET}"
    echo "${GREEN}${BOLD}                    SERVER STARTING${RESET}"
    echo "${GREEN}${BOLD}============================================================${RESET}"
    echo ""

    # Start the server
    # shellcheck disable=SC2086
    python run.py $CMD_ARGS &
    SERVER_PID=$!

    # Wait for the server process
    wait $SERVER_PID
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    print_banner

    # Run setup steps
    check_python_version
    check_system_dependencies
    setup_virtual_environment
    check_python_dependencies
    setup_binary_permissions
    increase_file_limits

    # Start the server
    start_server
}

# Run main function
main
