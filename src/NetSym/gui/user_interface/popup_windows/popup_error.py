from __future__ import annotations

from pyglet.window import key

from NetSym.consts import WINDOWS, KEYBOARD, COLORS, T_Color
from NetSym.gui.user_interface.button import Button
from NetSym.gui.user_interface.popup_windows.popup_window_containing_text import PopupWindowContainingText


class PopupError(PopupWindowContainingText):
    """
    This is a window that pops up when some error occurs and we would like to inform a user about it.
    """
    def __init__(self,
                 text: str,
                 color: T_Color = COLORS.RED) -> None:
        """
        Initiates the window
        """
        x, y = WINDOWS.POPUP.TEXTBOX.COORDINATES
        super(PopupError, self).__init__(
            x, y,
            text=text,
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

    def __repr__(self) -> str:
        return f"<< PopupError(text={self.information_text.text!r}) >>"
