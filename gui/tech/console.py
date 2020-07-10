from collections import namedtuple

from consts import CONSOLE
from gui.abstracts.user_interface_graphics_object import UserInterfaceGraphicsObject
from gui.main_loop import MainLoop
from gui.shape_drawing import draw_rectangle
from gui.user_interface.text_graphics import Text

ChildGraphicsObjects = namedtuple("ChildGraphicsObject", "text")


class Console(UserInterfaceGraphicsObject):
    """
    An object were the computer can write its output.
    This command line is drawn when the computer is viewed in the UserInterface's `VIEW_MODE`

    It views errors, ping replies and requests, dhcp requests and more.
    """
    def __init__(self, x, y, initial_text='Console:\n', width=CONSOLE.WIDTH, height=CONSOLE.HEIGHT):
        """
        Initiates the object with its location and initial text.
        """
        super(Console, self).__init__(x, y)

        self.is_hidden = True

        self._text = initial_text
        self.child_graphics_objects = ChildGraphicsObjects(
            Text(
                self._text, x, y, self,
                padding=((width / 2) + 2, height),
                start_hidden=True,
                font_size=CONSOLE.FONT_SIZE,
                max_width=width,
                align='left',
                color=CONSOLE.TEXT_COLOR,
            )
        )

        self.width, self.height = width, height

    def draw(self):
        """
        Draws the graphics object - The Console.
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

    def num_lines(self, text):
        """
        The number of lines that some text would be split into in the console.
        This is somewhat of an approximation.
        :param text: a string
        :return: None
        """
        return ((len(text) * CONSOLE.CHAR_WIDTH) // self.width) + 1

    def is_full(self):
        """
        Returns whether or not the console is full (and should go down a line)
        """
        text_height = sum([self.num_lines(line) for line in self._text.split('\n')]) * CONSOLE.LINE_HEIGHT
        return text_height > self.height

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
