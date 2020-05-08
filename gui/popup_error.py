from collections import namedtuple

from pyglet.window import key

from consts import *
from gui.main_loop import MainLoop
from gui.text_box import TextBox
from usefuls import called_in_order
from usefuls import with_args

ChildGraphicsObjects = namedtuple("ChildGraphicsObjects", [
    "title_text",
    "ok_button",
])


class PopupError(TextBox):
    """
    This is a window that pops up when some error occurs and we would like to inform a user about it.
    """
    def __init__(self, text, user_interface):
        """
        Initiates the window
        """
        super(PopupError, self).__init__(text, None)
        self.outline_color = RED
        title, written, ok_button = self.child_graphics_objects

        MainLoop.instance.unregister_graphics_object(written)

        error_buttons = user_interface.buttons.get(ERROR_WINDOW_BUTTONS_ID, [])
        error_buttons.append(ok_button)
        user_interface.buttons[ERROR_WINDOW_BUTTONS_ID] = error_buttons

        ok_button.child_graphics_objects.text.set_text("OK")
        ok_button.child_graphics_objects.text.font_size *= 2
        ok_button.action = called_in_order(
            with_args(MainLoop.instance.unregister_graphics_object, self),
            with_args(user_interface.buttons[ERROR_WINDOW_BUTTONS_ID].remove, ok_button),
        )
        ok_button.key = (key.ENTER, NO_MODIFIER)

        self.child_graphics_objects = ChildGraphicsObjects(
            title,
            ok_button,
        )

    def delete_me(self):
        """
        Deletes this window
        :return:
        """
        MainLoop.instance.unregister_graphics_object(self)

    def __repr__(self):
        return "Popup Error window"
