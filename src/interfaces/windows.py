"""Windows interface discovery via netsh and WMI."""

import re
from src.interfaces.base import AbstractInterface
from src.utils.platform import run_command


class WindowsInterface(AbstractInterface):

    def list_interfaces(self):
        """List network interfaces via netsh."""
        result = run_command(
            ["netsh", "interface", "show", "interface"], capture=True
        )
        if not result or not result.stdout:
            return []

        interfaces = []
        for line in result.stdout.split("\n"):
            match = re.match(
                r"\s*(Enabled|Disabled|Connected|Disconnected)\s+(Dedicated|Internal|Loopback)?\s*(.+?)\s*$",
                line,
            )
            if match:
                name = match.group(3).strip()
                interfaces.append(name)
        return interfaces

    def get_mac(self, interface):
        """Get MAC address using getmac."""
        result = run_command(
            ["getmac", "/v", "/fo", "csv"], capture=True
        )
        if not result or not result.stdout:
            return "N/A"

        for line in result.stdout.split("\n"):
            if interface.lower() in line.lower():
                parts = line.split(",")
                if len(parts) >= 3:
                    mac = parts[2].strip('"').strip()
                    if mac:
                        return mac.replace("-", ":").lower()
        return "N/A"

    def get_ip(self, interface):
        """Get IP address via netsh."""
        result = run_command(
            ["netsh", "interface", "ip", "show", "addresses", f'"{interface}"'],
            capture=True,
        )
        if not result or not result.stdout:
            return "N/A"

        match = re.search(r"IP Address:\s*(\d+\.\d+\.\d+\.\d+)", result.stdout)
        if match:
            ip = match.group(1)
            mask_match = re.search(r"Subnet Prefix:\s*\d+\.\d+\.\d+\.\d+/(\d+)", result.stdout)
            if mask_match:
                return f"{ip}/{mask_match.group(1)}"
            return ip
        return "N/A"

    def get_netmask(self, interface):
        """Get subnet mask via netsh."""
        result = run_command(
            ["netsh", "interface", "ip", "show", "addresses", f'"{interface}"'],
            capture=True,
        )
        if not result or not result.stdout:
            return "N/A"

        match = re.search(r"Subnet Prefix:\s*(\d+\.\d+\.\d+\.\d+)", result.stdout)
        if match:
            return match.group(1)
        return "N/A"

    def is_up(self, interface):
        """Check if interface is up."""
        result = run_command(
            ["netsh", "interface", "show", "interface"], capture=True
        )
        if not result or not result.stdout:
            return False

        for line in result.stdout.split("\n"):
            if interface.lower() in line.lower():
                if line.strip().lower().startswith("enabled") or line.strip().lower().startswith("connected"):
                    return True
        return False
