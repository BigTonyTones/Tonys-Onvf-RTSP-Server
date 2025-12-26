@echo off
REM ============================================================================
REM Tonys Onvif-RTSP Server - Windows Startup Script
REM ============================================================================
REM
REM This script starts the ONVIF-RTSP server with proper error handling,
REM Python detection, and command line argument support.
REM
REM Usage: start_onvif_server.bat [OPTIONS]
REM   --port PORT       Set the web UI port (default: 5552)
REM   --no-browser      Don't open browser automatically
REM   --debug           Enable debug mode
REM   --config FILE     Use custom config file
REM   --help            Show this help message
REM
REM ============================================================================

setlocal EnableDelayedExpansion

REM ============================================================================
REM CONFIGURATION
REM ============================================================================

set "SCRIPT_DIR=%~dp0"
set "MIN_PYTHON_MAJOR=3"
set "MIN_PYTHON_MINOR=10"

REM Command line arguments to pass to run.py
set "RUN_ARGS="

REM ============================================================================
REM PARSE COMMAND LINE ARGUMENTS
REM ============================================================================

:parse_args
if "%~1"=="" goto :end_parse_args
if /I "%~1"=="--help" goto :show_help
if /I "%~1"=="-h" goto :show_help
if /I "%~1"=="--port" (
    set "RUN_ARGS=!RUN_ARGS! --port %~2"
    shift
    shift
    goto :parse_args
)
if /I "%~1"=="--no-browser" (
    set "RUN_ARGS=!RUN_ARGS! --no-browser"
    shift
    goto :parse_args
)
if /I "%~1"=="--debug" (
    set "RUN_ARGS=!RUN_ARGS! --debug"
    shift
    goto :parse_args
)
if /I "%~1"=="--config" (
    set "RUN_ARGS=!RUN_ARGS! --config %~2"
    shift
    shift
    goto :parse_args
)
echo [ERROR] Unknown option: %~1
echo Use --help for usage information
exit /b 1

:end_parse_args

REM ============================================================================
REM BANNER
REM ============================================================================

echo.
echo ============================================================
echo         Tonys Onvif-RTSP Server - Windows Startup
echo ============================================================
echo.

REM Change to the script directory
cd /d "%SCRIPT_DIR%"
echo [INFO] Working directory: %CD%
echo.

REM ============================================================================
REM PYTHON DETECTION AND VERSION CHECK
REM ============================================================================

echo [INFO] Checking Python installation...

REM Try to find Python
set "PYTHON_CMD="

REM Check 'python' first
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
    goto :found_python
)

REM Check 'python3'
python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python3"
    goto :found_python
)

REM Check 'py' launcher
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py"
    goto :found_python
)

REM Python not found
echo.
echo [ERROR] Python is not installed or not in PATH
echo.
echo Please install Python %MIN_PYTHON_MAJOR%.%MIN_PYTHON_MINOR% or higher from:
echo   https://www.python.org/downloads/
echo.
echo Make sure to check "Add Python to PATH" during installation.
echo.
echo Alternatively, install via winget:
echo   winget install Python.Python.3.12
echo.
pause
exit /b 1

:found_python
echo [OK] Found Python command: %PYTHON_CMD%

REM Get Python version
for /f "tokens=2 delims= " %%v in ('%PYTHON_CMD% --version 2^>^&1') do set "PYTHON_VERSION=%%v"
echo [INFO] Python version: %PYTHON_VERSION%

REM Parse version numbers
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set "PY_MAJOR=%%a"
    set "PY_MINOR=%%b"
)

REM Version check
if %PY_MAJOR% lss %MIN_PYTHON_MAJOR% goto :version_error
if %PY_MAJOR% equ %MIN_PYTHON_MAJOR% (
    if %PY_MINOR% lss %MIN_PYTHON_MINOR% goto :version_error
)

echo [OK] Python version meets requirements (>= %MIN_PYTHON_MAJOR%.%MIN_PYTHON_MINOR%)
goto :check_runpy

:version_error
echo.
echo [ERROR] Python %MIN_PYTHON_MAJOR%.%MIN_PYTHON_MINOR%+ required, but found %PYTHON_VERSION%
echo.
echo Please upgrade Python from:
echo   https://www.python.org/downloads/
echo.
pause
exit /b 1

REM ============================================================================
REM CHECK FOR RUN.PY
REM ============================================================================

:check_runpy
echo.
echo [INFO] Checking for run.py...

if not exist "run.py" (
    echo.
    echo [ERROR] run.py not found in current directory
    echo [INFO] Current directory: %CD%
    echo.
    echo Please make sure you are running this script from the
    echo Tonys Onvif-RTSP Server installation directory.
    echo.
    pause
    exit /b 1
)

echo [OK] Found run.py

REM ============================================================================
REM CHECK/CREATE VIRTUAL ENVIRONMENT (Optional)
REM ============================================================================

echo.
echo [INFO] Checking virtual environment...

if exist "venv\Scripts\activate.bat" (
    echo [OK] Virtual environment exists
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
    set "PYTHON_CMD=python"
    echo [OK] Virtual environment activated
) else (
    echo [INFO] No virtual environment found, using system Python
    echo [INFO] Tip: Run install.ps1 to set up a virtual environment
)

REM ============================================================================
REM CHECK DEPENDENCIES
REM ============================================================================

echo.
echo [INFO] Checking Python dependencies...

%PYTHON_CMD% -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Missing dependencies detected
    echo [INFO] Installing required packages...
    %PYTHON_CMD% -m pip install flask flask-cors requests pyyaml psutil --quiet
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies
        echo [INFO] Please run: %PYTHON_CMD% -m pip install flask flask-cors requests pyyaml psutil
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed
) else (
    echo [OK] All dependencies are installed
)

REM ============================================================================
REM START SERVER
REM ============================================================================

echo.
echo ============================================================
echo                     SERVER STARTING
echo ============================================================
echo.
echo [INFO] Starting Tonys Onvif-RTSP Server...
echo [INFO] Press Ctrl+C to stop the server
echo.

REM Start the Python server with arguments
%PYTHON_CMD% run.py %RUN_ARGS%

REM Check exit code
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Server exited with error code: %errorlevel%
    pause
)

exit /b %errorlevel%

REM ============================================================================
REM HELP MESSAGE
REM ============================================================================

:show_help
echo.
echo Tonys Onvif-RTSP Server - Windows Startup Script
echo.
echo USAGE:
echo     %~nx0 [OPTIONS]
echo.
echo OPTIONS:
echo     --port PORT       Set the web UI port (default: 5552)
echo     --no-browser      Don't open browser automatically
echo     --debug           Enable debug mode with verbose output
echo     --config FILE     Use a custom configuration file
echo     --help, -h        Show this help message
echo.
echo EXAMPLES:
echo     %~nx0                          Start with defaults
echo     %~nx0 --port 8080              Start on port 8080
echo     %~nx0 --no-browser --debug     Start without browser, debug mode
echo.
echo REQUIREMENTS:
echo     - Python %MIN_PYTHON_MAJOR%.%MIN_PYTHON_MINOR% or higher
echo     - Internet connection (for first-time setup)
echo.
exit /b 0
