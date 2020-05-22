from consts import FTP_REQUEST_PACKET, FTP_DATA_PACKET
from packets.protocol import Protocol


class FTP(Protocol):
    """
    A Packet of the FTP protocol.
    Contains (for now) data string for the FTP client and server processes
    """
    def __init__(self, data, is_request=False):
        """
        Initiates the FTP packet as a protocol in the fifth layer
        """
        super(FTP, self).__init__(5, data)
        self.is_request = is_request

    @property
    def opcode(self):
        """
        An opcode of the packet that is used for the graphics.
        :return:
        """
        if self.is_request:
            return FTP_REQUEST_PACKET
        return FTP_DATA_PACKET

    def copy(self):
        """
        Copies the FTP layer
        :return: `FTP`
        """
        return self.__class__(
            self.data,
            self.is_request,
        )

    def __len__(self):
        """
        This is required by all protocols that are encapsulated in TCP
        :return: `int`
        """
        return len(self.data)

    def multiline_repr(self):
        """
        The multiline side representation of the layer
        :return: `str`
        """
        return f"""
FTP: {"(request)" if self.is_request else ""}
data:
{self.data}
"""

    def __repr__(self):
        """
        A string representation of the FTP packet
        :return: `str`
        """
        return f"FTP({self.data})"
