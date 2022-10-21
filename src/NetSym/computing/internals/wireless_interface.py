from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Callable, Dict

from NetSym.address.ip_address import IPAddress
from NetSym.address.mac_address import MACAddress
from NetSym.computing.internals.interface import Interface
from NetSym.consts import T_Color, INTERFACES
from NetSym.exceptions import *

if TYPE_CHECKING:
    from NetSym.packets.packet import Packet
    from NetSym.computing.internals.frequency import Frequency


class WirelessInterface(Interface):
    """
    This class represents a computer net interface.
    It can send and receive packets.
    It contains methods that provide abstraction for sending many types of packets.

    An interface can be either connected or disconnected to a `ConnectionSide` object, which enables it to move its packets
    down the connection further.
    """
    def __init__(self,
                 mac:           Optional[MACAddress] = None,
                 ip:            Optional[IPAddress]  = None,
                 name:          Optional[str]        = None,
                 frequency:     Optional[Frequency]  = None,
                 display_color: T_Color              = INTERFACES.COLOR) -> None:
        """
        Initiates the Interface instance with addresses (mac and possibly ip), the operating system, and a name.
        :param mac: a string MAC address ('aa:bb:cc:11:22:76' for example)
        :param ip: a string ip address ('10.3.252.5/24' for example)
        """
        super(WirelessInterface, self).__init__(mac, ip, name, display_color=display_color, type_=INTERFACES.TYPE.WIFI)

        self.connection = frequency.get_side(self) if frequency is not None else None
        self.frequency = frequency.frequency if frequency is not None else None

    @property
    def frequency_object(self) -> Frequency:
        if self.connection is None or self.frequency is None:
            raise InterfaceNotConnectedError("No frequency object to get!")

        return self.connection.connection

    @property
    def connection_length(self) -> Optional[float]:
        """
        The length of the connection this `Interface` is connected to. (The time a packet takes to go through it in seconds)
        :return: a number of seconds.
        """
        if not self.is_connected():
            return None
        return self.connection.connection.deliver_time

    def is_connected(self) -> bool:
        return self.frequency is not None and self.connection is not None

    def connect(self, frequency: Frequency) -> None:
        """
        Connects this interface to a frequency, return the `Frequency` object.
        :param frequency:
        :return: The `Connection` object.
        """
        if self.is_connected():
            self.disconnect()

        self.connection = frequency.get_side(self) if frequency is not None else None
        self.frequency = frequency.frequency if frequency is not None else None

    def disconnect(self) -> None:
        """
        Disconnect an interface from its `Frequency`.
        :return: None
        """
        if not self.is_connected():
            raise InterfaceNotConnectedError("Cannot disconnect an interface that is not connected!")
        self.frequency_object.remove_side(self.connection)
        self.connection = None
        self.frequency = None

    def block(self, accept: Optional[Callable[[Packet], bool]] = None) -> None:
        """
        Blocks the connection and does not receive packets from it anymore.
        It only accepts packets that contain the `accept` layer (for example "STP")
        if blocked, does nothing (updates the 'accept')
        :return: None
        """
        raise NotImplementedError()

    def unblock(self) -> None:
        """
        Releases the blocking of the connection and allows it to receive packets again.
        if not blocked, does nothing...
        :return: None
        """
        raise NotImplementedError()

    def toggle_block(self, accept: Optional[Callable[[Packet], bool]] = None) -> None:
        """
        Toggles between block() and unblock()
        :param accept:
        :return:
        """
        raise NotImplementedError()

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
