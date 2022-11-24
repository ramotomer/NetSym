from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, Any, List

from NetSym.exceptions import GraphicsObjectNotYetInitialized

if TYPE_CHECKING:
    from NetSym.gui.abstracts.graphics_object import GraphicsObject


class LogicObject(ABC):
    """
    Every object in the simulation has a `GraphicsObject` that takes care of all of the graphics (picture, location, color, etc...)
    The computing logic and complex algorithm of every object should be held in the `LogicObject`.

    Every `GraphicsObject` knows his `LogicObject`

    For now also every `LogicObject` knows its `GraphicsObject` - I want this to change in the future (to decrease coupling)
    TODO: this ^
    """
    graphics: Optional[GraphicsObject]

    @abstractmethod
    def init_graphics(self, *args: Any, **kwargs: Any) -> List[GraphicsObject]:
        """
        Adds the `GraphicObject` of this class and gives it the parameters it requires.
        """

    def get_graphics(self) -> GraphicsObject:
        """
        Return the graphics object or raise if the `init_graphics` was not yet called
        """
        if self.graphics is None:
            raise GraphicsObjectNotYetInitialized(f"self: {self}, self.graphics: {self.graphics}")
        return self.graphics
