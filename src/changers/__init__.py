"""Auto-import the correct changer backend for the current OS."""

from src.utils.platform import get_os

_os = get_os()

if _os == "linux":
    from src.changers.linux import LinuxChanger as Changer
elif _os == "windows":
    from src.changers.windows import WindowsChanger as Changer
else:
    raise OSError(f"Unsupported platform: {_os}")
