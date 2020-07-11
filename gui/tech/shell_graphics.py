from collections import namedtuple

from computing.inner_workings.shell.command_parser import CommandParser
from consts import CONSOLE, TEXT
from gui.tech.output_console import OutputConsole
from gui.user_interface.key_writer import KeyWriter
from gui.user_interface.text_graphics import Text

ChildrenGraphicsObjects = namedtuple("ChildGraphicsObject", [
        "text",
        "input_line",
    ])


class ShellGraphics(OutputConsole):
    """
    Like an `OutputConsole` only you can write things into it!
    """
    def __init__(self, x, y, initial_text, computer, width=CONSOLE.SHELL.WIDTH, height=CONSOLE.SHELL.HEIGHT):
        super(ShellGraphics, self).__init__(x, y, initial_text, width, height, font_size=TEXT.FONT.DEFAULT_SIZE)
        self.computer = computer

        self.key_writer = KeyWriter(self.write_to_line, self.delete, self.submit_line)

        self.child_graphics_objects = ChildrenGraphicsObjects(
            self.child_graphics_objects.text,
            Text(
                CONSOLE.SHELL.PREFIX, self.x + (self.width / 2), self.y + 20,
                parent_graphics=self,
                padding=((self.width / 2), 20),
                max_width=self.width,
                align=TEXT.ALIGN.LEFT,
                color=CONSOLE.TEXT_COLOR,
            ),
        )

        self.command_parser = CommandParser(computer, self)

    def write_to_line(self, string):
        """
        Writes a string to the input line of the shell
        :param string:
        :return:
        """
        self.child_graphics_objects.input_line.append_text(string)

        # TODO: fix it when the line it too long
        # TODO: fix it when the shell fills up
        # TODO: make it so that you can actually run the commands you print in...

    def delete(self):
        """
        Delete one char off the input line of the shell.
        :return:
        """
        self.child_graphics_objects.input_line.set_text(
            CONSOLE.SHELL.PREFIX + self.child_graphics_objects.input_line.text[len(CONSOLE.SHELL.PREFIX):-1]
        )

    def submit_line(self):
        """
        Press enter in the input line basically.
        :return:
        """
        command_and_args = self.child_graphics_objects.input_line.text[len(CONSOLE.SHELL.PREFIX):]
        self.write(CONSOLE.SHELL.PREFIX + command_and_args)
        self.child_graphics_objects.input_line.set_text(CONSOLE.SHELL.PREFIX)

        self.command_parser.execute(command_and_args)
