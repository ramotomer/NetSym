from collections import namedtuple

from consts import *
from gui.abstracts.user_interface_graphics_object import UserInterfaceGraphicsObject
from gui.main_loop import MainLoop
from gui.shape_drawing import draw_rect
from gui.user_interface.text_graphics import Text

ChildGraphicsObjects = namedtuple("ChildGraphicsObject", "text")


class Console(UserInterfaceGraphicsObject):
    """
    An object were the computer can write its output.
    This command line is drawn when the computer is viewed in the UserInterface's `VIEW_MODE`

    It views errors, ping replies and requests, dhcp requests and more.
    """
    def __init__(self, x, y, initial_text='Console:\n'):
        """
        Initiates the object with its location and initial text.
        """
        super(Console, self).__init__(x, y)

        self.is_hidden = True

        self._text = initial_text
        self.child_graphics_objects = ChildGraphicsObjects(
            Text(
                self._text, x, y, self,
                padding=((CONSOLE_WIDTH / 2) + 2, CONSOLE_HEIGHT),
                start_hidden=True,
                font_size=CONSOLE_FONT_SIZE,
                max_width=CONSOLE_WIDTH,
                align='left',
                color=GRAY,
            )
        )

    def draw(self):
        """
        Draws the graphics object - The Console.
        :return: None
        """
        if not self.is_hidden:
            draw_rect(self.x, self.y, CONSOLE_WIDTH, CONSOLE_HEIGHT, VERY_LIGHT_GRAY)

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

    @staticmethod
    def num_lines(text):
        """
        The number of lines that some text would be split into in the console.
        This is somewhat of an approximation.
        :param text: a string
        :return: None
        """
        return ((len(text) * CONSOLE_CHAR_WIDTH) // CONSOLE_WIDTH) + 1

    def is_full(self):
        """
        Returns whether or not the console is full (and should go down a line)
        """
        text_height = sum([self.num_lines(line) for line in self._text.split('\n')]) * CONSOLE_LINE_HEIGHT
        return text_height > CONSOLE_HEIGHT

    def write(self, text):
        """
        Writes some text to the console.
        :param text: a string to write.
        :return: None
        """
        if self.is_full():
            self._text = '\n'.join(self._text.split('\n')[self.num_lines(text):])
            # remove the up most lines if we are out of space.
        self._text += text + '\n'
        self.child_graphics_objects.text.set_text(self._text)

    def __repr__(self):
        return "Console"
