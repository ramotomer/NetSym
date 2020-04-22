from gui.graphics_object import GraphicsObject
import pyglet
from consts import *


class Text(GraphicsObject):
    """
    This represents permanent text on the screen.

    The text that is drawn on the screen is kept because if it is created each
    time the screen is updated (like was before) the program crashes and says it is out of memory.
    """
    def __init__(self, text, x, y, parent_graphics=None, padding=(0, DEFAULT_TEXT_Y_PADDING), line_gap=TEXT_LINE_GAP, is_button=False, start_hidden=False, max_width=None):
        """
        Initiates a new `Text` object.
        A `Text` object can have a parent `GraphicsObject` which it will set
        its coordinates according to it.
        at all times, the coordinates of the `Text` object will be the ones
        of the `parent_graphics` object plus the padding.

        `padding` is a tuple to add to the `parent_graphics`'s coordinates.

        The coordinates `x` and `y` of the `Text` object are in the middle of
        the last line that is drawn on the screen.
        """
        super(Text, self).__init__(x, y, centered=True)
        self._text = text
        self.parent_graphics = parent_graphics
        self.x_padding, self.y_padding = padding
        self.line_gap = line_gap
        self.is_button = is_button  # whether or not it is on a _text on a button
        self.is_hidden = start_hidden
        self.max_width = max_width
        self.font_size = DEFAULT_FONT_SIZE
        self.lines = []

        self.set_text(text)

        self.done_loading = True

    @property
    def text(self):
        return self._text

    @staticmethod
    def line_width(label):
        """
        Takes in a `pyglet.text.Label` object and returns its width.
        :param label: a `pyglet.text.Label` object.
        :return: its width in pixels
        """
        return len(label.text) * (label.font_size)

    def correct_too_long_lines(self, text):
        """
        Receive a text with lines that might be too long and return a string with '\n's where you need to
        go down a line so it wont be too long (longer than `self.max_width`)
        :return a new string object with corrected lines.
        """
        if self.max_width is None:
            return text
        returned = []
        max_length = self.max_width // self.font_size
        for line in text.split('\n'):
            if len(line) * self.font_size > self.max_width:
                returned.append('\n'.join(line[i:(i + max_length)] for i in range(0, len(line), max_length)))
            else:
                returned.append(line)
        return '\n'.join(returned)

    def set_text(self, text):
        """
        The correct way to update the text of a `Text` object.
        updates the text and corrects the lines and everything necessary.
        :param text: a string which is the new text.
        :return: None
        """
        self._text = self.correct_too_long_lines(text)
        self.lines = [pyglet.text.Label(line,
                                        font_name=DEFAULT_FONT,
                                        font_size=self.font_size,
                                        x=self.x + self.x_padding, y=(self.y + self.y_padding) - (i * self.line_gap),
                                        anchor_x='center', anchor_y='center') for i, line in enumerate(self._text.split('\n'))]

        for line in self.lines:
            self.x, self.y = line.x, line.y + ((len(self.lines) * line.font_size) + TEXT_LINE_GAP)
            line.x = self.x

    def draw(self):
        """
        Draws each of the lines in the text.
        :return: None
        """
        if hasattr(self, 'done_loading') and not self.is_hidden:
            for line in self.lines:
                line.draw()

    def move(self):
        """
        Moves the _text according to the parent object.
        :return: None
        """
        if self.parent_graphics is None:
            return
        for i, line in enumerate(self.lines):
            self.x, self.y = self.parent_graphics.x + self.x_padding, (self.parent_graphics.y + self.y_padding) - (i * self.line_gap)
            line.x, line.y = self.x, self.y

    def __str__(self):
        return f"Text Graphics: '{self.text}'"

    def __repr__(self):
        return f"Text(text={self.text!r})"
