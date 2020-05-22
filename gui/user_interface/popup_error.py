from consts import *
from gui.user_interface.popup_window import PopupWindow


class PopupError(PopupWindow):
    """
    This is a window that pops up when some error occurs and we would like to inform a user about it.
    """
    def __init__(self, text, user_interface):
        """
        Initiates the window
        """
        super(PopupError, self).__init__(*TEXTBOX_COORDINATES, text, user_interface)
        self.outline_color = RED
        self.child_graphics_objects.exit_button.color = RED

    def __repr__(self):
        return "Popup Error window"
