from __future__ import annotations

from typing import Callable

from pyglet.window import key

from NetSym.consts import WINDOWS, COLORS, KEYBOARD
from NetSym.gui.user_interface.button import Button
from NetSym.gui.user_interface.popup_windows.popup_window_containing_text import PopupWindowContainingText
from NetSym.usefuls.funcs import called_in_order


class YesNoPopupWindow(PopupWindowContainingText):
    """
    This is a window that asks a yes/no question, performs an action according to each button
    """
    def __init__(self,
                 text: str,
                 yes_action: Callable = lambda: None,
                 no_action: Callable = lambda: None) -> None:
        """
        :param yes_action: function that is called when the 'yes' button is pressed.
        :param no_action: function that is called when the 'no' button is pressed.
        """
        yes_x, yes_y = WINDOWS.POPUP.YES_BUTTON_COORDINATES
        no_x, no_y = WINDOWS.POPUP.NO_BUTTON_COORDINATES

        buttons = [
            Button(
                yes_x, yes_y,
                called_in_order(yes_action, self.delete),
                "yes",
                width=WINDOWS.POPUP.SUBMIT_BUTTON.WIDTH,
                key=(key.ENTER, KEYBOARD.MODIFIERS.NONE),
            ),
            Button(
                no_x, no_y,
                called_in_order(no_action, self.delete),
                "no",
                width=WINDOWS.POPUP.SUBMIT_BUTTON.WIDTH,
            ),
        ]

        textbox_x, textbox_y = WINDOWS.POPUP.TEXTBOX.COORDINATES
        super(YesNoPopupWindow, self).__init__(
            textbox_x, textbox_y,
            text=text,
            buttons=buttons,
            color=COLORS.ORANGE,
            title="yes or no",
        )
