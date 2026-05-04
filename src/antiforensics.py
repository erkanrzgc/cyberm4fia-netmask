"""Anti-forensics suite: DNS/ARP flush, hostname randomization, cache cleaning.

Each rotation can optionally wipe forensic traces that would otherwise
persist across MAC/IP changes and defeat the purpose of identity rotation.
"""

import os
import random
import string
from utils.platform import get_os, run_command


def flush_dns():
    """Flush all DNS caches on the system.

    Linux: systemd-resolved, nscd, dnsmasq, resolv.conf hints
    Windows: ipconfig /flushdns
    """
    if get_os() == "linux":
        run_command(["resolvectl", "flush-caches"], check=False)
        run_command(["systemctl", "restart", "systemd-resolved"], check=False)
        run_command(["systemctl", "restart", "nscd"], check=False)
        run_command(["systemctl", "restart", "dnsmasq"], check=False)
    elif get_os() == "windows":
        run_command(["ipconfig", "/flushdns"], check=False)
        run_command(["ipconfig", "/registerdns"], check=False)
        run_command(
            ["netsh", "winsock", "reset"],
            check=False,
            capture=False,
        )


def flush_arp():
    """Flush ARP (neighbor) cache.

    Linux: ip neigh flush all
    Windows: netsh interface ip delete arpcache
    """
    if get_os() == "linux":
        run_command(["ip", "neigh", "flush", "all"], check=False)
    elif get_os() == "windows":
        run_command(
            ["netsh", "interface", "ip", "delete", "arpcache"],
            check=False,
        )


def randomize_hostname():
    """Temporarily randomize system hostname.

    Generates a realistic-looking hostname like 'DESKTOP-A7X3K9M'.
    Changes via hostnamectl (Linux) or wmic (Windows).
    """
    prefix = random.choice(["DESKTOP", "LAPTOP", "WORKSTATION", "PC", "NODE"])
    suffix = "-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=7))
    new_name = prefix + suffix

    if get_os() == "linux":
        run_command(["hostnamectl", "set-hostname", new_name], check=False)
        with open("/etc/hostname", "w") as f:
            f.write(new_name + "\n")
    elif get_os() == "windows":
        run_command(
            ["wmic", "computersystem", "where", "name='%COMPUTERNAME%'",
             "call", "rename", "name='{new_name}'"],
            check=False,
        )

    return new_name


def clean_browser_cache():
    """Attempt to clean browser caches for common browsers.

    Warning: this forcefully kills browser processes and deletes cache dirs.
    Only runs on explicit opt-in via --anti-forensics --aggressive.
    """
    home = os.path.expanduser("~")

    if get_os() == "linux":
        cache_dirs = [
            os.path.join(home, ".cache", "google-chrome"),
            os.path.join(home, ".cache", "chromium"),
            os.path.join(home, ".cache", "mozilla", "firefox"),
            os.path.join(home, ".cache", "BraveSoftware"),
            os.path.join(home, ".config", "google-chrome"),
            os.path.join(home, ".config", "chromium"),
            os.path.join(home, ".mozilla", "firefox"),
        ]
        for browser in ["chrome", "chromium", "firefox", "brave"]:
            run_command(["pkill", "-f", browser], check=False)
    elif get_os() == "windows":
        home = os.environ.get("LOCALAPPDATA", home)
        cache_dirs = [
            os.path.join(home, "Google", "Chrome", "User Data", "Default", "Cache"),
            os.path.join(home, "Mozilla", "Firefox", "Profiles"),
            os.path.join(home, "BraveSoftware"),
        ]

    import shutil
    for d in cache_dirs:
        if os.path.exists(d):
            try:
                if os.path.isdir(d):
                    shutil.rmtree(d, ignore_errors=True)
                else:
                    os.remove(d)
            except (IOError, PermissionError):
                pass


def run_anti_forensics(aggressive=False):
    """Execute full anti-forensics suite.

    Args:
        aggressive: If True, also wipes browser caches.
    """
    results = {}

    results["dns"] = True
    flush_dns()

    results["arp"] = True
    flush_arp()

    hostname = randomize_hostname()
    results["hostname"] = hostname

    if aggressive:
        try:
            clean_browser_cache()
            results["browser_cache"] = True
        except Exception:
            results["browser_cache"] = False

    return results
