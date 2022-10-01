from __future__ import annotations

from typing import NamedTuple, Callable, Optional

from consts import *
from gui.abstracts.user_interface_graphics_object import UserInterfaceGraphicsObject
from gui.main_window import MainWindow
from gui.shape_drawing import draw_button
from gui.user_interface.text_graphics import Text
from usefuls.funcs import sum_tuples


class ChildGraphicsObjects(NamedTuple):
    text: Text


class Button(UserInterfaceGraphicsObject):
    """
    A class of a button which you can press and assign text and an action to.
    """
    def __init__(self,
                 x: float,
                 y: float,
                 action: Callable[[], None] = lambda: None,
                 text: str = BUTTONS.DEFAULT_TEXT,
                 start_hidden: bool = False,
                 width: float = BUTTONS.DEFAULT_WIDTH,
                 height: float = BUTTONS.DEFAULT_HEIGHT,
                 key: Optional[Tuple[int, int]] = None,
                 color: T_Color = BUTTONS.COLOR,
                 text_color: T_Color = BUTTONS.TEXT_COLOR,
                 is_outlined: bool = True,
                 custom_active_color: Optional[T_Color] = None) -> None:
        """
        Initiates the button.
        :param x:
        :param y: coordinates of the bottom left
        :param action: a function that will be called when the button is pressed.
        :param text: a string that will be written on the button.
            in the same group.
        :param start_hidden: whether or not this button should be created hidden, and only later shown.
        :param width: the button's width.
        :param height: the button's height.
        :param custom_active_color: the color the button will be once it is hovered. If None - will be the same color but a little lighter
        """
        super(Button, self).__init__(x, y)
        self.initial_location = x, y
        self.is_button = True
        self.is_hidden = start_hidden

        self.width, self.height = width, height
        self.action = action
        self.child_graphics_objects = ChildGraphicsObjects(
            Text(text, x, y, self, (self.width / 2, self.height / 2 + BUTTONS.TEXT_PADDING),
                 is_button=True,
                 start_hidden=start_hidden,
                 max_width=WINDOWS.SIDE.WIDTH,
                 color=text_color),
        )
        self.key = key

        self.color = color
        self.is_outlined = is_outlined
        self.__custom_active_color = custom_active_color

    @property
    def light_color(self) -> T_Color:
        return tuple(int(rgb + COLORS.COLOR_DIFF) for rgb in self.color)
    
    @property
    def active_color(self) -> T_Color:
        return self.__custom_active_color if self.__custom_active_color is not None else self.light_color

    def is_mouse_in(self) -> bool:
        """Returns whether or not the mouse is located inside of the button."""
        mouse_x, mouse_y = MainWindow.main_window.get_mouse_location()
        return (self.x < mouse_x < self.x + self.width) and \
               (self.y < mouse_y < self.y + self.height)

    def toggle_showing(self) -> None:
        """
        Hides the button when it is not in use (when it is not supposed to be pressed)
        If the button is hidden now, shows it.
        """
        self.is_hidden = not self.is_hidden
        self.child_graphics_objects.text.is_hidden = not self.child_graphics_objects.text.is_hidden

    def hide(self) -> None:
        """
        Hides the button so it cannot be pressed or seen
        """
        self.is_hidden = True
        self.child_graphics_objects.text.hide()

    def show(self) -> None:
        """
        Shows the button again if it was hidden, allows it to be pressed regularly.
        """
        self.is_hidden = False
        self.child_graphics_objects.text.show()

    def draw(self) -> None:
        """
        Draws the button (If it is not hidden).
        :return: None
        """
        if not self.is_hidden:
            draw_button(self.x, self.y, self.width, self.height,
                        color=(self.active_color if self.is_mouse_in() else self.color),
                        outline_width=(BUTTONS.OUTLINE_WIDTH if self.is_outlined else 0))

    def move(self) -> None:
        """
        Moves the button according to its parent graphics (if it has any)
        :return: None
        """
        if self.parent_graphics is not None:
            self.x, self.y = sum_tuples(self.parent_graphics.location, self.padding)

    def __str__(self) -> str:
        state = "[HIDDEN]" if self.is_hidden else "[SHOWING]"
        return f"{state} '{self.child_graphics_objects.text.text}'"

    def __repr__(self) -> str:
        return f"Button('{self.child_graphics_objects.text}')"
