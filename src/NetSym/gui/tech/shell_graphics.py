from __future__ import annotations

from typing import TYPE_CHECKING, Union, NamedTuple, Iterable

from pyglet.window import key

from NetSym.computing.internals.shell.shell import Shell
from NetSym.consts import CONSOLE, TEXT, KEYBOARD
from NetSym.gui.abstracts.graphics_object import GraphicsObject
from NetSym.gui.tech.output_console import OutputConsole
from NetSym.gui.user_interface.key_writer import KeyWriter
from NetSym.gui.user_interface.text_graphics import Text
from NetSym.usefuls.funcs import with_args

if TYPE_CHECKING:
    from NetSym.gui.user_interface.popup_windows.popup_window import PopupWindow
    from NetSym.computing.computer import Computer


class ChildGraphicsObjects(NamedTuple):
        text: Text
        input_line: Text


class ShellGraphics(OutputConsole):
    """
    Like an `OutputConsole` only you can write things into it!
    """

    def __init__(self,
                 x: float,
                 y: float,
                 initial_text: str,
                 computer: Computer,
                 carrying_window: PopupWindow,
                 width: float = CONSOLE.SHELL.WIDTH,
                 height: float = CONSOLE.SHELL.HEIGHT) -> None:
        """
        initiate the graphics of the shell
        """
        super(ShellGraphics, self).__init__(
            x, y,
            initial_text,
            width, height,
            font_size=CONSOLE.SHELL.FONT_SIZE,
            font=CONSOLE.SHELL.FONT
        )
        self.computer = computer
        self.carrying_window = carrying_window

        self._ShellGraphics__child_graphics_objects = ChildGraphicsObjects(
            self.get_text(),
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

        self.key_writer = KeyWriter(self.write_to_line, self._delete_last_char, self.submit_line)
        self.key_writer.add_key_combination(key.C, KEYBOARD.MODIFIERS.CTRL, self.clear_line)
        self.key_writer.add_key_combination(key.L, KEYBOARD.MODIFIERS.CTRL, self.clear_screen)
        self.key_writer.add_key_combination([key.Q, key.D], KEYBOARD.MODIFIERS.CTRL, self.exit)
        self.key_writer.add_key_combination(key.A, KEYBOARD.MODIFIERS.CTRL, with_args(self.move_caret, -float('inf')))
        self.key_writer.add_key_combination(key.E, KEYBOARD.MODIFIERS.CTRL, with_args(self.move_caret, float('inf')))
        self.key_writer.add_key_combination(key.K, KEYBOARD.MODIFIERS.CTRL, self.delete_from_caret_until_the_end)
        self.key_writer.add_key_combination(key.U, KEYBOARD.MODIFIERS.CTRL, self.delete_from_the_start_up_to_caret)

        self.key_writer.add_key_combination(key.DELETE, KEYBOARD.MODIFIERS.NONE, self._delete_next_char)
        self.key_writer.add_key_combination(key.UP,    KEYBOARD.MODIFIERS.NONE, self.command_parser.scroll_up_history)
        self.key_writer.add_key_combination(key.DOWN,  KEYBOARD.MODIFIERS.NONE, self.command_parser.scroll_down_history)
        self.key_writer.add_key_combination(key.RIGHT, KEYBOARD.MODIFIERS.NONE, with_args(self.move_caret, 1))
        self.key_writer.add_key_combination(key.LEFT,  KEYBOARD.MODIFIERS.NONE, with_args(self.move_caret, -1))
        self.key_writer.add_key_combination(key.HOME,  KEYBOARD.MODIFIERS.NONE, with_args(self.move_caret, -float('inf')))
        self.key_writer.add_key_combination(key.END,   KEYBOARD.MODIFIERS.NONE, with_args(self.move_caret, float('inf')))

        self.caret_index = 0
        
    @property
    def input_line_content(self) -> str:
        text = self._ShellGraphics__child_graphics_objects.input_line.text[len(CONSOLE.SHELL.PREFIX):]
        return text[:self.caret_index] + text[self.caret_index + 1:]

    def get_children(self) -> Iterable[GraphicsObject]:
        return self._ShellGraphics__child_graphics_objects

    def write_to_line(self, string: str) -> None:
        """
        Writes a string to the input line of the shell
        :param string:
        :return:
        """
        text = self.input_line_content
        text = text[:self.caret_index] + string + CONSOLE.SHELL.CARET + text[self.caret_index:]
        self.caret_index += len(string)
        self._ShellGraphics__child_graphics_objects.input_line.set_text(CONSOLE.SHELL.PREFIX + text)

    def _delete_last_char(self) -> None:
        """
        Delete one char off the input line of the shell.
        """
        if self.caret_index == 0:
            return
        text = self.input_line_content
        text = text[:self.caret_index - 1] + CONSOLE.SHELL.CARET + text[self.caret_index:]
        self.caret_index = max(self.caret_index - 1, 0)
        self._ShellGraphics__child_graphics_objects.input_line.set_text(CONSOLE.SHELL.PREFIX + text)

    def _delete_next_char(self) -> None:
        """
        Delete one char off the input line of the shell - from the other side of the caret.
        """
        text = self.input_line_content
        if self.caret_index == len(text):
            return

        text = text[:self.caret_index] + CONSOLE.SHELL.CARET + text[self.caret_index + 1:]
        self._ShellGraphics__child_graphics_objects.input_line.set_text(CONSOLE.SHELL.PREFIX + text)

    def delete_from_caret_until_the_end(self) -> None:
        """
        Delete all of the text until the end of the line
        :return:
        """
        text = self.input_line_content
        text = text[:self.caret_index] + CONSOLE.SHELL.CARET
        # self.caret_index = max(self.caret_index - 1, 0)
        self._ShellGraphics__child_graphics_objects.input_line.set_text(CONSOLE.SHELL.PREFIX + text)

    def delete_from_the_start_up_to_caret(self) -> None:
        """
        Delete all of the text until the end of the line
        :return:
        """
        text = self.input_line_content
        text = CONSOLE.SHELL.CARET + text[self.caret_index:]
        self.caret_index = 0
        self._ShellGraphics__child_graphics_objects.input_line.set_text(CONSOLE.SHELL.PREFIX + text)

    def submit_line(self) -> None:
        """
        Press enter in the input line basically.
        :return:
        """
        command_and_args = self.input_line_content
        self.write(CONSOLE.SHELL.PREFIX + command_and_args)
        self.clear_line()

        self.command_parser.execute(command_and_args)

    def clear_line(self) -> None:
        """
        Clears the input line.
        :return:
        """
        self.caret_index = 0
        self._ShellGraphics__child_graphics_objects.input_line.set_text(CONSOLE.SHELL.PREFIX + CONSOLE.SHELL.CARET)

    def clear_screen(self) -> None:
        """
        Clears the shell screen.
        :return:
        """
        self._text = ''
        self._ShellGraphics__child_graphics_objects.text.set_text('')

    def exit(self) -> None:
        """
        Closes the shell and the window that carries it.
        :return:
        """
        self.carrying_window.delete()

    def move_caret(self, amount: Union[int, float]) -> None:
        """
        moves the caret some distance right (the amount can be negative)
        can also receive in `mount` the values `chr(ey.HOME)` or `chr(key.END)` to signal the start of end of the line.
        """
        if amount == -float('inf'):
            return self.move_caret(-self.caret_index)

        if amount == float('inf'):
            return self.move_caret(len(self.input_line_content) - self.caret_index)

        text = self.input_line_content
        self.caret_index = int(min(max(self.caret_index + amount, 0), len(text)))
        text = text[:self.caret_index] + CONSOLE.SHELL.CARET + text[self.caret_index:]
        self._ShellGraphics__child_graphics_objects.input_line.set_text(CONSOLE.SHELL.PREFIX + text)

    def __str__(self) -> str:
        """a general string representation of the object"""
        return "ShellGraphics"

    def __repr__(self) -> str:
        """a string representation of the object (mainly for debugging)"""
        return f"<< ShellGraphics of computer {self.computer.name!r} >>"
