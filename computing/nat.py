import random
from collections import namedtuple

from address.ip_address import IPAddress
from computing.computer import Computer
from computing.interface import Interface
from consts import *
from exceptions import WrongUsageError, SomethingWentTerriblyWrongError
from gui.tech.computer_graphics import ComputerGraphics
from processes.process import Process, WaitingForPacket, ReturnedPacket
from usefuls import get_the_one


class NAT(Computer):
    """
    This is a device that allows multiple 'private' ip addresses to communicate to the internet
    using just one 'public' internet address.
    """
    def __init__(self):
        """
        Initiates the device and adds to it the NAT process.
        """
        super(NAT, self).__init__()
        self.interfaces = [
            Interface(name="InternetIF", display_color=VERY_LIGHT_BLUE),
        ]
        self.add_startup_process(NATProcess)

    def show(self, x, y):
        """
        Starts displaying the NAT.
        :param x:
        :param y: the location
        :return: None
        """
        self.graphics = ComputerGraphics(x, y, self, NAT_IMAGE)


NATTableKey = namedtuple("NATTableKey", [
    "protocol",
    "fourtuple",
])

NATTableValue = namedtuple("NATTableValue", [
    "local_ip",
    "port_index",
])

FourTuple = namedtuple("FourTuple", [
    "src_ip",
    "dst_ip",
    "src_port",
    "dst_port",
])  # from inside the LAN computer's point of view...


class NATProcess(Process):
    """
    This is the process that allows multiple 'private' ip addresses to communicate with the
    internet using just one internet ip address of the NAT
    """
    def __init__(self, nat):
        """
        Initiates the process with the NAT that is running it.
        """
        super(NATProcess, self).__init__(nat)
        self.internet_interface = get_the_one(self.computer.interfaces,
                                              lambda i: i.has_ip() and i.ip.is_internet_address())
        self.nat_table = {}  # {NATTableKey: NATTableValue}

    @staticmethod
    def is_nat_packet(packet):
        """
        Returns whether or not a given `Packet` is for this NAT.
        (if it has ports)
        :param packet: the packet
        :return: bool
        """
        if "IP" in packet:
            if "UDP" in packet or "TCP" in packet:  # or "ICMP" in packet:
                return packet["IP"].dst_ip.is_internet_address()
        return False

    @classmethod
    def get_outgoing_packet_fourtuple(cls, packet):
        """
        Receives a packet that is sent from the LAN, and returns the four-tuple
        (IPs and ports) and a `FourTuple` object
        :param packet: a `Packet`
        :return: `FourTuple`
        """
        ip_layer = packet["IP"]
        inner_protocol = packet[cls.packet_nat_protocol(packet)]

        return FourTuple(
            IPAddress.copy(ip_layer.src_ip),
            IPAddress.copy(ip_layer.dst_ip),
            inner_protocol.src_port,
            inner_protocol.dst_port,
        )

    @classmethod
    def packet_nat_protocol(cls, packet):
        """
        Receives a packet and returns the name of the protocol that the NAT looks at (usually UDP or TCP)
        :param packet: `Packet`
        :return: str
        """
        return get_the_one(["UDP", "TCP"], lambda p: p in packet, WrongUsageError)

    def is_incoming(self, packet, interface):
        """
        Receives a packet and returns whether or not it is coming in to the LAN from the internet
        :param packet: `Packet`
        :param interface: the interface it was received on
        :return: bool
        """
        return packet["IP"].dst_ip == self.internet_interface.ip and interface is self.internet_interface

    def is_outgoing(self, packet, interface):
        """
        Receives a packet and returns whether or not it is going out of the LAN.
        :param packet: `Packet`
        :param interface: the interface it was received on
        :return: bool
        """
        return packet["IP"].dst_ip.is_internet_address() and interface is not self.internet_interface

    def is_packet_coming_in_for_known_session(self, packet):
        """
        Returns whether or not the packet that came in is for a known session or not.
        :param packet: `Packet`
        :return: bool
        """
        protocol = self.packet_nat_protocol(packet)
        return any(packet[protocol].dst_port == port_index for port_index in self.nat_table.values())

    def add_session(self, protocol: str, fourtuple: FourTuple):
        """
        Adds a new session to the NAT table.
        :param protocol: the protocol of the session
        :param fourtuple: the FourTuple of the session
        :return: None
        """
        port_index = random.randint(*USERMODE_USABLE_PORT_RANGE)
        while any(port_index == other_index for other_index in self.nat_table.values()):
            port_index = random.randint(*USERMODE_USABLE_PORT_RANGE)

        self.nat_table[NATTableKey(protocol, fourtuple)] = NATTableValue(fourtuple.src_ip, port_index)

    def send_out_to_internet(self, packet):
        """
        Receives a packet that is going out, changes the ports and IP on it and sends it to the internet
        :param packet: `Packet`
        :return: None
        """
        protocol = self.packet_nat_protocol(packet)
        packet["IP"].src_ip = IPAddress.copy(self.internet_interface.ip)
        packet[protocol].src_port = self.nat_table[(protocol, self.get_outgoing_packet_fourtuple(packet))].port_index

        self.computer.start_sending_process(packet["IP"].dst_ip, packet[protocol].copy())

    def send_in_to_lan(self, packet):
        """
        Receives a packet that came in from the internet and sends it into the LAN to the correct IP.
        :param packet: `Packet`
        :return: None
        """
        protocol = self.packet_nat_protocol(packet)
        port_index = packet[protocol].dst_port
        _, fourtuple = get_the_one(lambda key: self.nat_table[key].port_index == port_index,
                                   self.nat_table,
                                   SomethingWentTerriblyWrongError)
        packet[protocol].dst_port = fourtuple.src_port
        packet["IP"].dst_ip = fourtuple.src_ip

        self.computer.start_sending_process(packet["IP"].dst_ip, packet[protocol].copy())

    def code(self):
        """
        The main code of the NAT, This is where the magic happens
        :return:
        """
        while True:
            packets = ReturnedPacket()
            yield WaitingForPacket(self.is_nat_packet, packets)

            if self.internet_interface is None:
                self.internet_interface = get_the_one(self.computer.interfaces,
                                                      lambda i: i.has_ip() and i.ip.is_internet_address())
                self.computer.print("Cannot NAT without an internet IP address!!!")
                continue

            for packet, interface in packets:
                protocol = self.packet_nat_protocol(packet)

                if self.is_outgoing(packet, interface):
                    fourtuple = self.get_outgoing_packet_fourtuple(packet)
                    if (protocol, fourtuple) not in self.nat_table:
                        self.add_session(protocol, fourtuple)
                    self.send_out_to_internet(packet)

                elif self.is_incoming(packet, interface):
                    if self.is_packet_coming_in_for_known_session(packet):
                        self.send_in_to_lan(packet)

                else:
                    raise SomethingWentTerriblyWrongError("A packet always goes either in or out!!!")
