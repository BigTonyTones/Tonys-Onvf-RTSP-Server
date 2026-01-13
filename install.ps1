# Tonys Onvif-RTSP Server - One-Line Windows Installer
# Usage: irm https://raw.githubusercontent.com/BigTonyTones/Tonys-Onvf-RTSP-Server/main/install.ps1 | iex
# Or:    Invoke-WebRequest -Uri "https://raw.githubusercontent.com/BigTonyTones/Tonys-Onvf-RTSP-Server/main/install.ps1" -UseBasicParsing | Invoke-Expression

#Requires -RunAsAdministrator

# Installation directory - use current directory or default if running from remote
$INSTALL_DIR = if (Test-Path "run.py") { 
    Get-Location 
}
else { 
    "C:\Program Files\Tonys-Onvif-Server" 
}
$REPO_URL = "https://github.com/BigTonyTones/Tonys-Onvf-RTSP-Server.git"

# Color functions
function Write-Banner {
    Write-Host ""
    Write-Host "==============================================================" -ForegroundColor Cyan
    Write-Host "     Tonys Onvif-RTSP Server - Automated Installer" -ForegroundColor Yellow
    Write-Host "==============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Installation Directory: " -NoNewline -ForegroundColor Cyan
    Write-Host $INSTALL_DIR
    Write-Host ""
}

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> " -NoNewline -ForegroundColor Blue
    Write-Host $Message
}

function Write-Info {
    param([string]$Message)
    Write-Host "    $Message"
}

function Write-Success {
    param([string]$Message)
    Write-Host "    [OK] " -NoNewline -ForegroundColor Green
    Write-Host $Message
}

function Write-Warning {
    param([string]$Message)
    Write-Host "    [WARN] " -NoNewline -ForegroundColor Yellow
    Write-Host $Message
}

function Write-Error {
    param([string]$Message)
    Write-Host "    [ERROR] " -NoNewline -ForegroundColor Red
    Write-Host $Message
}

# Check if running as Administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Administrator)) {
    Write-Error "This installer must be run as Administrator!"
    Write-Host ""
    Write-Host "Please right-click PowerShell and select 'Run as Administrator'"
    exit 1
}

# Detect OS and Architecture
function Get-SystemInfo {
    Write-Step "STEP 1: Detecting Operating System"
    
    $os = Get-CimInstance Win32_OperatingSystem
    $arch = $env:PROCESSOR_ARCHITECTURE
    
    Write-Info "Operating System: $($os.Caption)"
    Write-Info "Version: $($os.Version)"
    Write-Info "Architecture: $arch"
    Write-Success "OS detection complete"
    
    return @{
        OS           = $os.Caption
        Version      = $os.Version
        Architecture = $arch
    }
}

# Install Chocolatey if not present
function Install-Chocolatey {
    if (Get-Command choco -ErrorAction SilentlyContinue) {
        Write-Info "Chocolatey already installed"
        return $true
    }
    
    Write-Info "Installing Chocolatey package manager..."
    try {
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        
        # Refresh environment variables
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        
        Write-Success "Chocolatey installed successfully"
        return $true
    }
    catch {
        Write-Warning "Failed to install Chocolatey: $_"
        return $false
    }
}

# Install system dependencies
function Install-Dependencies {
    Write-Step "STEP 2: Installing System Dependencies"
    
    # Check for Python
    $pythonInstalled = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonInstalled) {
        Write-Info "Python not found. Installing Python..."
        
        if (Install-Chocolatey) {
            choco install python -y --no-progress
            # Refresh PATH
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            Write-Success "Python installed"
        }
        else {
            Write-Error "Could not install Python. Please install manually from https://www.python.org/"
            exit 1
        }
    }
    else {
        $pythonVersion = & python --version 2>&1
        Write-Success "Python already installed: $pythonVersion"
    }
    
    # Check for Git
    $gitInstalled = Get-Command git -ErrorAction SilentlyContinue
    if (-not $gitInstalled) {
        Write-Info "Git not found. Installing Git..."
        
        if (Install-Chocolatey) {
            choco install git -y --no-progress
            # Refresh PATH
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            Write-Success "Git installed"
        }
        else {
            Write-Warning "Could not install Git automatically"
        }
    }
    else {
        Write-Success "Git already installed"
    }
    
    Write-Success "System dependencies ready"
}

