#Requires -Version 5.1
<#
.SYNOPSIS
    Tonys Onvif-RTSP Server - Windows Installation Script

.DESCRIPTION
    One-command installation script for Windows.
    - Checks for and optionally installs Python via winget
    - Creates a Python virtual environment
    - Installs Python dependencies
    - Downloads MediaMTX and FFmpeg binaries
    - Optionally creates a desktop shortcut

.PARAMETER NoBinaries
    Skip downloading MediaMTX and FFmpeg

.PARAMETER NoShortcut
    Skip creating desktop shortcut

.PARAMETER Uninstall
    Remove desktop shortcut and virtual environment

.PARAMETER Help
    Show this help message

.EXAMPLE
    .\install.ps1
    Full installation with all components

.EXAMPLE
    .\install.ps1 -NoBinaries
    Install without downloading binaries

.EXAMPLE
    .\install.ps1 -Uninstall
    Remove installation components

.NOTES
    Author: Tonys Onvif-RTSP Server Team
    Version: 1.0.0
#>

[CmdletBinding()]
param(
    [switch]$NoBinaries,
    [switch]$NoShortcut,
    [switch]$Uninstall,
    [switch]$Help
)

# =============================================================================
# CONFIGURATION
# =============================================================================

$ScriptVersion = "1.0.0"
$MinPythonMajor = 3
$MinPythonMinor = 10
$VenvDir = "venv"
$MediaMtxVersion = "v1.15.5"

# Installation directory (script location)
$InstallDir = $PSScriptRoot
if (-not $InstallDir) {
    $InstallDir = Get-Location
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Type = "Info"
    )

    switch ($Type) {
        "Info"    { Write-Host "[INFO] " -ForegroundColor Blue -NoNewline; Write-Host $Message }
        "OK"      { Write-Host "[OK] " -ForegroundColor Green -NoNewline; Write-Host $Message }
        "Warn"    { Write-Host "[WARN] " -ForegroundColor Yellow -NoNewline; Write-Host $Message }
        "Error"   { Write-Host "[ERROR] " -ForegroundColor Red -NoNewline; Write-Host $Message }
        "Step"    { Write-Host "`n=== $Message ===" -ForegroundColor Cyan }
        default   { Write-Host $Message }
    }
}

function Show-Banner {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "    Tonys Onvif-RTSP Server - Windows Installer v$ScriptVersion" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Show-HelpMessage {
    $helpText = @"

Tonys Onvif-RTSP Server - Windows Installation Script
Version: $ScriptVersion

USAGE:
    .\install.ps1 [OPTIONS]

OPTIONS:
    -NoBinaries     Skip downloading MediaMTX and FFmpeg
    -NoShortcut     Skip creating desktop shortcut
    -Uninstall      Remove desktop shortcut and virtual environment
    -Help           Show this help message

WHAT THIS SCRIPT DOES:
    1. Checks for Python 3.10+ (offers to install via winget)
    2. Creates a Python virtual environment
    3. Installs Python dependencies
    4. Downloads MediaMTX and FFmpeg binaries
    5. Optionally creates a desktop shortcut

EXAMPLES:
    .\install.ps1                   # Full installation
    .\install.ps1 -NoBinaries       # Install without binaries
    .\install.ps1 -Uninstall        # Remove components

"@
    Write-Host $helpText
    exit 0
}

# =============================================================================
# SHOW HELP IF REQUESTED
# =============================================================================

if ($Help) {
    Show-HelpMessage
}

# =============================================================================
# UNINSTALL FUNCTION
# =============================================================================

function Invoke-Uninstall {
    Write-ColorOutput "Uninstalling Tonys Onvif-RTSP Server" -Type "Step"

    # Remove desktop shortcut
    $desktopPath = [Environment]::GetFolderPath("Desktop")
    $shortcutPath = Join-Path $desktopPath "Tonys Onvif-RTSP Server.lnk"

    if (Test-Path $shortcutPath) {
        Remove-Item $shortcutPath -Force
        Write-ColorOutput "Desktop shortcut removed" -Type "OK"
    } else {
        Write-ColorOutput "No desktop shortcut found" -Type "Info"
    }

    # Remove virtual environment
    $venvPath = Join-Path $InstallDir $VenvDir
    if (Test-Path $venvPath) {
        Write-ColorOutput "Removing virtual environment..." -Type "Info"
        Remove-Item $venvPath -Recurse -Force
        Write-ColorOutput "Virtual environment removed" -Type "OK"
    } else {
        Write-ColorOutput "No virtual environment found" -Type "Info"
    }

    Write-Host ""
    Write-ColorOutput "Uninstall complete!" -Type "OK"
    Write-Host ""
    Write-Host "Note: Application files and binaries were not removed."
    Write-Host "To completely remove, delete the installation directory:"
    Write-Host "  $InstallDir"
    Write-Host ""

    exit 0
}

if ($Uninstall) {
    Show-Banner
    Invoke-Uninstall
}

# =============================================================================
# CHECK ADMIN RIGHTS (for winget)
# =============================================================================

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# =============================================================================
# PYTHON DETECTION AND INSTALLATION
# =============================================================================

function Find-Python {
    Write-ColorOutput "Checking Python Installation" -Type "Step"

    $pythonCommands = @("python", "python3", "py")
    $pythonCmd = $null
    $pythonVersion = $null

    foreach ($cmd in $pythonCommands) {
        try {
            $output = & $cmd --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                $pythonCmd = $cmd
                $pythonVersion = ($output -replace "Python ", "").Trim()
                break
            }
        } catch {
            continue
        }
    }

    return @{
        Command = $pythonCmd
        Version = $pythonVersion
    }
}

