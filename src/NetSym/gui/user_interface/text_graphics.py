from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

import pyglet

from NetSym.consts import TEXT, T_Color, WINDOWS
from NetSym.exceptions import *
from NetSym.gui.abstracts.user_interface_graphics_object import UserInterfaceGraphicsObject

if TYPE_CHECKING:
    from NetSym.gui.abstracts.graphics_object import GraphicsObject


class Text(UserInterfaceGraphicsObject):
    """
    This represents permanent text on the screen.

    The text that is drawn on the screen is kept because if it is created each
    time the screen is updated (like it was before) the program crashes and says it is out of memory.
    Apparently pyglet is having a lot of trouble drawing text.
    """
    def __init__(self, text: str,
                 x: float, y: float,
                 parent_graphics: Optional[GraphicsObject] = None,
                 padding: Tuple[float, float] = (0, TEXT.DEFAULT_Y_PADDING),
                 is_button: bool = False,
                 start_hidden: bool = False,
                 max_width: float = WINDOWS.MAIN.WIDTH,
                 font_size: float = TEXT.FONT.DEFAULT_SIZE,
                 align: str = TEXT.ALIGN.CENTER,
                 color: T_Color = TEXT.COLOR,
                 font: str = TEXT.FONT.DEFAULT) -> None:
        """
        Initiates a new `Text` object.
        A `Text` object can have a parent `GraphicsObject` which it will set its coordinates according to it. (if it
            moves, the text moves with it)
        At all times, the coordinates of the `Text` object will be the ones of the `parent_graphics` object plus the
        padding.

        The coordinates `x` and `y` of the `Text` object are in the middle of
        the first line that is drawn on the screen.
        :param text: the actual string that is presented.
        :param x:
        :param y: coordinates
        :param parent_graphics: a `GraphicsObject` to follow
        :param padding: a tuple of x and y padding around the parent object.
        :param is_button:  whether or not this text is on a button (for `hide` and `show` of buttons)
        :param start_hidden:  whether or not to start off hidden.
        :param max_width:  The maximum length that this text is allowed to reach in one line.
        :param font_size: THE FONT SIZE!!!!!!!!!!!!!!!
        :param color: the text color- defaults to white.
        """
        super(Text, self).__init__(x, y, centered=True)
        self._text = text
        self.is_button = is_button  # whether or not it is on a text on a button
        self.is_hidden = start_hidden
        self.max_width = max_width
        self.font_size = font_size
        self.align = align
        self.color = color
        self.font = font

        self._label: Optional[pyglet.text.Label] = None
        if parent_graphics is not None:
            self.set_parent_graphics(parent_graphics, padding)
        self.set_text(text)

    @property
    def text(self) -> str:
        return self._text

    @property
    def label(self) -> pyglet.text.Label:
        if self._label is None:
            raise GraphicsObjectNotYetInitialized

        return self._label

    def set_text(self, text: str, hard_refresh: bool = False) -> None:
        """
        The correct way to update the text of a `Text` object.
        updates the text and corrects the lines and everything necessary.
        :param text: a string which is the new text.
        :param hard_refresh: whether or not to recreate the `Label` object of the text
        :return: None
        """
        x_padding, y_padding = (0, 0) if not self.padding else self.padding

        self._text = text
        if not self._label or hard_refresh:
            self._label = pyglet.text.Label(self._text,
                                           font_name=self.font,
                                           font_size=self.font_size,
                                           x=self.x + x_padding, y=(self.y + y_padding),
                                           color=self.color + (255,),
                                           anchor_x='center', anchor_y='top',
                                           align=self.align)
        else:
            self._label.text = self._text

        self.label.width = self.max_width
        self.label.multiline = True
        self.x, self.y = self.label.x, self.label.y
        self.move()

    def refresh_text(self) -> None:
        """
        Enforce text parameters on actual visible text on the screen (update it)
        """
        self.set_text(self._text, hard_refresh=True)

    def append_text(self, text: str) -> None:
        """
        appends a string to the end of the text of the `Text` object.
        :param text:
        :return:
        """
        self.set_text(self.text + text)

    def draw(self) -> None:
        """
        Draws the text to the screen
        :return: None
        """
        # debug_circle(self.x, self.y)
        if not self.is_hidden:
            self.label.draw()

    def show(self) -> None:
        """
        Shows the text if it is hidden
        :return: None
        """
        self.is_hidden = False

    def hide(self) -> None:
        """
        Hides the text if it is is_showing.
        :return: None
        """
        self.is_hidden = True

    def move(self) -> None:
        """
        Moves the text according to the parent object's location.
        :return: None
        """
        if self.parent_graphics is None:
            self.label.x, self.label.y = self.x, self.y
            return
        super(Text, self).move()
        self.label.x, self.label.y = self.x, self.y

    def resize(self, new_padding: Tuple[float, float], new_max_size: float) -> None:
        self.padding = new_padding
        self.max_width = new_max_size
        self.refresh_text()

    def __str__(self) -> str:
        return f"Text Graphics: '{self.text}'"

    def __repr__(self) -> str:
        return f"Text(text={self.text!r})"
