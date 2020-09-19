import pyglet

from consts import *
from gui.main_loop import MainLoop
from gui.main_window import MainWindow
from gui.user_interface.user_interface import UserInterface

if __name__ == '__main__':
    user_interface = UserInterface()
    main_window = MainWindow(user_interface, WINDOWS.MAIN.WIDTH, WINDOWS.MAIN.HEIGHT, WINDOWS.MAIN.NAME, resizable=True)
    main_loop = MainLoop(main_window)
    pyglet.clock.schedule_interval(main_window.update, WINDOWS.MAIN.FRAME_RATE)
    pyglet.app.run()

    # TODO: make sure no two computers or interfaces have the same name!
    # TODO: there are errors with removing connections and the routing table
    # TODO: loopback connection graphics are not deleted when the parent computer is.
