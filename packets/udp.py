from packets.protocol import Protocol


class UDP(Protocol):
    """
    The udp protocol.
    """
    def __init__(self, source_port, destination_port, data):
        """
        Initiates the UDP packet with src and dst ports
        """
        super(UDP, self).__init__(4, data)
        self.src_port = source_port
        self.dst_port = destination_port

    def multiline_repr(self):
        """The multiline representation of the packet."""
        return f"\nUDP:\nsrc_port: {self.src_port}\ndst_port: {self.dst_port}\n{self.data.multiline_repr() if hasattr(self.data, 'multiline_repr') else self.data}"
