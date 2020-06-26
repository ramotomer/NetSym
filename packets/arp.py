from address.ip_address import IPAddress
from address.mac_address import MACAddress
from consts import *
from packets.protocol import Protocol


class ARP(Protocol):
    """
    This class represents an ARP layer of a packet.
    """
    def __init__(self, opcode, src_ip, dst_ip, src_mac, dst_mac=None):
        """
        Initiates an ARP layer instance.
        :param opcode: Whether the ARP is a request or a reply or gratuitous
        :param src_mac: The mac of the sender (MACAddress object)
        :param dst_ip: The ip of the destination.
        :param src_ip: The IPAddress address of the sender (if not given, is '0.0.0.0' (arp probe))
        :param dst_mac: The mac of the destination. None if request or gratARP.
        """
        super(ARP, self).__init__(3, '')  # 3rd layer.
        self.opcode = opcode
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.src_mac = src_mac
        self.dst_mac = dst_mac if dst_ip is not None else MACAddress.broadcast()

        self.string = f"Who has {dst_ip}? tell {src_ip}!"
        if self.opcode == ARP_REPLY:
            self.string = f"{src_ip} is at {src_mac}!"
        elif self.opcode == ARP_GRAT:
            self.string = f"Gratuitous arp at {src_ip}"

    @classmethod
    def create_probe(cls, dst_ip, src_mac):
        """
        This is a constructor for an 'ARP probe'
        :return: an ARP probe instance
        """
        return cls(ARP_REQUEST, IPAddress('0.0.0.0/0'), dst_ip, src_mac)

    @classmethod
    def create_reply(cls, arp_request, my_mac):
        """
        Receives an arp request (ARP instance with opcode=ARP_REQUEST) and returns
        the appropriate arp reply object.
        :param arp_request: The ARP request object
        :param my_mac: My MAC address to insert in the reply object.
        :return: The ARP reply object
        """
        return cls(ARP_REPLY, arp_request.dst_mac, my_mac, arp_request.dst_ip, arp_request.src_ip)

    def copy(self):
        """
        Copies the ARP
        :return:
        """
        return self.__class__(
            self.opcode,
            IPAddress.copy(self.src_ip),
            IPAddress.copy(self.dst_ip),
            MACAddress.copy(self.src_mac),
            MACAddress.copy(self.dst_mac) if isinstance(self.dst_mac, MACAddress) else None,
        )

    def __repr__(self):
        """ip_layer representation of the ARP object"""
        return f"{self.opcode} from {self.src_ip!r} to {self.dst_ip!r}, {self.string}"

    def multiline_repr(self):
        """The multiline representation of the packet"""
        return f"\nARP:\n{self.opcode}\nfrom {self.src_ip}\nto {self.dst_ip}\n {self.string}"
