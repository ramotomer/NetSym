from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional, Sequence

from NetSym.computing.connections.connection import Connection, SentPacket, BaseConnectionSide
from NetSym.consts import CONNECTIONS, PACKET
from NetSym.exceptions import *
from NetSym.gui.main_loop import MainLoop
from NetSym.gui.tech.cable_connection_graphics import CableConnectionGraphics

if TYPE_CHECKING:
    from NetSym.gui.abstracts.graphics_object import GraphicsObject
    from NetSym.packets.packet import Packet
    from NetSym.gui.tech.packet_graphics import PacketGraphics
    from NetSym.gui.tech.computer_graphics import ComputerGraphics


@dataclass
class CableSentPacket(SentPacket):
    """
    a packet that is currently being sent through the connection.
    """
    direction: str = PACKET.DIRECTION.RIGHT


class CableConnection(Connection):
    """
    This class represents a cable or any connection between two `CableNetworkInterface` objects.
    It allows for packets to move in both sides, To be sent and received.

    Each packet that is sent takes some time through the cable, that time is
    defined in the `speed` and `length` properties. They can be different for each connection.
    There is a default value for the speed, and the length is defined by the graphics object and the locations of the
    connected computers. These properties of the `CableConnection` class is mainly so the packet sending could be
    displayed nicely.

    The `CableConnection` object keeps references to its two `CableConnectionSide` objects. These are nice interfaces for
        the `CableNetworkInterface` object to talk to its connection.
    """
    def __init__(self,
                 length: float = CONNECTIONS.DEFAULT_LENGTH,
                 speed: float = CONNECTIONS.DEFAULT_SPEED,
                 packet_loss: float = 0,
                 latency: float = 0,
                 ) -> None:
        """
        Initiates a CableConnection object.

        `self.sent_packets` is the list of packets that are currently being sent through the connection.

        :param length: The length of the cable connection (in pixels)
        :param speed: The speed of the connection (in pixels per second)
        """
        self.speed = speed
        self.initial_length = length
        self.sent_packets: List[CableSentPacket] = []  # represents the packets that are currently being sent through the connection

        self.right_side, self.left_side = CableConnectionSide(self), CableConnectionSide(self)

        self.last_packet_motion = MainLoop.get_time()

        self.graphics: Optional[CableConnectionGraphics] = None

        self.is_blocked = False

        self.packet_loss = packet_loss
        self.latency = latency

    @property
    def length(self) -> float:
        """The length of the connection in pixels"""
        if self.graphics is None:
            raise SomethingWentTerriblyWrongError("Graphics was not yet initiated!!!")
        return self.graphics.length

    @property
    def deliver_time(self) -> float:
        """The time in seconds a packet takes to go through the connection"""
        return self.length / self.speed

    def init_graphics(self, start_computer: ComputerGraphics, end_computer: ComputerGraphics) -> List[GraphicsObject]:
        """
        Adds the `GraphicObject` of this class and gives it the parameters it requires.

        :param start_computer: The `GraphicsObject` of the computer which is the start of the connection
        :param end_computer: The `GraphicsObject` of the computer which is the end of the connection
        :return: None
        """
        graphics = CableConnectionGraphics(self, start_computer, end_computer, self.packet_loss)
        self.graphics = graphics
        return [graphics]

    def get_graphics(self) -> CableConnectionGraphics:
        """
        Return the graphics object or raise if the `init_graphics` was not yet called
        """
        if self.graphics is None:
            raise GraphicsObjectNotYetInitialized(f"self: {self}, self.graphics: {self.graphics}")

        return self.graphics

    def get_sides(self) -> Sequence[CableConnectionSide]:
        """Returns the two sides of the connection as a tuple (they are `CableConnectionSide` objects)"""
        return self.left_side, self.right_side

    def mark_as_blocked(self) -> None:
        """
        Marks the connection as blocked!
        Makes sure that one of the connection sides is really blocked.
        :return: None
        """
        if any(side.is_blocked for side in self.get_sides()):
            self.is_blocked = True

    def mark_as_unblocked(self) -> None:
        """
        Marks the connection as an unblocked connection.
        Makes sure first that both sides are actually unblocked. (That causes bugs!!)
        :return: None
        """
        if all(not side.is_blocked for side in self.get_sides()):
            self.is_blocked = False

    def _add_packet(self, packet: Packet, direction: str) -> None:
        """
        Add a packet that was sent on one of the `CableConnectionSide`-s to the `self.sent_packets` list.
        This method starts the motion of the packet through the connection.

        :direction: the direction the packet is going to (PACKET.DIRECTION.RIGHT or PACKET.DIRECTION.LEFT)
        """
        self.sent_packets.append(
            CableSentPacket(
                packet         =packet,
                sending_time   =MainLoop.get_time(),
                will_be_dropped=(random.random() < self.packet_loss),
                will_be_delayed=(random.random() < self.latency),
                direction      =direction,
            )
        )

    def _receive_on_sides_if_reached_destination(self, sent_packet: CableSentPacket) -> None:
        """
        Adds the packet to its appropriate destination side's `received_packets` list.
        This is called to check when the packet finished its route through this connection and is ready to be received at the
        connected `CableNetworkInterface`.
        """
        if sent_packet.packet.get_graphics().progress < 1:
            return  # did not reach...

        sent_packet.packet.get_graphics().unregister()

        if sent_packet.direction == PACKET.DIRECTION.RIGHT:
            self.right_side.get_packet_from_connection(sent_packet)
        elif sent_packet.direction == PACKET.DIRECTION.LEFT:
            self.left_side.get_packet_from_connection(sent_packet)
        else:
            raise WrongUsageError('The packet can only go left or right!')

        self.sent_packets.remove(sent_packet)

    def _send_packets_from_side(self, side: CableConnectionSide) -> List[PacketGraphics]:
        """
        Takes all of the packets that are waiting to be sent on one CableConnectionSide and sends them down the main connection.
        :param side: a `CableConnectionSide` object.
        :return: None
        """
        if side not in self.get_sides():
            raise NoSuchConnectionSideError()

        new_graphics_to_register = []
        direction = PACKET.DIRECTION.LEFT if side is self.right_side else PACKET.DIRECTION.RIGHT
        if side.is_sending():
            for packet in side.pop_packets_to_send():
                self._add_packet(packet, direction)
                new_graphics_to_register.extend(packet.init_graphics(self.graphics, direction))
        return new_graphics_to_register

    def _update_packet(self, sent_packet: CableSentPacket) -> None:
        """
        Receives a CableSentPacket object and updates its progress on the connection.
        If the packet has reached the end of the connection, make it be received at the appropriate CableConnectionSide
        :param sent_packet: a `CableSentPacket`
        :return: None
        """
        sent_packet.packet.get_graphics().progress += \
            (MainLoop.get_time_since(sent_packet.last_update_time) / self.deliver_time) * sent_packet.packet.get_graphics().speed
        sent_packet.last_update_time = MainLoop.get_time()

    def _is_lucky_packet(self, sent_packet: SentPacket) -> bool:
        """
        Checks whether a certain event should happen to a packet
        The chances go up as the packet moves further and further down the connection
        """
        return bool(sent_packet.packet.get_graphics().progress >= (random.random() + 0.3))

    def __repr__(self) -> str:
        """The ip_layer representation of the connection"""
        return f"CableConnection({self.length}, {self.speed})"


class CableConnectionSide(BaseConnectionSide):
    """
    This represents one side of a given `CableConnection` object.
    This is the API that the `CableNetworkInterface` object sees.
    Each CableConnection object holds two of these, one for each of its sides (Duh).

    The `CableConnectionSide` has a list of packets the user sent, but were not yet picked up by the main `CableConnection`.
    It also has a list of packets that reached this side but were not yet picked up by the appropriate connected
        `CableNetworkInterface` object.
    """
    connection: CableConnection

    def __init__(self, main_connection: CableConnection) -> None:
        super(CableConnectionSide, self).__init__(main_connection)
        self.is_blocked = False

    def mark_as_blocked(self) -> None:
        """
        Marks the connection as being a blocked connection (paints it a different color)
        :return: None
        """
        self.is_blocked = True
        self.connection.mark_as_blocked()

    def mark_as_unblocked(self) -> None:
        """
        Marks the connection as a regular (unblocked) connection.
        :return: None
        """
        self.is_blocked = False
        self.connection.mark_as_unblocked()
