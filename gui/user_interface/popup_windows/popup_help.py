import os

from pyglet.window import key

from consts import DIRECTORIES, COLORS, WINDOWS, KEYBOARD
from gui.user_interface.button import Button
from gui.user_interface.popup_windows.popup_window import PopupWindow


class PopupHelp(PopupWindow):
    """
    A window that shows you the help menu
    """
    def __init__(self, user_interface):
        """
        """
        text = open(os.path.join(DIRECTORIES.FILES, "help_message.txt"), 'r').read()
        super(PopupHelp, self).__init__(
            *WINDOWS.POPUP.HELP.COORDINATES,
            text,
            user_interface,
            buttons=[
                Button(
                    *WINDOWS.POPUP.HELP.OK_BUTTON_COORDINATES,
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
