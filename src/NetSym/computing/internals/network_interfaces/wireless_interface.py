from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Dict, Union

from NetSym.address.ip_address import IPAddress
from NetSym.address.mac_address import MACAddress
from NetSym.computing.internals.network_interfaces.base_interface import BaseInterface
from NetSym.consts import T_Color, INTERFACES
from NetSym.exceptions import *
from NetSym.gui.tech.wireless_interface_graphics import WirelessInterfaceGraphics

if TYPE_CHECKING:
    from NetSym.computing.connections.frequency import Frequency, FrequencyConnectionSide


class WirelessInterface(BaseInterface):
    """
    This class represents a computer net interface.
    It can send and receive packets.
    It contains methods that provide abstraction for sending many types of packets.

    An interface can be either connected or disconnected to a `ConnectionSide` object, which enables it to move its packets
    down the connection further.
    """
    GRAPHICS_CLASS = WirelessInterfaceGraphics

    connection:      Frequency
    connection_side: Optional[FrequencyConnectionSide]

    def __init__(self,
                 mac:           Optional[Union[MACAddress, str]] = None,
                 ip:            Optional[IPAddress]              = None,
                 name:          Optional[str]                    = None,
                 frequency:     Optional[Frequency]              = None,
                 display_color: T_Color                          = INTERFACES.COLOR) -> None:
        """
        Initiates the Interface instance with addresses (mac and possibly ip), the operating system, and a name.
        :param mac: a string MAC address ('aa:bb:cc:11:22:76' for example)
        :param ip: a string ip address ('10.3.252.5/24' for example)
        """
        super(WirelessInterface, self).__init__(mac, ip, name, display_color=display_color, type_=INTERFACES.TYPE.WIFI)

        self.connection_side = frequency.get_side(self) if frequency is not None else None
        self.frequency       = frequency.frequency      if frequency is not None else None

    @property
    def frequency_object(self) -> Frequency:
        if self.connection_side is None or self.frequency is None:
            raise InterfaceNotConnectedError("No frequency object to get!")

        return self.connection

    def is_connected(self) -> bool:
        return self.frequency is not None and self.connection_side is not None

    def connect(self, frequency: Frequency) -> None:
        """
        Connects this interface to a frequency, return the `Frequency` object.
        :param frequency:
        :return: The `Connection` object.
        """
        if self.is_connected():
            self.disconnect()

        self.connection_side = frequency.get_side(self) if frequency is not None else None
        self.frequency = frequency.frequency if frequency is not None else None

    def disconnect(self) -> None:
        """
        Disconnect an interface from its `Frequency`.
        :return: None
        """
        if not self.is_connected():
            raise InterfaceNotConnectedError("Cannot disconnect an interface that is not connected!")
        self.frequency_object.remove_side(self.connection_side)
        self.connection_side = None
        self.frequency = None

    def generate_view_text(self) -> str:
        """
        Generates the text for the side view of the interface
        :return: `str`
        """
        return super(WirelessInterface, self).generate_view_text() + f"\nfrequency: {self.frequency}"

    @classmethod
    def from_dict_load(cls, dict_: Dict) -> WirelessInterface:
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
        # TODO: make it so configured frequencies are also saved to files

        return loaded

    def __repr__(self) -> str:
        return f"WirelessInterface(name={self.name}, mac='{self.mac.string_mac}', ip={self.ip})"
