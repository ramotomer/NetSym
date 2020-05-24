import random
from collections import namedtuple

from consts import *
from exceptions import ConnectionsError
from exceptions import SomethingWentTerriblyWrongError, NoSuchConnectionSideError
from gui.main_loop import MainLoop
from gui.tech.connection_graphics import ConnectionGraphics

SentPacket = namedtuple("SentPacket", [
    "packet",
    "sending_time",
    "direction",
    "is_dropped",
])
# ^ a packet that is currently being sent through the connection.


class Connection:
    """
    This class represents a cable or any connection between two `Interface` objects.
    It allows for packets to move in both sides, To be sent and received.

    Each packet that is sent takes some time through the cable, that time is
    defined in the `speed` and `length` properties. They can be different for each connection.
    There is a default value for the speed, and the length is defined by the graphics object and the locations of the connected computers.
    These properties of the `Connection` class is mainly so the packet sending could be displayed nicely.

    The `Connection` object keeps references to its two `ConnectionSide` objects. These are nice interfaces for
        the `Interface` object to talk to its connection.
    """
    def __init__(self, length=DEFAULT_CONNECTION_LENGTH, speed=DEFAULT_CONNECTION_SPEED, packet_loss=0):
        """
        Initiates a Connection object.

        `self.sent_packets` is the list of packets that are currently being sent through the connection.

        :param length: The length of the cable connection (in pixels)
        :param speed: The speed of the connection (in pixels per second)
        """
        self.speed = speed
        self.initial_length = length
        self.sent_packets = []
        # ^ a list of `SentPacket`-s which represent packets that are currently being sent through the connection

        self.right_side, self.left_side = ConnectionSide(self), ConnectionSide(self)

        self.last_packet_motion = MainLoop.instance.time()

        self.graphics = None

        self.is_blocked = False

        self.packet_loss = packet_loss

        MainLoop.instance.insert_to_loop_pausable(self.move_packets)

    @property
    def length(self):
        """The length of the connection in pixels"""
        if self.graphics is None:
            raise SomethingWentTerriblyWrongError("Graphics was not yet initiated!!!")
        return self.graphics.length

    @property
    def deliver_time(self):
        """The time in seconds a packet takes to go through the connection"""
        return self.length / self.speed

    def show(self, start_computer, end_computer):
        """
        Adds the `GraphicObject` of this class and gives it the parameters it requires.

        :param start_computer: The `GraphicsObject` of the computer which is the start of the connection
        :param end_computer: The `GraphicsObject` of the computer which is the end of the connection
        :return: None
        """
        self.graphics = ConnectionGraphics(self, start_computer, end_computer, self.packet_loss)

    def get_sides(self):
        """Returns the two sides of the connection as a tuple (they are `ConnectionSide` objects)"""
        return self.left_side, self.right_side

    def set_speed(self, new_speed):
        """Sets the speed of the connection"""
        if new_speed <= 0:
            raise ConnectionsError("A connection cannot have negative speed!")
        self.speed = new_speed

    def set_pl(self, new_pl):
        """Sets the PL amount of this connection"""
        if not (0 <= new_pl <= 1):
            raise ConnectionsError(f"A connection cannot have this PL amount!!! {new_pl}")
        self.packet_loss = new_pl
        self.graphics.update_color_by_pl(new_pl)

    def mark_as_blocked(self):
        """
        Marks the connection as blocked!
        Makes sure that one of the connection sides is really blocked.
        :return: None
        """
        if any(side.is_blocked for side in self.get_sides()):
            self.graphics.color = BLOCKED_CONNECTION_COLOR
            self.is_blocked = True

    def mark_as_unblocked(self):
        """
        Marks the connection as an unblocked connection.
        Makes sure first that both sides are actually unblocked. (That causes bugs!!)
        :return: None
        """
        if all(not side.is_blocked for side in self.get_sides()):
            self.graphics.color = self.graphics.regular_color
            self.is_blocked = False

    def add_packet(self, packet, direction):
        """
        Add a packet that was sent on one of the `ConnectionSide`-s to the `self.sent_packets` list.
        This method starts the motion of the packet through the connection.
        :param packet: a `Packet` object
        :param direction: the direction the packet is going to (PACKET_GOING_RIGHT or PACKET_GOING_LEFT)
        :return: None
        """
        is_dropped = (random.random() < self.packet_loss)
        self.sent_packets.append(SentPacket(packet, MainLoop.instance.time(), direction, is_dropped))
        packet.show(self.graphics, direction, is_opaque=self.is_blocked)  # initiate the `GraphicsObject` of the packet.

    def reach_destination(self, sent_packet):
        """
        Adds the packet to its appropriate destination side's `received_packets` list.
        This is called when the packet finished its route through this connection and is ready to be received at the
        connected `Interface`.
        :param sent_packet: a `SentPacket` namedtuple.
        :return: None
        """
        packet, _, direction, _ = sent_packet
        MainLoop.instance.unregister_graphics_object(packet.graphics)
        if direction == PACKET_GOING_RIGHT:
            self.right_side.packets_to_receive.append(packet)
        elif direction == PACKET_GOING_LEFT:
            self.left_side.packets_to_receive.append(packet)
        else:
            raise SomethingWentTerriblyWrongError('The packet can only go left or right!')

        self.sent_packets.remove(sent_packet)

    def _send_packets_from_side(self, side):
        """
        Takes all of the packets that are waiting to be sent on one ConnectionSide and sends them down the main connection.
        :param side: a `ConnectionSide` object.
        :return: None
        """
        if side not in self.get_sides():
            raise NoSuchConnectionSideError()

        direction = PACKET_GOING_LEFT if side is self.right_side else PACKET_GOING_RIGHT
        if side.is_sending():
            for packet in side.packets_to_send:
                self.add_packet(packet, direction)
            side.packets_to_send.clear()

    def _update_packet(self, sent_packet):
        """
        Receives a SentPacket object and updates its progress on the connection.
        If the packet has reached the end of the connection, make it be received at the appropriate ConnectionSide
        :param sent_packet: a `SentPacket` namedtuple
        :return: None
        """
        packet_travel_percent = MainLoop.instance.time_since(sent_packet.sending_time) / self.deliver_time

        if packet_travel_percent >= 1:
            self.reach_destination(sent_packet)
        else:
            sent_packet.packet.graphics.progress = packet_travel_percent

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

        self._drop_packets()  # drops the packets that were chosen by the random PL (packet loss)

    def _drop_packets(self):
        """
        Goes through the packets that are being sent, When they reach the middle of the connection, check if they need
        to be dropped (by PL) if so, remove them from the list, and do the animation.
        :return: None
        """
        for sent_packet in self.sent_packets[:]:
            packet_travel_percent = MainLoop.instance.time_since(sent_packet.sending_time) / self.deliver_time
            if sent_packet.is_dropped and packet_travel_percent >= (random.random()+0.3):
                self.sent_packets.remove(sent_packet)
                sent_packet.packet.graphics.drop()

    def stop_packets(self):
        """
        This is used to stop all of the action in the connection.
        Kills all of the packets in the connection and unregisters their `GraphicsObject`-s
        :return: None
        """
        for packet, _, _, _ in self.sent_packets:
            MainLoop.instance.unregister_graphics_object(packet.graphics)
        self.sent_packets.clear()

    def __repr__(self):
        """The data representation of the connection"""
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
    def __init__(self, main_connection):
        self.packets_to_send = []
        self.packets_to_receive = []
        self.connection = main_connection
        self.is_blocked = False

    def send(self, packet):
        """
        This is an API for the Interface class to send its packets to the Connection object.
        :param packet: The packet to send. An `Ethernet` object.
        :return: None
        """
        self.packets_to_send.append(packet)

    def receive(self):
        """
        This is an API for the Interface class to receive its packets from the
        Connection object. If no packets have arrived, returns None.
        :return: A `Packet` object that was received from the connection. or None.
        """
        returned = self.packets_to_receive[:]
        self.packets_to_receive.clear()
        return returned

    def is_sending(self):
        """Returns whether or not this side has packets that needs to be sent"""
        return bool(self.packets_to_send)

    def mark_as_blocked(self):
        """
        Marks the connection as being a blocked connection (paints it a different color)
        :return: None
        """
        self.is_blocked = True
        self.connection.mark_as_blocked()

    def mark_as_unblocked(self):
        """
        Marks the connection as a regular (unblocked) connection.
        :return: None
        """
        self.is_blocked = False
        self.connection.mark_as_unblocked()
