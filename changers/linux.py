"""Linux MAC/IP changer using ip link/addr and dhclient."""

import time
from changers.base import AbstractChanger
from utils.platform import run_command
from validator import mask_to_cidr


class LinuxChanger(AbstractChanger):

    def disable_interface(self, interface):
        run_command(["ip", "link", "set", "dev", interface, "down"])

    def enable_interface(self, interface):
        run_command(["ip", "link", "set", "dev", interface, "up"])

    def change_mac(self, interface, mac):
        self.disable_interface(interface)
        time.sleep(0.3)
        result = run_command(
            ["ip", "link", "set", "dev", interface, "address", mac]
        )
        time.sleep(0.3)
        self.enable_interface(interface)
        time.sleep(1)
        return result and result.returncode == 0

    def change_ip(self, interface, ip, netmask, gateway=None):
        cidr = mask_to_cidr(netmask)
        self.disable_interface(interface)
        time.sleep(0.3)

        run_command(["ip", "addr", "flush", "dev", interface])
        time.sleep(0.3)

        result = run_command(
            ["ip", "addr", "add", f"{ip}/{cidr}", "dev", interface]
        )

        if gateway:
            time.sleep(0.3)
            run_command(["ip", "route", "add", "default", "via", gateway])

        time.sleep(0.3)
        self.enable_interface(interface)
        time.sleep(1)
        return result and result.returncode == 0

    def dhcp_renew(self, interface):
        print(f"[+] Releasing DHCP lease on {interface}...")
        run_command(["dhclient", "-r", interface], check=False)
        time.sleep(1)

        print(f"[+] Requesting new DHCP lease on {interface}...")
        result = run_command(["dhclient", interface], timeout=60)
        time.sleep(2)
        return result is not None and (isinstance(result, int) or result.returncode == 0)
