import pyglet

from consts import WINDOWS
from gui.main_loop import MainLoop
from gui.main_window import MainWindow
from gui.user_interface.user_interface import UserInterface

if __name__ == '__main__':
    user_interface = UserInterface()
    main_window = MainWindow(user_interface, WINDOWS.MAIN.WIDTH, WINDOWS.MAIN.HEIGHT, WINDOWS.MAIN.NAME, resizable=True)
    main_loop = MainLoop(main_window)
    pyglet.clock.schedule_interval(main_window.update, WINDOWS.MAIN.FRAME_RATE)
    pyglet.app.run()

    # TODO: BUG: pressing `delete` in a shell deletes the device you have selected