function Test-PythonVersion {
    param(
        [string]$Version
    )

    $parts = $Version.Split(".")
    $major = [int]$parts[0]
    $minor = [int]$parts[1]

    if ($major -lt $MinPythonMajor) { return $false }
    if ($major -eq $MinPythonMajor -and $minor -lt $MinPythonMinor) { return $false }

    return $true
}

function Install-PythonViaWinget {
    Write-ColorOutput "Attempting to install Python via winget..." -Type "Info"

    # Check if winget is available
    try {
        $wingetVersion = & winget --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "winget not available"
        }
    } catch {
        Write-ColorOutput "winget is not available on this system" -Type "Warn"
        Write-Host ""
        Write-Host "Please install Python manually from:"
        Write-Host "  https://www.python.org/downloads/"
        Write-Host ""
        Write-Host "Make sure to check 'Add Python to PATH' during installation."
        Write-Host ""
        return $false
    }

    Write-ColorOutput "Installing Python 3.12 via winget..." -Type "Info"

    try {
        # Install Python
        & winget install Python.Python.3.12 --accept-source-agreements --accept-package-agreements

        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "Python installed successfully" -Type "OK"
            Write-Host ""
            Write-ColorOutput "IMPORTANT: Please restart PowerShell and run this script again" -Type "Warn"
            Write-Host "           This is required for Python to be available in PATH."
            Write-Host ""
            return $true
        } else {
            throw "winget install failed"
        }
    } catch {
        Write-ColorOutput "Failed to install Python via winget" -Type "Error"
        Write-Host ""
        Write-Host "Please install Python manually from:"
        Write-Host "  https://www.python.org/downloads/"
        Write-Host ""
        return $false
    }
}

function Ensure-Python {
    $python = Find-Python

    if (-not $python.Command) {
        Write-ColorOutput "Python is not installed" -Type "Warn"
        Write-Host ""

        $response = Read-Host "Would you like to install Python via winget? [Y/n]"
        if ($response -eq "" -or $response -match "^[Yy]") {
            $installed = Install-PythonViaWinget
            if ($installed) {
                exit 0  # User needs to restart PowerShell
            } else {
                exit 1
            }
        } else {
            Write-Host ""
            Write-Host "Please install Python $MinPythonMajor.$MinPythonMinor+ manually from:"
            Write-Host "  https://www.python.org/downloads/"
            Write-Host ""
            exit 1
        }
    }

    Write-ColorOutput "Found Python $($python.Version) ($($python.Command))" -Type "Info"

    # Check version
    if (-not (Test-PythonVersion -Version $python.Version)) {
        Write-ColorOutput "Python $MinPythonMajor.$MinPythonMinor+ required, but found $($python.Version)" -Type "Error"
        Write-Host ""

        $response = Read-Host "Would you like to install Python 3.12 via winget? [Y/n]"
        if ($response -eq "" -or $response -match "^[Yy]") {
            $installed = Install-PythonViaWinget
            if ($installed) {
                exit 0  # User needs to restart PowerShell
            } else {
                exit 1
            }
        } else {
            exit 1
        }
    }

    Write-ColorOutput "Python version meets requirements (>= $MinPythonMajor.$MinPythonMinor)" -Type "OK"

    return $python.Command
}

