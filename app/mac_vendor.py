"""
MAC Vendor (OUI) Lookup and Device Type Detection

Uses the first 3 octets of a MAC address to identify the device manufacturer.
Also provides quick port probing to detect device types.
"""

import socket
import threading

# ============================================================
# OUI Database — first 3 octets → Vendor Name
# Covers cameras, networking, computing, mobile, IoT, etc.
# ============================================================
OUI_DATABASE = {
    # --- IP Cameras & Security ---
    "00:12:17": "Cisco-Linksys",
    "28:57:BE": "Hikvision",
    "C0:56:E3": "Hikvision",
    "44:19:B6": "Hikvision",
    "54:C4:15": "Hikvision",
    "A4:14:37": "Hikvision",
    "C4:2F:90": "Hikvision",
    "BC:AD:28": "Hikvision",
    "18:68:CB": "Hikvision",
    "E0:50:8B": "Hikvision",
    "80:A5:89": "Hikvision",
    "4C:BD:8F": "Hikvision",
    "D4:61:DA": "Hikvision",
    "48:57:02": "Hikvision",
    "8C:E7:48": "Hikvision",
    "AC:CC:8E": "Hikvision",
    "3C:EF:8C": "Dahua",
    "40:F4:EC": "Dahua",
    "A0:BD:CD": "Dahua",
    "E0:2C:C1": "Dahua",
    "D4:43:A8": "Dahua",
    "4C:11:BF": "Dahua",
    "14:A7:8B": "Dahua",
    "00:1F:54": "Dahua",
    "90:02:A9": "Dahua",
    "B4:A3:82": "Dahua",
    "E8:AB:FA": "Reolink",
    "B8:98:AD": "Reolink",
    "EC:71:DB": "Reolink",
    "9C:8E:CD": "Amcrest",
    "AC:B1:87": "Amcrest",
    "00:40:8C": "Axis Communications",
    "B8:27:EB": "Axis Communications",
    "00:02:D1": "Vivotek",
    "00:0F:7C": "ACTi",
    "00:1C:27": "Sunell",
    "00:80:F0": "Panasonic",
    "00:0E:53": "Avigilon",
    "00:18:85": "Avigilon",
    "00:1A:07": "Avigilon",
    "00:50:6B": "Bosch Security",
    "00:07:5F": "Bosch Security",
    "00:04:A3": "Hanwha Techwin",
    "00:09:18": "Hanwha Techwin",
    "00:16:6C": "Hanwha (Samsung)",
    "78:A5:DD": "Hanwha Techwin",
    "00:1E:C0": "Microchip (FLIR)",
    "00:40:7F": "FLIR Systems",
    "00:1C:B3": "Apple (HomeKit Cam)",
    "00:24:B5": "Nortel/Uniview",
    "A0:12:73": "Uniview",
    "00:04:70": "Uniview",
    "00:40:73": "Uniview",
    "C0:39:5A": "Uniview",

    # --- Networking / Routers / Switches ---
    "00:1A:2B": "Cisco",
    "00:1B:D4": "Cisco",
    "00:1E:BD": "Cisco",
    "00:23:04": "Cisco",
    "00:25:B5": "Cisco",
    "00:26:0B": "Cisco",
    "00:50:56": "VMware",
    "00:0C:29": "VMware",
    "00:15:5D": "Microsoft (Hyper-V)",
    "00:1A:A0": "Dell",
    "A4:BA:DB": "Dell",
    "14:18:77": "Dell",
    "F8:DB:88": "Dell",
    "EC:F4:BB": "Dell",
    "B0:83:FE": "Dell",
    "78:45:C4": "Dell",
    "54:B2:03": "TP-Link",
    "50:C7:BF": "TP-Link",
    "14:CF:92": "TP-Link",
    "60:A4:B7": "TP-Link",
    "30:DE:4B": "TP-Link",
    "14:EB:B6": "TP-Link",
    "98:DA:C4": "TP-Link",
    "C0:06:C3": "TP-Link",
    "EC:08:6B": "TP-Link",
    "B0:95:75": "TP-Link",
    "5C:E9:31": "TP-Link",
    "E8:48:B8": "TP-Link",
    "B4:B0:24": "TP-Link",
    "84:D8:1B": "TP-Link",
    "20:0D:B0": "Netgear",
    "A4:2B:8C": "Netgear",
    "6C:B0:CE": "Netgear",
    "C4:3D:C7": "Netgear",
    "E4:F4:C6": "Netgear",
    "9C:3D:CF": "Netgear",
    "B0:7F:B9": "Netgear",
    "C0:FF:D4": "Netgear",
    "28:80:88": "Netgear",
    "84:1B:5E": "Netgear",
    "FC:EC:DA": "Ubiquiti",
    "18:E8:29": "Ubiquiti",
    "F0:9F:C2": "Ubiquiti",
    "24:5A:4C": "Ubiquiti",
    "78:8A:20": "Ubiquiti",
    "68:D7:9A": "Ubiquiti",
    "80:2A:A8": "Ubiquiti",
    "B4:FB:E4": "Ubiquiti",
    "E0:63:DA": "Ubiquiti",
    "AC:8B:A9": "Ubiquiti",
    "74:83:C2": "Ubiquiti",
    "DC:9F:DB": "Ubiquiti",
    "9E:97:26": "Ubiquiti",
    "44:D9:E7": "Ubiquiti",
    "00:15:6D": "Ubiquiti",
    "00:27:22": "Ubiquiti",
    "74:AC:B9": "Ubiquiti",
    "20:A6:CD": "MikroTik",
    "4C:5E:0C": "MikroTik",
    "00:0C:42": "MikroTik",
    "6C:3B:6B": "MikroTik",
    "B8:69:F4": "MikroTik",
    "CC:2D:E0": "MikroTik",
    "E4:8D:8C": "MikroTik",
    "48:A9:8A": "MikroTik",
    "D4:CA:6D": "MikroTik",
    "18:FD:74": "MikroTik",
    "08:55:31": "MikroTik",
    "2C:C8:1B": "MikroTik",
    "74:4D:28": "MikroTik",
    "78:9A:18": "MikroTik",
    "C4:AD:34": "MikroTik",
    "64:D1:54": "MikroTik",
    "B8:27:EB": "Raspberry Pi",
    "DC:A6:32": "Raspberry Pi",
    "E4:5F:01": "Raspberry Pi",
    "D8:3A:DD": "Raspberry Pi",
    "28:CD:C1": "Raspberry Pi",
    "2C:CF:67": "Raspberry Pi",
    "D4:01:C3": "Aruba",
    "00:1A:1E": "Aruba",
    "00:0B:86": "Aruba",
    "24:DE:C6": "Aruba",
    "94:B4:0F": "Aruba",
    "AC:A3:1E": "Aruba",
    "00:1F:33": "Netgear",
    "E0:46:9A": "Netgear",
    "00:23:69": "Cisco-Linksys",
    "20:AA:4B": "Cisco-Linksys",
    "C8:D7:19": "Cisco-Linksys",
    "58:6D:8F": "Cisco-Linksys",
    "00:25:9C": "Cisco-Linksys",
    "A0:F3:C1": "TP-Link",
    "70:4F:57": "TP-Link",
    "CC:32:E5": "TP-Link",
    "28:EE:52": "TP-Link",

    # --- Computers / Servers ---
    "00:25:90": "Supermicro",
    "AC:1F:6B": "Supermicro",
    "00:25:B3": "Hewlett Packard",
    "00:1A:4B": "Hewlett Packard",
    "3C:D9:2B": "Hewlett Packard",
    "00:17:A4": "Hewlett Packard",
    "EC:B1:D7": "Hewlett Packard",
    "10:60:4B": "Hewlett Packard",
    "F0:92:1C": "Hewlett Packard",
    "30:E1:71": "Hewlett Packard",
    "00:21:5A": "Hewlett Packard",
    "48:0F:CF": "Hewlett Packard",
    "54:E1:AD": "LGIT",
    "C8:1F:66": "Lenovo",
    "00:12:FE": "Lenovo",
    "28:D2:44": "Lenovo",
    "E8:2A:EA": "Intel",
    "3C:97:0E": "Intel",
    "00:1B:21": "Intel",
    "A4:C4:94": "Intel",
    "A4:BB:6D": "Intel",
    "8C:EC:4B": "Intel",
    "8C:16:45": "Intel",
    "D4:3D:7E": "Intel",
    "48:21:0B": "Intel",
    "AC:E0:10": "ASUS",
    "00:1A:92": "ASUS",
    "BC:EE:7B": "ASUS",
    "60:45:CB": "ASUS",
    "38:D5:47": "ASUS",
    "04:92:26": "ASUS",
    "A8:5E:45": "ASUS",
    "2C:4D:54": "ASUS",
    "6C:B7:49": "ASUS",
    "A8:5E:45": "ASUS",
    "50:46:5D": "ASRock",
    "70:85:C2": "ASRock",
    "BC:5C:4C": "ASRock",

    # --- Apple ---
    "00:03:93": "Apple",
    "00:1E:52": "Apple",
    "F8:1E:DF": "Apple",
    "D8:30:62": "Apple",
    "AC:BC:32": "Apple",
    "14:99:E2": "Apple",
    "A4:83:E7": "Apple",
    "78:7B:8A": "Apple",
    "70:56:81": "Apple",
    "A8:51:AB": "Apple",
    "54:72:4F": "Apple",
    "3C:15:C2": "Apple",
    "48:A9:1C": "Apple",
    "D4:61:9D": "Apple",
    "AC:87:A3": "Apple",
    "DC:A9:04": "Apple",
    "F0:B4:79": "Apple",
    "18:9E:FC": "Apple",
    "98:01:A7": "Apple",
    "E0:B5:2D": "Apple",
    "68:FE:F7": "Apple",
    "F4:5C:89": "Apple",
    "CC:29:F5": "Apple",
    "6C:4D:73": "Apple",
    "64:A3:CB": "Apple",
    "50:A6:7F": "Apple",
    "8C:85:90": "Apple",
    "10:DD:B1": "Apple",

    # --- Samsung ---
    "00:1A:8A": "Samsung",
    "00:23:99": "Samsung",
    "00:26:37": "Samsung",
    "E4:7C:F9": "Samsung",
    "8C:F5:A3": "Samsung",
    "78:AB:BB": "Samsung",
    "B4:79:A7": "Samsung",
    "AC:5F:3E": "Samsung",
    "5C:3C:27": "Samsung",
    "50:B7:C3": "Samsung",
    "A4:08:01": "Samsung",
    "50:01:BB": "Samsung",
    "C4:50:06": "Samsung",
    "34:23:BA": "Samsung",
    "C0:97:27": "Samsung",
    "C8:BA:94": "Samsung",
    "D0:22:BE": "Samsung",
    "E8:50:8B": "Samsung",

    # --- Amazon ---
    "F0:F0:A4": "Amazon (Echo/Fire)",
    "FC:65:DE": "Amazon (Echo/Fire)",
    "A0:02:DC": "Amazon (Echo/Fire)",
    "84:D6:D0": "Amazon (Echo/Fire)",
    "FE:0B:AC": "Amazon (Echo/Fire)",
    "74:C2:46": "Amazon (Echo/Fire)",
    "44:65:0D": "Amazon (Echo/Fire)",
    "68:54:FD": "Amazon (Echo/Fire)",

    # --- Google ---
    "F4:F5:D8": "Google",
    "54:60:09": "Google",
    "A4:77:33": "Google",
    "30:FD:38": "Google",
    "20:DF:B9": "Google (Nest)",
    "18:B4:30": "Google (Nest)",
    "64:16:66": "Google (Nest)",
    "D8:EB:46": "Google",

    # --- NAS / Storage ---
    "00:11:32": "Synology",
    "00:11:31": "Synology",
    "BC:FB:F4": "Synology",
    "00:08:9B": "QNAP",
    "24:5E:BE": "QNAP",
    "00:06:29": "IBM (Storage)",

    # --- IoT / Smart Home ---
    "B0:F8:93": "Ring (Amazon)",
    "7C:64:56": "Ring (Amazon)",
    "00:17:88": "Philips Hue",
    "EC:B5:FA": "Philips Hue",
    "00:0E:58": "Sonos",
    "94:9F:3E": "Sonos",
    "48:A6:B8": "Sonos",
    "34:7E:5C": "Sonos",
    "B8:E9:37": "Sonos",
    "5C:AA:FD": "Sonos",
    "78:28:CA": "Sonos",
    "00:04:20": "Ecobee",
    "64:90:C1": "Espressif (ESP32)",
    "24:0A:C4": "Espressif (ESP32)",
    "30:AE:A4": "Espressif (ESP32)",
    "A4:CF:12": "Espressif (ESP32)",
    "B4:E6:2D": "Espressif (ESP8266)",
    "2C:F4:32": "Espressif (ESP)",
    "CC:50:E3": "Espressif (ESP)",
    "84:F3:EB": "Espressif (ESP)",
    "AC:67:B2": "Espressif (ESP)",
    "7C:DF:A1": "Espressif (ESP)",
    "84:CC:A8": "Espressif (ESP)",
    "C4:4F:33": "Espressif (ESP)",
    "3C:61:05": "Espressif (ESP)",
    "C4:DD:57": "Espressif (ESP)",
    "D8:BF:C0": "Espressif (ESP)",
    "60:01:94": "Espressif (ESP)",
    "10:52:1C": "Espressif (ESP)",
    "98:CD:AC": "Espressif (ESP)",
    "E0:98:06": "Shenzhen Bilian (Tuya/Smart)",
    "DC:4F:22": "Espressif (ESP)",
    "48:3F:DA": "Espressif (ESP)",
    "34:AB:95": "Espressif (ESP)",
    "08:B6:1F": "Espressif (ESP)",

    # --- Printers ---
    "00:00:48": "Seiko Epson",
    "00:1B:A9": "Brother",
    "00:80:77": "Brother",
    "00:1E:8F": "Canon",
    "00:1F:F3": "HP (Printer)",
    "C8:B5:B7": "HP (Printer)",
    "30:CD:A7": "HP (Printer)",

    # --- Mobile / Wireless ---
    "F0:79:59": "Huawei",
    "00:E0:FC": "Huawei",
    "E0:19:1D": "Huawei",
    "04:B0:E7": "Huawei",
    "CC:A2:23": "Huawei",
    "AC:E2:15": "Huawei",
    "58:2A:F7": "Huawei",
    "70:8A:09": "Huawei",
    "F4:63:1F": "Xiaomi",
    "28:6C:07": "Xiaomi",
    "64:CE:91": "Xiaomi",
    "7C:1D:D9": "Xiaomi",
    "FC:B4:67": "Xiaomi",
    "34:CE:00": "Xiaomi",
    "78:11:DC": "Xiaomi",
    "00:9E:C8": "Xiaomi",
    "94:E9:79": "Xiaomi",
    "50:64:2B": "OnePlus",
    "C0:EE:FB": "OnePlus",

    # --- Streaming / Entertainment ---
    "DC:F7:56": "Roku",
    "B0:A7:37": "Roku",
    "AC:3A:7A": "Roku",
    "D8:31:CF": "Roku",
    "B8:3E:59": "Roku",
    "84:EA:ED": "Roku",
    "00:07:61": "Apple TV",
    "40:33:1A": "Apple TV",
    "78:7E:61": "Apple TV",

    # --- Gaming ---
    "00:D9:D1": "Sony (PlayStation)",
    "00:04:1F": "Sony",
    "BC:60:A7": "Sony (PlayStation)",
    "7C:BB:8A": "Nintendo",
    "E8:4E:CE": "Nintendo",
    "34:AF:2C": "Nintendo",
    "58:2F:40": "Microsoft (Xbox)",
    "28:18:78": "Microsoft (Xbox)",
    "7C:ED:8D": "Microsoft (Xbox)",

    # --- Additional Networking ---
    "CC:40:D0": "Arris",
    "00:1D:D1": "Arris",
    "E8:65:D4": "Arris",
    "F8:E4:3B": "Arris",
    "00:26:F2": "Netgear",
    "C4:04:15": "Netgear",
    "00:14:6C": "Netgear",
    "00:1F:33": "Netgear",
}


