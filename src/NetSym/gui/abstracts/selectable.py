from __future__ import annotations

from abc import abstractmethod

from NetSym.gui.abstracts.graphics_object import GraphicsObject


class Selectable(GraphicsObject):
    """
    a GraphicsObject that can be set as the `selected_object` and surrounded by a blue rectangle
    """
    @abstractmethod
    def mark_as_selected(self) -> None:
        """
        What to draw when the object is selected or marked
        """
