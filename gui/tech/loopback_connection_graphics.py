from math import pi, sin, cos

from consts import *
from gui.shape_drawing import draw_circle
from gui.tech.connection_graphics import ConnectionGraphics


def circle_parameter(radius):
    """Receives the radius of a circle and returns its parameter"""
    return 2 * pi * radius


class LoopbackConnectionGraphics(ConnectionGraphics):
    """
    This is the circular connection of the loopback interface to itself.
    """
    def __init__(self, connection, computer_graphics, radius):
        """Initiates the connection graphics with a given radius"""
        super(LoopbackConnectionGraphics, self).__init__(connection, None, None)
        self.radius = radius
        self.computer_graphics = computer_graphics
        self.is_showing = False
        self.is_pressable = False

    @property
    def length(self):
        return circle_parameter(self.radius)

    def is_mouse_in(self):
        return False

    def get_coordinates(self, direction=PACKET.DIRECTION.RIGHT):
        """Returns the start and end coordinates of the connection (both are self.computer_graphics.location)"""
        return (*self.computer_graphics.location, *self.computer_graphics.location)

    def packet_location(self, direction, progress):
        """
        Calculates the location of a packet according to its direction and progress.
        The connection is circular so the packets go around it as one would expect.
        :param direction: It does not matter here (all go in the same direction) but necessary to override the super-method
        :param progress: the progress (a number from 0 to 1)
        :return: None
        """
        angle = 2 * pi * progress
        x, y = self.computer_graphics.location
        y = y + self.radius

        return x + (self.radius * cos(angle - (pi / 2))), y + (self.radius * sin(angle - (pi / 2)))

    def show(self):
        self.is_showing = True

    def hide(self):
        self.is_showing = False

    def draw(self):
        """
        Draws the circular connection.
        :return: None
        """
        if self.is_showing:
            x, y = self.computer_graphics.location
            draw_circle(x, y + self.radius, self.radius, self.color)

    def get_computer_coordinates(self, direction=PACKET.DIRECTION.RIGHT):
        """
        Return a tuple of the coordinates at the start and the end of the connection.
        Receives a `direction` that we look at the connection from (to know which is the end and which is the start)
        If the connection is opposite the coordinates will also be flipped.
        :param direction: `PACKET.DIRECTION.RIGHT` or `PACKET.DIRECTION.LEFT`.
        :return: (self.computers.start.x, self.computers.start.y, self.computers.end.x, self.computers.end.y)
        """
        return self.computer_graphics.x, self.computer_graphics.y, self.computer_graphics.x, self.computer_graphics.y

    def __repr__(self):
        return "loopback connection graphics"