def lookup_vendor(mac_address: str) -> str:
    """
    Look up the vendor/manufacturer for a given MAC address.
    Returns the vendor name or empty string if not found.
    """
    if not mac_address:
        return ''
    
    # Normalize MAC to XX:XX:XX format (uppercase, colon-separated)
    mac_clean = mac_address.upper().replace('-', ':')
    prefix = mac_clean[:8]  # First 3 octets like "AA:BB:CC"
    
    return OUI_DATABASE.get(prefix, '')


# ============================================================
# Quick Port Prober — detect device type by open ports
# ============================================================
DEVICE_PORT_SIGNATURES = {
    # (port, label)  →  ordered by priority
    554:  'RTSP Camera',
    8554: 'RTSP Camera',
    8899: 'RTSP Camera',
    80:   'Web Device',
    443:  'Web Device (HTTPS)',
    8080: 'Web Device',
    9100: 'Printer',
    515:  'Printer',
    631:  'Printer (CUPS)',
    548:  'Apple File Server',
    445:  'SMB/File Server',
    139:  'NetBIOS/File Server',
    5000: 'NAS/Synology',
    5001: 'NAS/Synology',
    8443: 'NAS/QNAP',
    3389: 'Remote Desktop',
    22:   'SSH Server',
    5353: 'mDNS Device',
    8200: 'GoToMeeting/Media',
    1883: 'MQTT/IoT',
    8883: 'MQTT/IoT (TLS)',
    8123: 'Home Assistant',
    32400: 'Plex Media Server',
    8096: 'Jellyfin/Emby',
    9090: 'Prometheus/Web',
    3000: 'Web App',
    8000: 'Web App',
    5900: 'VNC',
}

