"""Platform detection and system utilities."""

import os
import sys
import subprocess
import ctypes


def get_os():
    """Detect operating system. Returns 'linux' or 'windows'."""
    if sys.platform.startswith("linux"):
        return "linux"
    elif sys.platform.startswith("win"):
        return "windows"
    raise OSError(f"Unsupported platform: {sys.platform}")


def require_admin():
    """Check admin/root privileges. Exit if insufficient."""
    if get_os() == "linux":
        if os.geteuid() != 0:
            print("[-] This tool requires root privileges. Run with sudo.")
            sys.exit(1)
    elif get_os() == "windows":
        try:
            if not ctypes.windll.shell32.IsUserAnAdmin():
                print("[-] This tool requires Administrator privileges.")
                print("[-] Run from an elevated command prompt.")
                sys.exit(1)
        except AttributeError:
            pass


def run_command(cmd, check=True, capture=True, timeout=30, shell=False):
    """Execute a shell command and return the result.

    Args:
        cmd: List of command arguments or string if shell=True
        check: Raise on non-zero exit
        capture: Capture stdout/stderr
        timeout: Command timeout in seconds
        shell: Use shell execution

    Returns:
        subprocess.CompletedProcess or None on timeout/error
    """
    kwargs = {}
    if capture:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE

    try:
        return subprocess.run(
            cmd,
            check=check,
            timeout=timeout,
            shell=shell,
            text=True,
            **kwargs,
        )
    except subprocess.TimeoutExpired:
        print(f"[-] Command timed out: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
        return None
    except subprocess.CalledProcessError as e:
        print(f"[-] Command failed: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
        return e
    except FileNotFoundError:
        print(f"[-] Command not found: {cmd[0] if isinstance(cmd, list) else cmd}")
        return None
