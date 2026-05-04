"""Linux interface discovery via /sys/class/net and ip command."""

import os
import re
from netmask.interfaces.base import AbstractInterface
from netmask.utils.platform import run_command


class LinuxInterface(AbstractInterface):

    def list_interfaces(self):
        """List all network interfaces from /sys/class/net/."""
        net_dir = "/sys/class/net"
        if not os.path.exists(net_dir):
            return []
        return sorted(os.listdir(net_dir))

    def get_mac(self, interface):
        """Read MAC from /sys/class/net/{iface}/address."""
        addr_file = f"/sys/class/net/{interface}/address"
        try:
            with open(addr_file) as f:
                return f.read().strip()
        except (IOError, PermissionError):
            return "N/A"

    def get_ip(self, interface):
        """Get IPv4 address via ip addr show."""
        result = run_command(["ip", "-4", "addr", "show", interface])
        if not result or not result.stdout:
            return "N/A"

        match = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+/\d+)", result.stdout)
        if match:
            return match.group(1)
        return "N/A"

    def get_netmask(self, interface):
        """Get subnet mask via ip addr show."""
        result = run_command(["ip", "-4", "addr", "show", interface])
        if not result or not result.stdout:
            return "N/A"

        ip_match = re.search(r"inet\s+\d+\.\d+\.\d+\.\d+/(\d+)", result.stdout)
        if ip_match:
            cidr = int(ip_match.group(1))
            mask = (0xFFFFFFFF << (32 - cidr)) & 0xFFFFFFFF
            return ".".join(str((mask >> (24 - 8 * i)) & 0xFF) for i in range(4))
        return "N/A"

    def is_up(self, interface):
        """Check if interface is administratively up."""
        flags_file = f"/sys/class/net/{interface}/flags"
        try:
            with open(flags_file) as f:
                flags = int(f.read().strip(), 16)
            return bool(flags & 0x1)
        except (IOError, PermissionError, ValueError):
            return False
