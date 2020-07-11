from collections import namedtuple

from consts import COLORS, CONSOLE
from gui.main_loop import MainLoop
from gui.tech.shell_graphics import ShellGraphics
from gui.user_interface.popup_windows.popup_window import PopupWindow

ChildrenGraphicsObjects = namedtuple("ChildrenGraphicsObjects", [
    'title_text',
    'exit_button',
    'shell',
])


class PopupConsole(PopupWindow):
    """
    A console in a popup window that you can also write in.
    """
    def __init__(self, user_interface, computer):
        super(PopupConsole, self).__init__(
            *CONSOLE.SHELL.START_LOCATION,
            '',
            user_interface,
            [],
            color=COLORS.PINK,
            title='console',
            width=CONSOLE.SHELL.WIDTH,
            height=CONSOLE.SHELL.HEIGHT,
        )

        title_text, info_text, exit_button = self.child_graphics_objects[:3]
        MainLoop.instance.unregister_graphics_object(info_text)

        shell = ShellGraphics(*self.location, '', computer)
        shell.width, shell.height = self.width, self.height
        shell.set_parent_graphics(self)
        shell.show()
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
