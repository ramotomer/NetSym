from address.mac_address import MACAddress
from address.ip_address import IPAddress
from computing.connection import Connection
from packets.ethernet import Ethernet
from consts import *
from packets.packet import Packet
from exceptions import *
import random


class Interface:
    """
    This class represents a computer net interface.
    It can send and receive packets.
    It contains methods that provide abstraction for sending many types of packets.

    An interface can be either connected or disconnected to a `ConnectionSide` object, which enables it to move its packets
    down the connection further.
    """
    def __init__(self, mac, ip=None, name=None):
        """
        Initiates the Interface instance with addresses (mac and possibly ip), the operating system, and a name.
        :param os: The operating system of the computer above.
        :param mac: a string MAC address ('aa:bb:cc:11:22:76' for example)
        :param connection: a `Connection` object
        :param ip: a string ip address ('10.3.252.5/24' for example)
        """
        self.connection = None
        self.name = name if name is not None else Interface.random_name()

        self.mac = MACAddress(mac)
        self.ip = IPAddress(ip) if ip is not None else None

        self.is_promisc = True
        self.is_sniffing = False

    @staticmethod
    def random_name():
        """Returns a random Interface name"""
        return random.choice(INTERFACE_NAMES) + str(random.randint(0, 10))

    @classmethod
    def with_ip(cls, ip_address):
        """Constructor for an interface with a given (string) IP address, a random name and a random MAC address"""
        return cls(MACAddress.randomac(), ip_address, cls.random_name())

    def is_directly_for_me(self, packet):
        """
        Receives a packet and determines whether it is destined directly for this Interface (broadcast is not)
        :param packet: a `Packet` object.
        :return: whether the destination MAC address is of this Interface
        """
        return self.mac == packet["Ethernet"].dst_mac

    def is_for_me(self, packet):
        """
        Receives a packet and determines whether it is destined for this Interface (or is broadcast)
        :param packet: a `Packet` object.
        :return: whether the detination MAC address is of this Interface
        """
        return self.is_directly_for_me(packet) or (packet["Ethernet"].dst_mac.is_broadcast())

    def has_ip(self):
        """Returns whether the Interface has an IP address"""
        return self.ip is not None

    def has_this_ip(self, ip_address):
        """
        Returns whether or not this interface has the given IP
        :param ip_address: IPAddress
        :return: boolean
        """
        return self.ip == ip_address

    def validate_DHCP_given_ip(self, ip_address):
        """
        This is for future implementation if you want, for now it is not doing anything.
        :param ip_address: an IPAddress object.
        :return: theoretically, whether or not the interface approves of the address given to it by DHCP server.
        """
        return isinstance(ip_address, IPAddress) and self is self

    def is_connected(self):
        """Returns whether the interface is connected or not"""
        return self.connection is not None

    def connect(self, other):
        """
        Connects this interface to another interface, return the `Connection` object.
        If grat arps are enabled, each interface sends a gratuitous arp.
        :param other: The other `Interface` object to connect to.
        :return: The `Connection` object.
        """
        if self.is_connected() or other.is_connected():
            raise DeviceAlreadyConnectedError()
        connection = Connection()
        self.connection, other.connection = connection.get_sides()
        return connection

    def disconnect(self):
        """
        Disconnect an interface from its `Connection`.

        Note that the `Connection` object does not know about this disconnection,
        so the other interface should be disconnected as well or this side of
        connection should be reconnected.
        :return: None
        """
        if not self.is_connected():
            raise InterfaceNotConnectedError("Cannot disconnect an interface that is not connected!")
        self.connection = None

    def send(self, packet):
        """
        Receives a packet to send and just sends it!
        for Tomer: if the interface is not connected maybe an error should be raised but
            for now it just does nothing and it works very well.
        :param packet: The full packet `Packet` object.
        :return: None
        """
        if self.is_connected():
            self.connection.send(packet)

    def receive(self):
        """
        Returns the packet that was received (if one was received) else, returns None.
        If the interface is not in promiscuous, only retruns packets that are directed for it (and broadcast).
        :return: A `Packet` object that was sent from the other side of the connection.
        """
        try:
            packets = self.connection.receive()
            if self.is_promisc:
                return packets
            return list(filter(lambda packet: self.is_for_me(packet), packets))
        except AttributeError:
            # raise InterfaceNotConnectedError()
            pass

    def ethernet_wrap(self, dst_mac, data):
        """
        Takes in data (string, a `Protocol` object...) and wraps it as an `Ethernet` packet ready to be sent.
        :param data: any data to put in the ethernet packet (ARP, IP, str, more Ethernet, whatever you want, only
            the receiver computer should know whats coming and how to handle it...)
        :param dst_mac: a `MACAddress` object of the destination of the packet.
        :return: the ready `Packet` object
        """
        return Packet(Ethernet(self.mac, dst_mac, data))

    def send_with_ethernet(self, dst_mac, protocol):
        """
        Receives a `Procotol` object, wraps it with ethernet and sends it.
        :param protocol: a `Protocol` instance.
        :return: None
        """
        self.send(self.ethernet_wrap(dst_mac, protocol))

    def __eq__(self, other):
        """Determines which interfaces are equal"""
        return self is other

    def __hash__(self):
        """hash of the interface"""
        return hash(id(self))

    def __str__(self):
        """A shorter string representation of the Interface"""
        return f"{self.name}: \n{self.mac}" + ('\n' + repr(self.ip) if self.has_ip() else '')

    def __repr__(self):
        """The string representation of the Interface"""
        return f"Interface(name={self.name}, mac={self.mac}, ip={self.ip}, os={self.os})"
