from collections import namedtuple

from pyglet.window import key

from computing.internals.shell.shell import Shell
from consts import CONSOLE, TEXT, KEYBOARD
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
    def __init__(self, x, y, initial_text, computer, carrying_window, width=CONSOLE.SHELL.WIDTH, height=CONSOLE.SHELL.HEIGHT):
        super(ShellGraphics, self).__init__(x, y, initial_text, width, height,
                                            font_size=CONSOLE.SHELL.FONT_SIZE, font='Courier New')
        self.computer = computer
        self.carrying_window = carrying_window

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

        self.command_parser = Shell(computer, self)

        self.key_writer = KeyWriter(self.write_to_line, self.delete_last_char, self.submit_line)
        self.key_writer.add_key_combination(key.C, KEYBOARD.MODIFIERS.CTRL, self.clear_line)
        self.key_writer.add_key_combination(key.L, KEYBOARD.MODIFIERS.CTRL, self.clear_screen)
        self.key_writer.add_key_combination(key.Q, KEYBOARD.MODIFIERS.CTRL, self.exit)
        self.key_writer.add_key_mapping(key.UP, self.command_parser.scroll_up_history)
        self.key_writer.add_key_mapping(key.DOWN, self.command_parser.scroll_down_history)

    def write_to_line(self, string):
        """
        Writes a string to the input line of the shell
        :param string:
        :return:
        """
        self.child_graphics_objects.input_line.append_text(string)
        # TODO: fix it when the line that is inserted is too long

    def delete_last_char(self):
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
        self.clear_line()

        self.command_parser.execute(command_and_args)

    def clear_line(self):
        """
        Clears the input line.
        :return:
        """
        self.child_graphics_objects.input_line.set_text(CONSOLE.SHELL.PREFIX)

    def clear_screen(self):
        """
        Clears the shell screen.
        :return:
        """
        self._text = ''
        self.child_graphics_objects.text.set_text('')

    def exit(self):
        """
        Closes the shell and the window that carries it.
        :return:
        """
        self.carrying_window.delete()
