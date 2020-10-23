from consts import *
from gui.abstracts.graphics_object import GraphicsObject
from gui.shape_drawing import draw_circle


class WirelessPacketGraphics(GraphicsObject):
    """
    This class is a `GraphicsObject` subclass which is the graphical representation
    of packets that are sent between computers.

    The packets know the connection's length, speed start and end, and so they can calculate where they should be at
    any given moment.
    """
    def __init__(self, center_x, center_y, deepest_layer, frequency_object):
        super(WirelessPacketGraphics, self).__init__(center_x, center_y)

        self.is_packet = True

        self.frequency_object = frequency_object
        self.direction = PACKET.DIRECTION.WIRELESS
        self.distance = 0
        self.str = str(deepest_layer)

        self.buttons_id = None

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
        draw_circle(*self.location, self.distance, outline_color=self.frequency_object.color)

    def drop(self):
        """
        Displays the animation of the packet when it is dropped by PL in a connection.
        :return: None
        """
        raise NotImplementedError()

    @staticmethod
    def image_from_packet(layer):
        """
        Returns an image name from the `layer` name it receives.
        The `layer` will usually be the most inner layer in a packet.
        :param layer: The `Protocol` instance that you wish to get an image for.
        :return: a string of the corresponding image's location.
        """
        raise NotImplementedError()
        # if hasattr(layer, "opcode"):
        #     return PACKET.TYPE_TO_IMAGE[type(layer).__name__][layer.opcode]
        # return PACKET.TYPE_TO_IMAGE[type(layer).__name__]

    def start_viewing(self, user_interface):
        """
        Starts viewing the packet graphics object in the side-window view.
        :param user_interface: the `UserInterface` object we can use the methods of it.
        :return: a tuple <display sprite>, <display text>, <new button id>
        """
        raise NotImplementedError()
        # buttons = {
        #     "Drop (alt+d)": with_args(user_interface.drop_packet, self),
        # }
        # self.buttons_id = user_interface.add_buttons(buttons)
        # return self.copy_sprite(self.sprite), '', self.buttons_id

    def end_viewing(self, user_interface):
        """
        Ends the viewing of the object in the side window
        """
        raise NotImplementedError()
        # user_interface.remove_buttons(self.buttons_id)

    def __repr__(self):
        return self.str

    def dict_save(self):
        """
        The packets cannot be saved into the file.
        :return:
        """
        return None
