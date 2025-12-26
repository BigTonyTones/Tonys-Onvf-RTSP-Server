# 🎥 Tonys Onvif-RTSP Server v4.0

![Dashboard Screenshot](assets/dashboard_screenshot.png)

A robust Virtual ONVIF-RTSP Gateway designed to bridge incompatible cameras into NVRs like UniFi Protect. 

### 1. Ubiquiti Protect NVR Compatibility
The Ubiquiti Protect NVR platform has limited compatibility with many generic ONVIF cameras. This tool bridges that gap by allowing incompatible RTSP streams to be imported and presented as fully compliant virtual ONVIF cameras, ensuring seamless integration and reliable operation within the Protect ecosystem.

Additionally, Ubiquiti Protect requires a **unique MAC address** for each camera. This can be achieved in several ways:
* **Virtualized Environment**: Running the application in a virtualized environment and assigning multiple virtual network interfaces.
* **Physical NICs**: Physically installing additional network interface cards (NICs) on the host system.
* **Linux macvlan**: Using Linux `macvlan` networking. This program fully supports `macvlan` and has been tested on **Ubuntu 25.04** for compatibility and stable operation.

### 2. Stream Rebroadcasting and Performance Optimization
The application also enables reliable rebroadcasting of a single RTSP stream. Many physical cameras struggle to handle multiple concurrent connections, often resulting in lag or instability. This server functions as a high-performance proxy, efficiently managing multiple viewers while minimizing load on the original camera hardware.

> [!IMPORTANT]
> **Platform Optimization & Limitations:**
> * **Ubuntu 25.04 Optimized**: This application is specifically optimized for Ubuntu 25.04.
> * **Linux Exclusive Features**: The **Virtual NIC (Unique IP & MAC Address)** feature uses `macvlan` and is **ONLY available on Linux**.
> * **Windows Limitation**: The Virtual NIC feature is **NOT available on Windows**. Multiple cameras will share the same host IP on Windows.
> * **Virtualization Requirement**: If you are running this server inside a Virtual Machine (ESXi, Proxmox, VirtualBox, etc.), you **MUST enable Promiscuous Mode** on the network interface and port group for `macvlan` (Virtual NIC) to function correctly.
> * **Transcoding Alert**: Enabling live transcoding is **extremely resource-intensive** (high CPU usage) and is **not recommended** for multiple cameras unless strictly required for codec compatibility.
> * **Manual Restart**: It is recommended to **manually restart the server** after adding or updating custom network settings (IP/MAC) to ensure clean initialization.
> * **Manual Adoption**: You must perform a **manual adoption** of each camera within the UniFi Protect application using the ONVIF IP and credentials provided by this server.

## 🌟 Key Features
- **NVR Compatibility**: Specifically optimized for UniFi Protect, providing the unique MAC addresses and Serial Numbers required for seamless integration.
- **Unique Virtual NICs**: Full support for Linux MACVLAN to assign unique hardware identities to each virtual camera.
- **High Performance**: Built on MediaMTX for stable, low-latency HLS and RTSP streaming.
- **Live Transcoding**: Built-in FFmpeg integration to resize or re-encode streams on the fly. *(Note: Transcoding is very resource-intensive and not recommended unless necessary for compatibility).*
- **Premium Web UI**: Modern, responsive dashboard with multiple themes and a real-time "Matrix View" for monitoring all cameras.
- **Resource Management**: Optimized for high-concurrency with automated file descriptor management to prevent "Too many open files" errors.

---

## 🚀 Installation & Setup (Ubuntu 25.04)

### 1. Clone the Repository
Open your terminal and run the following commands to download the code and enter the project folder:

```bash
git clone https://github.com/BigTonyTones/Tonys-Onvf-RTSP-Server.git
cd "Tonys-Onvf-RTSP-Server"
```

### 2. Prepare the Startup Script
The project includes a startup script that automates the installation of Python dependencies and optimizes system limits for high-performance streaming. 

Give the script permission to execute:
```bash
sudo chmod +x start_ubuntu_25.sh
```

### 3. Start the Server
Run the script to initialize the environment and launch the application:
```bash
sudo ./start_ubuntu_25.sh
```

**What this script handles for you:**
*   Installs `python3-full` and `python3-venv` only if they aren't already on your system.
*   Sets up an isolated Python Virtual Environment (`venv`).
*   Installs all required Python libraries.
*   **Performance Tuning:** Automatically increases the system file descriptor limit (`ulimit -n 65535`), which is required to prevent "Too many open files" errors when running many cameras.

### 4. Access the Web UI
Once the script finishes, it will provide a link (usually `http://localhost:5552`). Open this in your browser to begin adding your cameras.

### 5. Enable Auto-Boot (Optional)
To make your ONVIF server start automatically when your Ubuntu machine restarts:
1.  In the Web UI, go to **Settings**.
2.  Toggle **"Auto-start on System Boot (Ubuntu Service)"**.
3.  Enter your `sudo` password in the terminal when prompted to install the systemd service.

---

## 🪟 Windows Setup
1. Ensure Python 3.7+ is installed and in your PATH.
2. Run `start_onvif_server.bat`.
3. The script will automatically download the Windows versions of MediaMTX and FFmpeg if they are not present.

**Note**: The "Virtual NIC" (Unique IP/MAC) feature is not supported on Windows. All virtual cameras will be accessed via the host's IP address on different ONVIF ports.

---

## 🌐 Networking & UniFi Protect
To ensure Ubiquiti Protect treats your virtual cameras as separate devices:
- **On Linux**: Use the "Virtual NIC" feature in the camera settings. This uses `macvlan` to grant each camera its own IP and MAC address on your physical network.
- **Manual Adoption**: You must manually adopt these virtual cameras within your UniFi Protect app using the ONVIF IP, port, and credentials shown in the dashboard.
- **Restart Recommendation**: It is highly recommended to **completely restart the program manually** after adding or modifying any custom IP addresses or MAC addresses to ensure all network interfaces are correctly initialized.
- **I-Frame Intervals**: If you see "segment duration changed" warnings in your logs, disable "Smart Codec" or "H.264+" on your physical cameras and set a fixed I-Frame interval (GOP) that matches your frame rate.

---

## 🛠️ Credits
Built with ❤️ for the surveillance community. Utilizing [MediaMTX](https://github.com/bluenviron/mediamtx) and [FFmpeg](https://ffmpeg.org/).

<a href="https://buymeacoffee.com/tonytones" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>
