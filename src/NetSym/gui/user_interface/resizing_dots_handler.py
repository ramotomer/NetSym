from __future__ import annotations

from itertools import product
from typing import List, Optional, Protocol, Tuple

from NetSym.gui.user_interface.resizing_dot import ResizingDot


class Resizable(Protocol):
    def mark_as_selected(self) -> None:
        ...

    def get_corner_by_direction(self, direction: Tuple[int, int]) -> Tuple[float, float]:
        ...


class ResizingDotsHandler:
    """
    This class is responsible for all code that deals with the small ResizingDots that objects have around them
    """
    def __init__(self, dots: Optional[List[ResizingDot]] = None) -> None:
        """
        Initiates the object
        """
        self.dots: List[ResizingDot] = dots if dots is not None else []
        self.resized_object = None

    def select(self, graphics_object: Resizable) -> None:
        """
        Set the object that currently has the dots around it
        """
        self.resized_object = graphics_object

    def deselect(self) -> None:
        """
        Make it so no object currently has dots around it
        """
        self.resized_object = None

    def _create_dot(self, direction: Tuple[int, int], constrain_proportions: bool = False) -> None:
        """
        Create a new `ResizingDot` at the appropriate location
        """
        corner_x, corner_y = self.resized_object.get_corner_by_direction(direction)
        self.dots.append(ResizingDot(corner_x, corner_y, self.resized_object, direction, constrain_proportions))

    def _create_new_dots(self) -> bool:
        """
        Check if it is necessary to create `ResizingDot`s for any object at the moment
        If it is the case, create all of them
        :return: Whether or not new dots were created at this time
        """
        if any(dot.resized_object is self.resized_object for dot in self.dots):
            return False

        if self.resized_object is None:
            return False

        for direction in map(tuple, set(product((-1, 0, 1), repeat=2)) - {(0, 0)}):
            self._create_dot(direction, constrain_proportions=(0 not in direction))
        return True

    def _remove_old_dots(self) -> None:
        """
        Test all dots to see that they all belong to the currently displayed object
        Remove and unregister the ones that do not.
        """
        for dot in self.dots[:]:
            if dot.resized_object is not self.resized_object:
                dot.unregister()
                self.dots.remove(dot)

    def update_dot_state(self) -> bool:
        """
        Perform all of the actions `ResizingDot`s require doing periodically
        Returns whether or not new `ResizingDot`s where created at this time (So the MainLoop will know to register them as new `GraphicsObject`s
        """
        self._remove_old_dots()
        has_new_dots = self._create_new_dots()
        return has_new_dots
