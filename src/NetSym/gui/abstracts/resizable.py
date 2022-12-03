from __future__ import annotations

from abc import abstractmethod
from typing import Tuple

from NetSym.gui.abstracts.selectable import Selectable


class Resizable(Selectable):
    """
    Describes an object that has a changeable size
    """
    @abstractmethod
    def resize(self, width_diff: float, height_diff: float, constrain_proportions: bool = False) -> None:
        """
        Change the size of the GraphicsObject by a certain amount
        """

    @abstractmethod
    def get_corner_by_direction(self, direction: Tuple[int, int]) -> Tuple[float, float]:
        """
        Returns the location of a corner based on a direction, which is a tuple indicating the
        sign (positivity or negativity) of the corner
        :param direction: (1, 1) for example, or (0, -1)
        """