# Clone or update repository
function Get-Repository {
    Write-Step "STEP 3: Setting Up Repository"
    
    Write-Info "Target directory: $INSTALL_DIR"
    
    # Create directory if it doesn't exist
    if (-not (Test-Path $INSTALL_DIR)) {
        New-Item -ItemType Directory -Path $INSTALL_DIR -Force | Out-Null
    }
    
    Set-Location $INSTALL_DIR
    
    # Check if we're already in the repository
    if (Test-Path "run.py") {
        Write-Success "Repository already exists in this directory"
        
        if (Test-Path ".git") {
            Write-Info "Checking for updates from GitHub..."
            try {
                git fetch origin 2>&1 | Out-Null
                git reset --hard origin/main 2>&1 | Out-Null
                Write-Info "Repository updated to latest version"
            }
            catch {
                Write-Warning "Could not update repository: $_"
            }
        }
        return
    }
    
    # Check if this is a git repo that needs updating
    if (Test-Path ".git") {
        Write-Warning "Git repository found but incomplete"
        Write-Info "Pulling latest changes..."
        try {
            git fetch origin 2>&1 | Out-Null
            git reset --hard origin/main 2>&1 | Out-Null
            Write-Success "Repository updated"
        }
        catch {
            Write-Warning "Could not update repository: $_"
        }
        return
    }
    
    # Clone repository
    Write-Info "Cloning repository from GitHub..."
    Write-Info "URL: $REPO_URL"
    
    try {
        git clone $REPO_URL $INSTALL_DIR 2>&1 | Out-Null
        Write-Success "Repository cloned successfully"
    }
    catch {
        Write-Error "Failed to clone repository: $_"
        exit 1
    }
}

# Setup Python virtual environment
function Setup-PythonEnvironment {
    Write-Step "STEP 4: Setting Up Python Environment"
    
    Set-Location $INSTALL_DIR
    
    if (-not (Test-Path "venv")) {
        Write-Info "Creating Python virtual environment..."
        python -m venv venv
        Write-Info "Virtual environment created: $INSTALL_DIR\venv"
    }
    else {
        Write-Info "Virtual environment already exists"
    }
    
    # Activate virtual environment
    $venvActivate = Join-Path $INSTALL_DIR "venv\Scripts\Activate.ps1"
    & $venvActivate
    
    Write-Info "Upgrading pip..."
    python -m pip install --quiet --upgrade pip 2>&1 | Out-Null
    
    Write-Info "Installing Python packages:"
    Write-Info "  - flask (web framework)"
    Write-Info "  - flask-cors (CORS support)"
    Write-Info "  - requests (HTTP client)"
    Write-Info "  - pyyaml (YAML parsing)"
    Write-Info "  - psutil (system utilities)"
    Write-Info "  - onvif-zeep (ONVIF protocol)"
    
    pip install --quiet flask flask-cors requests pyyaml psutil onvif-zeep 2>&1 | Out-Null
    
    Write-Success "Python environment configured"
}

# Detect architecture for downloads
function Get-Architecture {
    $arch = $env:PROCESSOR_ARCHITECTURE
    switch ($arch) {
        "AMD64" { return "amd64" }
        "ARM64" { return "arm64" }
        default { return "amd64" }
    }
}

# Install MediaMTX
function Install-MediaMTX {
    Write-Step "STEP 5: Installing MediaMTX (RTSP Server)"
    
    Set-Location $INSTALL_DIR
    
    # Check if already exists
    if (Test-Path "mediamtx.exe") {
        Write-Success "MediaMTX already installed"
        Write-Info "Location: $INSTALL_DIR\mediamtx.exe"
        return
    }
    
    $arch = Get-Architecture
    $version = "1.15.6"
    $url = "https://github.com/bluenviron/mediamtx/releases/download/v$version/mediamtx_v${version}_windows_$arch.zip"
    
    Write-Info "Downloading MediaMTX v$version..."
    Write-Info "Platform: windows/$arch"
    Write-Info "URL: $url"
    
    try {
        $tempZip = Join-Path $env:TEMP "mediamtx.zip"
        Invoke-WebRequest -Uri $url -OutFile $tempZip -UseBasicParsing
        
        Write-Info "Extracting MediaMTX..."
        Expand-Archive -Path $tempZip -DestinationPath $INSTALL_DIR -Force
        
        Write-Info "Cleaning up..."
        Remove-Item $tempZip -Force
        
        Write-Success "MediaMTX v$version installed"
    }
    catch {
        Write-Warning "Failed to download MediaMTX: $_"
        Write-Info "You can install it manually later"
    }
}

