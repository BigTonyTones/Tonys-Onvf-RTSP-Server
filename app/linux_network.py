import subprocess
import platform
import os
import re
import time
import tempfile

from .logging_config import get_logger

logger = get_logger(__name__)


class LinuxNetworkManager:
    """Manages Linux network interfaces for virtual cameras"""

    @staticmethod
    def is_linux():
        return platform.system().lower() == "linux"

    @staticmethod
    def get_physical_interfaces():
        """Get a list of physical network interfaces"""
        if not LinuxNetworkManager.is_linux():
            return []

        try:
            # Look in /sys/class/net
            interfaces = os.listdir('/sys/class/net')
            # Filter out loopback and virtual ones (usually)
            physical = []
            for iface in interfaces:
                if iface == 'lo':
                    continue
                # Check if it's a physical device (has a 'device' link)
                if os.path.exists(f'/sys/class/net/{iface}/device'):
                    physical.append(iface)
            return physical
        except:
            return []

    def create_macvlan(self, parent_if, name, mac):
        """Create a MACVLAN interface"""
        if not self.is_linux():
            return False

        logger.info("Creating Virtual NIC %s on %s with MAC %s", name, parent_if, mac)

        # 0. Check if parent interface exists
        if not os.path.exists(f'/sys/class/net/{parent_if}'):
            logger.error("Parent interface '%s' does not exist.", parent_if)
            # List available interfaces for the user
            available = self.get_physical_interfaces()
            if available:
                logger.info("Available interfaces: %s", ', '.join(available))
            return False

        try:
            # 1. Enable promiscuous mode on parent (often required for MACVLAN to work)
            logger.debug("Enabling promiscuous mode on %s...", parent_if)
            subprocess.run(['sudo', 'ip', 'link', 'set', parent_if, 'promisc', 'on'], check=False)

            # 2. Check if interface already exists and remove it
            if os.path.exists(f'/sys/class/net/{name}'):
                subprocess.run(['sudo', 'ip', 'link', 'delete', name], check=False)

            # 3. Create the link
            subprocess.run(['sudo', 'ip', 'link', 'add', name, 'link', parent_if, 'type', 'macvlan', 'mode', 'bridge'], check=True)
            # 4. Set MAC address
            subprocess.run(['sudo', 'ip', 'link', 'set', name, 'address', mac], check=True)

            # 5. Bring it up
            subprocess.run(['sudo', 'ip', 'link', 'set', name, 'up'], check=True)

            # 6. Apply ARP isolation to prevent host from "hijacking" the virtual IP (ARP Flux)
            # This is crucial for stability when multiple IPs are on one physical interface
            subprocess.run(['sudo', 'sysctl', '-w', f'net.ipv4.conf.{name}.arp_ignore=1'], check=False)
            subprocess.run(['sudo', 'sysctl', '-w', f'net.ipv4.conf.{name}.arp_announce=2'], check=False)

            return True
        except subprocess.CalledProcessError as e:
            logger.error("Error creating MACVLAN: %s", e)
            return False

    def setup_ip(self, name, mode, ip=None, mask=None, gw=None):
        """Setup IP address using DHCP or Static"""
        if not self.is_linux():
            return None

        try:
            if mode == 'dhcp':
                logger.info("Requesting DHCP for %s (timeout 15s)...", name)

                # Try dhclient with a custom config to prevent it from touching host DNS/Routes
                conf_fd = None
                conf_path = None
                try:
                    # Create a minimal dhclient.conf using secure temp file (prevents race condition)
                    conf_fd, conf_path = tempfile.mkstemp(prefix=f'dhclient_{name}_', suffix='.conf')
                    with os.fdopen(conf_fd, 'w') as f:
                        conf_fd = None  # fd is now owned by the file object
                        f.write(f'interface "{name}" {{\n')
                        f.write('    # Request only IP and subnet, skip DNS and Routers to avoid breaking host connection\n')
                        f.write('    request subnet-mask, broadcast-address, time-offset, host-name, interface-mtu;\n')
                        f.write('}\n')

                    # Clean up any stale PIDs or leases
                    subprocess.run(['sudo', 'dhclient', '-r', name], check=False, timeout=5)
                    # Run with custom config
                    subprocess.run(['sudo', 'dhclient', '-1', '-nw', '-cf', conf_path, name], check=False)

                    # Wait up to 5 seconds for IP (most fast networks respond in 1-2s)
                    for _ in range(5):
                        result = subprocess.run(['ip', '-4', 'addr', 'show', name], capture_output=True, text=True)
                        match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', result.stdout)
                        if match:
                            assigned_ip = match.group(1)
                            logger.info("IP assigned: %s", assigned_ip)
                            # Clean up temp conf
                            if conf_path:
                                try:
                                    os.remove(conf_path)
                                except OSError:
                                    pass
                            return assigned_ip
                        time.sleep(1)

                    # Clean up temp conf if failed
                    if conf_path:
                        try:
                            os.remove(conf_path)
                        except OSError:
                            pass
                except Exception as e:
                    logger.warning("'dhclient' attempt failed: %s", e)
                    # Clean up temp file on exception
                    if conf_fd is not None:
                        try:
                            os.close(conf_fd)
                        except OSError:
                            pass
                    if conf_path:
                        try:
                            os.remove(conf_path)
                        except OSError:
                            pass

                # Try udhcpc if dhclient isolated attempt fails
                try:
                    logger.warning("Isolated DHCP failed, trying 'udhcpc' fallback...")
                    subprocess.run(['sudo', 'udhcpc', '-i', name, '-n', '-q', '-T', '1', '-t', '5', '-s', '/bin/true'], check=True, timeout=7)
                except:
                    pass

                # Ultimate Fallback: Try plain dhclient (exactly like user's manual command)
                # Keep this as a last resort as it might touch host routes
                result = subprocess.run(['ip', '-4', 'addr', 'show', name], capture_output=True, text=True)
                if not re.search(r'inet \d+', result.stdout):
                    try:
                        logger.warning("Standard DHCP attempts failed. Trying plain 'dhclient' (User Success Mode)...")
                        subprocess.run(['sudo', 'dhclient', '-nw', name], check=False)
                        # Wait a bit
                        for _ in range(3):
                            result = subprocess.run(['ip', '-4', 'addr', 'show', name], capture_output=True, text=True)
                            if re.search(r'inet \d+', result.stdout): break
                            time.sleep(1)
                    except:
                        pass

                # Check final result
                result = subprocess.run(['ip', '-4', 'addr', 'show', name], capture_output=True, text=True)
                match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', result.stdout)
                if match:
                    assigned_ip = match.group(1)
                    logger.info("IP assigned: %s", assigned_ip)
                    return assigned_ip

                logger.error("DHCP failed to acquire address in time.")
                logger.info("Tip: Try 'Static IP' mode instead if your router is slow to respond.")
                return None

            elif mode == 'static' and ip:
                logger.info("Setting static IP %s for %s...", ip, name)
                full_ip = f"{ip}/{mask}" if mask else ip
                # Add the IP address
                subprocess.run(['sudo', 'ip', 'addr', 'add', full_ip, 'dev', name], check=True)

                # IMPORTANT: We do NOT add a 'default gateway' here.
                # Adding a default route to a virtual interface will override the host's
                # main internet connection and cause the server to lose connectivity.
                # Virtual cameras only need to be reachable on the local network.

                return ip

        except subprocess.CalledProcessError as e:
            logger.error("Error setting up IP: %s", e)

        return None

    def remove_interface(self, name):
        """Clean up virtual interface"""
        if not self.is_linux():
            return

        logger.info("Removing Virtual NIC %s...", name)
        try:
            # Release DHCP
            try:
                subprocess.run(['sudo', 'dhclient', '-r', name], check=False)
            except:
                pass
            # Delete link
            subprocess.run(['sudo', 'ip', 'link', 'delete', name], check=False)
        except Exception as e:
            logger.warning("Error cleaning up NIC %s: %s", name, e)

    def cleanup_all_vnics(self):
        """Global cleanup of all vnic_ interfaces at startup"""
        if not self.is_linux():
            return

        logger.info("Cleaning up old virtual network interfaces...")
        try:
            # Get list of all interfaces
            result = subprocess.run(['ip', 'link', 'show'], capture_output=True, text=True)
            # Find all interfaces starting with vnic_
            vnics = re.findall(r'vnic_[^:@\s]+', result.stdout)

            # Remove duplicates and clean up
            cleaned = []
            for vnic in set(vnics):
                if vnic not in cleaned:
                    self.remove_interface(vnic)
                    cleaned.append(vnic)

            if cleaned:
                logger.info("Cleaned up %d stale virtual interfaces.", len(cleaned))
            else:
                logger.info("No stale virtual interfaces found.")
        except Exception as e:
            logger.warning("Error during global NIC cleanup: %s", e)
