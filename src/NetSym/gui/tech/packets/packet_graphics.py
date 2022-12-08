from __future__ import annotations

import random
from abc import abstractmethod
from typing import TYPE_CHECKING, Optional, Dict, Callable, Tuple

import pyglet
import scapy

from NetSym.consts import CONNECTIONS, ANIMATIONS, PACKET
from NetSym.gui.abstracts.animation_graphics import AnimationGraphics
from NetSym.gui.abstracts.selectable import Selectable
from NetSym.packets.usefuls.type_to_opcode_function import TYPE_TO_OPCODE_FUNCTION
from NetSym.packets.usefuls.usefuls import get_original_layer_name_by_instance

if TYPE_CHECKING:
    from NetSym.gui.user_interface.user_interface import UserInterface


def image_from_packet(layer: scapy.packet.Packet) -> str:
    """
    Returns an image name from the `layer` name it receives.
    The `layer` will usually be the most inner layer in a packet.
    :param layer: The `Protocol` instance that you wish to get an image for.
    :return: a string of the corresponding image's location.
    """
    name = get_original_layer_name_by_instance(layer)

    if name in TYPE_TO_OPCODE_FUNCTION:
        return PACKET.TYPE_TO_IMAGE[name][TYPE_TO_OPCODE_FUNCTION[name](layer)]
    return PACKET.TYPE_TO_IMAGE[name]


class PacketGraphics(Selectable):
    """
    This class is a `GraphicsObject` subclass which is the graphical representation
    of packets that are sent between computers.

    The packets know the connection's length, speed start and end, and so they can calculate where they should be at
    any given moment.
    """
    deepest_layer: scapy.packet.Packet
    speed: float

    def decrease_speed(self) -> None:
        """
        Decreases the speed of the packet by a half
        """
        self.speed *= random.uniform(0.9, 1) * CONNECTIONS.PACKETS.DECREASE_SPEED_BY

    def get_decrease_speed_animation(self) -> AnimationGraphics:
        """
        Returns the animation object that should be shown when decreasing the speed of a packet
        """
        return AnimationGraphics(ANIMATIONS.LATENCY, self.x, self.y, scale=CONNECTIONS.LATENCY_ANIMATION_SIZE)

    def get_drop_animation(self) -> AnimationGraphics:
        """
        Returns the animation object that should be shown when dropping a packet
        """
        return AnimationGraphics(ANIMATIONS.EXPLOSION, self.x, self.y)

    @abstractmethod
    def start_viewing(self,
                      user_interface: UserInterface,
                      additional_buttons: Optional[Dict[str, Callable[[], None]]] = None) -> Tuple[pyglet.sprite.Sprite, str, int]:
        """
        Starts viewing the packet graphics object in the side-window view.
        :param additional_buttons: more buttons!!!
        :param user_interface: the `UserInterface` object we can use the methods of it.
        :return: a tuple <display sprite>, <display text>, <new button id>
        """

    def dict_save(self) -> Dict:
        """
        The packets cannot be saved into the file.
        :return:
        """
        pass