# Install FFmpeg
function Install-FFmpeg {
    Write-Step "STEP 6: Installing FFmpeg (Video Processing)"
    
    Set-Location $INSTALL_DIR
    
    # Check if FFmpeg is in PATH
    $ffmpegInPath = Get-Command ffmpeg -ErrorAction SilentlyContinue
    if ($ffmpegInPath) {
        $version = & ffmpeg -version 2>&1 | Select-Object -First 1
        Write-Success "FFmpeg already available in PATH"
        Write-Info "$version"
        return
    }
    
    # Check if local ffmpeg exists
    if (Test-Path "ffmpeg\ffmpeg.exe") {
        Write-Success "FFmpeg already installed locally"
        Write-Info "Location: $INSTALL_DIR\ffmpeg\ffmpeg.exe"
        
        # Add to PATH if not already there
        $ffmpegDir = Join-Path $INSTALL_DIR "ffmpeg"
        $currentPath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
        if ($currentPath -notlike "*$ffmpegDir*") {
            Write-Info "Adding FFmpeg to system PATH..."
            [System.Environment]::SetEnvironmentVariable("Path", "$currentPath;$ffmpegDir", "Machine")
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            Write-Success "FFmpeg added to system PATH"
        }
        return
    }
    
    # Try to install via Chocolatey first
    Write-Info "Attempting to install FFmpeg via Chocolatey..."
    if (Install-Chocolatey) {
        try {
            choco install ffmpeg -y --no-progress 2>&1 | Out-Null
            
            # Refresh PATH
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            
            # Verify installation
            $ffmpegInPath = Get-Command ffmpeg -ErrorAction SilentlyContinue
            if ($ffmpegInPath) {
                $version = & ffmpeg -version 2>&1 | Select-Object -First 1
                Write-Success "FFmpeg installed via Chocolatey"
                Write-Info "Verified: $version"
                return
            }
        }
        catch {
            Write-Warning "Chocolatey installation failed, trying direct download..."
        }
    }
    
    # Fallback: Download FFmpeg directly
    Write-Info "Downloading FFmpeg static build..."
    
    $arch = Get-Architecture
    $ffmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    
    Write-Info "Architecture: $arch"
    Write-Info "Download URL: $ffmpegUrl"
    
    try {
        $tempZip = Join-Path $env:TEMP "ffmpeg.zip"
        Write-Info "Downloading FFmpeg (this may take a moment)..."
        Invoke-WebRequest -Uri $ffmpegUrl -OutFile $tempZip -UseBasicParsing
        
        Write-Info "Download complete. Extracting FFmpeg..."
        $tempExtract = Join-Path $env:TEMP "ffmpeg-extract"
        
        if (Test-Path $tempExtract) {
            Remove-Item $tempExtract -Recurse -Force
        }
        
        Expand-Archive -Path $tempZip -DestinationPath $tempExtract -Force
        
        # Find the ffmpeg binaries
        $ffmpegBin = Get-ChildItem -Path $tempExtract -Recurse -Directory | Where-Object { $_.Name -eq "bin" } | Select-Object -First 1
        
        if ($ffmpegBin) {
            Write-Info "Installing FFmpeg binaries to $INSTALL_DIR\ffmpeg\..."
            
            # Create ffmpeg directory
            $ffmpegDir = Join-Path $INSTALL_DIR "ffmpeg"
            if (-not (Test-Path $ffmpegDir)) {
                New-Item -ItemType Directory -Path $ffmpegDir -Force | Out-Null
            }
            
            # Copy binaries
            Copy-Item -Path (Join-Path $ffmpegBin.FullName "ffmpeg.exe") -Destination $ffmpegDir -Force
            Copy-Item -Path (Join-Path $ffmpegBin.FullName "ffprobe.exe") -Destination $ffmpegDir -Force -ErrorAction SilentlyContinue
            
            Write-Info "Cleaning up temporary files..."
            Remove-Item $tempZip -Force
            Remove-Item $tempExtract -Recurse -Force
            
            # Verify installation
            $ffmpegExe = Join-Path $ffmpegDir "ffmpeg.exe"
            if (Test-Path $ffmpegExe) {
                $version = & $ffmpegExe -version 2>&1 | Select-Object -First 1
                Write-Success "FFmpeg installed successfully to $ffmpegDir"
                Write-Info "$version"
                
                # Add to system PATH
                Write-Info "Adding FFmpeg to system PATH..."
                $currentPath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
                if ($currentPath -notlike "*$ffmpegDir*") {
                    [System.Environment]::SetEnvironmentVariable("Path", "$currentPath;$ffmpegDir", "Machine")
                    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
                    Write-Success "FFmpeg added to system PATH"
                }
            }
            else {
                Write-Error "FFmpeg installation verification failed"
                exit 1
            }
        }
        else {
            Write-Error "Could not find FFmpeg binaries in downloaded archive"
            exit 1
        }
    }
    catch {
        Write-Error "Failed to download/install FFmpeg: $_"
        Write-Info "Please install FFmpeg manually from https://ffmpeg.org/"
        exit 1
    }
}

