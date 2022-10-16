from __future__ import annotations

from operator import itemgetter
from typing import TYPE_CHECKING, Iterable, Union, Tuple

from NetSym.consts import SELECTION_SQUARE
from NetSym.exceptions import WrongUsageError
from NetSym.gui.abstracts.graphics_object import GraphicsObject
from NetSym.gui.abstracts.image_graphics import ImageGraphics
from NetSym.gui.main_window import MainWindow
from NetSym.gui.shape_drawing import draw_rect_by_corners

if TYPE_CHECKING:
    from NetSym.gui.user_interface.user_interface import UserInterface


class SelectingSquare(GraphicsObject):
    """
    The square that is drawn when one drags the mouse over the screen.
    It allows one to select multiple items at the same time.
    """
    def __init__(self,
                 x: float, y: float,
                 graphics_objects: Iterable[ImageGraphics],
                 user_interface: UserInterface) -> None:
        """
        initiates the square with the coordinates of the initial mouse press,
        after that, the other coordinates will be of the mouse.
        """
        super(SelectingSquare, self).__init__(x, y, is_pressable=False)
        self.graphics_objects = graphics_objects
        self.user_interface = user_interface

    @property
    def width(self) -> float:
        return abs(self.x - MainWindow.main_window.get_mouse_location()[0])

    @property
    def height(self) -> float:
        return abs(self.y - MainWindow.main_window.get_mouse_location()[1])

    def dict_save(self) -> None:
        pass

    def draw(self) -> None:
        """
        draws the rectangle.
        :return:
        """
        mouse_location = MainWindow.main_window.get_mouse_location()
        draw_rect_by_corners(self.location, mouse_location, outline_color=SELECTION_SQUARE.COLOR, outline_width=1)

    def __contains__(self, item: Union[Tuple[float, float], ImageGraphics]) -> bool:
        """
        Returns whether or not another graphics object is inside of the selecting object.
        :param item:
        :return:
        """
        x1, y1 = self.location
        x2, y2 = MainWindow.main_window.get_mouse_location()
        points = [(x1, y1), (x2, y2), (x1, y2), (x2, y1)]
        sorted_points = list(sorted(sorted(points, key=itemgetter(0)), key=itemgetter(1)))
        (bottom_left_x, bottom_left_y), (upper_right_x, upper_right_y) = sorted_points[0], sorted_points[-1]

        if isinstance(item, tuple) and len(item) == 2:
            x, y = item
            return bottom_left_x < x < upper_right_x and bottom_left_y < y < upper_right_y
        elif isinstance(item, ImageGraphics):
            return any(corner in self for corner in item.corners)
        raise WrongUsageError("Receives a tuple or a graphics object only!")

    def move(self) -> None:
        self.select_objects()

    def select_objects(self) -> None:
        """
        Take in a list of objects. Select the objects that are inside the square.
        """
        for graphics_object in self.graphics_objects:
            if graphics_object not in self.user_interface.marked_objects:
                if graphics_object in self:
                    self.user_interface.marked_objects.append(graphics_object)
                continue

            if graphics_object not in self:
                self.user_interface.marked_objects.remove(graphics_object)
