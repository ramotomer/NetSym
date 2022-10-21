from __future__ import annotations

import time
from typing import TYPE_CHECKING, Tuple

from NetSym.consts import SHAPES, SELECTION_SQUARE, COLORS
from NetSym.exceptions import ObjectIsNotResizableError
from NetSym.gui.abstracts.different_color_when_hovered import DifferentColorWhenHovered
from NetSym.gui.abstracts.uniquely_dragged import UniquelyDragged
from NetSym.gui.abstracts.user_interface_graphics_object import UserInterfaceGraphicsObject
from NetSym.gui.main_loop import MainLoop
from NetSym.gui.shape_drawing import draw_circle
from NetSym.usefuls.funcs import distance

if TYPE_CHECKING:
    from NetSym.gui.abstracts.image_graphics import ImageGraphics


class ResizingDot(UserInterfaceGraphicsObject, DifferentColorWhenHovered, UniquelyDragged):
    """
    The Dot in the side of the selected resizable objects. 
    Enables you to resize the objects. 
    """
    def __init__(self,
                 x: float, y: float,
                 resized_object: ImageGraphics,
                 direction: Tuple[int, int],
                 constrain_proportions: bool = False) -> None:
        """
        Initiates the dot with the graphics object to allow it to resize it. 
        :param x: 
        :param y:
        :param direction: a tuple simulating where in the object the dot is located (1, 1) for example if it is in
        """
        super(ResizingDot, self).__init__(x, y, centered=True, do_render=False)
        self.radius = SHAPES.CIRCLE.RESIZE_DOT.RADIUS
        self.resized_object = resized_object

        self._x_diff, self._y_diff = self.resized_object.x - x, self.resized_object.y - y

        self.__last_drawn = time.time()

        if not hasattr(self.resized_object, "resize"):
            raise ObjectIsNotResizableError(f"{self.resized_object} has not 'resize' method")

        self.direction = direction
        self.constrain_proportions = constrain_proportions

        self.color = SELECTION_SQUARE.COLOR

    def is_in(self, x: float, y: float) -> bool:
        return distance((x, y), self.location) <= self.radius

    def set_hovered_color(self) -> None:
        self.color = SHAPES.CIRCLE.RESIZE_DOT.COLOR_WHEN_SELECTED

    def set_normal_color(self):
        self.color = SELECTION_SQUARE.COLOR

    def draw(self) -> None:
        draw_circle(self.x, self.y, self.radius, COLORS.BLACK, self.color)
        self.__last_drawn = MainLoop.get_time()

    def move(self) -> None:
        """
        Drag the resizing dot around - and resize the appropriate object
        """
        self.update_by_object_size()
        self.update_by_object_location()

    def drag(self, mouse_x: float, mouse_y: float, drag_x: float, drag_y: float) -> None:
        """
        Occurs when the point is dragged around
        """
        self.location = mouse_x, mouse_y
        x, y = self.location
        current_x_diff, current_y_diff = self.resized_object.x - x, self.resized_object.y - y

        direction_x, direction_y = self.direction
        self.resized_object.resize(
            (self._x_diff - current_x_diff) * 2 * direction_x,
            (self._y_diff - current_y_diff) * 2 * direction_y,
            constrain_proportions=self.constrain_proportions,
        )

        self._x_diff, self._y_diff = self.resized_object.x - x, self.resized_object.y - y
        self.move()

    def update_by_object_location(self) -> None:
        """
        Set the location the object should have according to the current place of the Dot
        """
        x, y = self.resized_object.location
        self.x = x - self._x_diff
        self.y = y - self._y_diff

    def update_by_object_size(self) -> None:
        """
        Set the size the object should have according to the current place of the Dot
        """
        x, y = self.location = self.resized_object.get_corner_by_direction(self.direction)
        self._x_diff, self._y_diff = self.resized_object.x - x, self.resized_object.y - y

    def dict_save(self) -> None:
        pass

    def __str__(self) -> str:
        return "ResizingDot"

    def __repr__(self) -> str:
        return f"<< ResizingDot {self.location} for object: {self.resized_object!r} >>"
