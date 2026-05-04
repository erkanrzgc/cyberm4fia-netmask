"""Daemon module for continuous MAC/IP rotation in the background."""

import os
import sys
import time
import signal
import atexit
from datetime import datetime, timedelta

from src.config import CONFIG_DIR, PID_FILE, LOG_FILE, DURATION_FILE, MIN_INTERVAL
from src.interfaces import Interface
from src.changers import Changer
from src.backup import BackupManager
from src.validator import random_mac, random_private_ip, format_duration
from src.utils.platform import get_os, run_command


class Daemon:
    """Background daemon that rotates MAC and IP at regular intervals.

    On Linux: uses double-fork for proper daemonization.
    On Windows: runs as a detached background process.

    On shutdown (SIGTERM/SIGINT) or duration expiry, restores original MAC/IP.
    """

    def __init__(self, interface, interval=30, duration=0,
                 kill_switch=False, anti_forensics=False):
        self.interface = interface
        self.interval = max(interval, MIN_INTERVAL)
        self.duration = duration
        self.kill_switch = kill_switch
        self.anti_forensics = anti_forensics
        self.iface = Interface()
        self.changer = Changer()
        self.backup = BackupManager()
        self.started_at = None
        self.rotations = 0
        self._running = False
        self._shutting_down = False
        self._ks_active = False

    def start(self):
        """Start the daemon process."""
        require_admin()
        self._ensure_dirs()

        original_mac = self.iface.get_mac(self.interface)
        original_ip = self.iface.get_ip(self.interface)
        original_netmask = self.iface.get_netmask(self.interface)

        self.backup.save(self.interface, original_mac, original_ip, original_netmask)
        self.started_at = datetime.now()

        # Write duration to a marker file so child process can read it
        if self.duration > 0:
            self._write_duration(self.duration)

        if get_os() == "linux":
            self._daemonize_linux()
        else:
            self._daemonize_windows()

    def _ensure_dirs(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)

    def _daemonize_linux(self):
        """Double-fork to detach from the terminal (Unix daemon)."""
        pid = os.fork()
        if pid > 0:
            print(f"[+] Daemon started (PID: {pid})")
            print(f"[+] Interface: {self.interface}")
            print(f"[+] Interval: {self.interval}s")
            if self.duration > 0:
                print(f"[+] Duration: {format_duration(self.duration)}")
            print(f"[+] Log: {LOG_FILE}")
            print(f"[+] Run 'netmask.py --stop' to terminate")
            self._write_pid(pid)
            sys.exit(0)

        os.setsid()
        os.umask(0)

        pid = os.fork()
        if pid > 0:
            sys.exit(0)

        self._run_loop()

    def _daemonize_windows(self):
        """Detach on Windows by re-spawning as a separate process."""
        import subprocess as sp

        python = sys.executable
        script = os.path.abspath(sys.argv[0])
        args = [
            python, script,
            "--daemon", "-i", self.interface, "-t", str(self.interval),
            "--_internal-daemon",
        ]
        if self.duration > 0:
            args += ["-d", str(self.duration)]
        if self.kill_switch:
            args.append("-ks")
        if self.anti_forensics:
            args.append("-af")

        proc = sp.Popen(
            args,
            stdout=sp.DEVNULL,
            stderr=sp.DEVNULL,
            stdin=sp.DEVNULL,
            creationflags=sp.CREATE_NO_WINDOW if hasattr(sp, "CREATE_NO_WINDOW") else 0,
        )

        print(f"[+] Daemon started (PID: {proc.pid})")
        print(f"[+] Interface: {self.interface}")
        print(f"[+] Interval: {self.interval}s")
        if self.duration > 0:
            print(f"[+] Duration: {format_duration(self.duration)}")
        print(f"[+] Log: {LOG_FILE}")
        print(f"[+] Run 'netmask.py --stop' to terminate")
        self._write_pid(proc.pid)
        sys.exit(0)

    def _run_loop(self):
        """Main daemon rotation loop."""
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)
        atexit.register(self._cleanup)

        self._write_pid(os.getpid())
        self._running = True
        self.started_at = datetime.now()

        # Read duration from file (set by parent process)
        self.duration = self._read_duration()

        self._log("Daemon started")
        if self.duration > 0:
            self._log(f"Duration set: {format_duration(self.duration)}")

        try:
            while not self._shutting_down:
                self._rotate()
                self.rotations += 1
                self._log(
                    f"Rotation #{self.rotations} — "
                    f"MAC: {self.iface.get_mac(self.interface)}, "
                    f"IP: {self.iface.get_ip(self.interface)}"
                )

                if self.duration > 0:
                    elapsed = (datetime.now() - self.started_at).total_seconds()
                    remaining = self.duration - elapsed
                    if remaining <= 0:
                        self._log("Duration expired, shutting down...")
                        self._shutting_down = True
                        break

                time.sleep(self.interval)
        except Exception as e:
            self._log(f"Error: {e}")

        self._cleanup()

    def _rotate(self):
        """Perform one MAC + IP rotation cycle with optional kill switch + anti-forensics."""
        mac = random_mac()
        ip = random_private_ip()

        if self._shutting_down:
            return

        backup_data = self.backup.load(self.interface)
        netmask = backup_data.get("netmask", "255.255.255.0") if backup_data else "255.255.255.0"

        try:
            if self.kill_switch:
                self._ks_block()

            self.changer.disable_interface(self.interface)
            time.sleep(0.3)

            run_command(
                ["ip", "link", "set", "dev", self.interface, "address", mac],
                check=False,
            )
            time.sleep(0.3)

            from src.validator import mask_to_cidr
            cidr = mask_to_cidr(netmask)
            run_command(["ip", "addr", "flush", "dev", self.interface], check=False)
            time.sleep(0.3)
            run_command(
                ["ip", "addr", "add", f"{ip}/{cidr}", "dev", self.interface],
                check=False,
            )
            time.sleep(0.3)

            self.changer.enable_interface(self.interface)
            time.sleep(1)

            if self.kill_switch:
                self._ks_unblock()

            if self.anti_forensics:
                self._run_anti_forensics()

        except Exception as e:
            self._log(f"Rotation error: {e}")
            if self.kill_switch:
                self._log("KILL SWITCH: rotation failed, network remains blocked")
                self._shutting_down = True

    def _ks_block(self):
        """Kill switch: block all traffic on this interface via iptables."""
        self._ks_active = True
        run_command(
            ["iptables", "-I", "OUTPUT", "-o", self.interface, "-j", "DROP"],
            check=False,
        )
        run_command(
            ["iptables", "-I", "INPUT", "-i", self.interface, "-j", "DROP"],
            check=False,
        )

    def _ks_unblock(self):
        """Kill switch: remove the DROP rules for this interface."""
        run_command(
            ["iptables", "-D", "OUTPUT", "-o", self.interface, "-j", "DROP"],
            check=False,
        )
        run_command(
            ["iptables", "-D", "INPUT", "-i", self.interface, "-j", "DROP"],
            check=False,
        )
        self._ks_active = False

    def _run_anti_forensics(self):
        """Execute anti-forensics suite after successful rotation."""
        from src.antiforensics import flush_dns, flush_arp, randomize_hostname
        try:
            flush_dns()
            flush_arp()
            hostname = randomize_hostname()
            self._log(f"Anti-forensics: DNS flushed, ARP flushed, hostname={hostname}")
        except Exception as e:
            self._log(f"Anti-forensics error: {e}")

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals — restore original settings."""
        self._log(f"Received signal {signum}, shutting down...")
        self._shutting_down = True

    def _cleanup(self):
        """Restore original MAC/IP, remove kill switch rules, and remove PID file."""
        # Remove kill switch rules first
        if self._ks_active:
            self._ks_unblock()
            self._log("Kill switch: rules removed")

        try:
            original = self.backup.load(self.interface)
            if original:
                self._log("Restoring original settings...")

                self.changer.disable_interface(self.interface)
                time.sleep(0.3)

                run_command(
                    ["ip", "link", "set", "dev", self.interface, "address", original["mac"]],
                    check=False,
                )
                time.sleep(0.3)

                if original.get("ip") and original.get("ip") != "N/A":
                    from src.validator import mask_to_cidr
                    ip = original["ip"].split("/")[0] if "/" in original["ip"] else original["ip"]
                    netmask = original.get("netmask", "255.255.255.0")
                    cidr = mask_to_cidr(netmask)
                    run_command(["ip", "addr", "flush", "dev", self.interface], check=False)
                    time.sleep(0.3)
                    run_command(
                        ["ip", "addr", "add", f"{ip}/{cidr}", "dev", self.interface],
                        check=False,
                    )
                    time.sleep(0.3)

                self.changer.enable_interface(self.interface)
                time.sleep(1)
                self._log("Original settings restored")
        except Exception as e:
            self._log(f"Cleanup error: {e}")
        finally:
            self._remove_pid()
            self._running = False

    def _write_pid(self, pid):
        """Write PID to file."""
        self._ensure_dirs()
        with open(PID_FILE, "w") as f:
            f.write(str(pid))

    def _remove_pid(self):
        """Remove PID file."""
        try:
            os.remove(PID_FILE)
        except (IOError, OSError):
            pass

    def _write_duration(self, duration_seconds):
        """Write duration to a marker file for the child process."""
        self._ensure_dirs()
        with open(DURATION_FILE, "w") as f:
            f.write(str(int(duration_seconds)))

    def _read_duration(self):
        """Read duration from marker file, then remove it."""
        try:
            if os.path.exists(DURATION_FILE):
                with open(DURATION_FILE) as f:
                    duration = int(f.read().strip())
                os.remove(DURATION_FILE)
                return duration
        except (ValueError, IOError):
            pass
        return 0

    def _log(self, message):
        """Write timestamped log entry."""
        self._ensure_dirs()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] {message}\n")


def daemon_status():
    """Print daemon status (called from --status)."""
    if not os.path.exists(PID_FILE):
        print("[-] No daemon is running (no PID file found).")
        return

    try:
        with open(PID_FILE) as f:
            pid = int(f.read().strip())
    except (ValueError, IOError):
        print("[-] Invalid PID file.")
        return

    is_linux = get_os() == "linux"
    alive = False
    if is_linux:
        try:
            os.kill(pid, 0)
            alive = True
        except OSError:
            alive = False
    else:
        import subprocess as sp
        result = sp.run(
            ["tasklist", "/FI", f"PID eq {pid}"],
            capture_output=True, text=True, timeout=5,
        )
        alive = str(pid) in result.stdout

    if not alive:
        print(f"[-] Daemon (PID: {pid}) is not running (stale PID file).")
        os.remove(PID_FILE)
        return

    iface = Interface()
    changer = Changer()
    backup = BackupManager()

    rotations = 0
    uptime_str = "N/A"
    started_at = "N/A"

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            lines = f.readlines()
            start_match = [l for l in lines if "Daemon started" in l]
            rot_count = sum(1 for l in lines if "Rotation" in l)
            rotations = rot_count
            if start_match:
                try:
                    ts = start_match[0][1:20]
                    started = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                    delta = datetime.now() - started
                    h, rem = divmod(int(delta.total_seconds()), 3600)
                    m, s = divmod(rem, 60)
                    uptime_str = f"{h}h {m}m {s}s"
                    started_at = ts
                except (ValueError, IndexError):
                    pass

    original = {}
    iface_name = ""
    for name in backup.get_all_backed_up():
        iface_name = name
        original = backup.load(name)
        break

    if iface_name:
        current_mac = iface.get_mac(iface_name)
        current_ip = iface.get_ip(iface_name)
    else:
        iface_name = "unknown"
        current_mac = "N/A"
        current_ip = "N/A"

    widths = [31, 31]
    total = 68

    print()
    print(BOX_TL + BOX_H * (total - 2) + BOX_TR)
    pad = (total - 24) // 2
    print(BOX_V + " " * pad + "NETMASK DAEMON STATUS" + " " * (total - pad - 26) + BOX_V)
    print(BOX_LJ + BOX_H * (total - 2) + BOX_RJ)

    fields = [
        ("Status", "\033[32mRUNNING\033[0m" if alive else "\033[31mSTOPPED\033[0m"),
        ("PID", str(pid)),
        ("Interface", iface_name),
        ("Interval", "N/A"),
        ("Duration", "N/A"),
        ("Remaining", "N/A"),
        ("Uptime", uptime_str),
        ("Started", started_at),
        ("Rotations", str(rotations)),
    ]

    for label, value in fields:
        print(f"{BOX_V} {label:<14}: {value:<47} {BOX_V}")

    print(BOX_LJ + BOX_H * (total - 2) + BOX_RJ)

    print(f"{BOX_V} {'Current MAC':<14}: {current_mac:<17} {'Original MAC':<11}: {original.get('mac', 'N/A')} {BOX_V}")
    print(f"{BOX_V} {'Current IP':<14}: {current_ip:<17} {'Original IP':<11}: {original.get('ip', 'N/A')} {BOX_V}")

    print(BOX_LJ + BOX_H * (total - 2) + BOX_RJ)
    print(f"{BOX_V} {'Log':<14}: {LOG_FILE:<47} {BOX_V}")
    print(BOX_BL + BOX_H * (total - 2) + BOX_BR)
    print()


def daemon_stop():
    """Stop a running daemon by PID."""
    if not os.path.exists(PID_FILE):
        print("[-] No daemon is running (no PID file found).")
        return

    try:
        with open(PID_FILE) as f:
            pid = int(f.read().strip())
    except (ValueError, IOError):
        print("[-] Invalid PID file. Removing...")
        os.remove(PID_FILE)
        return

    print(f"[+] Sending shutdown signal to daemon (PID: {pid})...")

    try:
        if get_os() == "linux":
            os.kill(pid, signal.SIGTERM)
        else:
            import subprocess as sp
            sp.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                   capture_output=True, timeout=10)
    except OSError as e:
        print(f"[-] Failed to stop daemon: {e}")
        return

    for _ in range(10):
        if not os.path.exists(PID_FILE):
            print("[+] Daemon stopped and original settings restored.")
            return
        time.sleep(0.5)

    print("[!] Daemon may not have shut down cleanly.")
    print("[!] Check logs and restore settings manually if needed.")


def require_admin():
    """Local admin check for daemon context."""
    from src.utils.platform import require_admin as _ra
    _ra()
