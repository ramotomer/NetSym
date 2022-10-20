import pyglet

from NetSym.consts import WINDOWS
from NetSym.gui.main_loop import MainLoop
from NetSym.gui.main_window import MainWindow
from NetSym.gui.user_interface.user_interface import UserInterface

if __name__ == '__main__':
    main_loop = MainLoop()
    main_window = MainWindow(WINDOWS.MAIN.WIDTH, WINDOWS.MAIN.HEIGHT, WINDOWS.MAIN.NAME, resizable=True)
    user_interface = UserInterface(main_loop, main_window)

    pyglet.clock.schedule_interval(main_window.update, WINDOWS.MAIN.FRAME_RATE)
    pyglet.app.run()

# TODO: deleting an interface using the DELETE button does not work
# TODO: viewing a wireless packet does not work :(
# TODO: there is no good way to set the default domain and dns server (of computers that did not get address from DHCP)
