from packets.protocol import Protocol


class ICMP(Protocol):
    """
    This class represents a Ping packet between computers.
    """
    def __init__(self, opcode, data=''):
        """
        Create an ICMP packet.
        :param opcode: ICMP_REPLY or ICMP_REQUEST.
        """
        super(ICMP, self).__init__(4, data)  # I put in 4th layer because it goes over IP which is 3rd.
        self.opcode = opcode

    @staticmethod
    def create_string():
        """
        Returns the ip_layer that is in the ICMP packets
        :return: ip_layer
        """
        return ''.join([chr(letter) for letter in range(ord('a'), ord('z') + 1)])

    def copy(self):
        """
        Copy the ICMP packet
        :return:
        """
        return self.__class__(
            self.opcode,
            self.data.copy() if hasattr(self.data, "copy") else self.data,
        )

    def __str__(self):
        """A shorter string representation of the ICMP layer"""
        return f"ICMP({self.opcode})"

    def __repr__(self):
        """The ip_layer representation of the ICMP packet"""
        return f"ICMP({self.opcode}, Data: {self.data})"

    def multiline_repr(self):
        """The multiline representation of the packet"""
        return f"\nICMP:\nopcode: {self.opcode}\n{self.data}"
