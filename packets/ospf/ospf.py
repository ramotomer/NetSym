from address.ip_address import IPAddress
from packets.protocol import Protocol


class OSPF(Protocol):
    """
    This class represents an OSPF packet instance
    """
    def __init__(self, message_type, router_id, area_id="0.0.0.0"):
        """
        Create an OSPF packet.
        :param message_type: one of OPCODES.OSPF.MESSAGE_TYPES
        """
        super(OSPF, self).__init__(4, "")
        self.message_type = message_type

        self.router_id = IPAddress(router_id)
        self.area_id = IPAddress(area_id)

    def copy(self):
        """
        Copy the OSPF packet
        :return:
        """
        return self.__class__(
            self.message_type,
            self.router_id,
            self.area_id,
            self.data.copy() if hasattr(self.data, "copy") else self.data,
        )

    def __str__(self):
        """A shorter string representation of the OSPF layer"""
        return f"OSPF({self.message_type}, {self.router_id})"

    def __repr__(self):
        """The ip_layer representation of the OSPF packet"""
        return f"OSPF({self.message_type}, {self.router_id}, {self.area_id}, Data: {repr(self.data)})"

    def multiline_repr(self):
        """The multiline representation of the packet"""
        pass
