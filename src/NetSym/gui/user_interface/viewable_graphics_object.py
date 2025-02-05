from __future__ import annotations

from abc import abstractmethod
from typing import Optional, Dict, Callable, TYPE_CHECKING, Tuple, Any

import pyglet

from NetSym.exceptions import *
from NetSym.gui.abstracts.selectable import Selectable

if TYPE_CHECKING:
    from NetSym.gui.user_interface.user_interface import UserInterface


class ViewableGraphicsObject(Selectable):
    """
    This is a graphics object that can viewed on the side-window of the simulation
    """
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super(ViewableGraphicsObject, self).__init__(*args, **kwargs)

        self.buttons_id: Optional[int] = None

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
        if self.buttons_id is None:
            raise WrongUsageError("Do not call `end_viewing` if `start_viewing` was never called")

        user_interface.remove_buttons(self.buttons_id)
