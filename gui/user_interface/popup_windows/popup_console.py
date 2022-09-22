from __future__ import annotations

from collections import namedtuple
from typing import TYPE_CHECKING

from consts import COLORS, CONSOLE, COMPUTER
from gui.main_loop import MainLoop
from gui.tech.shell_graphics import ShellGraphics
from gui.user_interface.popup_windows.popup_window import PopupWindow

if TYPE_CHECKING:
    from computing.computer import Computer
    from gui.user_interface.user_interface import UserInterface


ChildrenGraphicsObjects = namedtuple("ChildrenGraphicsObjects", [
    'title_text',
    'exit_button',
    'shell',
])


class PopupConsole(PopupWindow):
    """
    A console in a popup window that you can also write in.
    """
    def __init__(self, user_interface: UserInterface, computer: Computer) -> None:
        x, y = CONSOLE.SHELL.START_LOCATION
        super(PopupConsole, self).__init__(
            x, y,
            '',
            user_interface,
            [],
            color=COLORS.PINK,
            title='console',
            width=CONSOLE.SHELL.WIDTH,
            height=CONSOLE.SHELL.HEIGHT,
        )

        title_text, info_text, exit_button = self.child_graphics_objects[:3]
        # TODO: ^ disgusting!!!!
        MainLoop.instance.unregister_graphics_object(info_text)

        self.computer = computer
        self.computer.output_method = COMPUTER.OUTPUT_METHOD.SHELL

        shell = ShellGraphics(self.x, self.y, f"Shell on {computer.name}\n", computer, self)
        shell.width, shell.height = self.width, self.height
        shell.set_parent_graphics(self)
        shell.show()
        self.computer.active_shells.append(shell)
        MainLoop.instance.move_to_front(shell)

        self.child_graphics_objects = ChildrenGraphicsObjects(
            title_text,
            exit_button,
            shell,
        )
        MainLoop.instance.move_to_front(shell.child_graphics_objects.input_line)

    @property
    def shell(self):
        return self.child_graphics_objects.shell

    def delete(self, user_interface: UserInterface = None) -> None:
        super(PopupConsole, self).delete(user_interface)
        self.computer.active_shells.remove(self.shell)
        if not self.computer.active_shells:
            self.computer.output_method = COMPUTER.OUTPUT_METHOD.CONSOLE

    def resize(self, width, height):
        super(PopupConsole, self).resize(width, height)
        self.shell.width, self.shell.height = width, height
        self.shell.child_graphics_objects.text.resize(self.shell.get_text_padding(), width)
