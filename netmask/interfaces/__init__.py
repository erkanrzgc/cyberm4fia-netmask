"""Auto-import the correct interface backend for the current OS."""

from netmask.utils.platform import get_os

_os = get_os()

if _os == "linux":
    from netmask.interfaces.linux import LinuxInterface as Interface
elif _os == "windows":
    from netmask.interfaces.windows import WindowsInterface as Interface
else:
    raise OSError(f"Unsupported platform: {_os}")
