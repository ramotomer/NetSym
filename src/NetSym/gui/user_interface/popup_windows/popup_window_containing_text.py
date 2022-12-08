from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Sequence, Iterable, NamedTuple, List, Iterator

from NetSym.consts import WINDOWS, T_Color, SHAPES
from NetSym.gui.user_interface.popup_windows.popup_window import PopupWindow
from NetSym.gui.user_interface.text_graphics import Text

if TYPE_CHECKING:
    from NetSym.gui.abstracts.graphics_object import GraphicsObject
    from NetSym.gui.user_interface.button import Button


class ChildGraphicsObjects(NamedTuple):
    title_text:       Text
    information_text: Text
    exit_button:      Button
    buttons:          List[Button]

    def __iter__(self) -> Iterator[GraphicsObject]:
        return iter([self.title_text, self.information_text, self.exit_button] + self.buttons)


class PopupWindowContainingText(PopupWindow):
    """
    This ia a popup window that should contain some static text (error message, an input request from the user, etc...)
    """

    def __init__(self,
                 x: float,
                 y: float,
                 text: str,
                 buttons: Optional[Sequence[Button]] = None,
                 width: float = WINDOWS.POPUP.TEXTBOX.WIDTH,
                 height: float = WINDOWS.POPUP.TEXTBOX.HEIGHT,
                 color: T_Color = WINDOWS.POPUP.TEXTBOX.OUTLINE_COLOR,
                 title: str = "window!",
                 outline_width: float = SHAPES.RECT.DEFAULT_OUTLINE_WIDTH) -> None:
        """
        Initiate the window
        """
        super(PopupWindowContainingText, self).__init__(x, y, buttons, width, height, color, title, outline_width)
        self.information_text = Text(
            text,
            self.x, self.y,
            self,
            ((self.width / 2), self.height - 25),
            max_width=self.width
        )

        self.__child_graphics_objects = ChildGraphicsObjects(
            self.title_text,
            self.information_text,
            self.exit_button,
            (buttons if buttons is not None else [])
        )

    def get_title_text(self) -> Text:
        return self.__child_graphics_objects.title_text

    def get_information_text(self) -> Text:
        return self.__child_graphics_objects.information_text

    def get_exit_button(self) -> Button:
        return self.__child_graphics_objects.exit_button

    def get_children(self) -> Iterable[GraphicsObject]:
        return self.__child_graphics_objects
