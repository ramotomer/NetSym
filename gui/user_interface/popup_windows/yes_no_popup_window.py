from pyglet.window import key

from consts import *
from gui.user_interface.button import Button
from gui.user_interface.popup_windows.popup_window import PopupWindow
from usefuls import called_in_order


class YesNoPopupWindow(PopupWindow):
    """
    This is a window that asks a yes/no question, performs an action according to each button
    """
    def __init__(self, text, user_interface, yes_action=lambda: None, no_action=lambda: None):
        """
        :param user_interface: the UserInterface object
        :param yes_action: function that is called when the yes button is pressed.
        :param no_action:
        """
        buttons = [
            Button(
                *WINDOWS.POPUP.YES_BUTTON_COORDINATES,
                called_in_order(yes_action, self.delete),
                "yes",
                width=WINDOWS.POPUP.SUBMIT_BUTTON.WIDTH,
                key=(key.ENTER, KEYBOARD.MODIFIERS.NONE),
            ),
            Button(
                *WINDOWS.POPUP.NO_BUTTON_COORDINATES,
                called_in_order(no_action, self.delete),
                "no",
                width=WINDOWS.POPUP.SUBMIT_BUTTON.WIDTH,
            ),
        ]

        super(YesNoPopupWindow, self).__init__(
            *WINDOWS.POPUP.TEXTBOX.COORDINATES,
            text=text,
            user_interface=user_interface,
            buttons=buttons,
            color=COLORS.ORANGE,
            title="yes or no",
        )
