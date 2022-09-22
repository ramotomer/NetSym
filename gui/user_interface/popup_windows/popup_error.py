from __future__ import annotations

from typing import TYPE_CHECKING

from pyglet.window import key

from consts import *
from gui.user_interface.button import Button
from gui.user_interface.popup_windows.popup_window_containing_text import PopupWindowContainingText

if TYPE_CHECKING:
    from gui.user_interface.user_interface import UserInterface


class PopupError(PopupWindowContainingText):
    """
    This is a window that pops up when some error occurs and we would like to inform a user about it.
    """
    def __init__(self,
                 text: str,
                 user_interface: UserInterface,
                 color: T_Color = COLORS.RED) -> None:
        """
        Initiates the window
        """
        x, y = WINDOWS.POPUP.TEXTBOX.COORDINATES
        super(PopupError, self).__init__(
            x, y,
            text=text,
            user_interface=user_interface,
            buttons=[
                Button(
                    *WINDOWS.POPUP.SUBMIT_BUTTON.COORDINATES,
                    text="OK",
                    width=WINDOWS.POPUP.SUBMIT_BUTTON.WIDTH,
                    key=(key.ENTER, KEYBOARD.MODIFIERS.NONE),
                    action=self.delete,
                ),
            ],
            color=color,
            title="error!",
        )

    def __repr__(self):
        return "Popup Error window"
