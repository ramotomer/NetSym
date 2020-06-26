from consts import *
from gui.abstracts.animation_graphics import AnimationGraphics
from gui.abstracts.image_graphics import ImageGraphics
from gui.main_loop import MainLoop
from usefuls import with_args


class PacketGraphics(ImageGraphics):
    """
    This class is a `GraphicsObject` subclass which is the graphical representation
    of packets that are sent between computers.

    The packets know the connection's length, speed start and end, and so they can calculate where they should be at
    any given moment.
    """
    def __init__(self, deepest_layer, connection_graphics, direction, is_opaque=False):
        """
        This method initiates a `PacketGraphics` instance.
        :param deepest_layer: The deepest packet layer in the packet.
        :param connection_graphics: The `ConnectionGraphics` object which is the graphics of the `Connection` this packet
            is sent through. It is used for the start and end coordinates.
            
        The self.progress variable is how much of the connection the packet has passed already. That information comes
        from the `Connection` class that sent the packet. It updates it in the `Connection.move_packets` method.
        """
        super(PacketGraphics, self).__init__(
            IMAGES.format(self.image_from_packet(deepest_layer)),
            connection_graphics.get_computer_coordinates(direction)[0],
            connection_graphics.get_computer_coordinates(direction)[1],
            centered=True,
            scale_factor=PACKET_SCALE_FACTOR,
            is_opaque=is_opaque,
            is_pressable=True,
        )

        self.is_packet = True

        self.connection_graphics = connection_graphics
        self.direction = direction
        self.progress = 0
        self.str = str(deepest_layer)

        self.drop_animation = None

        self.buttons_id = None

    def move(self):
        """
        Make the packet move on the screen.
        This is called every clock tick.
        Calculates its coordinates according to the `self.progress` attribute.
        :return: None
        """
        self.x, self.y = self.connection_graphics.packet_location(self.direction, self.progress)
        super(PacketGraphics, self).move()

        # if self.drop_animation is not None and self.drop_animation.is_finished:
        #   MainLoop.instance.unregister_graphics_object(self.drop_animation)

    def drop(self):
        """
        Displays the animation of the packet when it is dropped by PL in a connection.
        :return: None
        """
        MainLoop.instance.unregister_graphics_object(self)
        AnimationGraphics(EXPLOSION_ANIMATION, self.x, self.y)

    @staticmethod
    def image_from_packet(layer):
        """
        Returns an image name from the `layer` name it receives.
        The `layer` will usually be the most inner layer in a packet.
        :param layer: The `Protocol` instance that you wish to get an image for.
        :return: a string of the corresponding image's location.
        """

        if hasattr(layer, "opcode"):
            return PACKET_TYPE_TO_IMAGE[type(layer).__name__][layer.opcode]
        return PACKET_TYPE_TO_IMAGE[type(layer).__name__]

    def start_viewing(self, user_interface):
        """
        Starts viewing the packet graphics object in the side-window view.
        :param user_interface: the `UserInterface` object we can use the methods of it.
        :return: a tuple <display sprite>, <display text>, <new button id>
        """
        buttons = {
            "Drop (alt+d)": with_args(user_interface.drop_packet, self),
        }
        self.buttons_id = user_interface.add_buttons(buttons)
        return self.copy_sprite(self.sprite, VIEWING_OBJECT_SCALE_FACTOR), '', self.buttons_id

    def end_viewing(self, user_interface):
        """
        Ends the viewing of the object in the side window
        """
        user_interface.remove_buttons(self.buttons_id)

    def __repr__(self):
        return self.str

    def dict_save(self):
        """
        The packets cannot be saved into the file.
        :return:
        """
        return None
