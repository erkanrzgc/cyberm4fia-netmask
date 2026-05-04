"""Platform-aware configuration constants and paths."""

import os
from utils.platform import get_os

APP_NAME = "cyberm4fia"
APP_DIR = ".config"

if get_os() == "linux":
    CONFIG_DIR = os.path.join(os.path.expanduser("~"), APP_DIR, APP_NAME)
elif get_os() == "windows":
    CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), APP_NAME)
else:
    CONFIG_DIR = os.path.join(os.path.expanduser("~"), APP_DIR, APP_NAME)

BACKUP_FILE = os.path.join(CONFIG_DIR, "backup.json")
PID_FILE = os.path.join(CONFIG_DIR, "netmask.pid")
LOG_FILE = os.path.join(CONFIG_DIR, "netmask.log")
DURATION_FILE = os.path.join(CONFIG_DIR, "netmask.duration")

DEFAULT_INTERVAL = 30
MIN_INTERVAL = 10
DEFAULT_NETMASK = "255.255.255.0"
DEFAULT_PRIVATE_NETWORK = "192.168.0.0/16"

MAC_PATTERN = r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
IP_PATTERN = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"

BOX_H = "─"
BOX_V = "│"
BOX_TL = "┌"
BOX_TR = "┐"
BOX_BL = "└"
BOX_BR = "┘"
BOX_TJ = "┬"
BOX_BJ = "┴"
BOX_LJ = "├"
BOX_RJ = "┤"
BOX_CJ = "┼"
