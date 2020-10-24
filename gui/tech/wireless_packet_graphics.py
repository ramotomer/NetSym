from consts import *
from gui.abstracts.graphics_object import GraphicsObject
from gui.abstracts.image_graphics import ImageGraphics
from gui.main_window import MainWindow
from gui.shape_drawing import draw_circle, draw_rectangle
from gui.tech.packet_graphics import PacketGraphics
from usefuls.funcs import distance


class WirelessPacketGraphics(GraphicsObject):
    """
    This class is a `GraphicsObject` subclass which is the graphical representation
    of packets that are sent between computers.

    The packets know the connection's length, speed start and end, and so they can calculate where they should be at
    any given moment.
    """
    end_viewing = PacketGraphics.end_viewing

    def __init__(self, center_x, center_y, deepest_layer, frequency_object):
        super(WirelessPacketGraphics, self).__init__(center_x, center_y)

        self.is_packet = True

        self.frequency_object = frequency_object
        self.direction = PACKET.DIRECTION.WIRELESS
        self.distance = 0
        self.str = str(deepest_layer)
        self.deepest_layer = deepest_layer

        self.buttons_id = None

        self.image_from_packet = PacketGraphics.image_from_packet

    @property
    def center_x(self):
        return self.x

    @property
    def center_y(self):
        return self.y

    @property
    def center_location(self):
        return self.location

    def draw(self):
        color = COLORS.WHITE if self.is_mouse_in() else self.frequency_object.color
        draw_circle(*self.location, self.distance, outline_color=color)

    def is_mouse_in(self):
        mouse_dist = distance(self.center_location, MainWindow.main_window.get_mouse_location())
        return abs(mouse_dist - self.distance) < 5

    def start_viewing(self, user_interface):
        """
        Starts viewing the packet graphics object in the side-window view.
        :param user_interface: the `UserInterface` object we can use the methods of it.
        :return: a tuple <display sprite>, <display text>, <new button id>
        """
        buttons = {}
        self.buttons_id = user_interface.add_buttons(buttons)

        sprite = ImageGraphics.get_image_sprite(os.path.join(DIRECTORIES.IMAGES, self.image_from_packet(self.deepest_layer)))
        return sprite, '', self.buttons_id

    def mark_as_selected(self):
        """
        Marks the object as selected, but does not show the resizing dots :)
        :return:
        """
        x, y = self.x, self.y

        corner = self.center_x + self.distance - SELECTED_OBJECT.PADDING, y - SELECTED_OBJECT.PADDING
        draw_rectangle(*corner, 20, 20, outline_color=SELECTED_OBJECT.COLOR)

    def __repr__(self):
        return self.str

    def dict_save(self):
        """
        The packets cannot be saved into the file.
        :return:
        """
        return None
