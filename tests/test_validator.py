"""Tests for validator.py — MAC/IP validation, random generators, duration parsing."""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.validator import (
    is_valid_mac,
    is_unicast,
    random_mac,
    is_valid_ip,
    is_valid_netmask,
    mask_to_cidr,
    cidr_to_mask,
    random_ip,
    random_private_ip,
    parse_duration,
    format_duration,
    format_mac,
)


class TestMACValidation(unittest.TestCase):

    def test_valid_colon_mac(self):
        self.assertTrue(is_valid_mac("00:11:22:33:44:55"))
        self.assertTrue(is_valid_mac("aa:bb:cc:dd:ee:ff"))
        self.assertTrue(is_valid_mac("AA:BB:CC:DD:EE:FF"))

    def test_valid_dash_mac(self):
        self.assertTrue(is_valid_mac("00-11-22-33-44-55"))
        self.assertTrue(is_valid_mac("aa-bb-cc-dd-ee-ff"))

    def test_invalid_mac(self):
        self.assertFalse(is_valid_mac("00:11:22:33:44"))
        self.assertFalse(is_valid_mac("gg:11:22:33:44:55"))
        self.assertFalse(is_valid_mac("00:11:22:33:44:55:66"))
        self.assertFalse(is_valid_mac(""))
        self.assertFalse(is_valid_mac("not a mac"))

    def test_unicast_mac(self):
        self.assertTrue(is_unicast("00:11:22:33:44:55"))
        self.assertTrue(is_unicast("02:11:22:33:44:55"))
        self.assertTrue(is_unicast("fe:11:22:33:44:55"))
        self.assertFalse(is_unicast("01:11:22:33:44:55"))
        self.assertFalse(is_unicast("03:11:22:33:44:55"))
        self.assertFalse(is_unicast("ff:11:22:33:44:55"))

    def test_random_mac_generates_valid_unicast(self):
        for _ in range(100):
            mac = random_mac()
            self.assertTrue(is_valid_mac(mac), f"Invalid format: {mac}")
            self.assertTrue(is_unicast(mac), f"Not unicast: {mac}")

    def test_random_mac_uniqueness(self):
        macs = {random_mac() for _ in range(50)}
        self.assertGreater(len(macs), 45)

    def test_format_mac_colon(self):
        self.assertEqual(format_mac("aabbccddeeff", "colon"), "aa:bb:cc:dd:ee:ff")
        self.assertEqual(format_mac("AABBCCDDEEFF", "colon"), "aa:bb:cc:dd:ee:ff")

    def test_format_mac_dash(self):
        self.assertEqual(format_mac("aabbccddeeff", "dash"), "aa-bb-cc-dd-ee-ff")

    def test_format_mac_dirty(self):
        self.assertEqual(format_mac("aa:bb:cc:dd:ee:ff", "colon"), "aa:bb:cc:dd:ee:ff")
        self.assertEqual(format_mac("aa-bb-cc-dd-ee-ff", "dash"), "aa-bb-cc-dd-ee-ff")


class TestIPValidation(unittest.TestCase):

    def test_valid_ip(self):
        self.assertTrue(is_valid_ip("192.168.1.1"))
        self.assertTrue(is_valid_ip("10.0.0.1"))
        self.assertTrue(is_valid_ip("172.16.0.1"))
        self.assertTrue(is_valid_ip("0.0.0.0"))
        self.assertTrue(is_valid_ip("255.255.255.255"))

    def test_invalid_ip(self):
        self.assertFalse(is_valid_ip("256.1.1.1"))
        self.assertFalse(is_valid_ip("1.2.3.256"))
        self.assertFalse(is_valid_ip("192.168.1"))
        self.assertFalse(is_valid_ip("abc.def.ghi.jkl"))
        self.assertFalse(is_valid_ip(""))
        self.assertFalse(is_valid_ip("192.168.1.1.1"))

    def test_valid_netmask(self):
        self.assertTrue(is_valid_netmask("255.255.255.0"))
        self.assertTrue(is_valid_netmask("255.0.0.0"))
        self.assertTrue(is_valid_netmask("255.255.0.0"))

    def test_invalid_netmask(self):
        self.assertFalse(is_valid_netmask("300.300.300.0"))
        self.assertFalse(is_valid_netmask("not.a.mask"))

    def test_mask_to_cidr(self):
        self.assertEqual(mask_to_cidr("255.255.255.0"), 24)
        self.assertEqual(mask_to_cidr("255.255.0.0"), 16)
        self.assertEqual(mask_to_cidr("255.0.0.0"), 8)
        self.assertEqual(mask_to_cidr("255.255.255.255"), 32)
        self.assertEqual(mask_to_cidr("0.0.0.0"), 0)

    def test_mask_to_cidr_int(self):
        self.assertEqual(mask_to_cidr(24), 24)

    def test_cidr_to_mask(self):
        self.assertEqual(cidr_to_mask(24), "255.255.255.0")
        self.assertEqual(cidr_to_mask(16), "255.255.0.0")
        self.assertEqual(cidr_to_mask(8), "255.0.0.0")
        self.assertEqual(cidr_to_mask(32), "255.255.255.255")

    def test_random_ip_in_range(self):
        ip = random_ip("192.168.0.0/16")
        self.assertTrue(is_valid_ip(ip))
        octets = [int(x) for x in ip.split(".")]
        self.assertTrue(all(0 <= o <= 255 for o in octets))

    def test_random_private_ip(self):
        for _ in range(50):
            ip = random_private_ip()
            self.assertTrue(is_valid_ip(ip))
            octets = [int(x) for x in ip.split(".")]
            self.assertTrue(all(0 <= o <= 255 for o in octets))


class TestDurationParsing(unittest.TestCase):

    def test_seconds(self):
        self.assertEqual(parse_duration("30s"), 30)
        self.assertEqual(parse_duration("1s"), 1)

    def test_minutes(self):
        self.assertEqual(parse_duration("5m"), 300)
        self.assertEqual(parse_duration("1m"), 60)

    def test_hours(self):
        self.assertEqual(parse_duration("2h"), 7200)
        self.assertEqual(parse_duration("1h"), 3600)

    def test_days(self):
        self.assertEqual(parse_duration("1d"), 86400)

    def test_combined(self):
        self.assertEqual(parse_duration("1h30m"), 5400)
        self.assertEqual(parse_duration("2h30m15s"), 9015)

    def test_plain_number(self):
        self.assertEqual(parse_duration("30"), 30)
        self.assertEqual(parse_duration("300"), 300)

    def test_int_input(self):
        self.assertEqual(parse_duration(300), 300)

    def test_invalid(self):
        with self.assertRaises(ValueError):
            parse_duration("")
        with self.assertRaises(ValueError):
            parse_duration("abc")

    def test_format_duration(self):
        self.assertEqual(format_duration(30), "30s")
        self.assertEqual(format_duration(300), "5m")
        self.assertEqual(format_duration(5400), "1h30m")
        self.assertEqual(format_duration(3661), "1h1m1s")


if __name__ == "__main__":
    unittest.main()
