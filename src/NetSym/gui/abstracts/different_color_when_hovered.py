from __future__ import annotations

from abc import abstractmethod

from NetSym.gui.abstracts.graphics_object import GraphicsObject


class DifferentColorWhenHovered(GraphicsObject):
    @abstractmethod
    def set_hovered_color(self) -> None:
        """Sets the colored as it should be when the mouse is hovering over the object"""

    @abstractmethod
    def set_normal_color(self) -> None:
        """Sets the colored as it should be when the mouse is hovering over the object"""
