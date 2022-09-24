from __future__ import annotations

from typing import Tuple, NamedTuple

from consts import CONSOLE, TEXT
from gui.abstracts.user_interface_graphics_object import UserInterfaceGraphicsObject
from gui.main_loop import MainLoop
from gui.shape_drawing import draw_rectangle
from gui.user_interface.text_graphics import Text


class ChildGraphicsObjects(NamedTuple):
    text: Text


class OutputConsole(UserInterfaceGraphicsObject):
    """
    An object were the computer can write its output.
    This command line is drawn when the computer is viewed in the UserInterface's `VIEW_MODE`

    It views errors, ping replies and requests, dhcp requests and more.
    """

    def __init__(self, x, y, initial_text='OutputConsole:\n',
                 width=CONSOLE.WIDTH, height=CONSOLE.HEIGHT, font_size=CONSOLE.FONT_SIZE, font=TEXT.FONT.DEFAULT):
        """
        Initiates the object with its location and initial text.
        """
        super(OutputConsole, self).__init__(x, y)

        self.is_hidden = True

        self._text = initial_text
        self.width, self.height = width, height
        self.child_graphics_objects = ChildGraphicsObjects(
            Text(
                self._text, x, y, self,
                padding=self.get_text_padding(),
                start_hidden=True,
                font_size=font_size,
                max_width=self.width,
                align=TEXT.ALIGN.LEFT,
                color=CONSOLE.TEXT_COLOR,
                font=font,
            )
        )

    def get_text_padding(self) -> Tuple[float, float]:
        """
        Must be recalculated every time the size of the console changes
        """
        return (self.width / 2) + 2, self.height

    def draw(self):
        """
        Draws the graphics object - The OutputConsole.
        :return: None
        """
        if not self.is_hidden:
            draw_rectangle(self.x, self.y, self.width, self.height, color=CONSOLE.COLOR)

    def show(self):
        """
        Shows the console if it is hidden
        :return: None
        """
        self.is_hidden = False
        self.child_graphics_objects.text.show()
        MainLoop.instance.move_to_front(self)
        MainLoop.instance.move_to_front(self.child_graphics_objects.text)

    def hide(self):
        """
        Hides the console if it is is_showing.
        :return: None
        """
        self.is_hidden = True
        self.child_graphics_objects.text.hide()

    def toggle_showing(self):
        """
        If hidden, show, if showing, hide
        :return:
        """
        if self.is_hidden:
            self.show()
        else:
            self.hide()

    def approximate_line_count(self, text):
        """
        The number of lines that some text would be split into in the console.
        This is somewhat of an approximation.
        Tabs are 4 times the width of normal characters.
        :param text: a string
        :return: None
        """
        return int((((len(text) * CONSOLE.CHAR_WIDTH) +
                     (text.count('\t') * CONSOLE.CHAR_WIDTH * 3) -
                     (text.count(':') * CONSOLE.CHAR_WIDTH // 2) -
                     (text.count('.') * 2 * CONSOLE.CHAR_WIDTH // 3)) // self.width) + 1)
        # TODO: this method is totally shit...

    @property
    def line_height(self):
        return (7 * self.child_graphics_objects.text.label.font_size) / 4

    def is_full(self):
        """
        Returns whether or not the console is full (and should go down a line)
        """
        text_height = sum([self.approximate_line_count(line) for line in self._text.split('\n')]) * self.line_height
        return text_height >= self.height

    def write(self, text):
        """
        Writes some text to the console.
        :param text: a string to write.
        :return: None
        """
        if '\n' in text:
            for line in text.split('\n'):
                self.write(line)
            return
        if self.is_full():
            self._text = '\n'.join(self._text.split('\n')[self.approximate_line_count(text):])
            # remove the up most lines if we are out of space.
        self._text += text + '\n'
        self.child_graphics_objects.text.set_text(self._text)

    def __repr__(self):
        return "OutputConsole"
