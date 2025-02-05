from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Sequence

from NetSym.consts import T_Time
from NetSym.exceptions import *
from NetSym.gui.abstracts.animation_graphics import AnimationGraphics
from NetSym.gui.main_loop import MainLoop

if TYPE_CHECKING:
    from NetSym.packets.packet import Packet


@dataclass
class SentPacket:
    """
    a packet that is currently being sent through the connection.
    """
    packet:           Packet
    sending_time:     T_Time
    will_be_dropped:  bool   = False
    will_be_delayed:  bool   = False

    last_update_time: T_Time = field(default_factory=MainLoop.get_time)


class Connection(ABC):
    """
    This class represents a cable or any connection between two `CableNetworkInterface` objects.
    It allows for packets to move in both sides, To be sent and received.

    Each packet that is sent takes some time through the cable, that time is
    defined in the `speed` and `length` properties. They can be different for each connection.
    There is a default value for the speed, and the length is defined by the graphics object and the locations of the
    connected computers. These properties of the `Connection` class is mainly so the packet sending could be
    displayed nicely.

    The `Connection` object keeps references to its two `CableConnectionSide` objects. These are nice interfaces for
        the `CableNetworkInterface` object to talk to its connection.
    """
    speed:        float
    packet_loss:  float
    latency:      float
    sent_packets: Sequence[SentPacket]

    @abstractmethod
    def get_sides(self) -> Sequence[ConnectionSide]:
        """Returns the two sides of the connection as a tuple (they are `CableConnectionSide` objects)"""

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

    @abstractmethod
    def _is_lucky_packet(self, sent_packet: SentPacket) -> bool:
        """
        Checks whether a certain event should happen to a packet
        The chances go up as the packet moves further and further down the connection
        """

    @abstractmethod
    def _remove_packet(self, sent_packet: SentPacket) -> None:
        """
        Remove a packet from the `sent_packets` list
        """

    def _drop_predetermined_dropped_packets(self) -> List[AnimationGraphics]:
        """
        Goes through the packets that are being sent, When they reach the middle of the connection, check if they need
        to be dropped (by PL) if so, remove them from the list, and do the animation.
        """
        animations_to_register = []
        for sent_packet in self.sent_packets[:]:
            if sent_packet.will_be_dropped and self._is_lucky_packet(sent_packet):
                self._remove_packet(sent_packet)
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
            if sent_packet.will_be_delayed and self._is_lucky_packet(sent_packet):
                sent_packet.will_be_delayed = False
                sent_packet.packet.get_graphics().decrease_speed()
                animations_to_register.append(sent_packet.packet.get_graphics().get_decrease_speed_animation())
        return animations_to_register

    @abstractmethod
    def move_packets(self, main_loop: MainLoop) -> None:
        """
        This method is inserted into the main loop of the simulation when this `Connection` object is initialized.
        The packets in the connection should always be moving. (unless paused)
        This method sends new packets from the `CableConnectionSide` object, updates the time they have been in the cable, and
            removes them if they reached the end.
        """

    def stop_packets(self) -> None:
        """
        This is used to stop all of the action in the connection.
        Kills all of the packets in the connection and unregisters their `GraphicsObject`-s
        """
        for sent_packet in self.sent_packets[:]:
            sent_packet.packet.get_graphics().unregister()
            self._remove_packet(sent_packet)


class ConnectionSide(ABC):
    """
    This represents one side of a given `Connection` object.
    This is the API that the `CableNetworkInterface` object sees.
    Each Connection object holds two of these, one for each of its sides (Duh).

    The `ConnectionSide` has a list of packets the user sent, but were not yet picked up by the main `Connection`.
    It also has a list of packets that reached this side but were not yet picked up by the appropriate connected
        `NetworkInterface` object.
    """
    def __init__(self, main_connection: Connection) -> None:
        self._packets_to_send: List[Packet] = []
        self._packets_to_receive: List[Packet] = []
        self.connection: Connection = main_connection

    def get_packet_from_connection(self, sent_packet: SentPacket) -> None:
        """
        This will be called by the connection when a new packet arrives at this side of it
        """
        self._packets_to_receive.append(sent_packet.packet)

    def send(self, packet: Packet) -> None:
        """
        This is an API for the CableNetworkInterface class to send its packets to the Connection object.
        :param packet: The packet to send. An `Ethernet` object.
        :return: None
        """
        self._packets_to_send.append(packet)

    def receive(self) -> List[Packet]:
        """
        This is an API for the CableNetworkInterface class to receive its packets from the
        Connection object. If no packets have arrived, returns None.
        :return: A `Packet` object that was received from the connection. or None.
        """
        returned = self._packets_to_receive[:]
        self._packets_to_receive.clear()
        return returned

    def is_sending(self) -> bool:
        """Returns whether or not this side has packets that needs to be sent"""
        return bool(self._packets_to_send)

    def pop_packets_to_send(self) -> Sequence[Packet]:
        """
        Get all packets that should be sent and clear the sending queue
        """
        returned = self._packets_to_send[:]
        self._packets_to_send.clear()
        return returned
