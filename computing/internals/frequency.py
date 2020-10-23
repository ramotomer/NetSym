from collections import namedtuple
from math import sqrt

from pyautogui import size as get_screen_size

from computing.connection import Connection, ConnectionSide
from consts import CONNECTIONS
from exceptions import NoSuchConnectionSideError
from gui.main_loop import MainLoop
from packets.packet import Packet
from packets.wireless_packet import WirelessPacket
from usefuls.funcs import distance

SentWirelessPacket = namedtuple("SentWirelessPacket", [
    "packet",
    "sending_time",
    "id",
])


class Frequency(Connection):
    """
    A Wifi connection is a frequency on which the antennas transmit.
    It is a global object, since you do not need
    """
    def __init__(self, frequency):
        width, height = get_screen_size()
        longest_line_in_screen = sqrt((width ** 2) + (height ** 2))

        super(Frequency, self).__init__(length=longest_line_in_screen, speed=CONNECTIONS.WIRELESS.DEFAULT_SPEED)
        self.frequency = frequency

        del self.left_side, self.right_side
        self.connection_sides = []

        self.last_sent_id = 0

    @property
    def length(self):
        return self.initial_length

    def get_side(self, wireless_interface):
        """Returns the two sides of the connection as a tuple (they are `ConnectionSide` objects)"""
        new_side = FrequencyConnectionSide(self, wireless_interface)
        self.connection_sides.append(new_side)
        return new_side

    def remove_side(self, frequency_connection_side):
        """
        When a computer would like to disconnection from the frequency (shift to another or close the interface for
        example) the ConnectionSide is deleted
        :param frequency_connection_side:
        :return:
        """
        self.connection_sides.remove(frequency_connection_side)

    def get_sides(self):
        """Returns the two sides of the connection as a tuple (they are `ConnectionSide` objects)"""
        return self.connection_sides

    def set_speed(self, new_speed):
        """Sets the speed of the connection"""
        raise NotImplementedError()

    def set_pl(self, new_pl):
        """Sets the PL amount of this connection"""
        raise NotImplementedError()

    def mark_as_blocked(self):
        """
        Marks the connection as blocked!
        Makes sure that one of the connection sides is really blocked.
        :return: None
        """
        raise NotImplementedError()

    def mark_as_unblocked(self):
        """
        Marks the connection as an unblocked connection.
        Makes sure first that both sides are actually unblocked. (That causes bugs!!)
        :return: None
        """
        raise NotImplementedError()

    def add_packet(self, packet, sending_side):
        """
        Add a packet that was sent on one of the `FrequencyConnectionSide`-s to the `self.sent_packets` list.
        This method starts the motion of the packet through the connection.
        :param packet: a `Packet` object
        :param sending_side: the connection side the packet was sent from
        """
        wireless_packet = WirelessPacket(packet.data)
        self.sent_packets.append(SentWirelessPacket(wireless_packet, MainLoop.instance.time(), self.last_sent_id))
        self.last_sent_id += 1
        wireless_packet.show(self, sending_side.wireless_interface)

    def _reach_destinations(self, sent_packet):
        """
        Adds the packet to its appropriate destination side's `received_packets` list.
        This is called when the packet finished its route through this connection and is ready to be received at the
        connected `Interface`.
        :param sent_packet: a `SentPacket` namedtuple.
        :return: None
        """
        wireless_packet = sent_packet[0]

        for side in self.connection_sides:
            location = side.wireless_interface.graphics.location

            if distance(location, wireless_packet.graphics.center_location) - wireless_packet.graphics.distance < 20:
                if sent_packet.id not in side.received_packet_ids:  # dont get packets twice!
                    side.packets_to_receive.append(Packet(wireless_packet.data))
                    side.received_packet_ids.append(sent_packet.id)

    def _remove_out_of_screen_packet(self, sent_packet):
        """
        When a packet gets too far from its origin (the Antenna) it is not longer displayed nor used, so
        it should be deleted
        :param sent_packet: a `SentPacket`
        :return:
        """
        packet = sent_packet[0]
        MainLoop.instance.unregister_graphics_object(packet.graphics)
        self.sent_packets.remove(sent_packet)

    def _send_packets_from_side(self, side):
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

    def _update_packet(self, sent_packet):
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

    def move_packets(self):
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

    def stop_packets(self):
        """
        This is used to stop all of the action in the connection.
        Kills all of the packets in the connection and unregisters their `GraphicsObject`-s
        :return: None
        """
        for packet, _, _ in self.sent_packets:
            MainLoop.instance.unregister_graphics_object(packet.graphics)
        self.sent_packets.clear()

    def __repr__(self):
        """The ip_layer representation of the connection"""
        return f"Connection({self.length}, {self.speed})"


class FrequencyConnectionSide(ConnectionSide):
    """
    This is the API that a computer sees to the frequency, using it the computer can send and receive packets.
    Each computer in the Frequency receives a distinct `FrequencyConnectionSide` object
    """
    def __init__(self, main_connection, wireless_interface):
        super(FrequencyConnectionSide, self).__init__(main_connection)
        self.wireless_interface = wireless_interface
        self.received_packet_ids = []

    def mark_as_blocked(self):
        """
        Marks the connection as being a blocked connection (paints it a different color)
        :return: None
        """
        raise NotImplementedError()

    def mark_as_unblocked(self):
        """
        Marks the connection as a regular (unblocked) connection.
        :return: None
        """
        raise NotImplementedError()
