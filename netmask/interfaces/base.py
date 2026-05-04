"""Abstract base class for platform-specific interface operations."""

from abc import ABC, abstractmethod


class AbstractInterface(ABC):
    """Platform-agnostic interface for network interface discovery."""

    @abstractmethod
    def list_interfaces(self):
        """Return list of interface names."""
        pass

    @abstractmethod
    def get_mac(self, interface):
        """Return MAC address of an interface."""
        pass

    @abstractmethod
    def get_ip(self, interface):
        """Return IP address with CIDR prefix (e.g., '192.168.1.10/24')."""
        pass

    @abstractmethod
    def get_netmask(self, interface):
        """Return subnet mask of an interface."""
        pass

    @abstractmethod
    def is_up(self, interface):
        """Return True if interface is administratively up."""
        pass

    def get_all(self):
        """Return list of dicts with full info for each interface."""
        interfaces = []
        for name in self.list_interfaces():
            info = {
                "name": name,
                "mac": self.get_mac(name),
                "ip": self.get_ip(name),
                "netmask": self.get_netmask(name),
                "up": self.is_up(name),
            }
            interfaces.append(info)
        return interfaces
