from collections import namedtuple

from pyglet.window import key

from computing.internals.shell.shell import Shell
from consts import CONSOLE, TEXT, KEYBOARD
from gui.tech.output_console import OutputConsole
from gui.user_interface.key_writer import KeyWriter
from gui.user_interface.text_graphics import Text
from usefuls import with_args

ChildrenGraphicsObjects = namedtuple("ChildGraphicsObject", [
        "text",
        "input_line",
    ])


class ShellGraphics(OutputConsole):
    """
    Like an `OutputConsole` only you can write things into it!
    """
    def __init__(self, x, y, initial_text, computer, carrying_window,
                 width=CONSOLE.SHELL.WIDTH, height=CONSOLE.SHELL.HEIGHT):
        """
        initiate the graphics of the shell
        :param x:
        :param y:
        :param initial_text:
        :param computer:
        :param carrying_window:
        :param width:
        :param height:
        """
        super(ShellGraphics, self).__init__(x, y, initial_text, width, height,
                                            font_size=CONSOLE.SHELL.FONT_SIZE, font=CONSOLE.SHELL.FONT)
        self.computer = computer
        self.carrying_window = carrying_window

        self.child_graphics_objects = ChildrenGraphicsObjects(
            self.child_graphics_objects.text,
            Text(
                CONSOLE.SHELL.PREFIX + CONSOLE.SHELL.CARET, self.x + (self.width / 2), self.y + 20,
                parent_graphics=self,
                padding=((self.width / 2), 20),
                max_width=self.width,
                align=TEXT.ALIGN.LEFT,
                color=CONSOLE.TEXT_COLOR,
                font=CONSOLE.SHELL.FONT,
            ),
        )

        self.command_parser = Shell(computer, self)

        self.key_writer = KeyWriter(self.write_to_line, self.delete_last_char, self.submit_line)
        self.key_writer.add_key_combination(key.C, KEYBOARD.MODIFIERS.CTRL, self.clear_line)
        self.key_writer.add_key_combination(key.L, KEYBOARD.MODIFIERS.CTRL, self.clear_screen)
        self.key_writer.add_key_combination(key.Q, KEYBOARD.MODIFIERS.CTRL, self.exit)

        self.key_writer.add_key_mapping(key.UP, self.command_parser.scroll_up_history)
        self.key_writer.add_key_mapping(key.DOWN, self.command_parser.scroll_down_history)
        self.key_writer.add_key_mapping(key.RIGHT, with_args(self.move_caret, 1))
        self.key_writer.add_key_mapping(key.LEFT, with_args(self.move_caret, -1))
        self.key_writer.add_key_mapping(key.HOME, with_args(self.move_caret, chr(key.HOME)))
        self.key_writer.add_key_mapping(key.END, with_args(self.move_caret, chr(key.END)))

        self.caret_index = 0
        
    @property
    def input_line_content(self):
        text = self.child_graphics_objects.input_line.text[len(CONSOLE.SHELL.PREFIX):]
        return text[:self.caret_index] + text[self.caret_index + 1:]

    def write_to_line(self, string):
        """
        Writes a string to the input line of the shell
        :param string:
        :return:
        """
        text = self.input_line_content
        text = text[:self.caret_index] + string + CONSOLE.SHELL.CARET + text[self.caret_index:]
        self.caret_index += len(string)
        self.child_graphics_objects.input_line.set_text(CONSOLE.SHELL.PREFIX + text)

    def delete_last_char(self):
        """
        Delete one char off the input line of the shell.
        :return:
        """
        if self.caret_index == 0:
            return
        text = self.input_line_content
        text = text[:self.caret_index - 1] + CONSOLE.SHELL.CARET + text[self.caret_index:]
        self.caret_index = max(self.caret_index - 1, 0)
        self.child_graphics_objects.input_line.set_text(CONSOLE.SHELL.PREFIX + text)

    def submit_line(self):
        """
        Press enter in the input line basically.
        :return:
        """
        command_and_args = self.input_line_content
        self.write(CONSOLE.SHELL.PREFIX + command_and_args)
        self.clear_line()

        self.command_parser.execute(command_and_args)

    def clear_line(self):
        """
        Clears the input line.
        :return:
        """
        self.caret_index = 0
        self.child_graphics_objects.input_line.set_text(CONSOLE.SHELL.PREFIX + CONSOLE.SHELL.CARET)

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

    def move_caret(self, amount):
        """
        moves the caret some distance right (the amount can be negative)
        can also receive in `mount` the values `chr(ey.HOME)` or `chr(key.END)` to signal the start of end of the line.
        :param amount:
        :return:
        """
        if amount == chr(key.HOME):
            return self.move_caret(-self.caret_index)

        if amount == chr(key.END):
            return self.move_caret(len(self.input_line_content) - self.caret_index)

        text = self.input_line_content
        self.caret_index = min(max(self.caret_index + amount, 0), len(text))
        text = text[:self.caret_index] + CONSOLE.SHELL.CARET + text[self.caret_index:]
        self.child_graphics_objects.input_line.set_text(CONSOLE.SHELL.PREFIX + text)
