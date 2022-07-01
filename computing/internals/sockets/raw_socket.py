from typing import Tuple

from address.ip_address import IPAddress
from computing.internals.sockets.socket import Socket
from consts import COMPUTER, INTERFACES
from exceptions import ActionNotSupportedInARawSocket, RawSocketError, SocketNotBoundError


class RawSocket(Socket):
    """
    A socket is an operation-system object that allows for an abstraction of network access
    and sessions
    """

    def __init__(self, computer, kind):
        """
        Generates a socket

        filter: a function that takes in a packet and returns a `bool`. Tells us whether or not the socket wishes to take that packet in

        :param computer: the computer that contains the socket
        """
        super(RawSocket, self).__init__(computer, kind=COMPUTER.SOCKETS.TYPES.SOCK_RAW)
        self.is_connected = True
        self.allow_being_broken = True

        self.filter = None
        self.interface = INTERFACES.NO_INTERFACE

    @property
    def bound_address(self):
        raise ActionNotSupportedInARawSocket(f"It is meaningless to bind a raw socket to an address! socket: {self}, computer: {self.computer}")

    @property
    def foreign_address(self):
        raise ActionNotSupportedInARawSocket(f"Raw sockets are not connected! they are just ")

    @property
    def state(self):
        return self.computer.sockets[self].state

    def send(self, packet):
        """
        Directly sends the supplied packet down the socket and out into the world
        :param packet: a Packet object to send
        :return:
        """
        if not self.is_bound:
            raise SocketNotBoundError(f"Bind the raw socket to an interface and filter before trying to use it for sending!")
        if self.interface is INTERFACES.ANY_INTERFACE:
            raise RawSocketError("Cannot send on a raw socket that is bound to all interfaces!")
        self.computer.send(packet, self.interface)

    def recv(self, count=None):
        """
        Recv the information as specified in the BPF that was configured when the socket was bound
        :param count: is ignored
        """
        returned = self.received[:]
        self.received.clear()
        return returned

    def bind(self, filter, interface=INTERFACES.ANY_INTERFACE, promisc=False):
        """

        """
        self.is_bound = True

        self.filter = filter
        self.interface = interface
        if promisc:
            if interface is INTERFACES.ANY_INTERFACE:
                raise RawSocketError(f"Cannot use promiscuous mode when the socket is on all interfaces!!! socket: {self}, computer: {self.computer}")
            interface.is_promisc = True

    def connect(self, address: Tuple[IPAddress, int]):
        """
        Connect to a listening socket with the given address
        :param address:
        :return:
        """
        raise ActionNotSupportedInARawSocket("Do not call the connect method of a raw socket! What are you connecting to?")

    def listen(self, count: int):
        """
        Listen for connections to this socket.
        :param count:
        :return:
        """
        raise ActionNotSupportedInARawSocket("Do not call the listen method of a raw socket! What are you listening to?")

    def accept(self):
        """
        Accept connections to this socket.
        :return:
        """
        raise ActionNotSupportedInARawSocket("Do not call the accept method of a raw socket! What are you accepting?")

    def __repr__(self):
        return f"RAW    " \
            f"{'raw': <23}" \
            f"{'raw': <23}" \
            f"{self.state: <16}" \
            f"{self.acquiring_process_pid}"