# =============================================================================
# VIRTUAL ENVIRONMENT
# =============================================================================

function Setup-VirtualEnvironment {
    param(
        [string]$PythonCmd
    )

    Write-ColorOutput "Setting Up Python Virtual Environment" -Type "Step"

    $venvPath = Join-Path $InstallDir $VenvDir

    # Remove existing venv if present
    if (Test-Path $venvPath) {
        Write-ColorOutput "Removing existing virtual environment..." -Type "Info"
        Remove-Item $venvPath -Recurse -Force
    }

    Write-ColorOutput "Creating virtual environment..." -Type "Info"

    & $PythonCmd -m venv $venvPath

    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "Failed to create virtual environment" -Type "Error"
        exit 1
    }

    Write-ColorOutput "Virtual environment created at $venvPath" -Type "OK"

    # Activate and upgrade pip
    $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
    . $activateScript

    Write-ColorOutput "Upgrading pip..." -Type "Info"
    & python -m pip install --upgrade pip --quiet

    Write-ColorOutput "Virtual environment ready" -Type "OK"
}

# =============================================================================
# PYTHON DEPENDENCIES
# =============================================================================

function Install-PythonDependencies {
    Write-ColorOutput "Installing Python Dependencies" -Type "Step"

    # Ensure venv is activated
    $activateScript = Join-Path $InstallDir "$VenvDir\Scripts\Activate.ps1"
    . $activateScript

    $packages = @("flask", "flask-cors", "requests", "pyyaml", "psutil", "tzdata")

    Write-ColorOutput "Installing packages: $($packages -join ', ')" -Type "Info"

    & python -m pip install $packages --quiet

    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "Failed to install some packages" -Type "Warn"
    } else {
        Write-ColorOutput "Python dependencies installed" -Type "OK"
    }
}

# =============================================================================
# DOWNLOAD BINARIES
# =============================================================================

function Download-MediaMTX {
    Write-ColorOutput "Downloading MediaMTX" -Type "Step"

    $mediamtxPath = Join-Path $InstallDir "mediamtx.exe"

    # Check if already exists
    if (Test-Path $mediamtxPath) {
        try {
            $currentVersion = & $mediamtxPath --version 2>&1
            if ($currentVersion -match $MediaMtxVersion.TrimStart("v")) {
                Write-ColorOutput "MediaMTX $MediaMtxVersion already installed" -Type "OK"
                return
            }
        } catch {
            # Continue to download
        }
    }

    # Determine architecture
    $arch = if ([Environment]::Is64BitOperatingSystem) { "amd64" } else { "386" }

    $url = "https://github.com/bluenviron/mediamtx/releases/download/$MediaMtxVersion/mediamtx_${MediaMtxVersion}_windows_${arch}.zip"
    $archivePath = Join-Path $InstallDir "mediamtx.zip"

    Write-ColorOutput "Architecture: Windows $arch" -Type "Info"
    Write-ColorOutput "Downloading from: $url" -Type "Info"

    try {
        # Download with progress
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $url -OutFile $archivePath -UseBasicParsing
        $ProgressPreference = 'Continue'

        Write-ColorOutput "Download complete, extracting..." -Type "Info"

        # Extract
        Expand-Archive -Path $archivePath -DestinationPath $InstallDir -Force

        # Cleanup
        Remove-Item $archivePath -Force

        Write-ColorOutput "MediaMTX $MediaMtxVersion installed" -Type "OK"
    } catch {
        Write-ColorOutput "Failed to download MediaMTX: $_" -Type "Error"
    }
}

