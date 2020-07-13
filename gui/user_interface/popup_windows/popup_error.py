from pyglet.window import key

from consts import *
from gui.user_interface.button import Button
from gui.user_interface.popup_windows.popup_window import PopupWindow


class PopupError(PopupWindow):
    """
    This is a window that pops up when some error occurs and we would like to inform a user about it.
    """
    def __init__(self, text, user_interface, color=COLORS.RED):
        """
        Initiates the window
        """
        super(PopupError, self).__init__(
            *WINDOWS.POPUP.TEXTBOX.COORDINATES,
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
