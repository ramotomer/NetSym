import os
from collections import namedtuple

from pyglet.window import key

from consts import *
from gui.user_interface.button import Button
from gui.user_interface.popup_windows.popup_window import PopupWindow
from gui.user_interface.text_graphics import Text

ChildGraphicsObjects = namedtuple("ChildGraphicsObjects", [
    "title_text",
    "information_text",
    "written_text",
    "submit_button",
    "exit_button",
])


class PopupTextBox(PopupWindow):
    """
    A popup window - a text box that asks for text and does an action with it.
    The `PopupTextBox` has a field of text that you fill up and a below it a button with a 'submit' on it.
    """

    TO_UPPERCASE = {
        '-': '_', '=': '+', '0': ')', '9': '(', '8': '*', '7': '&', '6': '^', '5': '%', '4': '$', '3': '#', '2': '@',
        '1': '!', '`': '~', '/': '?', ',': '<', '.': '>', '[': '{', ']': '}', ';': ':', '\'': '"', '\\': '|'
    }

    def __init__(self, text, user_interface, action=lambda s: None):
        """
        Initiates the `PopupTextBox` object.

        :param text: the text for `self._text` attribute.
        :param action: the action that will be activated when the button is pressed.
            It should be a function that receives one string argument (the inserted string) and returns None.
        """
        submit_button = Button(
            *SUBMIT_BUTTON_COORDINATES,
            self.submit,
            "SUBMIT",
            width=SUBMIT_BUTTON_WIDTH,
            key=(key.ENTER, NO_MODIFIER),
        )

        super(PopupTextBox, self).__init__(*TEXTBOX_COORDINATES,
                                           text=text,
                                           user_interface=user_interface,
                                           buttons=[submit_button],
                                           color=TEXTBOX_OUTLINE_COLOR,
                                           title="input text")

        title_text, information_text, exit_button = self.child_graphics_objects[:3]
        self.action = action

        written_text = Text('', information_text.x, information_text.y - 20,
                            information_text, padding=(0, -20), max_width=TEXTBOX_WIDTH)

        self.child_graphics_objects = ChildGraphicsObjects(
            title_text,
            information_text,
            written_text,
            submit_button,
            exit_button,
        )

        self.is_done = False  # whether or not the window is done and completed the action of the submit button.

        self.old_inputs = ['']
        if os.path.isfile(WINDOW_INPUT_LIST_FILE):
            self.old_inputs = [''] + list(map(lambda line: line.strip(),
                                              reversed(open(WINDOW_INPUT_LIST_FILE, 'r').readlines())))
        self.old_inputs_index = 0

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
        This is called when the user is typing the string into the `PopupTextBox`.
        :param symbol: a string of the key that was pressed.
        :param modifiers: a bitwise representation of what other button were also pressed (CTRL_MODIFIER, SHIFT_MODIFIER, etc...)
        :return: None
        """
        if symbol == key.ENTER:
            self.submit()

        elif symbol == key.ESCAPE:
            self.delete()

        elif symbol == key.BACKSPACE:
            self.child_graphics_objects.written_text.set_text(self.child_graphics_objects.written_text.text[:-1])

        elif symbol == key.UP:
            self.old_inputs_index += 1 if self.old_inputs_index < len(self.old_inputs) - 1 else 0
            self.child_graphics_objects.written_text.set_text(self.old_inputs[self.old_inputs_index])

        elif symbol == key.DOWN:
            self.old_inputs_index -= 1 if self.old_inputs_index > 0 else 0
            self.child_graphics_objects.written_text.set_text(self.old_inputs[self.old_inputs_index])

        elif self._is_printable(symbol):
            char = chr(symbol).lower()
            if (modifiers & SHIFT_MODIFIER) ^ (modifiers & CAPS_MODIFIER):
                char = char.upper()
                char = self.TO_UPPERCASE.get(char, char)
            self.child_graphics_objects.written_text.set_text(self.child_graphics_objects.written_text.text + char)

    def submit(self):
        """
        Submits the text that was written and activates the `self.action` with it.
        :return: None
        """
        input_ = self.child_graphics_objects.written_text.text
        self.add_input_to_file(input_)
        self.action(input_)
        self.delete()
        self.is_done = True

    @staticmethod
    def add_input_to_file(input_):
        """
        Adds another item to the file of inputs given to the window
        :param input_: the input that was entered
        :return: None
        """
        new_file_content = input_

        if os.path.isfile(WINDOW_INPUT_LIST_FILE):
            new_file_content = "{}\n{}".format(open(WINDOW_INPUT_LIST_FILE, 'r').read(), input_)

        open(WINDOW_INPUT_LIST_FILE, 'w').write(new_file_content)

    def __str__(self):
        return "PopupTextBox Graphics"