function Download-FFmpeg {
    Write-ColorOutput "Downloading FFmpeg" -Type "Step"

    $ffmpegDir = Join-Path $InstallDir "ffmpeg"
    $ffmpegExe = Join-Path $ffmpegDir "ffmpeg.exe"

    # Check if already exists
    if ((Test-Path $ffmpegExe) -and (Test-Path (Join-Path $ffmpegDir "ffprobe.exe"))) {
        Write-ColorOutput "FFmpeg already installed" -Type "OK"
        return
    }

    # Create directory
    if (-not (Test-Path $ffmpegDir)) {
        New-Item -ItemType Directory -Path $ffmpegDir -Force | Out-Null
    }

    $url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    $archivePath = Join-Path $InstallDir "ffmpeg.zip"

    Write-ColorOutput "Downloading from: $url" -Type "Info"
    Write-ColorOutput "This may take a few minutes..." -Type "Info"

    try {
        # Download with progress
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $url -OutFile $archivePath -UseBasicParsing
        $ProgressPreference = 'Continue'

        Write-ColorOutput "Download complete, extracting..." -Type "Info"

        # Extract to temp directory
        $tempDir = Join-Path $InstallDir "ffmpeg_temp"
        Expand-Archive -Path $archivePath -DestinationPath $tempDir -Force

        # Find and move binaries
        $binDir = Get-ChildItem -Path $tempDir -Recurse -Directory -Filter "bin" | Select-Object -First 1
        if ($binDir) {
            Copy-Item -Path (Join-Path $binDir.FullName "ffmpeg.exe") -Destination $ffmpegDir -Force
            Copy-Item -Path (Join-Path $binDir.FullName "ffprobe.exe") -Destination $ffmpegDir -Force
        }

        # Cleanup
        Remove-Item $tempDir -Recurse -Force
        Remove-Item $archivePath -Force

        Write-ColorOutput "FFmpeg installed" -Type "OK"
    } catch {
        Write-ColorOutput "Failed to download FFmpeg: $_" -Type "Error"
    }
}

# =============================================================================
# DESKTOP SHORTCUT
# =============================================================================

function Create-DesktopShortcut {
    Write-ColorOutput "Creating Desktop Shortcut" -Type "Step"

    $desktopPath = [Environment]::GetFolderPath("Desktop")
    $shortcutPath = Join-Path $desktopPath "Tonys Onvif-RTSP Server.lnk"

    # Check if already exists
    if (Test-Path $shortcutPath) {
        Write-ColorOutput "Desktop shortcut already exists" -Type "OK"
        return
    }

    $response = Read-Host "Would you like to create a desktop shortcut? [Y/n]"
    if ($response -ne "" -and $response -notmatch "^[Yy]") {
        Write-ColorOutput "Skipping desktop shortcut" -Type "Info"
        return
    }

    try {
        $WScriptShell = New-Object -ComObject WScript.Shell
        $shortcut = $WScriptShell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = Join-Path $InstallDir "start_onvif_server.bat"
        $shortcut.WorkingDirectory = $InstallDir
        $shortcut.Description = "Start Tonys Onvif-RTSP Server"
        $shortcut.IconLocation = "shell32.dll,21"  # Video camera icon
        $shortcut.Save()

        Write-ColorOutput "Desktop shortcut created" -Type "OK"
    } catch {
        Write-ColorOutput "Failed to create desktop shortcut: $_" -Type "Warn"
    }
}

# =============================================================================
# SUMMARY
# =============================================================================

function Show-Summary {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "              Installation Complete!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Installation Directory: " -NoNewline -ForegroundColor Cyan
    Write-Host $InstallDir
    Write-Host "Virtual Environment: " -NoNewline -ForegroundColor Cyan
    Write-Host (Join-Path $InstallDir $VenvDir)
    Write-Host ""
    Write-Host "To start the server:" -ForegroundColor White
    Write-Host "  .\start_onvif_server.bat"
    Write-Host ""
    Write-Host "Or with command line options:" -ForegroundColor White
    Write-Host "  .\start_onvif_server.bat --port 8080 --no-browser"
    Write-Host ""
    Write-Host "Web UI: " -NoNewline -ForegroundColor White
    Write-Host "http://localhost:5552"
    Write-Host "RTSP:   " -NoNewline -ForegroundColor White
    Write-Host "rtsp://localhost:8554"
    Write-Host ""
    Write-Host "Note: " -NoNewline -ForegroundColor Yellow
    Write-Host "Run .\install.ps1 -Uninstall to remove components"
    Write-Host ""
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

function Main {
    Show-Banner

    # Change to install directory
    Set-Location $InstallDir
    Write-ColorOutput "Installation directory: $InstallDir" -Type "Info"

    # Check for Python and install if needed
    $pythonCmd = Ensure-Python

    # Setup virtual environment
    Setup-VirtualEnvironment -PythonCmd $pythonCmd

    # Install Python dependencies
    Install-PythonDependencies

    # Download binaries
    if (-not $NoBinaries) {
        Download-MediaMTX
        Download-FFmpeg
    }

    # Create desktop shortcut
    if (-not $NoShortcut) {
        Create-DesktopShortcut
    }

    # Show summary
    Show-Summary
}

# Run main
Main
