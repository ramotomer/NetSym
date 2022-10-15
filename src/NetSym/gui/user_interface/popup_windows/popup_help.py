from __future__ import annotations

import os
from typing import TYPE_CHECKING

from pyglet.window import key

from NetSym.consts import DIRECTORIES, COLORS, WINDOWS, KEYBOARD
from NetSym.gui.user_interface.button import Button
from NetSym.gui.user_interface.popup_windows.popup_window_containing_text import PopupWindowContainingText

if TYPE_CHECKING:
    from NetSym.gui.user_interface.user_interface import UserInterface


class PopupHelp(PopupWindowContainingText):
    """
    A window that shows you the help menu
    """
    def __init__(self, user_interface: UserInterface) -> None:
        """
        """
        text = open(os.path.join(DIRECTORIES.FILES, "help_message.txt"), 'r').read()
        x, y = WINDOWS.POPUP.HELP.COORDINATES
        ok_button_x, ok_button_y = WINDOWS.POPUP.HELP.COORDINATES
        super(PopupHelp, self).__init__(
            x, y,
            text,
            user_interface,
            buttons=[
                Button(
                    ok_button_x, ok_button_y,
                    text="EXIT",
                    width=WINDOWS.POPUP.SUBMIT_BUTTON.WIDTH,
                    key=(key.ENTER, KEYBOARD.MODIFIERS.NONE),
                    action=self.delete,
                ),
            ],
            color=COLORS.PURPLE,
            title="help!",
            width=WINDOWS.POPUP.HELP.WIDTH,
            height=WINDOWS.POPUP.HELP.HEIGHT,
        )
