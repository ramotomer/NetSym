from collections import namedtuple
from math import acos, sin

from consts import *
from exceptions import *
from gui.graphics_object import GraphicsObject
from gui.image_graphics import ImageGraphics
from gui.main_window import MainWindow
from gui.shape_drawing import draw_line
from gui.shape_drawing import draw_rect_no_fill
from usefuls import distance
from usefuls import with_args

Computers = namedtuple("Computer", "start end")
"""a data structure to save the two ComputerGraphics of the two sides of the connection."""


class ConnectionGraphics(GraphicsObject):
    """
    This is a GraphicsObject subclass which displays a connection.
    It shows the graphics of the connection (a line) between the two endpoints it is connected to.
    """
    def __init__(self, connection, computer_graphics_start, computer_graphics_end, packet_loss=0):
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
        self.regular_color = CONNECTION_COLOR if not packet_loss else PL_CONNECTION_COLOR
        self.color = self.regular_color
        self.marked_as_blocked = False
        self.is_connection = True
        self.x, self.y = 0, 0  # isnt used, just to avoid errors!

        self.connection = connection  # the `Connection` object.

    @property
    def length(self):  # the length of the connection.
        return distance(self.computers.start.location, self.computers.end.location)

    def update_color_by_pl(self, packet_loss):
        """Updates the color of the connection according to the pl of the connection"""
        self.regular_color = CONNECTION_COLOR if not packet_loss else PL_CONNECTION_COLOR
        self.color = self.regular_color

    def is_mouse_in(self):
        """Returns whether or not the mouse is close enough to the connection for it to count as pressed"""
        mouse_location = MainWindow.main_window.get_mouse_location()
        a = distance(self.computers.start.location, mouse_location)
        b = distance(self.computers.end.location, mouse_location)
        c = distance(self.computers.start.location, self.computers.end.location)
        if b > c or a > c:
            return False

        if 2*a*c == 0:
            return True

        beta = acos((c**2 + a**2 - b**2) / (2*a*c))  # the law of the cosines
        mouse_distance_to_connection = a * sin(beta)
        return (mouse_distance_to_connection <= MOUSE_IN_CONNECTION_LENGTH)

    def get_coordinates(self, direction=PACKET_GOING_RIGHT):
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

    def mark_as_selected(self):
        """
        Marks a rectangle around a `GraphicsObject` that is selected.
        Only call this function if the object is selected.
        :return: None
        """
        start_x, start_y, end_x, end_y = self.get_coordinates()
        x, y = (start_x + end_x) / 2, (start_y + end_y) / 2
        draw_rect_no_fill(x - 2*SELECTED_OBJECT_PADDING, y - 2*SELECTED_OBJECT_PADDING, (4 * SELECTED_OBJECT_PADDING), (4 * SELECTED_OBJECT_PADDING))

    def draw(self):
        """
        Draws the connection (The line) between its end point and its start point.
        :return: None
        """
        color = self.color if not self.is_mouse_in() else SELECTED_CONNECTION_COLOR
        draw_line((self.computers.start.x, self.computers.start.y), (self.computers.end.x, self.computers.end.y), color)

    def start_viewing(self, user_interface):
        """
        Starts the viewing of this object in the side window.
        :return: None
        """
        buttons = {
            "set PL amount": with_args(user_interface.ask_user_for_pl, self),
            "set speed": with_args(user_interface.ask_user_for_connection_speed, self),
        }

        self.buttons_id = user_interface.add_buttons(buttons)
        return ImageGraphics.get_image_sprite(IMAGES.format(CONNECTION_VIEW_IMAGE)), self.generate_view_text(), len(buttons)

    def end_viewing(self, user_interface):
        """
        Removes the buttons that were added in the start of the viewing.
        :return: None
        """
        user_interface.remove_buttons(self.buttons_id)

    def generate_view_text(self):
        """
        Generates the text that is under the buttons in the side-window when the connection is viewed.
        :return: None
        """
        return f"Connection:\n\nfrom: {self.computers.start.computer.name}\nto: " \
            f"{self.computers.end.computer.name}\nlength: {str(self.connection.length)[:6]} pixels\nspeed: " \
            f"{self.connection.speed} pixels/second\ndeliver time: {str(self.connection.deliver_time)[:4]} seconds" \
            f"\nPL percent: {self.connection.packet_loss}"

    def __repr__(self):
        return "Connection Graphics"
