@echo off
REM ========================================
REM Tonys Onvif-RTSP Server
REM Auto-Start Batch File
REM ========================================

echo.
echo ========================================
echo  Tonys Onvif-RTSP Server v5.3
echo ========================================
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Display current directory
echo Current directory: %CD%
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.7 or higher from https://www.python.org/
    echo.
    pause
    exit /b 1
)

REM Display Python version
echo Python version:
python --version
echo.

REM Check if run.py exists
if not exist "run.py" (
    echo [ERROR] run.py not found in current directory
    echo Current directory: %CD%
    echo.
    pause
    exit /b 1
)

echo Starting ONVIF Server...
echo.
echo ========================================
echo.

REM Start the Python server
python run.py

REM Exit immediately when process finishes
exit /b 0
