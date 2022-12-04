from __future__ import annotations

from typing import Optional, Dict, Union, Any, TYPE_CHECKING

import scapy

from NetSym.address.ip_address import IPAddress
from NetSym.address.mac_address import MACAddress
from NetSym.computing.connections.cable_connection import CableConnection
from NetSym.computing.connections.cable_connection import CableConnectionSide
from NetSym.computing.connections.connection import ConnectionSide
from NetSym.computing.internals.network_interfaces.network_interface import NetworkInterface
from NetSym.consts import INTERFACES, PROTOCOLS, T_Color, T_Time
from NetSym.exceptions import *
from NetSym.gui.tech.network_interfaces.cable_network_interface_graphics import CableNetworkInterfaceGraphics
from NetSym.packets.cable_packet import CablePacket

if TYPE_CHECKING:
    from NetSym.gui.abstracts.graphics_object import GraphicsObject
    from NetSym.gui.tech.computer_graphics import ComputerGraphics


class CableNetworkInterface(NetworkInterface):
    """
    Represents a computer network interface that leads to a cable
    """
    __connection:      Optional[CableConnection]
    __connection_side: Optional[CableConnectionSide]

    def __init__(self,
                 mac: Optional[Union[str, MACAddress]] = None,
                 ip: Optional[Union[str, IPAddress]] = None,
                 name: Optional[str] = None,
                 connection_side: Optional[CableConnectionSide] = None,
                 display_color: T_Color = INTERFACES.COLOR,
                 type_: str = INTERFACES.TYPE.ETHERNET,
                 mtu: int = PROTOCOLS.ETHERNET.MTU) -> None:
        """
        Initiates the CableNetworkInterface instance with addresses (mac and possibly ip), the operating system, and a name.
        :param mac: a string MAC address ('aa:bb:cc:11:22:76' for example)
        :param ip: a string ip address ('10.3.252.5/24' for example)
        """
        super(CableNetworkInterface, self).__init__(mac, ip, name, connection_side, display_color, type_, mtu)

    @property
    def connection(self) -> CableConnection:
        if self.__connection is None:
            raise NoSuchConnectionError(f"self: {self}, self.__connection: {self.__connection}")
        return self.__connection

    @property
    def connection_side(self) -> Optional[CableConnectionSide]:
        return self.__connection_side

    @connection_side.setter
    def connection_side(self, value: Optional[ConnectionSide]) -> None:
        if (value is not None) and (not isinstance(value, CableConnectionSide)):
            raise WrongUsageError(f"Do not set the `connection_side` of an `CableNetworkInterface` with something that is not a `CableConnectionSide` "
                                  f"You inserted {value!r} which is a {type(value)}...")

        self.__connection = None
        self.__connection_side = value

        if value is not None:
            self.__connection = value.connection

    @property
    def connection_length(self) -> T_Time:
        """
        The length of the connection_side this `CableNetworkInterface` is connected to. (The time a packet takes to go through it in seconds)
        :return: a number of seconds.
        """
        if not self.is_connected():
            raise InterfaceNotConnectedError(repr(self))

        return self.connection.deliver_time

    def init_graphics(self, parent_computer: ComputerGraphics, x: Optional[float] = None, y: Optional[float] = None) -> GraphicsObject:
        """
        Initiates the CableNetworkInterfaceGraphics object of this interface
        """
        self.graphics = CableNetworkInterfaceGraphics(x, y, self, parent_computer)
        return self.graphics

    def is_connected(self) -> bool:
        """Returns whether the interface is connected or not"""
        return (self.__connection_side is not None) and (self.__connection is not None)

    def connect(self, other: CableNetworkInterface) -> CableConnection:
        """
        Connects this interface to another interface, return the `CableConnection` object.
        If grat arps are enabled, each interface sends a gratuitous arp.
        """
        if self.is_connected() or other.is_connected():
            raise DeviceAlreadyConnectedError("The interface is connected already!!!")
        connection = CableConnection()
        self.connection_side, other.connection_side = connection.get_sides()
        return connection

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
    
    def block(self, accept: Optional[str] = None) -> None:
        """
        Blocks the connection_side and does not receive packets from it anymore.
        It only accepts packets that contain the `accept` layer (for example "STP")
        if blocked, does nothing (updates the 'accept')
        """
        super(CableNetworkInterface, self).block(accept)

        if self.connection_side is not None:
            self.connection_side.mark_as_blocked()

    def unblock(self) -> None:
        """
        Releases the blocking of the connection_side and allows it to receive packets again.
        if not blocked, does nothing...
        :return: None
        """
        super(CableNetworkInterface, self).unblock()

        if self.connection_side is not None:
            self.connection_side.mark_as_unblocked()

    def ethernet_wrap(self, dst_mac: MACAddress, data: scapy.packet.Packet) -> CablePacket:
        """
        Takes in ip_layer (string, a `Protocol` object...) and wraps it as an `Ethernet` packet ready to be sent.
        :param data: any ip_layer to put in the ethernet packet (ARP, IP, str, more Ethernet, whatever you want, only
            the receiver computer should know whats coming and how to handle it...)
        :param dst_mac: a `MACAddress` object of the destination of the packet.
        :return: the ready `CablePacket` object
        """
        return CablePacket(self.get_with_ethernet(dst_mac, data))

    def __eq__(self, other: Any) -> bool:
        """Determines which interfaces are equal"""
        return self is other

    def __hash__(self) -> int:
        """hash of the interface"""
        return hash(id(self))

    def __str__(self) -> str:
        """A shorter string representation of the CableNetworkInterface"""
        mac = f"\n{self.mac}" if not self.mac.is_no_mac() else ""
        return f"{self.name}: {mac}" + ('\n' + repr(self.ip) if self.has_ip() else '')

    def __repr__(self) -> str:
        """The string representation of the CableNetworkInterface"""
        return f"CableNetworkInterface(name={self.name}, mac={self.mac}, ip={self.ip})"

    @classmethod
    def from_dict_load(cls, dict_: Dict) -> CableNetworkInterface:
        """
        Loads a new interface from a dict
        :param dict_:
        :return:
        """
        loaded = cls(
            mac=dict_["mac"],
            ip=dict_["ip"],
            name=dict_["name"],
            type_=dict_["type_"],
            mtu=dict_.get("mtu", PROTOCOLS.ETHERNET.MTU),
        )

        return loaded
