from typing import cast

from NetSym.address.ip_address import IPAddress
from NetSym.address.mac_address import MACAddress
from NetSym.computing.connections.loopback_connection import LoopbackConnection
from NetSym.computing.internals.network_interfaces.interface import Interface


class LoopbackInterface(Interface):
    """
    This is just a regular interface - only with a `LoopbackConnection` as a connection
    """
    def __init__(self) -> None:
        """Constructor for a loopback interface"""
        super(LoopbackInterface, self).__init__(MACAddress.no_mac(), IPAddress.loopback(), "loopback", LoopbackConnection().get_side())

    @property
    def connection(self) -> LoopbackConnection:
        return cast("LoopbackConnection", super(LoopbackInterface, self).connection)

    def is_connected(self) -> bool:
        return True
