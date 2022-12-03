from __future__ import annotations

from typing import Optional, Dict, Union, Any, TYPE_CHECKING

from NetSym.address.ip_address import IPAddress
from NetSym.address.mac_address import MACAddress
from NetSym.computing.internals.network_interfaces.base_interface import BaseInterface
from NetSym.consts import INTERFACES, PROTOCOLS, T_Color

if TYPE_CHECKING:
    from NetSym.computing.connections.connection import ConnectionSide


class Interface(BaseInterface):
    """
    This class represents a computer net interface.
    It can send and receive packets.
    It contains methods that provide abstraction for sending many types of packets.

    An interface can be either connected or disconnected to a `ConnectionSide` object, which enables it to move its packets
    down the connection_side further.
    """
    def __init__(self,
                 mac: Optional[Union[str, MACAddress]] = None,
                 ip: Optional[Union[str, IPAddress]] = None,
                 name: Optional[str] = None,
                 connection_side: Optional[ConnectionSide] = None,
                 display_color: T_Color = INTERFACES.COLOR,
                 type_: str = INTERFACES.TYPE.ETHERNET,
                 mtu: int = PROTOCOLS.ETHERNET.MTU) -> None:
        """
        Initiates the Interface instance with addresses (mac and possibly ip), the operating system, and a name.
        :param mac: a string MAC address ('aa:bb:cc:11:22:76' for example)
        :param ip: a string ip address ('10.3.252.5/24' for example)
        """
        super(Interface, self).__init__(mac, ip, name, connection_side, display_color, type_, mtu)

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

    def __str__(self) -> str:
        """A shorter string representation of the Interface"""
        mac = f"\n{self.mac}" if not self.mac.is_no_mac() else ""
        return f"{self.name}: {mac}" + ('\n' + repr(self.ip) if self.has_ip() else '')

    def __repr__(self) -> str:
        """The string representation of the Interface"""
        return f"Interface(name={self.name}, mac={self.mac}, ip={self.ip})"

    @classmethod
    def from_dict_load(cls, dict_: Dict) -> Interface:
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
