from gui.connection_graphics import ConnectionGraphics
from math import pi, sin, cos
from gui.shape_drawing import draw_circle


def circle_parameter(radius):
    """Receives the radius of a circle and returns its parameter"""
    return 2 * pi * radius


class LoopbackConnectionGraphics(ConnectionGraphics):
    """
    This is the circular connection of the loopback interface to itself.
    """
    def __init__(self, computer_graphics, radius):
        """Initiates the connection graphics with a given radius"""
        super(LoopbackConnectionGraphics, self).__init__(None, None)
        self.radius = radius
        self.computer_graphics = computer_graphics
        self.is_showing = False

    @property
    def length(self):
        return circle_parameter(self.radius)

    def get_coordinates(self, direction):
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

        return x + (self.radius * cos(angle - (pi / 2))), y + (self.radius* sin(angle - (pi / 2)))

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