# Create start script
function New-StartScript {
    Write-Step "Creating start script..."
    
    $startScript = @"
@echo off
cd /d "%~dp0"
echo Starting Tonys Onvif-RTSP Server...
call venv\Scripts\activate.bat
python run.py
pause
"@
    
    $scriptPath = Join-Path $INSTALL_DIR "start-server.bat"
    $startScript | Out-File -FilePath $scriptPath -Encoding ASCII -Force
    
    Write-Success "Start script created: start-server.bat"
}

# Create Windows service (optional)
function New-WindowsService {
    Write-Step "Creating Windows service (optional)..."
    
    $serviceName = "TonysOnvifServer"
    $existingService = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
    
    if ($existingService) {
        Write-Info "Service '$serviceName' already exists"
        return
    }
    
    Write-Info "To create a Windows service, you can use NSSM (Non-Sucking Service Manager)"
    Write-Info "Install with: choco install nssm -y"
    Write-Info "Then run: nssm install $serviceName"
}

# Print completion message
function Write-Completion {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║          Installation Complete!                              ║" -ForegroundColor Green
    Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Installation Path: " -NoNewline -ForegroundColor Cyan
    Write-Host $INSTALL_DIR
    Write-Host ""
    Write-Host "  To start the server:" -ForegroundColor Yellow
    Write-Host "    cd `"$INSTALL_DIR`""
    Write-Host "    .\start-server.bat"
    Write-Host ""
    Write-Host "  Or run directly:" -ForegroundColor Yellow
    Write-Host "    cd `"$INSTALL_DIR`""
    Write-Host "    .\venv\Scripts\activate"
    Write-Host "    python run.py"
    Write-Host ""
    Write-Host "  Web UI: " -NoNewline -ForegroundColor Yellow
    Write-Host "http://localhost:5552"
    Write-Host ""
    Write-Host "  Thank you for using Tonys Onvif-RTSP Server!" -ForegroundColor Cyan
    Write-Host ""
}

# Main installation flow
function Start-Installation {
    Write-Banner
    
    $sysInfo = Get-SystemInfo
    Install-Dependencies
    Get-Repository
    Setup-PythonEnvironment
    Install-MediaMTX
    Install-FFmpeg
    New-StartScript
    New-WindowsService
    Write-Completion
    
    # Ask if user wants to start the server now
    Write-Host ""
    Write-Host "Would you like to start the server now? (y/n): " -NoNewline -ForegroundColor Yellow
    $startNow = Read-Host
    
    if ($startNow -eq 'y' -or $startNow -eq 'Y' -or $startNow -eq 'yes' -or $startNow -eq 'Yes') {
        Write-Host ""
        Write-Host "Starting Tonys Onvif-RTSP Server..." -ForegroundColor Green
        Write-Host ""
        Set-Location $INSTALL_DIR
        & ".\start-server.bat"
    }
    else {
        Write-Host ""
        Write-Host "Server not started. You can start it later with:" -ForegroundColor Cyan
        Write-Host "  cd `"$INSTALL_DIR`""
        Write-Host "  .\start-server.bat"
        Write-Host ""
    }
}

# Run installation
Start-Installation
