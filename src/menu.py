"""Interactive box-drawn menu system for NETMASK."""

import os
import sys
from src.config import BOX_H, BOX_V, BOX_TL, BOX_TR, BOX_BL, BOX_BR
from src.config import BOX_TJ, BOX_BJ, BOX_LJ, BOX_RJ, BOX_CJ
from src.banner import print_banner
from interfaces import Interface
from changers import Changer
from src.backup import BackupManager
from src.validator import (
    is_valid_mac, is_valid_ip, is_valid_netmask,
    random_mac, random_private_ip, is_unicast,
)
from utils.platform import get_os


class InteractiveMenu:
    """Interactive terminal menu for MAC/IP management."""

    def __init__(self):
        self.iface = Interface()
        self.changer = Changer()
        self.backup = BackupManager()
        self.os_name = get_os().title()

    def _clear(self):
        os.system("clear" if get_os() != "windows" else "cls")

    def _print_box_line(self, parts, widths, sep_top=False, sep_bot=False):
        """Print a single row in a box-drawn table.

        parts: list of column texts
        widths: list of column widths
        sep_top/bot: use junction chars for separator lines
        """
        left = BOX_TJ if sep_top else (BOX_LJ if sep_bot else BOX_V)
        right = BOX_RJ
        line = left
        for i, (text, w) in enumerate(zip(parts, widths)):
            line += f" {text:<{w}} "
            if i < len(parts) - 1:
                line += BOX_V
        line += right
        print(line)

    def _print_separator(self, widths, top=False, mid=False, bot=False):
        """Print a horizontal separator line."""
        if top:
            left, center, right = BOX_TL, BOX_TJ, BOX_TR
        elif bot:
            left, center, right = BOX_BL, BOX_BJ, BOX_BR
        elif mid:
            left, center, right = BOX_LJ, BOX_CJ, BOX_RJ
        else:
            left, center, right = BOX_LJ, BOX_CJ, BOX_RJ

        line = left
        for i, w in enumerate(widths):
            line += BOX_H * (w + 2)
            if i < len(widths) - 1:
                line += center
            else:
                line += right
        print(line)

    def _show_interfaces(self):
        """Display interface selection table."""
        interfaces = self.iface.get_all()

        headers = ["#", "Interface", "MAC", "IP", "UP"]
        widths = [3, 16, 20, 20, 4]
        total_width = sum(widths) + len(widths) * 3 + 1

        self._print_separator(widths, top=True)
        title = "INTERFACE SELECTION"
        pad = (total_width - len(title) - 4) // 2
        print(BOX_V + " " * pad + title + " " * (total_width - len(title) - pad - 2) + BOX_V)
        self._print_separator(widths, mid=True)
        self._print_box_line(headers, widths)
        self._print_separator(widths, mid=True)

        for i, iface in enumerate(interfaces):
            idx = str(i + 1)
            name = iface["name"][:14]
            mac = iface["mac"][:18]
            ip = iface["ip"][:18]
            up = "\033[32m✓\033[0m" if iface["up"] else "\033[31m✗\033[0m"

            row = [idx, name, mac, ip, up]
            self._print_box_line(row, widths)

        self._print_separator(widths, bot=True)
        return interfaces

    def _show_action_menu(self, interface_name):
        """Display the action selection menu."""
        print()
        title = f"ACTION MENU — {interface_name}"
        print(f"  {title}")
        print(f"  {'─' * len(title)}")
        print()
        print("  [\033[36m1\033[0m] Change MAC address")
        print("  [\033[36m2\033[0m] Change IP address")
        print("  [\033[36m3\033[0m] Change MAC + IP")
        print("  [\033[36m4\033[0m] DHCP renew")
        print("  [\033[36m5\033[0m] Quick random (MAC + IP)")
        print("  [\033[36m6\033[0m] Restore original")
        print("  [\033[36m7\033[0m] Start daemon")
        print("  [\033[36m0\033[0m] Exit")
        print()

    def _select_interface(self):
        """Let user select an interface."""
        interfaces = self._show_interfaces()

        if not interfaces:
            print("\n[-] No network interfaces found.")
            sys.exit(1)

        while True:
            try:
                choice = input(f"  Select [1-{len(interfaces)}]: ").strip()
                if not choice:
                    continue
                idx = int(choice) - 1
                if 0 <= idx < len(interfaces):
                    return interfaces[idx]
                print(f"  [-] Enter 1-{len(interfaces)}")
            except ValueError:
                print("  [-] Enter a valid number")
            except KeyboardInterrupt:
                print("\n  [!] Exiting...")
                sys.exit(0)

    def _value_input(self, prompt_type):
        """Get MAC or IP value from user (manual or random)."""
        print()
        print(f"  --- {prompt_type} Input ---")
        print("  [1] Enter manually")
        print("  [2] Generate random")

        while True:
            try:
                choice = input("  Select [1-2]: ").strip()
                if choice == "1":
                    value = input(f"  Enter {prompt_type}: ").strip()
                    if prompt_type == "MAC":
                        if not is_valid_mac(value):
                            print("  [-] Invalid MAC format (xx:xx:xx:xx:xx:xx)")
                            continue
                        if not is_unicast(value):
                            print("  [!] Warning: not a unicast MAC, may cause issues")
                    elif prompt_type == "IP":
                        if not is_valid_ip(value):
                            print("  [-] Invalid IP format")
                            continue
                    return value
                elif choice == "2":
                    if prompt_type == "MAC":
                        value = random_mac()
                    else:
                        value = random_private_ip()
                    print(f"  [+] Generated {prompt_type}: \033[36m{value}\033[0m")
                    return value
            except KeyboardInterrupt:
                print("\n  [!] Exiting...")
                sys.exit(0)

    def _confirm_and_apply(self, old_info, new_mac=None, new_ip=None, new_netmask=None):
        """Show summary and apply changes."""
        interface = old_info["name"]

        print()
        print(f"  ═══ Summary for {interface} ═══")

        if new_mac:
            print(f"  MAC: {old_info['mac']} → \033[33m{new_mac}\033[0m")
        if new_ip:
            old_ip = old_info["ip"].split("/")[0]
            print(f"  IP:  {old_ip} → \033[33m{new_ip}\033[0m")

        print()
        confirm = input("  Apply changes? [\033[32my\033[0m/N]: ").strip().lower()
        if confirm != "y":
            print("  [!] Cancelled.")
            return

        if not old_info.get("ip") or old_info["ip"] == "N/A":
            old_ip = "N/A"
            old_netmask = "N/A"
        else:
            old_ip = old_info["ip"]
            old_netmask = old_info.get("netmask", "255.255.255.0")

        self.backup.save(interface, old_info["mac"], old_ip, old_netmask)

        print()

        if new_mac:
            print(f"  [+] Changing MAC to {new_mac}...")
            success = self.changer.change_mac(interface, new_mac)
            if success:
                actual = self.iface.get_mac(interface)
                if actual.replace(":", "").lower() == new_mac.replace(":", "").lower():
                    print(f"  [\033[32m✓\033[0m] MAC changed successfully: {actual}")
                else:
                    print(f"  [\033[33m✓\033[0m] MAC set to: {actual}")
            else:
                print(f"  [\033[31m✗\033[0m] MAC change failed")

        if new_ip:
            mask = new_netmask or old_netmask or "255.255.255.0"
            print(f"  [+] Changing IP to {new_ip}/{mask}...")
            success = self.changer.change_ip(interface, new_ip, mask)
            if success:
                actual = self.iface.get_ip(interface)
                print(f"  [\033[32m✓\033[0m] IP changed successfully: {actual}")
            else:
                print(f"  [\033[31m✗\033[0m] IP change failed")

    def _dhcp_renew(self, interface_info):
        """Perform DHCP renew."""
        interface = interface_info["name"]
        print(f"\n  [+] Renewing DHCP on {interface}...")
        self.backup.save(
            interface,
            interface_info["mac"],
            interface_info.get("ip", "N/A"),
            interface_info.get("netmask", "N/A"),
        )
        success = self.changer.dhcp_renew(interface)
        if success:
            new_ip = self.iface.get_ip(interface)
            print(f"  [\033[32m✓\033[0m] DHCP renewed: {new_ip}")
        else:
            print(f"  [\033[31m✗\033[0m] DHCP renew failed")

    def _restore(self, interface_info):
        """Restore original MAC/IP from backup."""
        interface = interface_info["name"]
        original = self.backup.load(interface)

        if not original:
            print(f"\n  [-] No backup found for {interface}")
            print(f"  [!] Nothing to restore.")
            input("  Press Enter to continue...")
            return

        print(f"\n  --- Restoring {interface} ---")
        print(f"  MAC: {interface_info['mac']} → {original['mac']}")
        if original.get("ip_with_cidr"):
            print(f"  IP:  {interface_info['ip']} → {original['ip_with_cidr']}")

        print()
        confirm = input("  Restore? [\033[32my\033[0m/N]: ").strip().lower()
        if confirm != "y":
            return

        print()
        if original["mac"] != interface_info["mac"]:
            print(f"  [+] Restoring MAC to {original['mac']}...")
            self.changer.change_mac(interface, original["mac"])

        if original.get("ip") and original.get("netmask"):
            old_ip_no_cidr = interface_info["ip"].split("/")[0]
            if original["ip"] != old_ip_no_cidr:
                print(f"  [+] Restoring IP to {original['ip']}...")
                self.changer.change_ip(interface, original["ip"], original["netmask"])

        print("  [\033[32m✓\033[0m] Restore complete.")
        self.backup.remove(interface)

    def run(self):
        """Main interactive menu loop."""
        self._clear()
        print_banner()
        print(f"  \033[90mOS: {self.os_name}\033[0m\n")

        interface_info = self._select_interface()
        name = interface_info["name"]

        while True:
            self._clear()
            print_banner()

            print(f"  \033[36mSelected: {name}\033[0m")
            print(f"  MAC: {interface_info['mac']}  |  IP: {interface_info['ip']}")
            self._show_action_menu(interface_info["name"])

            try:
                choice = input("  Select [0-7]: ").strip()
            except KeyboardInterrupt:
                print("\n  [!] Exiting...")
                sys.exit(0)

            if choice == "1":
                mac = self._value_input("MAC")
                self._confirm_and_apply(interface_info, new_mac=mac)
                interface_info = {"name": name, **self._refresh_info(name)}
            elif choice == "2":
                ip = self._value_input("IP")
                netmask = input("  Netmask [255.255.255.0]: ").strip() or "255.255.255.0"
                self._confirm_and_apply(interface_info, new_ip=ip, new_netmask=netmask)
                interface_info = {"name": name, **self._refresh_info(name)}
            elif choice == "3":
                mac = self._value_input("MAC")
                ip = self._value_input("IP")
                netmask = input("  Netmask [255.255.255.0]: ").strip() or "255.255.255.0"
                self._confirm_and_apply(interface_info, new_mac=mac, new_ip=ip, new_netmask=netmask)
                interface_info = {"name": name, **self._refresh_info(name)}
            elif choice == "4":
                self._dhcp_renew(interface_info)
                interface_info = {"name": name, **self._refresh_info(name)}
            elif choice == "5":
                mac = random_mac()
                ip = random_private_ip()
                print(f"\n  [+] Random MAC: \033[33m{mac}\033[0m")
                print(f"  [+] Random IP:  \033[33m{ip}\033[0m")
                self._confirm_and_apply(interface_info, new_mac=mac, new_ip=ip)
                interface_info = {"name": name, **self._refresh_info(name)}
            elif choice == "6":
                self._restore(interface_info)
                interface_info = {"name": name, **self._refresh_info(name)}
            elif choice == "7":
                self._start_daemon(name)
            elif choice == "0":
                print("  [+] Exiting...")
                sys.exit(0)
            else:
                print("  [-] Invalid choice")

            input("\n  Press Enter to continue...")

    def _refresh_info(self, name):
        """Refresh interface info after changes."""
        return {
            "mac": self.iface.get_mac(name),
            "ip": self.iface.get_ip(name),
            "netmask": self.iface.get_netmask(name),
            "up": self.iface.is_up(name),
        }

    def _start_daemon(self, interface):
        """Prompt and start daemon mode."""
        from src.validator import parse_duration, format_duration

        print()
        print(f"  --- Start Daemon on {interface} ---")
        try:
            interval = int(input("  Interval in seconds [30]: ").strip() or "30")
        except ValueError:
            interval = 30
        interval = max(interval, 10)

        print(f"  Duration (e.g. 30s, 5m, 2h) or leave blank for indefinite: ", end="")
        dur_input = input().strip()
        duration = 0
        dur_str = "indefinite"
        if dur_input:
            try:
                duration = parse_duration(dur_input)
                dur_str = format_duration(duration)
            except ValueError:
                print(f"  [-] Invalid duration, using indefinite")
                dur_input = ""

        ks = input("  Kill switch? Block network during rotation [y/N]: ").strip().lower() == "y"
        af = input("  Anti-forensics? Flush DNS/ARP + randomize hostname [y/N]: ").strip().lower() == "y"

        print(f"\n  [+] Daemon will rotate MAC+IP every {interval}s")
        print(f"  [+] Duration: {dur_str}")
        if ks:
            print(f"  [+] Kill switch: \033[31mENABLED\033[0m")
        if af:
            print(f"  [+] Anti-forensics: \033[36mENABLED\033[0m")
        print(f"  [+] Safe shutdown restores original settings")
        confirm = input("  Start daemon? [\033[32my\033[0m/N]: ").strip().lower()
        if confirm != "y":
            return

        from src.daemon import Daemon
        daemon = Daemon(interface, interval, duration,
                        kill_switch=ks, anti_forensics=af)
        daemon.start()
