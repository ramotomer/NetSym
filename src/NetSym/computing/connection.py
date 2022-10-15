from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List

from consts import *
from exceptions import ConnectionsError
from exceptions import WrongUsageError, NoSuchConnectionSideError, SomethingWentTerriblyWrongError
from gui.main_loop import MainLoop
from gui.tech.connection_graphics import ConnectionGraphics

if TYPE_CHECKING:
    from packets.packet import Packet
    from gui.tech.computer_graphics import ComputerGraphics


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

    last_update_time: T_Time = field(default_factory=MainLoop.get_instance_time)


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

        self.last_packet_motion = MainLoop.instance.time()

        self.graphics = None

        self.is_blocked = False

        self.packet_loss = packet_loss
        self.latency = latency

        MainLoop.instance.insert_to_loop_pausable(self.move_packets)

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

    def show(self, start_computer: ComputerGraphics, end_computer: ComputerGraphics) -> None:
        """
        Adds the `GraphicObject` of this class and gives it the parameters it requires.

        :param start_computer: The `GraphicsObject` of the computer which is the start of the connection
        :param end_computer: The `GraphicsObject` of the computer which is the end of the connection
        :return: None
        """
        self.graphics = ConnectionGraphics(self, start_computer, end_computer, self.packet_loss)

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
        self.graphics.update_appearance()

    def set_latency(self, new_latency: float) -> None:
        """
        Set amount of latency the connection has
        """
        if not (0 <= new_latency <= 1):
            raise ConnectionsError(f"A connection cannot have this PL amount!!! {new_pl}")

        self.latency = new_latency
        self.graphics.update_appearance()

    def mark_as_blocked(self) -> None:
        """
        Marks the connection as blocked!
        Makes sure that one of the connection sides is really blocked.
        :return: None
        """
        if any(side.is_blocked for side in self.get_sides()):
            self.graphics.color = CONNECTIONS.BLOCKED_COLOR
            self.is_blocked = True

    def mark_as_unblocked(self) -> None:
        """
        Marks the connection as an unblocked connection.
        Makes sure first that both sides are actually unblocked. (That causes bugs!!)
        :return: None
        """
        if all(not side.is_blocked for side in self.get_sides()):
            self.graphics.color = self.graphics.regular_color
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
                MainLoop.instance.time(),
                direction,
                will_be_dropped=(random.random() < self.packet_loss),
                will_be_delayed=(random.random() < self.latency),
            )
        )
        packet.show(self.graphics, direction)  # initiate the `GraphicsObject` of the packet.

    def reach_destination(self, sent_packet: SentPacket) -> None:
        """
        Adds the packet to its appropriate destination side's `received_packets` list.
        This is called when the packet finished its route through this connection and is ready to be received at the
        connected `Interface`.
        """
        packet, direction = sent_packet.packet, sent_packet.direction
        MainLoop.instance.unregister_graphics_object(packet.graphics)

        if direction == PACKET.DIRECTION.RIGHT:
            self.right_side.packets_to_receive.append(packet)
        elif direction == PACKET.DIRECTION.LEFT:
            self.left_side.packets_to_receive.append(packet)
        else:
            raise WrongUsageError('The packet can only go left or right!')

        self.sent_packets.remove(sent_packet)

    def _send_packets_from_side(self, side: ConnectionSide) -> None:
        """
        Takes all of the packets that are waiting to be sent on one ConnectionSide and sends them down the main connection.
        :param side: a `ConnectionSide` object.
        :return: None
        """
        if side not in self.get_sides():
            raise NoSuchConnectionSideError()

        direction = PACKET.DIRECTION.LEFT if side is self.right_side else PACKET.DIRECTION.RIGHT
        if side.is_sending():
            for packet in side.packets_to_send:
                self.add_packet(packet, direction)
            side.packets_to_send.clear()

    def _update_packet(self, sent_packet: SentPacket) -> None:
        """
        Receives a SentPacket object and updates its progress on the connection.
        If the packet has reached the end of the connection, make it be received at the appropriate ConnectionSide
        :param sent_packet: a `SentPacket`
        :return: None
        """
        sent_packet.packet.graphics.progress += \
            (MainLoop.instance.time_since(sent_packet.last_update_time) / self.deliver_time) * sent_packet.packet.graphics.speed
        sent_packet.last_update_time = MainLoop.instance.time()

        if sent_packet.packet.graphics.progress >= 1:
            self.reach_destination(sent_packet)

    def move_packets(self) -> None:
        """
        This method is inserted into the main loop of the simulation when this `Connection` object is initiated.
        The packets in the connection should always be moving. (unless paused)
        This method sends new packets from the `ConnectionSide` object, updates the time they have been in the cable, and
            removes them if they reached the end.
        :return: None
        """
        for side in self.get_sides():
            self._send_packets_from_side(side)

        for sent_packet in self.sent_packets[:]:  # we copy the list because we alter it during the run
            self._update_packet(sent_packet)

        self._drop_predetermined_dropped_packets()  # drops the packets that were chosen by the random PL (packet loss)
        self._delay_predetermined_delayed_packets()

    def _drop_predetermined_dropped_packets(self) -> None:
        """
        Goes through the packets that are being sent, When they reach the middle of the connection, check if they need
        to be dropped (by PL) if so, remove them from the list, and do the animation.
        :return: None
        """
        for sent_packet in self.sent_packets[:]:
            if sent_packet.will_be_dropped and sent_packet.packet.graphics.progress >= (random.random() + 0.3):
                self.sent_packets.remove(sent_packet)
                sent_packet.packet.graphics.drop()

    def _delay_predetermined_delayed_packets(self) -> None:
        """
        Goes through the packets that are being sent, When they reach the middle of the connection, check if they need
        to be dropped (by PL) if so, remove them from the list, and do the animation.
        :return: None
        """
        for sent_packet in self.sent_packets:
            if sent_packet.will_be_delayed and sent_packet.packet.graphics.progress >= (random.random() + 0.3):
                sent_packet.packet.graphics.decrease_speed()
                sent_packet.will_be_delayed = False

    def stop_packets(self) -> None:
        """
        This is used to stop all of the action in the connection.
        Kills all of the packets in the connection and unregisters their `GraphicsObject`-s
        """
        for sent_packet in self.sent_packets:
            MainLoop.instance.unregister_graphics_object(sent_packet.packet.graphics)
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
