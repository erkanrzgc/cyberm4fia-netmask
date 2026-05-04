"""Windows MAC/IP changer using netsh and registry."""

import time
import re
from src.changers.base import AbstractChanger
from src.utils.platform import run_command


class WindowsChanger(AbstractChanger):

    def disable_interface(self, interface):
        run_command(
            ["netsh", "interface", "set", "interface", f'"{interface}"', "admin=disable"]
        )

    def enable_interface(self, interface):
        run_command(
            ["netsh", "interface", "set", "interface", f'"{interface}"', "admin=enable"]
        )

    def _find_adapter_guid(self, interface):
        """Find the registry GUID for a given network adapter name."""
        result = run_command(
            ["reg", "query",
             r"HKLM\SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002BE10318}",
             "/s", "/f", f'"{interface}"', "/d", "/e"],
            capture=True,
            check=False,
        )
        if result and result.stdout:
            for line in result.stdout.split("\n"):
                match = re.search(
                    r"\{4D36E972-E325-11CE-BFC1-08002BE10318\}\\(\d{4})\\", line
                )
                if match:
                    return match.group(1)
        return None

    def change_mac(self, interface, mac):
        guid = self._find_adapter_guid(interface)
        if not guid:
            print(f"[-] Could not find registry key for {interface}")
            return False

        self.disable_interface(interface)
        time.sleep(0.5)

        mac_no_sep = mac.replace(":", "").replace("-", "")

        key_path = (
            r"SYSTEM\CurrentControlSet\Control\Class"
            r"\{4D36E972-E325-11CE-BFC1-08002BE10318}"
            rf"\{guid}"
        )
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(key, "NetworkAddress", 0, winreg.REG_SZ, mac_no_sep)
            winreg.CloseKey(key)
        except Exception as e:
            print(f"[-] Registry write failed: {e}")
            self.enable_interface(interface)
            return False

        time.sleep(0.5)
        self.enable_interface(interface)
        time.sleep(2)
        return True

    def change_ip(self, interface, ip, netmask, gateway=None):
        cmd = [
            "netsh", "interface", "ip", "set", "address",
            f'"{interface}"', "static", ip, netmask,
        ]
        if gateway:
            cmd.append(gateway)
        else:
            cmd.append("none")

        result = run_command(cmd)
        time.sleep(1)
        return result and result.returncode == 0

    def dhcp_renew(self, interface):
        print(f"[+] Releasing DHCP lease on {interface}...")
        run_command(["ipconfig", "/release", f'"{interface}"'], check=False)
        time.sleep(2)

        print(f"[+] Requesting new DHCP lease on {interface}...")
        result = run_command(["ipconfig", "/renew", f'"{interface}"'], timeout=60)
        time.sleep(3)
        return result is not None and (isinstance(result, int) or result.returncode == 0)
