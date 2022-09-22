from __future__ import annotations

from typing import TYPE_CHECKING, Tuple

import scapy

from consts import *
from gui.abstracts.animation_graphics import AnimationGraphics
from gui.abstracts.image_graphics import ImageGraphics
from gui.main_loop import MainLoop
from packets.usefuls import get_original_layer_name_by_instance
from usefuls.funcs import with_args

if TYPE_CHECKING:
    from gui.tech.connection_graphics import ConnectionGraphics
    from gui.user_interface.user_interface import UserInterface


class PacketGraphics(ImageGraphics):
    """
    This class is a `GraphicsObject` subclass which is the graphical representation
    of packets that are sent between computers.

    The packets know the connection's length, speed start and end, and so they can calculate where they should be at
    any given moment.
    """
    def __init__(self,
                 deepest_layer: scapy.packet.Packet,
                 connection_graphics: ConnectionGraphics,
                 direction: str) -> None:
        """
        This method initiates a `PacketGraphics` instance.
        :param deepest_layer: The deepest packet layer in the packet.
        :param connection_graphics: The `ConnectionGraphics` object which is the graphics of the `Connection` this packet
            is sent through. It is used for the start and end coordinates.
            
        The self.progress variable is how much of the connection the packet has passed already. That information comes
        from the `Connection` class that sent the packet. It updates it in the `Connection.move_packets` method.
        """
        super(PacketGraphics, self).__init__(
            self.image_from_packet(deepest_layer),
            connection_graphics.get_computer_coordinates(direction)[0],
            connection_graphics.get_computer_coordinates(direction)[1],
            centered=True,
            scale_factor=IMAGES.SCALE_FACTORS.PACKETS,
            is_pressable=True,
        )

        self.connection_graphics = connection_graphics
        self.direction = direction
        self.progress = 0
        self.str = get_original_layer_name_by_instance(deepest_layer)
        self.deepest_layer = deepest_layer

        self.drop_animation = None

        self.buttons_id = None

    @property
    def should_be_transparent(self):
        """
        This property should be overridden - at any given time, the object will become transparent If and Only If this returns `True`
        """
        return self.connection_graphics.connection.is_blocked

    def move(self) -> None:
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

    def drop(self) -> None:
        """
        Displays the animation of the packet when it is dropped by PL in a connection.
        :return: None
        """
        MainLoop.instance.unregister_graphics_object(self)
        AnimationGraphics(ANIMATIONS.EXPLOSION, self.x, self.y)

    @staticmethod
    def image_from_packet(layer: scapy.packet.Packet) -> str:
        """
        Returns an image name from the `layer` name it receives.
        The `layer` will usually be the most inner layer in a packet.
        :param layer: The `Protocol` instance that you wish to get an image for.
        :return: a string of the corresponding image's location.
        """
        name = get_original_layer_name_by_instance(layer)

        if name in PACKET.TYPE_TO_OPCODE_FUNCTION:
            return PACKET.TYPE_TO_IMAGE[name][PACKET.TYPE_TO_OPCODE_FUNCTION[name](layer)]
        return PACKET.TYPE_TO_IMAGE[name]

    def start_viewing(self, user_interface: UserInterface) -> Tuple[pyglet.sprite.Sprite, str, int]:
        """
        Starts viewing the packet graphics object in the side-window view.
        :param user_interface: the `UserInterface` object we can use the methods of it.
        :return: a tuple <display sprite>, <display text>, <new button id>
        """
        buttons = {
            "Drop (alt+d)": with_args(user_interface.drop_packet, self),
        }
        self.buttons_id = user_interface.add_buttons(buttons)
        return self.copy_sprite(self.sprite), '', self.buttons_id

    def end_viewing(self, user_interface: UserInterface) -> None:
        """
        Ends the viewing of the object in the side window
        """
        user_interface.remove_buttons(self.buttons_id)

    def __repr__(self) -> str:
        return self.str

    def dict_save(self):
        """
        The packets cannot be saved into the file.
        :return:
        """
        return None

    def delete(self, user_interface: UserInterface) -> None:
        """
        Delete the packet and drop it from the connection it is currently going through
        """
        super(PacketGraphics, self).delete(user_interface)
        user_interface.drop_packet(self)
