import pyglet
from consts import *
from gui.user_interface import UserInterface
from gui.main_window import MainWindow
from gui.main_loop import MainLoop


if __name__ == '__main__':
    user_interface = UserInterface()
    main_window = MainWindow(user_interface, WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_NAME, resizable=False)
    main_loop = MainLoop(main_window)
    pyglet.clock.schedule_interval(main_window.update, FRAME_RATE)
    pyglet.app.run()
