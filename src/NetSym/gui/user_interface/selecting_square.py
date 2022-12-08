from __future__ import annotations

from operator import itemgetter
from typing import TYPE_CHECKING, Union, Tuple, Dict

from NetSym.consts import SELECTION_SQUARE
from NetSym.exceptions import WrongUsageError
from NetSym.gui.abstracts.graphics_object import GraphicsObject
from NetSym.gui.abstracts.image_graphics import ImageGraphics
from NetSym.gui.shape_drawing import draw_rect_by_corners

if TYPE_CHECKING:
    pass


class SelectingSquare(GraphicsObject):
    """
    The square that is drawn when one drags the mouse over the screen.
    It allows one to select multiple items at the same time.
    """
    def __init__(self,
                 x1: float, y1: float,
                 x2: float, y2: float
                 ) -> None:
        """
        initiates the square with the coordinates of the initial mouse press,
        after that, the other coordinates will be of the mouse.
        """
        super(SelectingSquare, self).__init__(x1, y1, is_pressable=False)
        self.x2, self.y2 = x2, y2

    @property
    def location2(self) -> Tuple[float, float]:
        return self.x2, self.y2

    @location2.setter
    def location2(self, value: Tuple[float, float]) -> None:
        self.x2, self.y2 = value

    @property
    def width(self) -> float:
        return abs(self.x - self.x2)

    @property
    def height(self) -> float:
        return abs(self.y - self.y2)

    def dict_save(self) -> Dict:
        raise NotImplementedError

    def draw(self) -> None:
        """
        draws the rectangle.
        :return:
        """
        draw_rect_by_corners(self.location, self.location2, outline_color=SELECTION_SQUARE.COLOR, outline_width=1)

    def __contains__(self, item: Union[Tuple[float, float], GraphicsObject]) -> bool:
        """
        Returns whether or not another graphics object is inside of the selecting object.
        :param item:
        :return:
        """
        x1, y1 = self.location
        x2, y2 = self.location2
        points = [(x1, y1), (x2, y2), (x1, y2), (x2, y1)]
        sorted_points = list(sorted(sorted(points, key=itemgetter(0)), key=itemgetter(1)))
        (bottom_left_x, bottom_left_y), (upper_right_x, upper_right_y) = sorted_points[0], sorted_points[-1]

        if isinstance(item, tuple) and len(item) == 2:
            x, y = item
            return (bottom_left_x < x < upper_right_x) and (bottom_left_y < y < upper_right_y)

        if isinstance(item, ImageGraphics):
            return any(corner in self for corner in item.corners)

        if isinstance(item, GraphicsObject):
            return item.location in self

        raise WrongUsageError("Receives a tuple or a graphics object only!")
