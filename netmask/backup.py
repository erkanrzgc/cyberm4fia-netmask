"""Backup and restore original MAC/IP addresses for each interface."""

import os
import json
from datetime import datetime
from netmask.config import CONFIG_DIR, BACKUP_FILE


class BackupManager:
    """Manages JSON-based backup of original network settings."""

    def __init__(self):
        self._ensure_dir()

    def _ensure_dir(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)

    def _read(self):
        if not os.path.exists(BACKUP_FILE):
            return {}
        try:
            with open(BACKUP_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _write(self, data):
        self._ensure_dir()
        with open(BACKUP_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def save(self, interface, mac, ip, netmask):
        """Save original settings for an interface if not already backed up."""
        data = self._read()
        if interface not in data:
            data[interface] = {
                "mac": mac,
                "ip": ip.split("/")[0] if "/" in ip else ip,
                "netmask": netmask,
                "ip_with_cidr": ip,
                "backed_up_at": datetime.now().isoformat(),
            }
        self._write(data)

    def load(self, interface):
        """Get the original settings for an interface."""
        return self._read().get(interface)

    def get_all_backed_up(self):
        """Return dict of all backed-up interfaces."""
        return self._read()

    def remove(self, interface):
        """Remove backup entry for an interface."""
        data = self._read()
        if interface in data:
            del data[interface]
            self._write(data)
