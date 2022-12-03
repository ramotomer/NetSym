from __future__ import annotations

from abc import abstractmethod, ABC


class UniquelyDragged(ABC):
    """
    A GraphicsObject that does something special when you drag it
    """
    @abstractmethod
    def drag(self, mouse_x: float, mouse_y: float, drag_x: float, drag_y: float) -> None:
        """
        What to do when the object is dragged around
        """
