from consts import *
from packets.protocol import Protocol


class IP(Protocol):
    """
    This class represents the IP layer of a packet.
    """
    def __init__(self, src_ip, dst_ip, ttl=TTLS[OS_WINDOWS], data=None):
        """
        Constructs a new IP layer with a given source and destination IP addresses.
        :param src_ip:
        :param dst_ip:
        """
        super(IP, self).__init__(data)
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.ttl = ttl

    def __repr__(self):
        """The data representation of the IP layer object"""
        return f"IP(from {self.src_ip}, to {self.dst_ip}, ttl: {self.ttl}, Data: {self.data!r})"

    def multiline_repr(self):
        """The multiline representation of the packet"""
        return f"\nIP:\nfrom: {self.src_ip}\nto: {self.dst_ip}\n TTL: {self.ttl}\n{self.data.multiline_repr()}"
