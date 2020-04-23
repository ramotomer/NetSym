from packets.protocol import Protocol
from collections import namedtuple


DHCPData = namedtuple("DHCPData", "given_ip given_gateway given_dns_server")


class DHCP(Protocol):
    """
    This represents a DHCP packet.
    """
    def __init__(self, opcode, data=DHCPData(None, None, None)):
        super(DHCP, self).__init__(3, data)  # TODO: move DHCP to be the fifth layer over UDP like it should be.
        self.opcode = opcode

    def dhcp_data_string(self):
        """Returns a string that shows nicely the DHCPData of the packet"""
        given_ip, given_gateway, given_dns_server = self.data
        ip_string = f"given IP:\n{given_ip}" if given_ip is not None else ''
        gateway_string = f"given gateway:\n{given_gateway}" if given_gateway is not None else ''
        dns_string = f"given DNS server:\n{given_dns_server}" if given_dns_server is not None else ''
        return '\n'.join([ip_string, gateway_string, dns_string])

    def __repr__(self):
        """The string representation of the DHCP packet"""
        return f"DHCP({self.opcode}, {self.data})"

    def multiline_repr(self):
        """The multiline representation of the packet"""
        return f"\nDHCP:\n{self.opcode} \n{self.dhcp_data_string()}"