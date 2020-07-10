from consts import COLORS, CONSOLE
from gui.main_loop import MainLoop
from gui.main_window import MainWindow
from gui.tech.console import Console
from gui.user_interface.popup_windows.popup_window import PopupWindow


class PopupConsole(PopupWindow):
    """
    A console in a popup window that you can also write in.
    """
    def __init__(self, user_interface, console=None):
        super(PopupConsole, self).__init__(
            *MainWindow.main_window.center,
            '',
            user_interface,
            [],
            color=COLORS.PINK,
            title='console',
            width=CONSOLE.WIDTH,
            height=CONSOLE.HEIGHT,
        )

        title_text, _, exit_button = self.child_graphics_objects[:3]

        if console is None:
            console = Console(*self.location, initial_text=">")

        console.width, console.height = self.width, self.height
        console.set_parent_graphics(self)
        MainLoop.instance.move_to_front(console)
        console.show()
        self.console = console

        self.child_graphics_objects = [
            title_text,
            exit_button,
        ]
