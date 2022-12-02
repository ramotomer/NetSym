from __future__ import annotations

import os
from typing import Callable, NamedTuple

from pyglet.window import key

from NetSym.consts import WINDOWS, KEYBOARD, FILE_PATHS
from NetSym.gui.user_interface.button import Button
from NetSym.gui.user_interface.key_writer import KeyWriter
from NetSym.gui.user_interface.popup_windows.popup_window_containing_text import PopupWindowContainingText
from NetSym.gui.user_interface.text_graphics import Text


class ChildGraphicsObjects(NamedTuple):
    title_text:       Text
    information_text: Text
    written_text:     Text
    submit_button:    Button
    exit_button:      Button


class PopupTextBox(PopupWindowContainingText):
    """
    A popup window - a text box that asks for text and does an action with it.
    The `PopupTextBox` has a field of text that you fill up and a below it a button with a 'submit' on it.
    """

    child_graphics_objects: ChildGraphicsObjects

    def __init__(self,
                 text: str,
                 action: Callable = lambda s: None) -> None:
        """
        Initiates the `PopupTextBox` object.

        :param text: the text for `self._text` attribute.
        :param action: the action that will be activated when the button is pressed.
            It should be a function that receives one string argument (the inserted string) and returns None.
        """
        x, y = WINDOWS.POPUP.SUBMIT_BUTTON.COORDINATES
        submit_button = Button(
            x, y,
            self.submit,
            "SUBMIT",
            width=WINDOWS.POPUP.SUBMIT_BUTTON.WIDTH,
            key=(key.ENTER, KEYBOARD.MODIFIERS.NONE),
        )

        super(PopupTextBox, self).__init__(*WINDOWS.POPUP.TEXTBOX.COORDINATES,
                                           text=text,
                                           buttons=[submit_button],
                                           color=WINDOWS.POPUP.TEXTBOX.OUTLINE_COLOR,
                                           title="input text")

        title_text, information_text, exit_button = self.child_graphics_objects[:3]
        self.action = action

        written_text = Text(
            '',
            information_text.x,
            information_text.y - 35,
            information_text,
            padding=(0, -35),
            max_width=WINDOWS.POPUP.TEXTBOX.WIDTH
        )

        self.child_graphics_objects = ChildGraphicsObjects(
            title_text,
            information_text,
            written_text,
            submit_button,
            exit_button,
        )

        self.is_done = False  # whether or not the window is done and completed the action of the submit button.

        self.old_inputs = ['']
        if os.path.isfile(FILE_PATHS.WINDOW_INPUT_LIST_FILE):
            self.old_inputs = [''] + list(map(lambda line: line.strip(),
                                              reversed(open(FILE_PATHS.WINDOW_INPUT_LIST_FILE, 'r').readlines())))
        self.old_inputs_index = 0

        self.key_writer = KeyWriter(self.write, self.delete_one_char, self.submit, self.delete)
        self.key_writer.add_key_mapping(key.UP, self.scroll_up_through_old_inputs)
        self.key_writer.add_key_mapping(key.DOWN, self.scroll_down_through_old_inputs)

    def scroll_up_through_old_inputs(self) -> None:
        """
        Scrolls up in the window through the old inputs you have already entered before.
        (occurs when you press the UP arrow)
        :return:
        """
        self.old_inputs_index += 1 if self.old_inputs_index < len(self.old_inputs) - 1 else 0
        self.child_graphics_objects.written_text.set_text(self.old_inputs[self.old_inputs_index])

    def scroll_down_through_old_inputs(self) -> None:
        """
        Scrolls down in the window through the old inputs you have already entered before.
        (occurs when you press the DOWN arrow)
        :return:
        """
        self.old_inputs_index -= 1 if self.old_inputs_index > 0 else 0
        self.child_graphics_objects.written_text.set_text(self.old_inputs[self.old_inputs_index])

    def write(self, string: str) -> None:
        """
        Appends a string to the input text in the window.
        :param string:
        :return:
        """
        self.child_graphics_objects.written_text.set_text(self.child_graphics_objects.written_text.text + string)

    def delete_one_char(self) -> None:
        """
        Deletes the last char from the input string in the window
        :return:
        """
        self.child_graphics_objects.written_text.set_text(self.child_graphics_objects.written_text.text[:-1])

    def submit(self) -> None:
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
    def add_input_to_file(input_: str) -> None:
        """
        Adds another item to the file of inputs given to the window
        :param input_: the input that was entered
        """
        new_file_content = input_

        if os.path.isfile(FILE_PATHS.WINDOW_INPUT_LIST_FILE):
            new_file_content = "{}\n{}".format(open(FILE_PATHS.WINDOW_INPUT_LIST_FILE, 'r').read(), input_)

        open(FILE_PATHS.WINDOW_INPUT_LIST_FILE, 'w').write(new_file_content)

    def __str__(self) -> str:
        return "PopupTextBox Graphics"
