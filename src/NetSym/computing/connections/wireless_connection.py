from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Sequence

from NetSym.computing.connections.base_connection import BaseSentPacket, BaseConnection, BaseConnectionSide
from NetSym.consts import CONNECTIONS, T_Color, WINDOWS
from NetSym.exceptions import NoSuchConnectionSideError, WrongUsageError
from NetSym.gui.main_loop import MainLoop
from NetSym.packets.packet import Packet
from NetSym.packets.wireless_packet import WirelessPacket
from NetSym.usefuls.funcs import distance

if TYPE_CHECKING:
    from NetSym.gui.abstracts.graphics_object import GraphicsObject
    from NetSym.computing.internals.network_interfaces.wireless_network_interface import WirelessNetworkInterface


@dataclass
class SentWirelessPacket(BaseSentPacket):
    id: int = 0


class WirelessConnection(BaseConnection):
    """
    A `WirelessConnection` is the "frequency" on which the antennas transmit.
    It is a global object, since you do not need to see it.
    Each antenna can be connected to one frequency, And an antenna can see only packets transmitted on the frequency it is on.

    The packets transmitted on each frequency have different colors.
    """
    sent_packets: List[SentWirelessPacket]

    def __init__(self,
                 frequency: float,
                 longest_line_on_the_screen: float,
                 speed: float = CONNECTIONS.WIRELESS.DEFAULT_SPEED,
                 packet_loss: float = 0, latency: float = 0) -> None:
        self.speed = speed
        self.sent_packets = []
        self.connection_sides: List[WirelessConnectionSide] = []

        self.last_packet_motion = MainLoop.get_time()

        self.packet_loss = packet_loss
        self.latency = latency

        self.frequency = frequency
        self.longest_line_on_the_screen = longest_line_on_the_screen

        self.sent_packet_id = 0

        self.color: T_Color = (random.randint(0, 150), random.randint(0, 150), random.randint(0, 150))

    def get_side(self, wireless_interface: WirelessNetworkInterface) -> WirelessConnectionSide:
        """Returns the two sides of the connection as a tuple (they are `CableConnectionSide` objects)"""
        new_side = WirelessConnectionSide(self, wireless_interface)
        self.connection_sides.append(new_side)
        return new_side

    def remove_side(self, wireless_connection_side: WirelessConnectionSide) -> None:
        """
        When a computer would like to disconnection from the `WirelessConnection` (shift to another frequency or close the interface for
        example) the `ConnectionSide` is deleted
        :param wireless_connection_side:
        :return:
        """
        self.connection_sides.remove(wireless_connection_side)

    def get_sides(self) -> Sequence[WirelessConnectionSide]:
        """Returns the two sides of the connection as a tuple (they are `CableConnectionSide` objects)"""
        return self.connection_sides

    def _add_packet(self, packet: Packet, sending_side: WirelessConnectionSide) -> WirelessPacket:
        """
        Add a packet that was sent on one of the `WirelessConnectionSide`-s to the `self.sent_packets` list.
        This method starts the motion of the packet through the connection.
        :param packet: a `Packet` object
        :param sending_side: the connection side the packet was sent from
        """
        wireless_packet = WirelessPacket(packet.data)
        self.sent_packets.append(
            SentWirelessPacket(
                packet=wireless_packet,
                sending_time=MainLoop.get_time(),
                id=self.sent_packet_id,
            )
        )
        sending_side.recognize_sent_packet(self.sent_packet_id)
        self.sent_packet_id += 1
        return wireless_packet

    def _receive_on_sides_if_reached_destination(self, sent_packet: SentWirelessPacket) -> None:
        """
        Adds the packet to its appropriate destination side's `received_packets` list.
        This is called when the packet finished its route through this connection and is ready to be received at the
        connected `CableNetworkInterface`.
        :param sent_packet: a `SentPacket` namedtuple.
        :return: None
        """
        wireless_packet = sent_packet.packet

        for side in self.connection_sides:
            location = side.wireless_interface.graphics.location

            if 0 != distance(location, wireless_packet.graphics.center_location) - wireless_packet.graphics.distance < 20:
                if side.was_already_received(sent_packet):  # dont get packets twice!
                    continue

                side.get_packet_from_connection(sent_packet)

    def _remove_packet_if_out_of_screen(self, sent_packet: SentWirelessPacket) -> None:
        """
        When a packet gets too far from its origin (the Antenna) it is not longer displayed nor used, so
        it should be deleted
        :param sent_packet: a `SentPacket`
        :return:
        """
        if self._get_distance(sent_packet) <= self.longest_line_on_the_screen:
            return  # packet still visible in screen...

        sent_packet.packet.graphics.unregister()
        self.sent_packets.remove(sent_packet)

    def _send_packets_from_side(self, side: WirelessConnectionSide) -> List[GraphicsObject]:
        """
        Takes all of the packets that are waiting to be sent on one CableConnectionSide and sends them down the main connection.
        :param side: a `CableConnectionSide` object.
        """
        if side not in self.get_sides():
            raise NoSuchConnectionSideError()

        packet_graphics_to_register = []
        if side.is_sending():
            for packet in side.pop_packets_to_send():
                wireless_packet = self._add_packet(packet, side)
                packet_graphics_to_register.extend(wireless_packet.init_graphics(self, side.wireless_interface))
        return packet_graphics_to_register

    def _update_packet(self, sent_packet: SentWirelessPacket) -> None:
        """
        Receives a SentPacket object and updates its progress on the connection.
        If the packet has reached the end of the connection, make it be received at the appropriate CableConnectionSide
        :param sent_packet: a `SentPacket` namedtuple
        """
        distance_ = self._get_distance(sent_packet)
        sent_packet.packet.graphics.distance = distance_

        self._remove_packet_if_out_of_screen(sent_packet)

    def _get_distance(self, sent_packet: BaseSentPacket) -> float:
        """
        Returns the distance of the packet from the source of origin
        Calculated by the time and speed of the wireless packet
        """
        return MainLoop.get_time_since(sent_packet.sending_time) * self.speed

    def _is_lucky_packet(self, sent_packet: BaseSentPacket) -> bool:
        """
        Checks whether a certain event should happen to a packet
        The chances go up as the packet moves further and further away from the center of origin.
        """
        return (2 * (self._get_distance(sent_packet) / WINDOWS.MAIN.WIDTH)) >= (random.random() + 0.3)

    def __repr__(self) -> str:
        """The ip_layer representation of the connection"""
        return f"WirelessConnection({self.frequency}, connected: {len(self.connection_sides)})"


