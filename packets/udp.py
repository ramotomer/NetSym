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

    def __str__(self):
        """A simple string representation of the packet"""
        return f"UDP from port {self.src_port} to port {self.dst_port})"

    def __repr__(self):
        """A string representation of the packet"""
        return f"UDP(src_port={self.src_port}, dst_port={self.dst_port}, data={self.data})"

    def multiline_repr(self):
        """The multiline representation of the packet."""
        return f"\nUDP:\nsrc_port: {self.src_port}\ndst_port: {self.dst_port}\n{self.data.multiline_repr() if hasattr(self.data, 'multiline_repr') else self.data}"
