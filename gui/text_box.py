from collections import namedtuple

from pyglet.window import key

from consts import *
from gui.main_window import MainWindow
from gui.popup_window import PopupWindow
from gui.text_graphics import Text
from usefuls import called_in_order

ChildGraphicsObjects = namedtuple("ChildGraphicsObjects", [
    "title_text",
    "written_text",
    "submit_button"
])


class TextBox(PopupWindow):
    """
    A popup window - a text box that asks for text and does an action with it.
    The `TextBox` has a field of text that you fill up and a below it a button with a 'submit' on it.
    """
    def __init__(self, text, user_interface, action=lambda s: None):
        """
        Initiates the `TextBox` object.

        :param text: the text for `self._text` attribute.
        :param action: the action that will be activated when the button is pressed.
            It should be a function that receives one string argument (the inserted string) and returns None.
        """
        super(TextBox, self).__init__(*TEXTBOX_COORDINATES, text, user_interface)
        self.action = action
        self.outline_color = TEXTBOX_OUTLINE_COLOR
        title_text, submit_button = self.child_graphics_objects

        written_text = Text('', title_text.x, title_text.y - 20, title_text, padding=(0, -20), max_width=TEXTBOX_WIDTH)

        submit_button.child_graphics_objects.text.set_text("SUBMIT")
        submit_button.action = called_in_order(
            self.submit,
            self.delete,
        )

        self.child_graphics_objects = ChildGraphicsObjects(
            title_text,
            written_text,
            submit_button,
        )

        self.is_done = False  # whether or not the window is done and completed the action of the submit button.

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
        :return:
        """
        pass

    @staticmethod
    def _is_printable(char_ord):
        """Receives an order of a character and returns whether or not that character is printable or not"""
        return 0x1f < char_ord < 0x7f

    def pressed(self, symbol, modifiers):
        """
        This is called when the user is typing the string into the `TextBox`.
        :param symbol: a string of the key that was pressed.
        :param modifiers: a bitwise representation of what other button were also pressed (CTRL_MODIFIER, SHIFT_MODIFIER, etc...)
        :return: None
        """
        if symbol == key.ENTER:
            self.submit()
            self.delete()

        elif symbol == key.BACKSPACE:
            self.child_graphics_objects.written_text.set_text(self.child_graphics_objects.written_text.text[:-1])

        elif self._is_printable(symbol):
            char = chr(symbol).lower()
            if (modifiers & SHIFT_MODIFIER) ^ (modifiers & CAPS_MODIFIER):
                char = char.upper()
                if char == '-':
                    char = '_'
                if char == '=':
                    char = '+'
            self.child_graphics_objects.written_text.set_text(self.child_graphics_objects.written_text.text + char)

    def submit(self):
        """
        Submits the text that was written and activates the `self.action` with it.
        :return: None
        """
        self.action(self.child_graphics_objects.written_text.text)
        self.is_done = True

    def __str__(self):
        return "TextBox Graphics"
