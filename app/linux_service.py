import os
import getpass
import subprocess
from pathlib import Path

class LinuxServiceManager:
    """Manages the systemd service for the ONVIF server on Linux"""
    
    SERVICE_NAME = "tony-onvif-server.service"
    
    @staticmethod
    def is_linux():
        import platform
        return platform.system().lower() == "linux"

    def __init__(self):
        self.app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.user = getpass.getuser()
        self.service_path = f"/etc/systemd/system/{self.SERVICE_NAME}"
        self.start_script = os.path.join(self.app_dir, "start_ubuntu_25.sh")

    def is_service_installed(self):
        """Check if the systemd service file exists"""
        if not self.is_linux():
            return False
        return os.path.exists(self.service_path)

    def is_service_enabled(self):
        """Check if the service is enabled to start on boot"""
        if not self.is_linux() or not self.is_service_installed():
            return False
        try:
            result = subprocess.run(['systemctl', 'is-enabled', self.SERVICE_NAME], 
                                  capture_output=True, text=True)
            return result.stdout.strip() == 'enabled'
        except:
            return False

    def install_service(self):
        """Create and enable the systemd service"""
        if not self.is_linux():
            return False, "Not running on Linux"

        service_content = f"""[Unit]
Description=Tonys Onvif-RTSP Server
After=network.target

[Service]
Type=simple
User={self.user}
WorkingDirectory={self.app_dir}
ExecStart=/bin/bash {self.start_script}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        
        try:
            # Create a temporary service file
            temp_path = "/tmp/tony-onvif.service"
            with open(temp_path, "w") as f:
                f.write(service_content)
            
            # Move to /etc/systemd/system (requires sudo)
            print(f"📦 Installing systemd service to {self.service_path}...")
            subprocess.run(['sudo', 'mv', temp_path, self.service_path], check=True)
            subprocess.run(['sudo', 'chmod', '644', self.service_path], check=True)
            
            # Reload, enable and start
            subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
            subprocess.run(['sudo', 'systemctl', 'enable', self.SERVICE_NAME], check=True)
            
            return True, "Service installed and enabled successfully"
        except subprocess.CalledProcessError as e:
            return False, f"Failed to install service: {e}"
        except Exception as e:
            return False, f"Error: {e}"

    def uninstall_service(self):
        """Stop, disable and remove the systemd service"""
        if not self.is_linux():
            return False, "Not running on Linux"
            
        if not self.is_service_installed():
            return True, "Service not installed"

        try:
            print(f"🧹 Disabling systemd service (removing from boot)...")
            # Only disable and remove the file. DO NOT 'stop' here, 
            # or the server will kill itself while trying to respond to the web request.
            subprocess.run(['sudo', 'systemctl', 'disable', self.SERVICE_NAME], check=False)
            if os.path.exists(self.service_path):
                subprocess.run(['sudo', 'rm', self.service_path], check=True)
            subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
            
            return True, "Service removed from system boot"
        except subprocess.CalledProcessError as e:
            return False, f"Failed to uninstall service: {e}"
        except Exception as e:
            return False, f"Error: {e}"
