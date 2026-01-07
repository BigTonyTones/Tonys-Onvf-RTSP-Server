@echo off
REM ========================================
REM Tonys Onvif-RTSP Server
REM Auto-Start Batch File
REM ========================================

echo.
echo ========================================
echo  Tonys Onvif-RTSP Server v5.6
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

REM Check if required Python packages are installed
echo Checking Python packages...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [WARNING] Missing core Python packages: flask, flask-cors, requests, pyyaml, psutil, onvif-zeep
    echo.
    set /p install="Would you like to install them now via pip? (y/n): "
    if /i "%install%"=="y" (
        echo.
        echo Installing packages...
        pip install flask flask-cors requests pyyaml psutil onvif-zeep
        echo.
        if errorlevel 1 (
            echo [ERROR] Failed to install packages
            echo Please install them manually with: pip install flask flask-cors requests pyyaml psutil onvif-zeep
            echo.
            pause
            exit /b 1
        )
        echo Packages installed successfully!
        echo.
    ) else (
        echo.
        echo [ERROR] Installation skipped. Please install dependencies manually.
        echo Run: pip install flask flask-cors requests pyyaml psutil onvif-zeep
        echo.
        pause
        exit /b 1
    )
) else (
    echo Core Python packages already installed.
    echo.
)

echo Starting ONVIF Server...
echo.
echo ========================================
echo.

REM Start the Python server
python run.py

REM Exit immediately when process finishes
exit /b 0
