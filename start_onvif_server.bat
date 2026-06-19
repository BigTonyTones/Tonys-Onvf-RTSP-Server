@echo off
REM ========================================
REM Tonys Onvif-RTSP-AI Server
REM Auto-Start Batch File
REM ========================================

echo.
echo ========================================
echo  Tonys Onvif-RTSP-AI Server
echo ========================================
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Display current directory
echo Current directory: %CD%
echo.

REM Detect global Python first
set "GLOBAL_PYTHON="
python --version >nul 2>&1
if "%errorlevel%"=="0" (
    set "GLOBAL_PYTHON=python"
    goto :global_python_found
)
py --version >nul 2>&1
if "%errorlevel%"=="0" (
    set "GLOBAL_PYTHON=py"
    goto :global_python_found
)
goto :python_not_found

:global_python_found
REM Check if virtual environment Python exists, if not create it
if exist "venv\Scripts\python.exe" goto :venv_exists

echo.
echo Virtual environment (venv) not found.
echo Creating Python virtual environment (venv) to isolate dependencies...
%GLOBAL_PYTHON% -m venv venv
if not "%errorlevel%"=="0" (
    echo.
    echo [WARNING] Could not create virtual environment.
    echo Falling back to system Python...
    set "PYTHON_CMD=%GLOBAL_PYTHON%"
    goto :python_found
)
echo Virtual environment created successfully!
echo.

:venv_exists
set "PYTHON_CMD=venv\Scripts\python.exe"
echo Using Python virtual environment...
goto :python_found

:python_not_found
echo [WARNING] Python is not installed or not in PATH.
set /p install_python="Would you like to automatically download and install Python 3.12? (y/n): "
if /i not "%install_python%"=="y" (
    echo.
    echo [ERROR] Python is required to run this server.
    echo Please install Python 3.7 or higher from https://www.python.org/
    echo.
    pause
    exit /b 1
)

echo.
echo Downloading Python 3.12.2 installer...
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.2/python-3.12.2-amd64.exe' -OutFile 'python_installer.exe'"

if not exist "python_installer.exe" (
    echo [ERROR] Failed to download Python installer.
    echo Please install it manually from https://www.python.org/
    pause
    exit /b 1
)

echo Installing Python... This may take a minute (Running Silently)...
echo Please grant Administrator permission if prompted.
start /wait python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

echo.
echo Cleaning up...
del python_installer.exe

echo.
echo [SUCCESS] Python has been installed! 
echo IMPORTANT: You MUST close this window and run "start_onvif_server.bat" again 
echo to refresh your system PATH variables.
echo.
pause
exit /b 0

:python_found
REM Display Python version
echo Python version:
%PYTHON_CMD% --version
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
%PYTHON_CMD% -c "import flask" >nul 2>&1
if %errorlevel% equ 0 goto :packages_ok

echo.
echo [WARNING] Missing core Python packages: flask, flask-cors, requests, pyyaml, psutil, onvif-zeep, paramiko, cryptography
echo.
choice /C YN /M "Would you like to install them now via pip?"
if %errorlevel% equ 2 (
    echo.
    echo [ERROR] Installation skipped. Please install dependencies manually.
    echo Run: %PYTHON_CMD% -m pip install flask flask-cors requests pyyaml psutil onvif-zeep paramiko cryptography
    echo.
    pause
    exit /b 1
)

echo.
echo Installing critical packages (Flask, etc.)...
%PYTHON_CMD% -m pip install flask flask-cors requests pyyaml onvif-zeep paramiko cryptography

echo.
echo Attempting to install optional system metrics (psutil)...
echo (This may fail on newer Python versions, but the server will still run)
%PYTHON_CMD% -m pip install psutil
echo.

REM Final verification: Is the core app (flask) actually usable?
%PYTHON_CMD% -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install core dependencies.
    echo Please try running this manually: %PYTHON_CMD% -m pip install flask flask-cors requests pyyaml onvif-zeep paramiko cryptography
    echo.
    pause
    exit /b 1
)

echo Packages setup complete!
echo.
goto :packages_ok

:packages_ok
echo Environment check passed.
echo.

echo Starting ONVIF Server...
echo.
echo ========================================
echo.

REM Start the Python server
%PYTHON_CMD% run.py

REM Exit immediately when process finishes
exit /b 0
