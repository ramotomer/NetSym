from collections import namedtuple

from pyglet.window import key

from consts import *
from gui.button import Button
from gui.graphics_object import GraphicsObject
from gui.main_loop import MainLoop
from gui.shape_drawing import draw_rect
from gui.text_graphics import Text

ChildGraphicsObjects = namedtuple("ChildGraphicsObjects", "title_text written_text submit_button")


class TextBox(GraphicsObject):
    """
    A popup window - a text box that asks for text and does an action with it.
    The `TextBox` has a field of text that you fill up and a below it a button with a 'submit' on it.
    """
    def __init__(self, text, action):
        """
        Initiates the `TextBox` object.

        :param text: the text for `self._text` attribute.
        :param action: the action that will be activated when the button is pressed.
            It should be a function that receives one string argument (the inserted string) and returns None.
        """
        super(TextBox, self).__init__(*TEXTBOX_COORDINATES, centered=True)
        self.action = action

        title_text = Text(text, self.x, self.y + (TEXTBOX_HEIGHT / 2), None)

        written_text = Text('', title_text.x, title_text.y - 20, max_width=TEXTBOX_WIDTH, padding=(0, 0))

        submit_button = Button(self.x - (SUBMIT_BUTTON_WIDTH / 2),
                               (self.y - (TEXTBOX_HEIGHT / 2)) + 10,
                               text="SUBMIT",
                               width=SUBMIT_BUTTON_WIDTH,
                               action=self.submit)

        self.child_graphics_objects = ChildGraphicsObjects(
            title_text,
            written_text,
            submit_button,
        )

        self.is_done = False  # whether or not the window is done and completed the action of the submit button.

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

        elif symbol == key.BACKSPACE:
            self.child_graphics_objects.written_text.set_text(self.child_graphics_objects.written_text.text[:-1])

        elif self._is_printable(symbol):
            char = chr(symbol).lower()
            if (modifiers & SHIFT_MODIFIER) ^ (modifiers & CAPS_MODIFIER):
                char = char.upper()
                if char == '-': char = '_'
                if char == '=': char = '+'
            self.child_graphics_objects.written_text.set_text(self.child_graphics_objects.written_text.text + char)

    def submit(self):
        """
        Submits the text that was written and activates the `self.action` with it.
        :return: None
        """
        self.action(self.child_graphics_objects.written_text.text)

        MainLoop.instance.unregister_graphics_object(self)  # unregisters recursively
        self.is_done = True

    def draw(self):
        """
        Draws the popup window (text box) on the screen.
        Basically a rectangle.
        :return: None
        """
        draw_rect(self.x - (TEXTBOX_WIDTH / 2), self.y - (TEXTBOX_HEIGHT / 2), TEXTBOX_WIDTH, TEXTBOX_HEIGHT, TEXTBOX_COLOR)

    def __str__(self):
        return "TextBox Graphics"
