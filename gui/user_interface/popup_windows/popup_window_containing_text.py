from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from consts import WINDOWS, T_Color, SHAPES
from gui.user_interface.popup_windows.popup_window import PopupWindow
from gui.user_interface.text_graphics import Text

if TYPE_CHECKING:
    from gui.user_interface.user_interface import UserInterface
    from gui.user_interface.button import Button


class PopupWindowContainingText(PopupWindow):
    """
    This ia a popup window that should contain some static text (error message, an input request from the user, etc...)
    """

    def __init__(self,
                 x: float,
                 y: float,
                 text: str,
                 user_interface: UserInterface,
                 buttons: Optional[List[Button]] = None,
                 width: float = WINDOWS.POPUP.TEXTBOX.WIDTH,
                 height: float = WINDOWS.POPUP.TEXTBOX.HEIGHT,
                 color: T_Color = WINDOWS.POPUP.TEXTBOX.OUTLINE_COLOR,
                 title: str = "window!",
                 outline_width: int = SHAPES.RECT.DEFAULT_OUTLINE_WIDTH) -> None:
        """
        Initiate the window
        """
        super(PopupWindowContainingText, self).__init__(x, y, user_interface, buttons, width, height, color, title, outline_width)
        self.information_text = Text(
            text,
            self.x, self.y,
            self,
            ((self.width / 2), self.height - 25),
            max_width=self.width
        )

        self.child_graphics_objects = [
            self.title_text,
            self.information_text,
            self.exit_button,
        ] + buttons
