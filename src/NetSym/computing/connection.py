from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Tuple, Optional

from NetSym.consts import CONNECTIONS, PACKET, T_Time
from NetSym.exceptions import *
from NetSym.gui.abstracts.animation_graphics import AnimationGraphics
from NetSym.gui.main_loop import MainLoop
from NetSym.gui.tech.connection_graphics import ConnectionGraphics

if TYPE_CHECKING:
    from NetSym.gui.abstracts.graphics_object import GraphicsObject
    from NetSym.packets.packet import Packet
    from NetSym.gui.tech.packet_graphics import PacketGraphics
    from NetSym.gui.tech.computer_graphics import ComputerGraphics


@dataclass
class SentPacket:
    """
    a packet that is currently being sent through the connection.
    """
    packet:           Packet
    sending_time:     T_Time
    direction:        str
    will_be_dropped:  bool
    will_be_delayed:  bool

    last_update_time: T_Time = field(default_factory=MainLoop.get_time)


class Connection:
    """
    This class represents a cable or any connection between two `Interface` objects.
    It allows for packets to move in both sides, To be sent and received.

    Each packet that is sent takes some time through the cable, that time is
    defined in the `speed` and `length` properties. They can be different for each connection.
    There is a default value for the speed, and the length is defined by the graphics object and the locations of the
    connected computers. These properties of the `Connection` class is mainly so the packet sending could be
    displayed nicely.

    The `Connection` object keeps references to its two `ConnectionSide` objects. These are nice interfaces for
        the `Interface` object to talk to its connection.
    """
    def __init__(self,
                 length: float = CONNECTIONS.DEFAULT_LENGTH,
                 speed: float = CONNECTIONS.DEFAULT_SPEED,
                 packet_loss: float = 0,
                 latency: float = 0,
                 ) -> None:
        """
        Initiates a Connection object.

        `self.sent_packets` is the list of packets that are currently being sent through the connection.

        :param length: The length of the cable connection (in pixels)
        :param speed: The speed of the connection (in pixels per second)
        """
        self.speed = speed
        self.initial_length = length
        self.sent_packets: List[SentPacket] = []  # represents the packets that are currently being sent through the connection

        self.right_side, self.left_side = ConnectionSide(self), ConnectionSide(self)

        self.last_packet_motion = MainLoop.get_time()

        self.graphics: Optional[ConnectionGraphics] = None

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
        graphics = ConnectionGraphics(self, start_computer, end_computer, self.packet_loss)
        self.graphics = graphics
        return [graphics]

    def get_graphics(self) -> ConnectionGraphics:
        """
        Return the graphics object or raise if the `init_graphics` was not yet called
        """
        if self.graphics is None:
            raise GraphicsObjectNotYetInitialized(f"self: {self}, self.graphics: {self.graphics}")

        return self.graphics

    def get_sides(self) -> Tuple[ConnectionSide, ConnectionSide]:
        """Returns the two sides of the connection as a tuple (they are `ConnectionSide` objects)"""
        return self.left_side, self.right_side

    def set_speed(self, new_speed: float) -> None:
        """Sets the speed of the connection"""
        if new_speed <= 0:
            raise ConnectionsError("A connection cannot have negative speed!")
        self.speed = new_speed

    def set_pl(self, new_pl: float) -> None:
        """Sets the PL amount of this connection"""
        if not (0 <= new_pl <= 1):
            raise ConnectionsError(f"A connection cannot have this PL amount!!! {new_pl}")

        self.packet_loss = new_pl

    def set_latency(self, new_latency: float) -> None:
        """
        Set amount of latency the connection has
        """
        if not (0 <= new_latency <= 1):
            raise ConnectionsError(f"A connection cannot have this PL amount!!! {new_latency}")

        self.latency = new_latency

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

    def add_packet(self, packet: Packet, direction: str) -> None:
        """
        Add a packet that was sent on one of the `ConnectionSide`-s to the `self.sent_packets` list.
        This method starts the motion of the packet through the connection.

        :direction: the direction the packet is going to (PACKET.DIRECTION.RIGHT or PACKET.DIRECTION.LEFT)
        """
        self.sent_packets.append(
            SentPacket(
                packet,
                MainLoop.get_time(),
                direction,
                will_be_dropped=(random.random() < self.packet_loss),
                will_be_delayed=(random.random() < self.latency),
            )
        )

    def reach_destination(self, sent_packet: SentPacket) -> None:
        """
        Adds the packet to its appropriate destination side's `received_packets` list.
        This is called when the packet finished its route through this connection and is ready to be received at the
        connected `Interface`.
        """
        packet, direction = sent_packet.packet, sent_packet.direction
        packet.get_graphics().unregister()

        if direction == PACKET.DIRECTION.RIGHT:
            self.right_side.packets_to_receive.append(packet)
        elif direction == PACKET.DIRECTION.LEFT:
            self.left_side.packets_to_receive.append(packet)
        else:
            raise WrongUsageError('The packet can only go left or right!')

        self.sent_packets.remove(sent_packet)

    def _send_packets_from_side(self, side: ConnectionSide) -> List[PacketGraphics]:
        """
        Takes all of the packets that are waiting to be sent on one ConnectionSide and sends them down the main connection.
        :param side: a `ConnectionSide` object.
        :return: None
        """
        if side not in self.get_sides():
            raise NoSuchConnectionSideError()

        new_graphics_to_register = []
        direction = PACKET.DIRECTION.LEFT if side is self.right_side else PACKET.DIRECTION.RIGHT
        if side.is_sending():
            for packet in side.packets_to_send:
                self.add_packet(packet, direction)
                new_graphics_to_register.extend(packet.init_graphics(self.graphics, direction))
            side.packets_to_send.clear()
        return new_graphics_to_register

    def _update_packet(self, sent_packet: SentPacket) -> None:
        """
        Receives a SentPacket object and updates its progress on the connection.
        If the packet has reached the end of the connection, make it be received at the appropriate ConnectionSide
        :param sent_packet: a `SentPacket`
        :return: None
        """
        sent_packet.packet.get_graphics().progress += \
            (MainLoop.get_time_since(sent_packet.last_update_time) / self.deliver_time) * sent_packet.packet.get_graphics().speed
        sent_packet.last_update_time = MainLoop.get_time()

        if sent_packet.packet.get_graphics().progress >= 1:
            self.reach_destination(sent_packet)

    def move_packets(self, main_loop: MainLoop) -> None:
        """
        This method is inserted into the main loop of the simulation when this `Connection` object is initiated.
        The packets in the connection should always be moving. (unless paused)
        This method sends new packets from the `ConnectionSide` object, updates the time they have been in the cable, and
            removes them if they reached the end.
        """
        for side in self.get_sides():
            new_packet_graphics_objects = self._send_packets_from_side(side)
            main_loop.register_graphics_object(new_packet_graphics_objects)

        for sent_packet in self.sent_packets[:]:  # we copy the list because we alter it during the run
            self._update_packet(sent_packet)

        main_loop.register_graphics_object(self._drop_predetermined_dropped_packets())
        main_loop.register_graphics_object(self._delay_predetermined_delayed_packets())

    def _drop_predetermined_dropped_packets(self) -> List[AnimationGraphics]:
        """
        Goes through the packets that are being sent, When they reach the middle of the connection, check if they need
        to be dropped (by PL) if so, remove them from the list, and do the animation.
        """
        animations_to_register = []
        for sent_packet in self.sent_packets[:]:
            if sent_packet.will_be_dropped and sent_packet.packet.get_graphics().progress >= (random.random() + 0.3):
                self.sent_packets.remove(sent_packet)
                sent_packet.packet.get_graphics().unregister()
                animations_to_register.append(sent_packet.packet.get_graphics().get_drop_animation())
        return animations_to_register

    def _delay_predetermined_delayed_packets(self) -> List[AnimationGraphics]:
        """
        Goes through the packets that are being sent, When they reach the middle of the connection, check if they need
        to be dropped (by PL) if so, remove them from the list, and do the animation.
        :return: None
        """
        animations_to_register = []
        for sent_packet in self.sent_packets:
            if sent_packet.will_be_delayed and sent_packet.packet.get_graphics().progress >= (random.random() + 0.3):
                sent_packet.will_be_delayed = False
                sent_packet.packet.get_graphics().decrease_speed()
                animations_to_register.append(sent_packet.packet.get_graphics().get_decrease_speed_animation())
        return animations_to_register

    def stop_packets(self) -> None:
        """
        This is used to stop all of the action in the connection.
        Kills all of the packets in the connection and unregisters their `GraphicsObject`-s
        """
        for sent_packet in self.sent_packets:
            sent_packet.packet.get_graphics().unregister()
        self.sent_packets.clear()

    def __repr__(self) -> str:
        """The ip_layer representation of the connection"""
        return f"Connection({self.length}, {self.speed})"


