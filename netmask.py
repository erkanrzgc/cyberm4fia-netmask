#!/usr/bin/env python3
"""CYBERM4FIA NETMASK — Cross-Platform MAC/IP Changer & Daemon.

Usage:
  Interactive:  sudo python netmask.py
  CLI one-shot: sudo python netmask.py -i eth0 -rm -ri
  Daemon:       sudo python netmask.py --daemon -i eth0 -t 30
  Status:       sudo python netmask.py --status
  Stop daemon:  sudo python netmask.py --stop
"""

import sys
import os
import argparse

from netmask.utils.platform import require_admin
from netmask.banner import print_banner
from netmask.interfaces import Interface
from netmask.changers import Changer
from netmask.backup import BackupManager
from netmask.validator import (
    is_valid_mac, is_valid_ip, random_mac, random_private_ip,
    is_unicast, mask_to_cidr,
)
from netmask.config import DEFAULT_INTERVAL, DEFAULT_NETMASK, MIN_INTERVAL


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="netmask",
        description="CYBERM4FIA NETMASK — Cross-Platform MAC/IP Changer & Daemon",
        epilog="Run without arguments for interactive mode.",
    )

    parser.add_argument(
        "-i", "--interface",
        help="Network interface name (eth0, wlan0, Ethernet0, etc.)",
    )

    mac_group = parser.add_mutually_exclusive_group()
    mac_group.add_argument(
        "-m", "--mac",
        help="New MAC address (xx:xx:xx:xx:xx:xx)",
    )
    mac_group.add_argument(
        "-rm", "--random-mac", action="store_true",
        help="Generate a random MAC address",
    )

    ip_group = parser.add_mutually_exclusive_group()
    ip_group.add_argument(
        "--ip",
        help="New IP address (e.g., 192.168.1.100)",
    )
    ip_group.add_argument(
        "-ri", "--random-ip", action="store_true",
        help="Generate a random private IP address",
    )

    parser.add_argument(
        "-n", "--netmask",
        default=DEFAULT_NETMASK,
        help=f"Subnet mask (default: {DEFAULT_NETMASK})",
    )

    parser.add_argument(
        "--dhcp", action="store_true",
        help="Release and renew DHCP lease",
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Restore original MAC/IP from backup",
    )

    daemon_group = parser.add_argument_group("Daemon options")
    daemon_group.add_argument(
        "--daemon", action="store_true",
        help="Start as background daemon (continuous rotation)",
    )
    daemon_group.add_argument(
        "-t", "--interval", type=int, default=DEFAULT_INTERVAL,
        help=f"Rotation interval in seconds (min {MIN_INTERVAL}, default: {DEFAULT_INTERVAL})",
    )
    daemon_group.add_argument(
        "--status", action="store_true",
        help="Show daemon status",
    )
    daemon_group.add_argument(
        "--stop", action="store_true",
        help="Stop running daemon and restore original settings",
    )
    daemon_group.add_argument(
        "--_internal-daemon", action="store_true",
        help=argparse.SUPPRESS,
    )

    return parser.parse_args()


def run_cli(args):
    """Execute CLI mode based on parsed arguments."""
    require_admin()

    # Daemon management commands (can run without -i)
    if args.status:
        print_banner()
        from netmask.daemon import daemon_status
        daemon_status()
        return

    if args.stop:
        print_banner()
        from netmask.daemon import daemon_stop
        daemon_stop()
        return

    # Internal daemon spawn (hidden, runs the actual daemon loop)
    if args._internal_daemon:
        from netmask.daemon import Daemon
        daemon = Daemon(args.interface, args.interval)
        daemon._run_loop()
        return

    # Interface is required for all other operations
    if not args.interface:
        print("[-] Interface is required. Use -i <interface>")
        print("    Run without arguments for interactive mode.")
        sys.exit(1)

    # Daemon start
    if args.daemon:
        from netmask.daemon import Daemon
        daemon = Daemon(args.interface, args.interval)
        daemon.start()
        return

    iface = Interface()
    changer = Changer()
    backup = BackupManager()

    # Validate interface exists
    if args.interface not in iface.list_interfaces():
        print(f"[-] Interface '{args.interface}' not found.")
        print(f"    Available: {', '.join(iface.list_interfaces())}")
        sys.exit(1)

    current_mac = iface.get_mac(args.interface)
    current_ip = iface.get_ip(args.interface)
    current_netmask = iface.get_netmask(args.interface)

    # Backup original settings
    backup.save(args.interface, current_mac, current_ip, current_netmask)

    # Reset / restore
    if args.reset:
        print_banner()
        original = backup.load(args.interface)
        if not original:
            print(f"[-] No backup found for {args.interface}")
            sys.exit(1)
        print(f"[+] Restoring {args.interface} to original settings...")
        changer.change_mac(args.interface, original["mac"])
        if original.get("ip") and original.get("ip") != "N/A":
            changer.change_ip(args.interface, original["ip"], original.get("netmask", "255.255.255.0"))
        backup.remove(args.interface)
        print(f"[✓] Restore complete")
        return

    # Determine new MAC
    new_mac = None
    if args.random_mac:
        new_mac = random_mac()
    elif args.mac:
        if not is_valid_mac(args.mac):
            print(f"[-] Invalid MAC format: {args.mac}")
            sys.exit(1)
        if not is_unicast(args.mac):
            print(f"[!] Warning: {args.mac} is not a unicast MAC")
        new_mac = args.mac

    # Determine new IP
    new_ip = None
    if args.random_ip:
        new_ip = random_private_ip()
    elif args.ip:
        if not is_valid_ip(args.ip):
            print(f"[-] Invalid IP format: {args.ip}")
            sys.exit(1)
        new_ip = args.ip

    # DHCP
    do_dhcp = args.dhcp

    print_banner()
    print(f"  Interface: {args.interface}")
    print(f"  Current MAC: {current_mac}")
    print(f"  Current IP:  {current_ip}")
    print()

    if new_mac:
        print(f"  [+] Setting MAC to {new_mac}...")
        if changer.change_mac(args.interface, new_mac):
            actual = iface.get_mac(args.interface)
            print(f"  [✓] MAC: {actual}")
        else:
            print(f"  [✗] MAC change failed")

    if do_dhcp:
        print(f"  [+] Renewing DHCP...")
        if changer.dhcp_renew(args.interface):
            actual = iface.get_ip(args.interface)
            print(f"  [✓] IP: {actual}")
        else:
            print(f"  [✗] DHCP renew failed")

    if new_ip and not do_dhcp:
        netmask = args.netmask
        print(f"  [+] Setting IP to {new_ip}/{netmask}...")
        if changer.change_ip(args.interface, new_ip, netmask):
            actual = iface.get_ip(args.interface)
            print(f"  [✓] IP: {actual}")
        else:
            print(f"  [✗] IP change failed")

    print()


def main():
    """Entry point. Interactive mode if no args, CLI mode otherwise."""
    args = parse_args()

    # Check if we should enter interactive mode
    has_cli_action = any([
        args.mac, args.random_mac, args.ip, args.random_ip,
        args.dhcp, args.reset, args.daemon, args.status,
        args.stop, args._internal_daemon,
    ])

    if not has_cli_action:
        # Interactive mode
        require_admin()
        from netmask.menu import InteractiveMenu
        menu = InteractiveMenu()
        menu.run()
    else:
        run_cli(args)


if __name__ == "__main__":
    main()
