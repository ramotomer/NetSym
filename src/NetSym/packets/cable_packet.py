from __future__ import annotations

from typing import TYPE_CHECKING, List, cast

from NetSym.gui.tech.packets.cable_packet_graphics import CablePacketGraphics
from NetSym.packets.packet import Packet

if TYPE_CHECKING:
    from NetSym.gui.tech.cable_connection_graphics import CableConnectionGraphics
    from NetSym.gui.abstracts.graphics_object import GraphicsObject


class CablePacket(Packet):
    """
    The container for all sendable packets.
    The class contains the Ethernet layer which is turn contains the IP layer
    and so on. The Packet class allows us to recursively check if a layer is in
    the packet and to draw the packet on the screen as one complete object.
    """
    def init_graphics(self, connection_graphics: CableConnectionGraphics, direction: str) -> List[GraphicsObject]:
        """
        This signals the packet that it starts to be sent and that where it
        is sent from and to (Graphically).
        :param connection_graphics: the graphics_object of the connection the packet is currently in
        :param direction: The direction that the packet is going in the connection.
        """
        self.graphics = CablePacketGraphics(self.deepest_layer(), connection_graphics, direction)
        return [self.graphics]

    def get_graphics(self) -> CablePacketGraphics:
        """
        Get the PacketGraphics object of this packet, If it is not yet initialized - raise
        """
        return cast("CablePacketGraphics", super(CablePacket, self).get_graphics())

    def __repr__(self) -> str:
        """The string representation of the packet"""
        return f"CablePacket({self.data!r})"
