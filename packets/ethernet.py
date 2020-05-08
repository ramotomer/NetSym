from address.mac_address import MACAddress
from packets.protocol import Protocol


class Ethernet(Protocol):
    """
    This class represents any packet that is sent over a connection.
    """
    def __init__(self, src_mac, dst_mac, data=None):
        """"""
        super(Ethernet, self).__init__(2, data)
        self.src_mac = src_mac
        self.dst_mac = dst_mac

    def copy(self):
        """
        Copy the ethernet packet
        :return:
        """
        return self.__class__(
            MACAddress.copy(self.src_mac),
            MACAddress.copy(self.dst_mac),
            self.data.copy(),
        )

    def __repr__(self):
        """
        a data representation of this class.
        """
        return f"Ethernet(from: {self.src_mac!r}, to: {self.dst_mac!r}, Data: {self.data!r})"

    def multiline_repr(self):
        """The multiline representation of the packet"""
        return f"\nEthernet:\nfrom: {self.src_mac}\nto: {self.dst_mac}\n{self.data.multiline_repr()}"
