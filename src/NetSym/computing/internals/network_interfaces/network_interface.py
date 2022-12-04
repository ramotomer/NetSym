from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Union, Any, TYPE_CHECKING, Set

import scapy

from NetSym.address.ip_address import IPAddress
from NetSym.address.mac_address import MACAddress
from NetSym.computing.connections.connection import Connection
from NetSym.consts import FILE_PATHS, INTERFACES, PROTOCOLS, T_Color
from NetSym.exceptions import *
from NetSym.packets.all import Ether
from NetSym.packets.packet import Packet

if TYPE_CHECKING:
    from NetSym.gui.tech.network_interfaces.network_interface_graphics import NetworkInterfaceGraphics
    from NetSym.gui.abstracts.graphics_object import GraphicsObject
    from NetSym.computing.connections.connection import BaseConnectionSide
    from NetSym.gui.tech.computer_graphics import ComputerGraphics


class NetworkInterface(ABC):
    """
    This class represents a computer net interface.
    It can send and receive packets.
    It contains methods that provide abstraction for sending many types of packets.

    An interface can be either connected or disconnected to a `CableConnectionSide` object, which enables it to move its packets
    down the connection_side further.
    """
    POSSIBLE_INTERFACE_NAMES: Optional[List[str]] = None
    EXISTING_INTERFACE_NAMES: Set[str] = set()

    def __init__(self,
                 mac: Optional[Union[str, MACAddress]] = None,
                 ip: Optional[Union[str, IPAddress]] = None,
                 name: Optional[str] = None,
                 connection_side: Optional[BaseConnectionSide] = None,
                 display_color: T_Color = INTERFACES.COLOR,
                 type_: str = INTERFACES.TYPE.ETHERNET,
                 mtu: int = PROTOCOLS.ETHERNET.MTU) -> None:
        """
        Initiates the CableNetworkInterface instance with addresses (mac and possibly ip), the operating system, and a name.
        :param mac: a string MAC address ('aa:bb:cc:11:22:76' for example)
        :param ip: a string ip address ('10.3.252.5/24' for example)
        """
        self.__connection: Optional[Connection] = None
        self.__connection_side: Optional[BaseConnectionSide] = None
        self.connection_side = connection_side

        self.name: str = name if name is not None else NetworkInterface.random_name()
        self.mac: MACAddress = MACAddress(MACAddress.randomac()) if mac is None else MACAddress(mac)
        self.ip: Optional[IPAddress] = IPAddress(ip) if ip is not None else None

        self.is_promisc = True
        self.is_blocked: bool = False
        self.accepting: Optional[str] = None

        self.is_powered_on = True
        self.type: str = type_
        self.mtu: int = mtu

        self.graphics: Optional[NetworkInterfaceGraphics] = None
        self.display_color: T_Color = display_color
        # TODO: This ^ belongs in the CableNetworkInterfaceGraphics class FOR SURE!!!

    @property
    def connection(self) -> Connection:
        if self.__connection is None:
            raise NoSuchConnectionError(f"self: {self}, self.__connection: {self.__connection}")
        return self.__connection

    @property
    def connection_side(self) -> Optional[BaseConnectionSide]:
        return self.__connection_side

    @connection_side.setter
    def connection_side(self, value: Optional[BaseConnectionSide]) -> None:
        self.__connection = None
        self.__connection_side = value

        if value is not None:
            self.__connection = value.connection

    @property
    def no_carrier(self) -> bool:
        return not self.is_connected()

    @classmethod
    def random_name(cls) -> str:
        """Returns a random CableNetworkInterface name and caches it to never be generated again :)"""
        if cls.POSSIBLE_INTERFACE_NAMES is None:
            cls.POSSIBLE_INTERFACE_NAMES = [line.strip() for line in open(FILE_PATHS.INTERFACE_NAMES_FILE_PATH).readlines()]

        name = random.choice(cls.POSSIBLE_INTERFACE_NAMES) + str(random.randint(0, 10))
        if name in cls.EXISTING_INTERFACE_NAMES:
            name = cls.random_name()
        cls.EXISTING_INTERFACE_NAMES.add(name)
        return name

    @classmethod
    def with_ip(cls, ip_address: Union[str, IPAddress]) -> NetworkInterface:
        """Constructor for an interface with a given (string) IP address, a random name and a random MAC address"""
        return cls(MACAddress.randomac(), ip_address, cls.random_name())

    def get_ip(self) -> IPAddress:
        """
        Return the IP of the interface.
        If it does not have one - raises
        """
        if self.ip is None:
            raise NoIPAddressError(f"Cannot get IP address of interface without an ip address (it is None)... interface: {self}")

        return self.ip

    def get_graphics(self) -> NetworkInterfaceGraphics:
        """

        """
        if self.graphics is None:
            raise GraphicsObjectNotYetInitialized

        return self.graphics

    def is_directly_for_me(self, packet: Packet) -> bool:
        """
        Receives a packet and determines whether it is destined directly for this CableNetworkInterface (broadcast is not)
        On the second layer
        :param packet: a `Packet` object.
        :return: whether the destination MAC address is of this CableNetworkInterface
        """
        return bool((self.mac == packet["Ether"].dst_mac) or packet["Ether"].dst_mac.is_no_mac())

    def is_for_me(self, packet: Packet) -> bool:
        """
        Receives a packet and determines whether it is destined for this CableNetworkInterface (or is broadcast)
        On the second layer
        :param packet: a `Packet` object.
        :return: whether the destination MAC address is of this CableNetworkInterface
        """
        return self.is_directly_for_me(packet) or (packet["Ether"].dst_mac.is_broadcast())

    def has_ip(self) -> bool:
        """Returns whether the CableNetworkInterface has an IP address"""
        return self.ip is not None

    def has_this_ip(self, ip_address: Union[str, IPAddress]) -> bool:
        """
        Returns whether or not this interface has the given IP
        :param ip_address: IPAddress
        :return: boolean
        """
        return self.has_ip() and self.get_ip() == IPAddress(ip_address)

    @abstractmethod
    def is_connected(self) -> bool:
        """Returns whether the interface is connected or not"""

    @abstractmethod
    def init_graphics(self, parent_computer: ComputerGraphics, x: Optional[float] = None, y: Optional[float] = None) -> GraphicsObject:
        """
        Initiate the GraphicsObject that represents the interface visually
        """

    def set_mac(self, new_mac: MACAddress) -> None:
        """
        Receive a new mac address and change my MAC to be that mac
        :param new_mac: the new mac
        :return: None
        """
        self.mac = new_mac

    def set_name(self, name: str) -> None:
        """
        Sets the name of the interface to be a new name
        Raises exception if the name is not valid
        :param name: the new name of the interface
        :return: None
        """
        if name == self.name:
            raise PopupWindowWithThisError("new computer name is the same as the old one!!!")
        elif len(name) < 2:
            raise PopupWindowWithThisError("name too short!!!")
        elif not any(char.isalpha() for char in name):
            raise PopupWindowWithThisError("name must contain letters!!!")

        self.name = name

    def set_mtu(self, mtu: int) -> None:
        """
        Sets the new MTU of the interface (must be 68 < mtu <= 1500)
        """
        if not (PROTOCOLS.ETHERNET.MINIMUM_MTU < mtu <= PROTOCOLS.ETHERNET.MTU):
            raise PopupWindowWithThisError(f"Invalid MTU {mtu}! valid range - between {PROTOCOLS.ETHERNET.MINIMUM_MTU} and {PROTOCOLS.ETHERNET.MTU}!")

        self.mtu = mtu

    def disconnect(self) -> None:
        """
        Disconnect an interface from its `CableConnection`.

        Note that the `CableConnection` object does not know about this disconnection,
        so the other interface should be disconnected as well or this side of
        connection_side should be reconnected.
        :return: None
        """
        if not self.is_connected():
            raise InterfaceNotConnectedError("Cannot disconnect an interface that is not connected!")
        self.connection_side = None

    def send(self, packet: Packet) -> bool:
        """
        Receives a packet to send and just sends it!
        for Tomer: if the interface is not connected maybe an error should be raised but
            for now it just does nothing and it works very well.
        :param packet: The full packet `Packet` object.
        :return: Whether or not the packet was sent successfully
        """
        if not self.is_powered_on:
            return False

        if len(packet.data) > (self.mtu + PROTOCOLS.ETHERNET.HEADER_LENGTH):
            print(f"{self!r} dropped a packet due to MTU being too large! packet is {len(packet.data) - PROTOCOLS.ETHERNET.HEADER_LENGTH} bytes long!"
                  f" MTU is only {self.mtu}")
            return False

        if self.is_connected() and (not self.is_blocked or (self.is_blocked and self.accepting in packet)):
            self.connection_side.send(packet)
            return True

    def receive(self) -> List[Packet]:
        """
        Returns the packet that was received (if one was received) else, returns None.
        If the interface is not in promiscuous, only returns packets that are directed for it (and broadcast).
        :return: A `Packet` object that was sent from the other side of the connection_side.
        """
        if not self.is_powered_on:
            return []

        if not self.is_connected():
            raise InterfaceNotConnectedError("The interface is not connected so it cannot receive packets!!!")

        packets = self.connection_side.receive()
        if self.is_blocked:
            return list(filter((lambda packet: self.accepting in packet), packets))
        if self.is_promisc:
            return packets
        return list(filter(lambda packet: self.is_for_me(packet), packets))

    def ethernet_wrap(self, dst_mac: MACAddress, data: scapy.packet.Packet) -> Packet:
        """
        Takes in ip_layer (string, a `Protocol` object...) and wraps it as an `Ethernet` packet ready to be sent.
        :param data: any ip_layer to put in the ethernet packet (ARP, IP, str, more Ethernet, whatever you want, only
            the receiver computer should know whats coming and how to handle it...)
        :param dst_mac: a `MACAddress` object of the destination of the packet.
        :return: the ready `Packet` object
        """
        return Packet(Ether(src_mac=str(self.mac), dst_mac=str(dst_mac)) / data)

    def send_with_ethernet(self, dst_mac: MACAddress, protocol: scapy.packet.Packet) -> None:
        """
        Receives a `Protocol` object, wraps it with ethernet and sends it.
        :param dst_mac: `MACAddress` object which will be the destination address of the ethernet frame
        :param protocol: a `Protocol` instance.
        :return: None
        """
        self.send(self.ethernet_wrap(dst_mac, protocol))

    def block(self, accept: Optional[str] = None) -> None:
        """
        Blocks the connection_side and does not receive packets from it anymore.
        It only accepts packets that contain the `accept` layer (for example "STP")
        if blocked, does nothing (updates the 'accept')
        """
        self.is_blocked = True
        self.accepting = accept

    def unblock(self) -> None:
        """
        Releases the blocking of the connection_side and allows it to receive packets again.
        if not blocked, does nothing...
        :return: None
        """
        self.is_blocked = False
        self.accepting = None

    def toggle_block(self, accept: Optional[str] = None) -> None:
        """
        Toggles between block() and unblock()
        :param accept:
        :return:
        """
        if self.is_blocked:
            self.unblock()
        else:
            self.block(accept)

    def __eq__(self, other: Any) -> bool:
        """Determines which interfaces are equal"""
        return self is other

    def __hash__(self) -> int:
        """hash of the interface"""
        return hash(id(self))

    def generate_view_text(self) -> str:
        """
        Generates the text for the side view of the interface
        :return: `str`
        """
        linesep = '\n'
        return f"""
Interface: 
{self.name}

{str(self.mac) if not self.mac.is_no_mac() else ""} 
{repr(self.ip) if self.has_ip() else ''}
MTU: {self.mtu}
{"Connected" if self.is_connected() else "Disconnected"}
{f"Promisc{linesep}" if self.is_promisc else ""}{"Blocked" if
        self.is_blocked else ""}
"""

    @classmethod
    @abstractmethod
    def from_dict_load(cls, dict_: Dict) -> NetworkInterface:
        """
        Loads a new interface from a dict
        :param dict_:
        :return:
        """
