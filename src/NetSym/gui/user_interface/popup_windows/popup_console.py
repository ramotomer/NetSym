from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple, Iterable

from NetSym.consts import COLORS, CONSOLE, COMPUTER
from NetSym.gui.abstracts.graphics_object import GraphicsObject
from NetSym.gui.tech.shell_graphics import ShellGraphics
from NetSym.gui.user_interface.popup_windows.popup_window import PopupWindow

if TYPE_CHECKING:
    from NetSym.gui.user_interface.text_graphics import Text
    from NetSym.gui.user_interface.button import Button
    from NetSym.computing.computer import Computer
    from NetSym.gui.user_interface.user_interface import UserInterface


class ChildrenGraphicsObjects(NamedTuple):
    title_text:  Text
    exit_button: Button
    shell:       ShellGraphics


class PopupConsole(PopupWindow):
    """
    A console in a popup window that you can also write in.
    """
    def __init__(self, computer: Computer) -> None:
        x, y = CONSOLE.SHELL.START_LOCATION
        super(PopupConsole, self).__init__(
            x, y,
            color=COLORS.PINK,
            title='console',
            width=CONSOLE.SHELL.WIDTH,
            height=CONSOLE.SHELL.HEIGHT,
        )

        self.computer = computer
        self.computer.output_method = COMPUTER.OUTPUT_METHOD.SHELL
        shell = self.computer.create_shell(self.x, self.y, self)

        self.__child_graphics_objects = ChildrenGraphicsObjects(
            self.get_title_text(),
            self.get_exit_button(),
            shell,
        )

    @property
    def shell(self) -> ShellGraphics:
        return self.__child_graphics_objects.shell

    def get_children(self) -> Iterable[GraphicsObject]:
        return self.__child_graphics_objects

    def delete(self, user_interface: UserInterface = None) -> None:
        super(PopupConsole, self).delete(user_interface)
        self.computer.active_shells.remove(self.shell)
        if not self.computer.active_shells:
            self.computer.output_method = COMPUTER.OUTPUT_METHOD.CONSOLE

    def resize(self, width: float, height: float) -> None:
        super(PopupConsole, self).resize(width, height)
        self.shell.width, self.shell.height = width, height
        self.shell.get_text().resize(self.shell.get_text_padding(), width)

    def __repr__(self) -> str:
        return f"<< PopupConsoleWindow of computer {self.computer.name!r} >>"
