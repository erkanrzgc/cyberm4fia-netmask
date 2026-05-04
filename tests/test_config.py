"""Tests for config.py — platform-aware paths and constants."""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import (
    APP_NAME,
    CONFIG_DIR,
    BACKUP_FILE,
    PID_FILE,
    LOG_FILE,
    DURATION_FILE,
    DEFAULT_INTERVAL,
    MIN_INTERVAL,
    DEFAULT_NETMASK,
    DEFAULT_PRIVATE_NETWORK,
    MAC_PATTERN,
    BOX_H,
    BOX_V,
)


class TestConfigPaths(unittest.TestCase):

    def test_app_name(self):
        self.assertEqual(APP_NAME, "cyberm4fia")

    def test_config_dir_exists(self):
        self.assertIsInstance(CONFIG_DIR, str)
        self.assertIn(APP_NAME, CONFIG_DIR)

    def test_backup_file_in_config_dir(self):
        self.assertTrue(BACKUP_FILE.startswith(CONFIG_DIR))
        self.assertTrue(BACKUP_FILE.endswith("backup.json"))

    def test_pid_file_in_config_dir(self):
        self.assertTrue(PID_FILE.startswith(CONFIG_DIR))
        self.assertTrue(PID_FILE.endswith(".pid"))

    def test_log_file_in_config_dir(self):
        self.assertTrue(LOG_FILE.startswith(CONFIG_DIR))
        self.assertTrue(LOG_FILE.endswith(".log"))

    def test_duration_file_in_config_dir(self):
        self.assertTrue(DURATION_FILE.startswith(CONFIG_DIR))
        self.assertTrue(DURATION_FILE.endswith(".duration"))


class TestConfigDefaults(unittest.TestCase):

    def test_default_interval(self):
        self.assertEqual(DEFAULT_INTERVAL, 30)

    def test_min_interval(self):
        self.assertEqual(MIN_INTERVAL, 10)
        self.assertLess(MIN_INTERVAL, DEFAULT_INTERVAL)

    def test_default_netmask(self):
        self.assertEqual(DEFAULT_NETMASK, "255.255.255.0")

    def test_default_private_network(self):
        self.assertEqual(DEFAULT_PRIVATE_NETWORK, "192.168.0.0/16")


class TestConfigPatterns(unittest.TestCase):

    def test_mac_pattern_colon(self):
        import re
        self.assertTrue(re.match(MAC_PATTERN, "00:11:22:33:44:55"))
        self.assertTrue(re.match(MAC_PATTERN, "aa-bb-cc-dd-ee-ff"))

    def test_mac_pattern_invalid(self):
        import re
        self.assertIsNone(re.match(MAC_PATTERN, "00:11:22:33:44"))
        self.assertIsNone(re.match(MAC_PATTERN, "not-a-mac"))


class TestBoxChars(unittest.TestCase):

    def test_box_chars_unicode(self):
        self.assertEqual(len(BOX_H), 1)
        self.assertEqual(len(BOX_V), 1)
        self.assertNotEqual(BOX_H, BOX_V)


if __name__ == "__main__":
    unittest.main()
