from __future__ import annotations

from typing import Optional, Tuple

from NetSym.gui.abstracts.graphics_object import GraphicsObject
from NetSym.usefuls.funcs import sum_tuples


class UserInterfaceGraphicsObject(GraphicsObject):
    """
    A GraphicsObject which is used only for the user interface (popup windows, buttons, etc...)

    TODO: get rid of this stupid class that means nothing ASAP - or at least change the name
    """
    def __init__(self,
                 x: Optional[float] = None,
                 y: Optional[float] = None,
                 do_render: bool = True,
                 centered: bool = False,
                 is_in_background: bool = False,
                 is_pressable: bool = False) -> None:
        super(UserInterfaceGraphicsObject, self).__init__(x, y, do_render, centered, is_in_background, is_pressable)
        self.parent_graphics = None
        self.padding = None

    def set_parent_graphics(self, parent_graphics: GraphicsObject, padding: Tuple[float, float] = (0, 0)) -> None:
        """
        Sets the parent graphics of the Graphics Object, It follows it around.
        :param parent_graphics:
        :param padding:
        :return:
        """
        self.parent_graphics = parent_graphics
        self.padding = padding

    def move(self) -> None:
        """
        For consoles that have to move relatively to a parent graphics object.
        :return:
        """
        if self.parent_graphics is not None:
            self.location = sum_tuples(self.parent_graphics.location, self.padding)

    def dict_save(self) -> None:
        """
        These do not need to be implement this method.
        It is used to save the simulation status into a file.
        They are loaded anyway, so there is no need to save them.
        :return: None
        """
        return None
