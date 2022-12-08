from __future__ import annotations

from typing import Tuple, NamedTuple, Iterable

from NetSym.consts import CONSOLE, TEXT
from NetSym.gui.abstracts.graphics_object import GraphicsObject
from NetSym.gui.abstracts.user_interface_graphics_object import UserInterfaceGraphicsObject
from NetSym.gui.shape_drawing import draw_rectangle
from NetSym.gui.user_interface.text_graphics import Text


class ChildGraphicsObjects(NamedTuple):
    text: Text


class OutputConsole(UserInterfaceGraphicsObject):
    """
    An object were the computer can write its output.
    This command line is drawn when the computer is viewed in the UserInterface's `VIEW_MODE`

    It views errors, ping replies and requests, dhcp requests and more.
    """

    def __init__(self,
                 x: float,
                 y: float,
                 initial_text: str = 'OutputConsole:\n',
                 width: float = CONSOLE.WIDTH,
                 height: float = CONSOLE.HEIGHT,
                 font_size: int = CONSOLE.FONT_SIZE,
                 font: str = TEXT.FONT.DEFAULT) -> None:
        """
        Initiates the object with its location and initial text.
        """
        super(OutputConsole, self).__init__(x, y)

        self.is_hidden = True

        self._text = initial_text
        self.width, self.height = width, height
        self.__child_graphics_objects = ChildGraphicsObjects(
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

    def get_children(self) -> Iterable[GraphicsObject]:
        return self.__child_graphics_objects

    def get_text(self) -> Text:
        return self.__child_graphics_objects.text

    def get_text_padding(self) -> Tuple[float, float]:
        """
        Must be recalculated every time the size of the console changes
        """
        return (self.width / 2) + 2, self.height

    def draw(self) -> None:
        """
        Draws the graphics object - The OutputConsole.
        :return: None
        """
        if not self.is_hidden:
            draw_rectangle(self.x, self.y, self.width, self.height, color=CONSOLE.COLOR)

    def show(self) -> None:
        """
        Shows the console if it is hidden
        :return: None
        """
        self.is_hidden = False
        self.__child_graphics_objects.text.show()

    def hide(self) -> None:
        """
        Hides the console if it is is_showing.
        :return: None
        """
        self.is_hidden = True
        self.__child_graphics_objects.text.hide()

    def toggle_showing(self) -> None:
        """
        If hidden, show, if showing, hide
        :return:
        """
        if self.is_hidden:
            self.show()
        else:
            self.hide()

    def approximate_line_count(self, text: str) -> int:
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
    def line_height(self) -> float:
        return (7 * self.__child_graphics_objects.text.label.font_size) / 4

    def is_full(self) -> bool:
        """
        Returns whether or not the console is full (and should go down a line)
        """
        text_height = sum([self.approximate_line_count(line) for line in self._text.split('\n')]) * self.line_height
        return text_height >= self.height

    def write(self, text: str) -> None:
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
        self.__child_graphics_objects.text.set_text(self._text)

    def __str__(self) -> str:
        return "OutputConsole"

    def __repr__(self) -> str:
        return f"<< OutputConsole at {self.location} >>"
