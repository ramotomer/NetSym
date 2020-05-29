from collections import namedtuple

from pyglet.window import key

from consts import *
from gui.abstracts.graphics_object import GraphicsObject
from gui.main_loop import MainLoop
from gui.main_window import MainWindow
from gui.shape_drawing import draw_rect, draw_rect_with_outline
from gui.user_interface.button import Button
from gui.user_interface.text_graphics import Text
from usefuls import with_args

ChildGraphicsObjects = namedtuple('ChildGraphicsObjects', [
    "text",
    "ok_button",
    "exit_button",
])


class PopupWindow(GraphicsObject):
    """

    """
    def __init__(self, x, y, text, user_interface):
        """
        Initiates the `PopupTextBox` object.

        :param text: the text for `self._text` attribute.
        :param action: the action that will be activated when the button is pressed.
            It should be a function that receives one string argument (the inserted string) and returns None.
        """
        super(PopupWindow, self).__init__(x, y)
        self.outline_color = TEXTBOX_OUTLINE_COLOR

        title_text = Text(text, self.x, self.y, self, (TEXTBOX_WIDTH / 2, 6 * TEXTBOX_HEIGHT / 7))

        ok_button = Button(
            self.x + (TEXTBOX_WIDTH / 2) - (SUBMIT_BUTTON_WIDTH / 2),
            self.y + 8,
            text="OK",
            width=SUBMIT_BUTTON_WIDTH
        )
        ok_button.set_parent_graphics(self, ((TEXTBOX_WIDTH / 2) - (SUBMIT_BUTTON_WIDTH / 2), 8))
        ok_button.key = (key.ENTER, NO_MODIFIER)

        exit_button = Button(
            self.x + (TEXTBOX_WIDTH / 2) - (SUBMIT_BUTTON_WIDTH / 2),
            self.y + 8,
            text="X",
            width=TEXTBOX_UPPER_PART_HEIGHT,
            height=TEXTBOX_UPPER_PART_HEIGHT,
            color=self.outline_color,
            text_color=BLACK,
        )
        exit_button.set_parent_graphics(self, (TEXTBOX_WIDTH - TEXTBOX_UPPER_PART_HEIGHT, TEXTBOX_HEIGHT))
        exit_button.key = (key.ESCAPE, NO_MODIFIER)

        self.remove_buttons = None
        user_interface.register_window(self, ok_button, exit_button)

        self.unregister_from_user_interface = with_args(user_interface.unregister_window, self)

        ok_button.action = self.delete
        exit_button.action = self.delete

        self.child_graphics_objects = ChildGraphicsObjects(
            title_text,
            ok_button,
            exit_button,
        )

    def is_mouse_in(self):
        """
        Returns whether or not the mouse is pressing the upper part of the window (where it can be moved)
        :return: `bool`
        """
        x, y = MainWindow.main_window.get_mouse_location()
        return self.x < x < self.x + TEXTBOX_WIDTH and \
            self.y + TEXTBOX_HEIGHT < y < self.y + TEXTBOX_HEIGHT + TEXTBOX_UPPER_PART_HEIGHT

    def mark_as_selected(self):
        """
        required for the API
        :return: None
        """
        pass

    def delete(self):
        """
        Deletes the window and removes it from the UserInterface.popup_windows list
        :return: None
        """
        MainLoop.instance.unregister_graphics_object(self)
        self.remove_buttons()
        self.unregister_from_user_interface()

    def draw(self):
        """
        Draws the popup window (text box) on the screen.
        Basically a rectangle.
        :return: None
        """
        draw_rect_with_outline(self.x, self.y,
                               TEXTBOX_WIDTH, TEXTBOX_HEIGHT,
                               TEXTBOX_COLOR, self.outline_color, TEXTBOX_OUTLINE_WIDTH)
        draw_rect(self.x - (TEXTBOX_OUTLINE_WIDTH / 2), self.y + TEXTBOX_HEIGHT,
                  TEXTBOX_WIDTH + TEXTBOX_OUTLINE_WIDTH, TEXTBOX_UPPER_PART_HEIGHT,
                  self.outline_color)

    def __str__(self):
        return "A popup window"
