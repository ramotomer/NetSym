from __future__ import annotations

import os
from typing import TYPE_CHECKING, Optional, Dict, Callable, Tuple

import pyglet
import scapy

from NetSym.consts import PACKET, COLORS, SELECTED_OBJECT, DIRECTORIES, T_Color
from NetSym.gui.abstracts.different_color_when_hovered import DifferentColorWhenHovered
from NetSym.gui.abstracts.image_graphics import ImageGraphics
from NetSym.gui.abstracts.selectable import Selectable
from NetSym.gui.shape_drawing import draw_circle, draw_rectangle
from NetSym.gui.tech.packets.packet_graphics import PacketGraphics, image_from_packet
from NetSym.gui.user_interface.viewable_graphics_object import ViewableGraphicsObject
from NetSym.usefuls.funcs import distance

if TYPE_CHECKING:
    from NetSym.gui.user_interface.user_interface import UserInterface
    from NetSym.computing.connections.wireless_connection import WirelessConnection


class WirelessPacketGraphics(PacketGraphics, ViewableGraphicsObject, DifferentColorWhenHovered, Selectable):
    """
    This class is a `GraphicsObject` subclass which is the graphical representation
    of packets that are sent between computers.

    The packets know the connection's length, speed start and end, and so they can calculate where they should be at
    any given moment.
    """
    def __init__(self,
                 center_x: float,
                 center_y: float,
                 deepest_layer: scapy.packet.Packet,
                 connection: WirelessConnection) -> None:
        super(WirelessPacketGraphics, self).__init__(center_x, center_y)

        self.connection = connection
        self.direction = PACKET.DIRECTION.WIRELESS
        self.distance = 0
        self.str = str(deepest_layer)
        self.deepest_layer = deepest_layer
        self.color: T_Color = COLORS.WHITE

    @property
    def center_x(self) -> float:
        return self.x

    @property
    def center_y(self) -> float:
        return self.y

    @property
    def center_location(self) -> Tuple[float, float]:
        return self.location

    def set_normal_color(self):
        self.color = self.connection.color

    def set_hovered_color(self):
        self.color = COLORS.WHITE

    def draw(self) -> None:
        draw_circle(*self.location, self.distance, outline_color=self.color)

    def is_in(self, x: float, y: float) -> bool:
        distance_from_point = distance(self.center_location, (x, y))
        return abs(distance_from_point - self.distance) < 5

    def start_viewing(self,
                      user_interface: UserInterface,
                      additional_buttons: Optional[Dict[str, Callable[[], None]]] = None) -> Tuple[pyglet.sprite.Sprite, str, int]:
        """
        Starts viewing the packet graphics object in the side-window view.
        :param additional_buttons: more buttons!@!!!!!!!
        :param user_interface: the `UserInterface` object we can use the methods of it.
        :return: a tuple <display sprite>, <display text>, <new button id>
        """
        buttons = additional_buttons or {}
        self.buttons_id = user_interface.add_buttons(buttons)

        sprite = ImageGraphics.get_image_sprite(os.path.join(DIRECTORIES.IMAGES, image_from_packet(self.deepest_layer)))
        return sprite, '', self.buttons_id

    def mark_as_selected(self) -> None:
        """
        Marks the object as selected, but does not show the resizing dots :)
        :return:
        """
        x, y = self.x, self.y

        corner = self.center_x + self.distance - SELECTED_OBJECT.PADDING, y - SELECTED_OBJECT.PADDING
        draw_rectangle(*corner, 20, 20, outline_color=SELECTED_OBJECT.COLOR)

    def __repr__(self) -> str:
        return self.str