class ConnectionSide:
    """
    This represents one side of a given `Connection` object.
    This is the API that the `Interface` object sees.
    Each Connection object holds two of these, one for each of its sides (Duh).

    The `ConnectionSide` has a list of packets the user sent, but were not yet picked up by the main `Connection`.
    It also has a list of packets that reached this side but were not yet picked up by the appropriate connected
        `Interface` object.
    """
    def __init__(self, main_connection: Connection) -> None:
        self.packets_to_send: List[Packet] = []
        self.packets_to_receive: List[Packet] = []
        self.connection: Connection = main_connection
        self.is_blocked = False

    def send(self, packet: Packet) -> None:
        """
        This is an API for the Interface class to send its packets to the Connection object.
        :param packet: The packet to send. An `Ethernet` object.
        :return: None
        """
        self.packets_to_send.append(packet)

    def receive(self) -> List[Packet]:
        """
        This is an API for the Interface class to receive its packets from the
        Connection object. If no packets have arrived, returns None.
        :return: A `Packet` object that was received from the connection. or None.
        """
        returned = self.packets_to_receive[:]
        self.packets_to_receive.clear()
        return returned

    def is_sending(self) -> bool:
        """Returns whether or not this side has packets that needs to be sent"""
        return bool(self.packets_to_send)

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
