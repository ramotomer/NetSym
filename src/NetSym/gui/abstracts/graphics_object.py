from __future__ import annotations

from abc import abstractmethod, ABC
from typing import Tuple, TYPE_CHECKING, Dict, List, Optional, Iterable, Union

from NetSym.gui.main_loop_function_to_call import FunctionToCall

if TYPE_CHECKING:
    from NetSym.gui.user_interface.user_interface import UserInterface


class GraphicsObject(ABC):
    """
    This is an abstract class that its instances are things that will be drawn on the screen, for example the images of
    the computer, the packets the lines that connect the computers and the buttons.

    They have to have a `draw`, a `move` and a `load` method.
    When a graphics object is created, it inserts itself into the main loop of the program.
    Every call of the main loop function will call its `draw` and `move` methods.
    The `draw` should contain the drawing of the object while the `move` should contain its movement. Reasonable I would say.

    """
    def __init__(self,
                 x: float,
                 y: float,
                 do_render: bool = True,
                 centered: bool = False,
                 is_in_background: bool = False,
                 is_pressable: bool = False) -> None:
        """
        Initiates a graphics object and registers it to the main loop.
        :param x: x coordinate
        :param y: y coordinate
        :param do_render: whether the GraphicsObject is rendered or not.
        :param centered: whether the coordinates of object are in the middle of the sprite or the bottom left point.
        :param is_in_background: whether the object is drawn in the back or the front of the other objects.
        :param is_pressable: whether or not this object can be clicked on.
        """
        self.x = x
        self.y = y
        self.do_render = do_render
        self.centered = centered
        self.is_pressable = is_pressable

        self.is_requesting_to_be_unregistered_from_main_loop = False
        self.is_requesting_to_register_children         = False

        # if self.do_render:
        # MainLoop.instance.register_graphics_object(self, is_in_background)

    @property
    def location(self) -> Tuple[float, float]:
        """
        The location property of the `GraphicsObject`.
        :return: (self.x, self.y)
        """
        return self.x, self.y

    @location.setter
    def location(self, new_location: Tuple[float, float]) -> None:
        self.x, self.y = new_location

    @property
    def additional_functions_to_register(self) -> List[FunctionToCall]:
        """
        The functions that will be registered to run periodically when the object is registered
        """
        return []

    def get_children(self) -> Iterable[Union[GraphicsObject, Iterable[GraphicsObject]]]:
        """
        Return the children of this graphics object.
        The children are graphics objects that are related to this one - they will be registered, and deleted
            whenever this parent will.
        """
        return []

    def is_in(self, x: float, y: float) -> bool:
        """
        Returns whether or not the mouse is located inside this graphics object.
        :return: None
        """
        return False

    def load(self) -> None:
        """
        The function that should load the object.
        It is called only once at the start of the object's lifetime.
        :return: None
        """
        pass

    @abstractmethod
    def draw(self) -> None:
        """
        This method should be overridden in any subclasses.
        It should handle the drawing of the object to the screen, it will be called every loop of the program.
        :return: None
        """
        pass

    def move(self) -> None:
        """
        This method should be overridden in any subclasses.
        It should handle the moving of the object on the screen, it will be called every loop of the program.
        :return: None
        """
        pass

    def __repr__(self) -> str:
        """The string representation of the graphics object"""
        rendered = 'rendered' if self.do_render else 'non-rendered'
        centered = 'centered' if self.centered else 'non-centered'
        return ' '.join([rendered, centered]) + f" GraphicsObject(x={self.x}, y={self.y})"

    @abstractmethod
    def dict_save(self) -> Dict:
        """
        Returns a representation of the object as a dict (that will be converted to string in the end).
        The object should be able to be initiated from the string alone to the exact state that it is in now.
        :return: str
        """
        pass

    def unregister(self) -> None:
        """
        Request from the MainLoop for this object to be unregistered
        """
        self.is_requesting_to_be_unregistered_from_main_loop = True

    def register_children(self) -> None:
        """
        Request from the MainLoop to go over the 'child_graphics_objects' and register the ones that are not registered
        """
        self.is_requesting_to_register_children = True

    def delete(self, user_interface: Optional[UserInterface]) -> None:
        """
        Deletes the graphics object and performs other operations that are necessary for deletion (cleanup)
        """
        self.unregister()
