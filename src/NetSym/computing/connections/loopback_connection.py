from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List, cast

from NetSym.computing.connections.cable_connection import CableConnection
from NetSym.consts import CONNECTIONS
from NetSym.gui.tech.loopback_connection_graphics import LoopbackConnectionGraphics
from NetSym.packets.cable_packet import CablePacket

if TYPE_CHECKING:
    from NetSym.computing.connections.cable_connection import CableSentPacket
    from NetSym.computing.connections.cable_connection import CableConnectionSide
    from NetSym.gui.tech.computer_graphics import ComputerGraphics
    from NetSym.gui.abstracts.graphics_object import GraphicsObject


class LoopbackConnection(CableConnection):
    """
    This class represents a connection of a loopback interface to itself. It enables its graphical is_showing.
    It only has a left_side, no right_side.
    """
    # TODO: IMPROVE: think... Should this inherit from CableConnection? Or directly from Connection?
    def __init__(self, radius: float = CONNECTIONS.LOOPBACK.RADIUS) -> None:
        """
        Initiates the circular connection
        :param radius: the radius of circle.
        """
        super(LoopbackConnection, self).__init__(length=CONNECTIONS.DEFAULT_LENGTH, speed=CONNECTIONS.LOOPBACK.SPEED)
        self.radius = radius

    def get_side(self) -> CableConnectionSide:
        """Returns the only side of the connection"""
        return self.left_side

    def init_graphics(self, computer_graphics: ComputerGraphics, end_computer: Optional[ComputerGraphics] = None) -> List[GraphicsObject]:
        """Starts the graphical appearance of the connection"""
        self.graphics = LoopbackConnectionGraphics(self, computer_graphics, self.radius)
        return [cast("GraphicsObject", self.graphics)]

    def get_graphics(self) -> LoopbackConnectionGraphics:
        return cast("LoopbackConnectionGraphics", super(LoopbackConnection, self).get_graphics())

    def _add_packet(self, packet: CablePacket, direction: str) -> None:
        """performs the super-method of `add_packet` but also makes sure the connection is visible."""
        super(LoopbackConnection, self)._add_packet(packet, direction)
        self.get_graphics().show()

    def _receive_on_sides_if_reached_destination(self, sent_packet: CableSentPacket) -> None:
        """
        performs the super-method of `reach_destination` but also checks if the connection should disappear.
        All of the packets are received on the left side, all of them will also be sent on it.
        """
        if sent_packet.packet.get_graphics().progress < 1:
            return  # did not reach...

        sent_packet.packet.get_graphics().unregister()
        self.left_side.get_packet_from_connection(sent_packet)  # the direction does not matter
        self.sent_packets.remove(sent_packet)

        if not self.sent_packets:
            self.get_graphics().hide()

    def __repr__(self) -> str:
        return "LoopbackConnection"
