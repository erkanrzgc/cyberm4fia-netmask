"""Auto-import the correct changer backend for the current OS."""

from netmask.utils.platform import get_os

_os = get_os()

if _os == "linux":
    from netmask.changers.linux import LinuxChanger as Changer
elif _os == "windows":
    from netmask.changers.windows import WindowsChanger as Changer
else:
    raise OSError(f"Unsupported platform: {_os}")