class WirelessConnectionSide(BaseConnectionSide):
    """
    This is the API that a computer sees to the `WirelessConnection`, using it the computer can send and receive packets.
    Each computer in the WirelessConnection receives a distinct `WirelessConnectionSide` object
    """
    def __init__(self, main_connection: WirelessConnection, wireless_interface: WirelessNetworkInterface) -> None:
        super(WirelessConnectionSide, self).__init__(main_connection)

        self.wireless_interface = wireless_interface
        self._received_packet_ids = []

    def get_packet_from_connection(self, sent_packet: BaseSentPacket) -> None:
        """
        This will be called by the frequency when a new packet arrives at this side of it
        """
        if not isinstance(sent_packet, SentWirelessPacket):
            raise WrongUsageError(f"Only call this function with a SentWirelessPacket object not {type(sent_packet)} like {sent_packet!r}!!!")

        self._packets_to_receive.append(Packet(sent_packet.packet.data))
        self._received_packet_ids.append(sent_packet.id)

    def was_already_received(self, sent_packet: SentWirelessPacket) -> bool:
        """
        Return whether or not the packet was already received on this side of the `WirelessConnection` and translated into a regular packet :)
        Does it by looking at the ID of that packet :)
        """
        return bool(sent_packet.id in self._received_packet_ids)

    def recognize_sent_packet(self, id_: int) -> None:
        """
        Lets the connection side know that a certain packet was sent by itself.
        That way it will not take it in at any case.
        """
        self._received_packet_ids.append(id_)
