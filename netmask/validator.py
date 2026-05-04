"""MAC and IP address validation and random generation."""

import re
import random
import ipaddress

from netmask.config import MAC_PATTERN


def is_valid_mac(mac):
    """Check if a string is a valid MAC address format (xx:xx:xx:xx:xx:xx or xx-xx-xx-xx-xx-xx)."""
    return bool(re.match(MAC_PATTERN, mac))


def is_unicast(mac):
    """Check if MAC address has unicast bit set (first byte LSB = 0)."""
    if not is_valid_mac(mac):
        return False
    first_byte = int(mac.replace(":", "").replace("-", "")[:2], 16)
    return (first_byte & 1) == 0


def random_mac():
    """Generate a random valid unicast MAC address.

    Ensures unicast (bit 0 = 0) and locally administered (bit 1 = 1).
    Format: xx:xx:xx:xx:xx:xx
    """
    mac = bytearray(random.randint(0, 255) for _ in range(6))
    mac[0] = (mac[0] | 2) & 0xFE
    return ":".join(f"{b:02x}" for b in mac)


def is_valid_ip(ip):
    """Check if a string is a valid IPv4 address."""
    try:
        ipaddress.IPv4Address(ip)
        return True
    except (ipaddress.AddressValueError, ValueError):
        return False


def is_valid_netmask(mask):
    """Check if a string is a valid subnet mask."""
    try:
        ipaddress.IPv4Network(f"0.0.0.0/{mask_to_cidr(mask)}")
        return True
    except (ipaddress.AddressValueError, ValueError):
        return False


def mask_to_cidr(mask):
    """Convert subnet mask to CIDR prefix length."""
    try:
        try:
            return int(mask)
        except (ValueError, TypeError):
            return sum(bin(int(octet)).count("1") for octet in mask.split("."))
    except Exception:
        return 24


def cidr_to_mask(cidr):
    """Convert CIDR prefix length to subnet mask."""
    cidr = int(cidr)
    mask = (0xFFFFFFFF << (32 - cidr)) & 0xFFFFFFFF
    return ".".join(str((mask >> (24 - 8 * i)) & 0xFF) for i in range(4))


def random_ip(network="192.168.0.0/16"):
    """Generate a random IP within a given private network."""
    try:
        net = ipaddress.IPv4Network(network, strict=False)
        host_bits = 32 - net.prefixlen
        random_offset = random.randint(1, (2**host_bits) - 2)
        return str(net.network_address + random_offset)
    except Exception:
        octets = [random.randint(1, 254) for _ in range(4)]
        if network.startswith("10."):
            octets[0] = 10
        elif network.startswith("172."):
            octets[0] = 172
            octets[1] = random.randint(16, 31)
        elif network.startswith("192.168"):
            octets[0] = 192
            octets[1] = 168
        return ".".join(str(o) for o in octets)


def random_private_ip():
    """Generate a random IP in common private ranges."""
    networks = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
    return random_ip(random.choice(networks))


def format_mac(mac, style="colon"):
    """Convert MAC to specified format: 'colon' (xx:xx) or 'dash' (xx-xx)."""
    clean = re.sub(r"[^0-9A-Fa-f]", "", mac)
    if len(clean) != 12:
        return mac
    sep = ":" if style == "colon" else "-"
    return sep.join(clean[i : i + 2].lower() for i in range(0, 12, 2))


def parse_duration(value):
    """Parse a human-readable duration string to total seconds.

    Supports formats: '30s', '5m', '2h', '1h30m', '90m', '1h 30m', '30'.
    Returns total seconds as int, or raises ValueError.
    """
    if not value:
        raise ValueError("Duration must not be empty")

    if isinstance(value, (int, float)):
        return max(1, int(value))

    value = str(value).strip().lower().replace(" ", "")

    if value.isdigit():
        return int(value)

    total = 0
    buf = ""

    for char in value:
        if char in "smhd":
            try:
                num = int(buf) if buf else 0
            except ValueError:
                raise ValueError(f"Invalid duration: {value}")
            if char == "s":
                total += num
            elif char == "m":
                total += num * 60
            elif char == "h":
                total += num * 3600
            elif char == "d":
                total += num * 86400
            buf = ""
        elif char.isdigit():
            buf += char
        else:
            raise ValueError(f"Invalid duration: {value}")

    if total <= 0:
        raise ValueError(f"Duration must be positive: {value}")
    return total


def format_duration(seconds):
    """Convert seconds to human-readable duration string."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        m, s = divmod(seconds, 60)
        return f"{m}m{s}s" if s else f"{m}m"
    else:
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        parts = f"{h}h"
        if m:
            parts += f"{m}m"
        if s:
            parts += f"{s}s"
        return parts
