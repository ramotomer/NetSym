from packets.protocol import Protocol


class ICMP(Protocol):
    """
    This class represents a Ping packet between computers.
    """
    def __init__(self, opcode):
        """
        Create an ICMP packet.
        :param opcode: ICMP_REPLY or ICMP_REQUEST.
        """
        super(ICMP, self).__init__(4, '')  # I put in 4th layer because it goes over IP which is 3rd.
        self.opcode = opcode

    @staticmethod
    def create_string():
        """
        Returns the data that is in the ICMP packets
        :return: data
        """
        return ''.join([chr(letter) for letter in range(ord('a'), ord('z') + 1)])

    def __str__(self):
        """A shorter string representation of the ICMP layer"""
        return f"ICMP({self.opcode})"

    def __repr__(self):
        """The data representation of the ICMP packet"""
        return f"ICMP({self.opcode}, Data: {self.data})"

    def multiline_repr(self):
        """The multiline representation of the packet"""
        return f"\nICMP:\nopcode: {self.opcode}\n{self.data}"
