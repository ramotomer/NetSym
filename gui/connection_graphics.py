from gui.graphics_object import GraphicsObject
from consts import *
from exceptions import *
from usefuls import distance
from collections import namedtuple
from gui.shape_drawing import draw_line


Computers = namedtuple("Computer", "start end")
"""a data structure to save the two ComputerGraphics of the two sides of the connection."""


class ConnectionGraphics(GraphicsObject):
    """
    This is a GraphicsObject subclass which displays a connection.
    It shows the graphics of the connection (a line) between the two endpoints it is connected to.
    """
    def __init__(self, computer_graphics_start, computer_graphics_end):
        """
        Initiates the Connection Graphics object which is basically a line between
        two dots (the two ends of the connection).
        It is given two `ComputerGraphics` objects which are the graphics of the computers that are conneceted on each
        side of this connection. They are used for their coordinates.
        :param computer_graphics_start: The computer graphics at the beginning of the connection.
        :param computer_graphics_end: The computer graphics at the end of the connection.
        """
        super(ConnectionGraphics, self).__init__(is_in_background=True)
        self.computers = Computers(computer_graphics_start, computer_graphics_end)
        self.color = CONNECTION_COLOR
        self.marked_as_blocked = False

    @property
    def length(self):  # the length of the connection.
        return distance(self.computers.start.location, self.computers.end.location)

    def get_coordinates(self, direction):
        """
        Return a tuple of the coordinates at the start and the end of the connection.
        Receives a `direction` that the we look at the connection from (to know which is the end and which is the start)
        If the connection is opposite the coordinates will also be flipped.
        :param direction: `PACKET_GOING_RIGHT` or `PACKET_GOING_LEFT`.
        :return: (self.computers.start.x, self.computers.start.y, self.computers.end.x, self.computers.end.y)
        """
        if direction == PACKET_GOING_RIGHT:
            return self.computers.start.x, self.computers.start.y, self.computers.end.x, self.computers.end.y
        elif direction == PACKET_GOING_LEFT:
            return self.computers.end.x, self.computers.end.y, self.computers.start.x, self.computers.start.y
        raise SomethingWentTerriblyWrongError("a packet can only go left or right!")

    def packet_location(self, direction, progress):
        """
        Returns the location of the packet in the connection based of its direction and its progress in it
        This method knows the start and end coordinates of the travel of the packet
        in the connection and it also knows the progress percent.
        It calculates (with a vector based calculation) the current coordinates of the packet
        on the screen.

        :param direction: the direction the packet is going in the connection.
        :param progress: the progress of the packet through the connection.
        :return: returns coordinates of the packet according to that
        """
        start_x, start_y, end_x, end_y = self.get_coordinates(direction)
        return ((((end_x - start_x) * progress) + start_x),
                (((end_y - start_y) * progress) + start_y))

    def draw(self):
        """
        Draws the connection (The line) between its end point and its start point.
        :return: None
        """
        draw_line((self.computers.start.x, self.computers.start.y), (self.computers.end.x, self.computers.end.y), self.color)

    def __repr__(self):
        return "Connection Graphics"
