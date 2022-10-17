from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List

from NetSym.computing.connection import Connection
from NetSym.consts import CONNECTIONS
from NetSym.gui.main_window import MainLoop
from NetSym.gui.tech.loopback_connection_graphics import LoopbackConnectionGraphics

if TYPE_CHECKING:
    from NetSym.packets.packet import Packet
    from NetSym.computing.connection import SentPacket
    from NetSym.computing.connection import ConnectionSide
    from NetSym.gui.tech.computer_graphics import ComputerGraphics


class LoopbackConnection(Connection):
    """
    This class represents a connection of a loopback interface to itself. It enables its graphical is_showing.
    It only has a left_side, no right_side.
    """
    def __init__(self, radius: float = CONNECTIONS.LOOPBACK.RADIUS) -> None:
        """
        Initiates the circular connection
        :param radius: the radius of circle.
        """
        super(LoopbackConnection, self).__init__(length=CONNECTIONS.DEFAULT_LENGTH, speed=CONNECTIONS.LOOPBACK.SPEED)
        self.radius = radius

    def get_side(self) -> ConnectionSide:
        """Returns the only side of the connection"""
        return self.left_side

    def init_graphics(self, computer_graphics: ComputerGraphics, end_computer: Optional[ComputerGraphics] = None) -> List[LoopbackConnectionGraphics]:
        """Starts the graphical appearance of the connection"""
        self.graphics = LoopbackConnectionGraphics(self, computer_graphics, self.radius)
        return [self.graphics]

    def add_packet(self, packet: Packet, direction: str) -> None:
        """performs the super-method of `add_packet` but also makes sure the connection is visible."""
        super(LoopbackConnection, self).add_packet(packet, direction)
        self.graphics.show()

    def reach_destination(self, sent_packet: SentPacket) -> None:
        """
        performs the super-method of `reach_destination` but also checks if the connection should disappear.
        All of the packets are received on the left side, all of them will also be sent on it.
        """
        MainLoop.instance.unregister_graphics_object(sent_packet.packet.graphics)
        self.left_side.packets_to_receive.append(sent_packet.packet)  # the direction does not matter
        self.sent_packets.remove(sent_packet)

        if not self.sent_packets:
            self.graphics.hide()

    def __repr__(self) -> str:
        return "LoopbackConnection"
