"""Abstract base class for platform-specific MAC/IP change operations."""

from abc import ABC, abstractmethod


class AbstractChanger(ABC):
    """Platform-agnostic interface for MAC/IP manipulation."""

    @abstractmethod
    def disable_interface(self, interface):
        """Bring interface down."""
        pass

    @abstractmethod
    def enable_interface(self, interface):
        """Bring interface up."""
        pass

    @abstractmethod
    def change_mac(self, interface, mac):
        """Set new MAC address on interface."""
        pass

    @abstractmethod
    def change_ip(self, interface, ip, netmask, gateway=None):
        """Set new static IP address on interface."""
        pass

    @abstractmethod
    def dhcp_renew(self, interface):
        """Release and renew DHCP lease."""
        pass
