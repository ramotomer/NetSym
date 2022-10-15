from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Optional, Dict, Callable, TYPE_CHECKING, Tuple, Any

import pyglet

from NetSym.gui.abstracts.graphics_object import GraphicsObject

if TYPE_CHECKING:
    from NetSym.gui.user_interface.user_interface import UserInterface


class ViewableGraphicsObject(GraphicsObject, metaclass=ABCMeta):
    """
    This is a graphics object that can viewed on the side-window of the simulation
    """
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super(ViewableGraphicsObject, self).__init__(*args, **kwargs)

        self.buttons_id = None

    @abstractmethod
    def start_viewing(self,
                      user_interface: UserInterface,
                      additional_buttons: Optional[Dict[str, Callable[[], None]]] = None) -> Tuple[pyglet.sprite.Sprite, str, int]:
        """
        Returns a tuple a `pyglet.sprite.Sprite` object and a `Text` object that should be shown on the side window
        when this object is pressed. also returns the added button id in the returned tuple.
        :return:
        """
        pass

    def end_viewing(self, user_interface: UserInterface) -> None:
        """
        Unregisters the buttons from the `UserInterface` object.
        :param user_interface:
        :return:
        """
        user_interface.remove_buttons(self.buttons_id)
