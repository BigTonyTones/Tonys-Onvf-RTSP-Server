# One-Line Installers

This directory contains automated installers for Tonys Onvif-RTSP Server that handle all dependencies automatically.

## Linux/macOS Installation

Run this single command to install everything:

```bash
curl -fsSL https://raw.githubusercontent.com/BigTonyTones/Tonys-Onvf-RTSP-Server/main/install.sh | sudo bash
```

Or with wget:

```bash
wget -qO- https://raw.githubusercontent.com/BigTonyTones/Tonys-Onvf-RTSP-Server/main/install.sh | sudo bash
```

### What Gets Installed (Linux/macOS):
- ✅ Git
- ✅ Python 3 + pip + venv
- ✅ Python packages (flask, flask-cors, requests, pyyaml, psutil, onvif-zeep)
- ✅ MediaMTX v1.15.6 (RTSP server)
- ✅ FFmpeg (via package manager or static build)
- ✅ Systemd service (Linux) or Launchd service (macOS)
- ✅ Convenience command: `tonys-onvif`

### After Installation (Linux/macOS):

Start the server:
```bash
sudo tonys-onvif
```

Or manually:
```bash
cd /opt/tonys-onvif-server
sudo ./start_ubuntu_25.sh
```

Enable auto-start on boot (Linux):
```bash
sudo systemctl enable tonys-onvif
sudo systemctl start tonys-onvif
```

---

## Windows Installation

Run this single command in PowerShell (as Administrator):

```powershell
irm https://raw.githubusercontent.com/BigTonyTones/Tonys-Onvf-RTSP-Server/main/install.ps1 | iex
```

Or the long form:

```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/BigTonyTones/Tonys-Onvf-RTSP-Server/main/install.ps1" -UseBasicParsing | Invoke-Expression
```

### What Gets Installed (Windows):
- ✅ Chocolatey package manager (if not present)
- ✅ Python 3 (if not present)
- ✅ Git (if not present)
- ✅ Python packages (flask, flask-cors, requests, pyyaml, psutil, onvif-zeep)
- ✅ MediaMTX v1.15.6 (RTSP server)
- ✅ FFmpeg (via Chocolatey or direct download)
- ✅ Start script: `start-server.bat`

### After Installation (Windows):

Start the server:
```cmd
cd "C:\Program Files\Tonys-Onvif-Server"
start-server.bat
```

Or manually:
```cmd
cd "C:\Program Files\Tonys-Onvif-Server"
venv\Scripts\activate
python run.py
```

---

## Web Interface

After installation, access the web interface at:
- **http://localhost:5552**

---

## Supported Platforms

### Linux:
- ✅ Ubuntu / Debian / Raspbian
- ✅ Fedora
- ✅ CentOS / RHEL / Rocky / Alma
- ✅ Arch / Manjaro

### macOS:
- ✅ macOS 10.15+ (Catalina and newer)

### Windows:
- ✅ Windows 10 / 11
- ✅ Windows Server 2016+

### Architectures:
- ✅ x86_64 / AMD64
- ✅ ARM64 / aarch64
- ✅ ARMv7 / ARMv6 (Linux only)

---

## Manual Installation

If you prefer to install manually, see the main [README.md](../README.md) for detailed instructions.

---

## Troubleshooting

### Linux/macOS:
- Make sure to run with `sudo`
- Check logs: `journalctl -u tonys-onvif -f` (systemd)
- Verify FFmpeg: `ffmpeg -version` or `./ffmpeg/ffmpeg -version`

### Windows:
- Make sure to run PowerShell as Administrator
- If execution policy blocks the script, run: `Set-ExecutionPolicy Bypass -Scope Process`
- Verify FFmpeg: `ffmpeg -version` or `.\ffmpeg\ffmpeg.exe -version`

### Common Issues:
- **Port 5552 already in use**: Stop any existing instances or change the port in settings
- **FFmpeg not found**: The installer should handle this, but you can install manually
- **Permission denied**: Make sure you're running with admin/sudo privileges

---

## Uninstallation

### Linux:
```bash
sudo systemctl stop tonys-onvif
sudo systemctl disable tonys-onvif
sudo rm /etc/systemd/system/tonys-onvif.service
sudo rm -rf /opt/tonys-onvif-server
sudo rm /usr/local/bin/tonys-onvif
```

### macOS:
```bash
sudo launchctl unload /Library/LaunchDaemons/com.tonys.onvif-server.plist
sudo rm /Library/LaunchDaemons/com.tonys.onvif-server.plist
sudo rm -rf /opt/tonys-onvif-server
```

### Windows:
```powershell
Remove-Item "C:\Program Files\Tonys-Onvif-Server" -Recurse -Force
```

---

## Support

For issues, questions, or feature requests, please visit:
- GitHub Issues: https://github.com/BigTonyTones/Tonys-Onvf-RTSP-Server/issues
- GitHub Discussions: https://github.com/BigTonyTones/Tonys-Onvf-RTSP-Server/discussions
