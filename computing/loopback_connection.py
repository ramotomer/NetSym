from computing.connection import Connection
from consts import *
from gui.loopback_connection_graphics import LoopbackConnectionGraphics
from gui.main_window import MainLoop


class LoopbackConnection(Connection):
    """
    This class represents a connection of a loopback interface to itself. It enables its graphical is_showing.
    It only has a left_side, no right_side.
    """
    def __init__(self, radius=LOOPBACK_CONNECTION_RADIUS):
        """
        Initiates the circular connection
        :param radius: the radius of circle.
        """
        super(LoopbackConnection, self).__init__(length=DEFAULT_CONNECTION_LENGTH, speed=LOOPBACK_CONNECTION_SPEED)
        self.radius = radius

    def get_side(self):
        """Returns the only side of the connection"""
        return self.left_side

    def show(self, computer_graphics, end_computer=None):
        """Starts the graphical appearance of the connection"""
        self.graphics = LoopbackConnectionGraphics(computer_graphics, self.radius)

    def add_packet(self, packet, direction):
        """performs the super-method of `add_packet` but also makes sure the connection is visible."""
        super(LoopbackConnection, self).add_packet(packet, direction)
        self.graphics.show()

    def reach_destination(self, sent_packet):
        """
        performs the super-method of `reach_destination` but also checks if the connection should disappear.
        All of the packets are received on the left side, all of them will also be sent on it.
        """
        packet, _, direction = sent_packet
        MainLoop.instance.unregister_graphics_object(packet.graphics)
        self.left_side.packets_to_receive.append(packet)                 # the direction does not matter
        self.sent_packets.remove(sent_packet)

        if not self.sent_packets:
            self.graphics.hide()
