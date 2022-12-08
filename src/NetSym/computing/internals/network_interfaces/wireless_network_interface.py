from __future__ import annotations

from typing import Optional, Dict, Union, TYPE_CHECKING

import scapy

from NetSym.address.ip_address import IPAddress
from NetSym.address.mac_address import MACAddress
from NetSym.computing.connections.wireless_connection import WirelessConnection, WirelessConnectionSide
from NetSym.computing.internals.network_interfaces.network_interface import NetworkInterface
from NetSym.consts import T_Color, INTERFACES
from NetSym.exceptions import *
from NetSym.gui.tech.network_interfaces.wireless_network_interface_graphics import WirelessNetworkInterfaceGraphics
from NetSym.packets.wireless_packet import WirelessPacket
from NetSym.usefuls.funcs import raise_on_none

if TYPE_CHECKING:
    from NetSym.gui.tech.network_interfaces.network_interface_graphics import NetworkInterfaceGraphics
    from NetSym.gui.tech.computer_graphics import ComputerGraphics


class WirelessNetworkInterface(NetworkInterface):
    """
    This class represents a computer net interface.
    It can send and receive packets.
    It contains methods that provide abstraction for sending many types of packets.

    An interface can be either connected or disconnected to a `CableConnectionSide` object, which enables it to move its packets
    down the connection further.
    """
    __connection:      Optional[WirelessConnection]
    __connection_side: Optional[WirelessConnectionSide]

    frequency:         Optional[float]
    graphics:          Optional[WirelessNetworkInterfaceGraphics]

    def __init__(self,
                 mac:           Optional[Union[MACAddress, str]] = None,
                 ip:            Optional[IPAddress]              = None,
                 name:          Optional[str]                    = None,
                 connection:    Optional[WirelessConnection]              = None,
                 display_color: T_Color                          = INTERFACES.COLOR) -> None:
        """
        Initiates the CableNetworkInterface instance with addresses (mac and possibly ip), the operating system, and a name.
        :param mac: a string MAC address ('aa:bb:cc:11:22:76' for example)
        :param ip: a string ip address ('10.3.252.5/24' for example)
        """
        super(WirelessNetworkInterface, self).__init__(mac, ip, name, display_color=display_color, type_=INTERFACES.TYPE.WIFI)

        self.connection_side = connection.get_side(self) if connection is not None else None
        self.frequency       = connection.frequency      if connection is not None else None

    @property
    def connection(self) -> WirelessConnection:
        if self.__connection is None:
            raise NoSuchConnectionError(f"self: {self}, self.__connection: {self.__connection}")
        return self.__connection

    @property
    def connection_side(self) -> Optional[WirelessConnectionSide]:
        return self.__connection_side

    @connection_side.setter
    def connection_side(self, new_connection_side: Optional[WirelessConnectionSide]) -> None:
        if (new_connection_side is not None) and (not isinstance(new_connection_side, WirelessConnectionSide)):
            raise WrongUsageError(f"Do not set the `connection_side` of a `WirelessNetworkInterface` with something that is not a "
                                  f"`WirelessConnectionSide` You inserted {new_connection_side!r} which is a {type(new_connection_side)}...")

        self.__connection = None
        self.__connection_side = new_connection_side

        if new_connection_side is not None:
            self.__connection = new_connection_side.connection

    def init_graphics(self, parent_computer: ComputerGraphics, x: Optional[float] = None, y: Optional[float] = None) -> NetworkInterfaceGraphics:
        """
        Initiates the CableNetworkInterfaceGraphics object of this interface
        """
        if (x is None) or (y is None):
            raise ThisValueShouldNeverBeNone

        self.graphics = WirelessNetworkInterfaceGraphics(x, y, self, parent_computer)
        return self.graphics

    def is_connected(self) -> bool:
        return (self.frequency is not None) and (self.connection_side is not None)

    def connect(self, wireless_connection: WirelessConnection) -> None:
        """
        Connects this interface to a `WirelessConnection`, return the `WirelessConnection` object.
        :param wireless_connection:
        :return: The `CableConnection` object.
        """
        if self.is_connected():
            self.disconnect()

        self.connection_side = wireless_connection.get_side(self) if wireless_connection is not None else None
        self.frequency       = wireless_connection.frequency      if wireless_connection is not None else None

    def disconnect(self) -> None:
        """
        Disconnect an interface from its `WirelessConnection`.
        :return: None
        """
        if not self.is_connected():
            raise InterfaceNotConnectedError("Cannot disconnect an interface that is not connected!")

        self.connection.remove_side(raise_on_none(self.connection_side))
        self.connection_side = None
        self.frequency = None

    def ethernet_wrap(self, dst_mac: MACAddress, data: scapy.packet.Packet) -> WirelessPacket:
        """
        Takes in ip_layer (string, a `Protocol` object...) and wraps it as an `Ethernet` packet ready to be sent.
        :param data: any ip_layer to put in the ethernet packet (ARP, IP, str, more Ethernet, whatever you want, only
            the receiver computer should know whats coming and how to handle it...)
        :param dst_mac: a `MACAddress` object of the destination of the packet.
        :return: the ready `WirelessPacket` object
        """
        return WirelessPacket(self.get_with_ethernet(dst_mac, data))

    def generate_view_text(self) -> str:
        """
        Generates the text for the side view of the interface
        :return: `str`
        """
        return super(WirelessNetworkInterface, self).generate_view_text() + f"\nfrequency: {self.frequency}"

    @classmethod
    def from_dict_load(cls, dict_: Dict) -> WirelessNetworkInterface:
        """
        Loads a new interface from a dict
        :param dict_:
        :return:
        """
        loaded = cls(
            mac=dict_["mac"],
            ip=dict_["ip"],
            name=dict_["name"],
        )
        # TODO: make it so configured wireless_connections are also saved to files

        return loaded

    def __repr__(self) -> str:
        return f"WirelessNetworkInterface(name={self.name}, mac='{self.mac.string_mac}', ip={self.ip})"
