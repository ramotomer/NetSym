from __future__ import annotations

import random
from math import sqrt
from typing import NamedTuple, TYPE_CHECKING, List

from NetSym.computing.connection import Connection, ConnectionSide
from NetSym.consts import CONNECTIONS, T_Time, T_Color
from NetSym.exceptions import NoSuchConnectionSideError
from NetSym.gui.main_loop import MainLoop
from NetSym.gui.main_window import MainWindow
from NetSym.packets.packet import Packet
from NetSym.packets.wireless_packet import WirelessPacket
from NetSym.usefuls.funcs import distance

if TYPE_CHECKING:
    from NetSym.computing.internals.wireless_interface import WirelessInterface


class SentWirelessPacket(NamedTuple):
    packet:       Packet
    sending_time: T_Time
    id:           int


class Frequency(Connection):
    """
    A Wifi connection is a frequency on which the antennas transmit.
    It is a global object, since you do not need
    """
    sent_packets: List[SentWirelessPacket]

    def __init__(self, frequency: float) -> None:
        width, height = MainWindow.main_window.width, MainWindow.main_window.height
        longest_line_in_screen = sqrt((width ** 2) + (height ** 2))

        super(Frequency, self).__init__(length=longest_line_in_screen, speed=CONNECTIONS.WIRELESS.DEFAULT_SPEED)
        self.frequency = frequency

        del self.left_side, self.right_side
        self.connection_sides = []

        self.sent_packet_id = 0

        self.color: T_Color = (random.randint(0, 150), random.randint(0, 150), random.randint(0, 150))

    @property
    def length(self) -> float:
        return self.initial_length

    def get_side(self, wireless_interface: WirelessInterface) -> FrequencyConnectionSide:
        """Returns the two sides of the connection as a tuple (they are `ConnectionSide` objects)"""
        new_side = FrequencyConnectionSide(self, wireless_interface)
        self.connection_sides.append(new_side)
        return new_side

    def remove_side(self, frequency_connection_side: FrequencyConnectionSide) -> None:
        """
        When a computer would like to disconnection from the frequency (shift to another or close the interface for
        example) the ConnectionSide is deleted
        :param frequency_connection_side:
        :return:
        """
        self.connection_sides.remove(frequency_connection_side)

    def get_sides(self) -> List[FrequencyConnectionSide]:
        """Returns the two sides of the connection as a tuple (they are `ConnectionSide` objects)"""
        return self.connection_sides

    def set_speed(self, new_speed: float) -> None:
        """Sets the speed of the connection"""
        raise NotImplementedError()

    def set_pl(self, new_pl: float) -> None:
        """Sets the PL amount of this connection"""
        raise NotImplementedError()

    def mark_as_blocked(self) -> None:
        """
        Marks the connection as blocked!
        Makes sure that one of the connection sides is really blocked.
        :return: None
        """
        raise NotImplementedError()

    def mark_as_unblocked(self) -> None:
        """
        Marks the connection as an unblocked connection.
        Makes sure first that both sides are actually unblocked. (That causes bugs!!)
        :return: None
        """
        raise NotImplementedError()

    def add_packet(self, packet: Packet, sending_side: FrequencyConnectionSide) -> None:
        """
        Add a packet that was sent on one of the `FrequencyConnectionSide`-s to the `self.sent_packets` list.
        This method starts the motion of the packet through the connection.
        :param packet: a `Packet` object
        :param sending_side: the connection side the packet was sent from
        """
        wireless_packet = WirelessPacket(packet.data)
        self.sent_packets.append(SentWirelessPacket(wireless_packet, MainLoop.get_time(), self.sent_packet_id))
        sending_side.received_packet_ids.append(self.sent_packet_id)
        self.sent_packet_id += 1
        wireless_packet.show(self, sending_side.wireless_interface)

    def _reach_destinations(self, sent_packet: SentWirelessPacket) -> None:
        """
        Adds the packet to its appropriate destination side's `received_packets` list.
        This is called when the packet finished its route through this connection and is ready to be received at the
        connected `Interface`.
        :param sent_packet: a `SentPacket` namedtuple.
        :return: None
        """
        wireless_packet = sent_packet.packet

        for side in self.connection_sides:
            location = side.wireless_interface.graphics.location

            if 0 != distance(location, wireless_packet.graphics.center_location) - wireless_packet.graphics.distance < 20:
                if sent_packet.id not in side.received_packet_ids:  # dont get packets twice!
                    side.packets_to_receive.append(Packet(wireless_packet.data))
                    side.received_packet_ids.append(sent_packet.id)

    def _remove_out_of_screen_packet(self, sent_packet: SentWirelessPacket) -> None:
        """
        When a packet gets too far from its origin (the Antenna) it is not longer displayed nor used, so
        it should be deleted
        :param sent_packet: a `SentPacket`
        :return:
        """
        MainLoop.instance.unregister_graphics_object(sent_packet.packet.graphics)
        self.sent_packets.remove(sent_packet)

    def _send_packets_from_side(self, side: FrequencyConnectionSide) -> None:
        """
        Takes all of the packets that are waiting to be sent on one ConnectionSide and sends them down the main connection.
        :param side: a `ConnectionSide` object.
        :return: None
        """
        if side not in self.get_sides():
            raise NoSuchConnectionSideError()

        if side.is_sending():
            for packet in side.packets_to_send:
                self.add_packet(packet, side)
            side.packets_to_send.clear()

    def _update_packet(self, sent_packet: SentWirelessPacket) -> None:
        """
        Receives a SentPacket object and updates its progress on the connection.
        If the packet has reached the end of the connection, make it be received at the appropriate ConnectionSide
        :param sent_packet: a `SentPacket` namedtuple
        :return: None
        """
        distance_ = MainLoop.instance.time_since(sent_packet.sending_time) * self.speed
        sent_packet.packet.graphics.distance = distance_

        if distance_ > self.length:
            self._remove_out_of_screen_packet(sent_packet)

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
            self._reach_destinations(sent_packet)

    def __repr__(self) -> str:
        """The ip_layer representation of the connection"""
        return f"Frequency({self.frequency}, connected: {len(self.connection_sides)})"


class FrequencyConnectionSide(ConnectionSide):
    """
    This is the API that a computer sees to the frequency, using it the computer can send and receive packets.
    Each computer in the Frequency receives a distinct `FrequencyConnectionSide` object
    """
    def __init__(self, main_connection: Frequency, wireless_interface: WirelessInterface) -> None:
        super(FrequencyConnectionSide, self).__init__(main_connection)
        self.wireless_interface = wireless_interface
        self.received_packet_ids = []

    def mark_as_blocked(self) -> None:
        """
        Marks the connection as being a blocked connection (paints it a different color)
        :return: None
        """
        raise NotImplementedError()

    def mark_as_unblocked(self) -> None:
        """
        Marks the connection as a regular (unblocked) connection.
        :return: None
        """
        raise NotImplementedError()
