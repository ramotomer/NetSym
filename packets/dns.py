from packets.protocol import Protocol


class DNS(Protocol):
    """
    A DNS packet.
    """
    def __init__(self, opcode, query, data):
        """
        init the packet.
        :param data:
        """
        super(DNS, self).__init__(5, data)
        self.opcode = opcode
        self.query = query

    def copy(self):
        """
        Copies the packet and returns a new identical instance.
        :return:
        """
        return self.__class__(
            self.opcode,
            self.query,
            self.data,
        )

    def multiline_repr(self):
        """
        The multiline representation that is viewed in the side window.
        :return:
        """
        return f"""
DNS:

data:
{self.data}
"""