# Ports to scan (ordered by interest level for camera-focused app)
SCAN_PORTS = [554, 80, 443, 8080, 8554, 22, 445, 5000, 9100, 3389, 5900, 32400, 8096, 8123, 1883]


def probe_ports(ip: str, ports: list = None, timeout: float = 0.5) -> dict:
    """
    Quickly probe a list of TCP ports on a host.
    Returns dict with 'open_ports' list and 'device_type' string.
    """
    if ports is None:
        ports = SCAN_PORTS
    
    open_ports = []
    port_lock = threading.Lock()
    
    def check_port(port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            result = s.connect_ex((ip, port))
            s.close()
            if result == 0:
                with port_lock:
                    open_ports.append(port)
        except Exception:
            pass
    
    threads = []
    for port in ports:
        t = threading.Thread(target=check_port, args=(port,), daemon=True)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join(timeout=timeout + 0.5)
    
    # Determine device type from open ports (priority order)
    device_type = ''
    for port in [554, 8554, 8899, 9100, 515, 631, 5000, 5001, 8443, 
                 32400, 8096, 8123, 1883, 3389, 5900, 22, 445, 139, 548, 80, 443, 8080]:
        if port in open_ports:
            device_type = DEVICE_PORT_SIGNATURES.get(port, '')
            if device_type:
                break
    
    # Format port labels
    port_labels = []
    for p in sorted(open_ports):
        label = DEVICE_PORT_SIGNATURES.get(p, f'Port {p}')
        port_labels.append({'port': p, 'service': label})
    
    return {
        'open_ports': port_labels,
        'device_type': device_type,
    }
