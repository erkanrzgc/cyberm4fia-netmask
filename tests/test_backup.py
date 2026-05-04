"""Tests for backup.py — JSON backup and restore."""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.backup import BackupManager
from src.config import BACKUP_FILE


class TestBackupManager(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._backup_file = BACKUP_FILE
        cls._original_data = None
        if os.path.exists(cls._backup_file):
            with open(cls._backup_file) as f:
                cls._original_data = f.read()

    @classmethod
    def tearDownClass(cls):
        if cls._original_data is not None:
            with open(cls._backup_file, "w") as f:
                f.write(cls._original_data)
        elif os.path.exists(cls._backup_file):
            os.remove(cls._backup_file)

    def setUp(self):
        if os.path.exists(self._backup_file):
            os.remove(self._backup_file)
        self.bm = BackupManager()

    def test_save_and_load(self):
        self.bm.save("eth0", "00:11:22:33:44:55", "192.168.1.10/24", "255.255.255.0")
        data = self.bm.load("eth0")
        self.assertIsNotNone(data)
        self.assertEqual(data["mac"], "00:11:22:33:44:55")
        self.assertEqual(data["ip"], "192.168.1.10")
        self.assertEqual(data["netmask"], "255.255.255.0")
        self.assertEqual(data["ip_with_cidr"], "192.168.1.10/24")
        self.assertIn("backed_up_at", data)

    def test_load_nonexistent(self):
        self.assertIsNone(self.bm.load("nonexistent"))

    def test_save_does_not_overwrite(self):
        self.bm.save("eth0", "00:11:22:33:44:55", "192.168.1.10/24", "255.255.255.0")
        self.bm.save("eth0", "aa:bb:cc:dd:ee:ff", "10.0.0.1/24", "255.255.255.0")
        data = self.bm.load("eth0")
        self.assertEqual(data["mac"], "00:11:22:33:44:55")

    def test_multiple_interfaces(self):
        self.bm.save("eth0", "00:11:22:33:44:55", "192.168.1.10/24", "255.255.255.0")
        self.bm.save("wlan0", "aa:bb:cc:dd:ee:ff", "10.0.0.5/24", "255.255.255.0")
        all_data = self.bm.get_all_backed_up()
        self.assertEqual(len(all_data), 2)
        self.assertIn("eth0", all_data)
        self.assertIn("wlan0", all_data)

    def test_remove(self):
        self.bm.save("eth0", "00:11:22:33:44:55", "192.168.1.10/24", "255.255.255.0")
        self.assertEqual(len(self.bm.get_all_backed_up()), 1)
        self.bm.remove("eth0")
        self.assertEqual(len(self.bm.get_all_backed_up()), 0)
        self.assertIsNone(self.bm.load("eth0"))

    def test_remove_nonexistent(self):
        self.bm.remove("nonexistent")

    def test_ip_without_cidr(self):
        self.bm.save("eth0", "00:11:22:33:44:55", "192.168.1.10", "255.255.255.0")
        data = self.bm.load("eth0")
        self.assertEqual(data["ip"], "192.168.1.10")
        self.assertEqual(data["ip_with_cidr"], "192.168.1.10")

    def test_empty_backup(self):
        self.assertEqual(self.bm.get_all_backed_up(), {})


if __name__ == "__main__":
    unittest.main()
