from computing.internals.sockets.socket import Socket
from consts import COMPUTER, INTERFACES
from exceptions import RawSocketError


class RawSocket(Socket):
    """
    A socket is an operation-system object that allows for an abstraction of network access
    and sessions
    """

    def __init__(self, computer, kind):
        """
        Generates a socket

        filter: a function that takes in a packet and returns a `bool`. Tells us whether or not the socket wishes to take that packet in
        interface: The interface to listen on. Can be set to INTERFACES.ANY_INTERFACE for all interfaces

        :param computer: the computer that contains the socket
        """
        super(RawSocket, self).__init__(computer, kind=COMPUTER.SOCKETS.TYPES.SOCK_RAW)
        self.is_connected = True

        self.filter = None
        self.interface = INTERFACES.NO_INTERFACE
        self.is_promisc = False

    def send(self, packet):
        """
        Directly sends the supplied packet down the socket and out into the world
        :param packet: a Packet object to send
        :return:
        """
        self.assert_is_bound()
        self.assert_is_not_closed()
        if self.interface is INTERFACES.ANY_INTERFACE:
            raise RawSocketError("Cannot send on a raw socket that is bound to all interfaces!")
        self.computer.send(packet, self.interface, sending_socket=self)

    def receive(self, count=None):
        """
        Receive the information as specified in the BPF that was configured when the socket was bound
        :param count: is ignored
        :return `list[ReturnedPacket]`
        """
        self.assert_is_bound()
        self.assert_is_not_closed()
        returned = self.received[:]
        self.received.clear()
        return returned

    def bind(self, filter, interface=INTERFACES.ANY_INTERFACE, promisc=False):
        """
        Binds the socket to an interface and filter.
        This is necessary for sniffing and sending using it.
        """
        self.assert_is_not_closed()

        self.is_bound = True
        self.filter = filter
        self.interface = interface
        if promisc:
            if interface is INTERFACES.ANY_INTERFACE:
                raise RawSocketError(f"Cannot use promiscuous mode when the socket is on all interfaces!!! socket: {self}, computer: {self.computer}")
            interface.is_promisc = True
        self.is_promisc = promisc
        self.computer.sockets[self].state = COMPUTER.SOCKETS.STATES.BOUND

    def __repr__(self):
        return f"RAW    " \
            f"{self.interface.name or 'unbound': <23}" \
            f"{'raw': <23}" \
            f"{self.state: <16}" \
            f"{self.acquiring_process_pid}"
