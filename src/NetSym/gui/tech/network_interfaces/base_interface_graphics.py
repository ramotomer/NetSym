from __future__ import annotations

import os
from abc import abstractmethod
from typing import Optional, Tuple, Dict, Callable, TYPE_CHECKING

from NetSym.consts import INTERFACES, IMAGES, DIRECTORIES, SELECTED_OBJECT
from NetSym.exceptions import *
from NetSym.gui.abstracts.image_graphics import ImageGraphics
from NetSym.gui.abstracts.selectable import Selectable
from NetSym.gui.shape_drawing import draw_rectangle
from NetSym.gui.tech.computer_graphics import ComputerGraphics
from NetSym.gui.user_interface.viewable_graphics_object import ViewableGraphicsObject

if TYPE_CHECKING:
    from NetSym.computing.internals.network_interfaces.network_interface import NetworkInterface
    from NetSym.gui.user_interface.user_interface import UserInterface


class BaseInterfaceGraphics(ViewableGraphicsObject, Selectable):
    """
    Everything in common between the graphics of the regular CableInterface and the WirelessNetworkInterface
    """
    width: float
    height: float

    def __init__(self,
                 x: Optional[float],
                 y: Optional[float],
                 interface: NetworkInterface,
                 computer_graphics: ComputerGraphics) -> None:
        """
        initiates the object.
        :param x:
        :param y: the location
        :param interface: the physical `CableNetworkInterface` of the computer.
        :param computer_graphics: the graphics object of the computer that this interface belongs to.
        """
        if (x is None) or (y is None):
            if (x is None and y is not None) or (x is not None and y is None):
                raise WrongUsageError(f"If one of x or y is None, the other should also be None! x, y: {x, y}")

            x, y = (computer_graphics.x + computer_graphics.interface_distance()), computer_graphics.y

        super(BaseInterfaceGraphics, self).__init__(x, y, centered=True, is_in_background=True, is_pressable=True)
        self.color = interface.display_color
        self.real_x, self.real_y = x, y  # TODO: why do you love shit code? WTF is real_x... change. thx.
        self.width, self.height = INTERFACES.WIDTH, INTERFACES.HEIGHT
        self.computer_graphics = computer_graphics

        self.interface: NetworkInterface = interface

    @property
    def logic_object(self):
        return self.interface

    @property
    def computer_location(self) -> Tuple[float, float]:
        return self.computer_graphics.location

    @abstractmethod
    def move(self) -> None:
        """
        Moves the interface.
        Keeps it within `INTERFACE_DISTANCE_FROM_COMPUTER` pixels away from the computer.
        """

    @abstractmethod
    def draw(self) -> None:
        """
        Draw the interface.
        :return:
        """

    @abstractmethod
    def _create_button_dict(self, user_interface: UserInterface) -> Dict[str, Callable[[], None]]:
        """
        Creates the dict of the buttons that are displayed in the side window when this object is viewed.
        :param user_interface:
        :return:
        """

    def start_viewing(self,
                      user_interface: UserInterface,
                      additional_buttons: Optional[Dict[str, Callable[[], None]]] = None) -> Tuple[pyglet.sprite.Sprite, str, int]:
        """
        Starts the side-window-view of the interface.
        :param user_interface: a `UserInterface` object to register the buttons in.
        :param additional_buttons: more buttons
        """
        buttons = self._create_button_dict(user_interface)
        buttons.update(additional_buttons or {})
        self.buttons_id = user_interface.add_buttons(buttons)
        copied_sprite = ImageGraphics.get_image_sprite(os.path.join(DIRECTORIES.IMAGES, IMAGES.VIEW.INTERFACE))
        return copied_sprite, self.interface.generate_view_text(), self.buttons_id

    def mark_as_selected(self) -> None:
        """
        Marks a rectangle around a `GraphicsObject` that is selected.
        Only call this function if the object is selected.
        :return: None
        """
        x, y = self.x - (self.width / 2), self.y - (self.height / 2)
        draw_rectangle(
            x - SELECTED_OBJECT.PADDING,
            y - SELECTED_OBJECT.PADDING,
            self.width + (2 * SELECTED_OBJECT.PADDING),
            self.height + (2 * SELECTED_OBJECT.PADDING),
            outline_color=SELECTED_OBJECT.COLOR,
        )

    @abstractmethod
    def dict_save(self) -> Dict:
        """
        Save the interface as a dict that can be later reconstructed to a new interface
        :return:
        """

    def delete(self, user_interface: UserInterface) -> None:
        """
        Delete the interface!
        """
        super(BaseInterfaceGraphics, self).delete(user_interface)
        user_interface.remove_interface(self.interface)
