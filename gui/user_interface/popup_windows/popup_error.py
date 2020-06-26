from pyglet.window import key

from consts import *
from gui.user_interface.button import Button
from gui.user_interface.popup_windows.popup_window import PopupWindow


class PopupError(PopupWindow):
    """
    This is a window that pops up when some error occurs and we would like to inform a user about it.
    """
    def __init__(self, text, user_interface):
        """
        Initiates the window
        """
        super(PopupError, self).__init__(
            *TEXTBOX_COORDINATES,
            text=text,
            user_interface=user_interface,
            buttons=[
                Button(
                    *SUBMIT_BUTTON_COORDINATES,
                    text="OK",
                    width=SUBMIT_BUTTON_WIDTH,
                    key=(key.ENTER, NO_MODIFIER),
                    action=self.delete,
                ),
            ],
            color=RED,
            title="error!",
        )

    def __repr__(self):
        return "Popup Error window"
