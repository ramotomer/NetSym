from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, cast

import scapy

from NetSym.gui.tech.packets.wireless_packet_graphics import WirelessPacketGraphics
from NetSym.packets.packet import Packet

if TYPE_CHECKING:
    from NetSym.computing.connections.wireless_connection import WirelessConnection
    from NetSym.computing.internals.network_interfaces.wireless_network_interface import WirelessNetworkInterface
    from NetSym.gui.abstracts.graphics_object import GraphicsObject


class WirelessPacket(Packet):
    """
    just like a regular packet but it is sent over a WirelessConnection rather than a regular connection.
    """
    graphics: Optional[WirelessPacketGraphics]

    def __init__(self, data: scapy.packet.Packet) -> None:
        super(WirelessPacket, self).__init__(data)

    def init_graphics(self, wireless_connection: WirelessConnection, sending_interface: WirelessNetworkInterface) -> List[GraphicsObject]:
        """
        Starts the display of the object. (Creating the graphics object)
        """
        self.graphics = WirelessPacketGraphics(
            sending_interface.get_graphics().x, sending_interface.get_graphics().y,
            self.deepest_layer(), wireless_connection
        )
        return [self.graphics]

    def get_graphics(self) -> WirelessPacketGraphics:
        """
        Get the PacketGraphics object of this packet, If it is not yet initialized - raise
        """
        return cast("WirelessPacketGraphics", super(WirelessPacket, self).get_graphics())

    def __repr__(self) -> str:
        """The string representation of the packet"""
        return f"WirelessPacket({self.data!r})"
