import pyglet

from consts import *
from gui.main_loop import MainLoop
from gui.main_window import MainWindow
from gui.user_interface import UserInterface

if __name__ == '__main__':
    user_interface = UserInterface()
    main_window = MainWindow(user_interface, WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_NAME, resizable=False)
    main_loop = MainLoop(main_window)
    pyglet.clock.schedule_interval(main_window.update, FRAME_RATE)
    pyglet.app.run()

    # TODO: there are errors with removing connections and the routing table
    # TODO: Movable popup windows
    # TODO: cannot add routes to a router.
    # TODO: maybe some-day add a `receiving_time` and a `receiving_interface` attributes to a `Packet` object. -
    #  you will have a big refactoring to do but the code will be *much* cleaner!
    # TODO: add udp `open_ports` list. Add to it DHCP
    # TODO: add lost packets handling for DHCP and non-existent DHCP server
    # TODO: handle PL anywhere in TCP! (retransmissions don't quite work)
    # TODO: sometimes in retransmissions a packet just freezes on the connection for no reason, pressing it crashes the program.

    # TODO: servers sometimes do not fin, usually if it is not the first time they are approached.
    # TODO: handle PL in the TCP handshakes!
    # TODO: add a receiving window in TCP.
    # TODO: add a different kind of PL that makes packets arrive in different order. (to test TCP)
    # TODO: handle lost ACKs (dup ack and retransmissions that you already received)
    # TODO: handle packets that are out of order in TCP!
    # TODO: add TCP SACK
    # TODO: FTP is a layer not just a string. Overall learn about FTP and actually implement it similarly to how it actually works!!!
