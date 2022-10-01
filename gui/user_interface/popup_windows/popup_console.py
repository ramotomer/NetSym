from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from consts import COLORS, CONSOLE, COMPUTER
from gui.main_loop import MainLoop
from gui.tech.shell_graphics import ShellGraphics
from gui.user_interface.popup_windows.popup_window import PopupWindow

if TYPE_CHECKING:
    from gui.user_interface.text_graphics import Text
    from gui.user_interface.button import Button
    from computing.computer import Computer
    from gui.user_interface.user_interface import UserInterface


class ChildrenGraphicsObjects(NamedTuple):
    title_text:  Text
    exit_button: Button
    shell:       ShellGraphics


class PopupConsole(PopupWindow):
    """
    A console in a popup window that you can also write in.
    """
    def __init__(self, user_interface: UserInterface, computer: Computer) -> None:
        x, y = CONSOLE.SHELL.START_LOCATION
        super(PopupConsole, self).__init__(
            x, y,
            user_interface,
            color=COLORS.PINK,
            title='console',
            width=CONSOLE.SHELL.WIDTH,
            height=CONSOLE.SHELL.HEIGHT,
        )

        title_text, exit_button = self.child_graphics_objects

        self.computer = computer
        self.computer.output_method = COMPUTER.OUTPUT_METHOD.SHELL
        shell = self._generate_computer_shell()

        self.child_graphics_objects = ChildrenGraphicsObjects(
            title_text,
            exit_button,
            shell,
        )
        MainLoop.instance.move_to_front(shell.child_graphics_objects.input_line)

    def _generate_computer_shell(self) -> ShellGraphics:
        """
        Creates the shell (graphics)object that rides the window object - And performs all of the required logic upon it
        That object contains the actual `Shell` object that holds all the actual logic of the shell
        """
        shell = ShellGraphics(self.x, self.y, f"Shell on {self.computer.name}\n", self.computer, self)
        shell.width, shell.height = self.width, self.height
        shell.set_parent_graphics(self)
        shell.show()
        self.computer.active_shells.append(shell)
        MainLoop.instance.move_to_front(shell)
        return shell

    @property
    def shell(self) -> ShellGraphics:
        return self.child_graphics_objects.shell

    def delete(self, user_interface: UserInterface = None) -> None:
        super(PopupConsole, self).delete(user_interface)
        self.computer.active_shells.remove(self.shell)
        if not self.computer.active_shells:
            self.computer.output_method = COMPUTER.OUTPUT_METHOD.CONSOLE

    def resize(self, width: float, height: float) -> None:
        super(PopupConsole, self).resize(width, height)
        self.shell.width, self.shell.height = width, height
        self.shell.child_graphics_objects.text.resize(self.shell.get_text_padding(), width)
