from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List, Callable, Union

from NetSym.computing.internals.network_interfaces.interface import Interface
from NetSym.computing.internals.sockets.socket import Socket
from NetSym.consts import COMPUTER, INTERFACES
from NetSym.exceptions import *

if TYPE_CHECKING:
    from NetSym.packets.packet import Packet
    from NetSym.computing.internals.processes.abstracts.process import ReturnedPacket
    from NetSym.computing.computer import Computer


class RawSocket(Socket):
    """
    A socket is an operation-system object that allows for an abstraction of network access
    and sessions
    """
    received: List[ReturnedPacket]  # type: ignore

    def __init__(self, computer: Computer, kind: int) -> None:
        """
        Generates a socket

        filter: a function that takes in a packet and returns a `bool`. Tells us whether or not the socket wishes to take that packet in
        interface: The interface to listen on. Can be set to INTERFACES.ANY_INTERFACE for all interfaces

        :param computer: the computer that contains the socket
        """
        super(RawSocket, self).__init__(computer, kind=COMPUTER.SOCKETS.TYPES.SOCK_RAW)
        self.is_connected = True

        self._filter: Optional[Callable[[Packet], bool]] = None
        self.interface: Optional[Union[str, Interface]] = INTERFACES.NO_INTERFACE
        self.is_promisc = False

    @property
    def filter(self) -> Callable[[Packet], bool]:
        if (self._filter is None) or not self.is_bound:
            raise SocketNotBoundError(f"Cannot get the filter if the socket was not yet bound! socket: {self!r}")

        return self._filter

    def get_interface(self) -> Interface:
        """
        Return the interface the socket is bound to.
        If the socket is not bound, or if it is bound to ANY - raise :)
        """
        if (self.interface is None) or (self.interface is INTERFACES.NO_INTERFACE):
            raise SocketNotBoundError(f"No interface to get! Socket: {self!r}")

        return self.interface

    def send(self, packet: Packet) -> None:
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

    def receive(self, count: Optional[int] = None) -> List[ReturnedPacket]:
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

    def bind(self,
             filter: Callable[[Packet], bool],
             interface: Optional[Interface] = INTERFACES.ANY_INTERFACE,
             promisc: bool = False) -> None:
        """
        Binds the socket to an interface and filter.
        This is necessary for sniffing and sending using it.
        """
        self.assert_is_not_closed()

        self.is_bound = True
        self._filter = filter
        self.interface = interface
        if promisc:
            if interface is INTERFACES.ANY_INTERFACE:
                raise RawSocketError(f"Cannot use promiscuous mode when the socket is on all interfaces!!! socket: {self}, computer: {self.computer}")
            interface.is_promisc = True
        self.is_promisc = promisc
        self.computer.sockets[self].state = COMPUTER.SOCKETS.STATES.BOUND

    def __repr__(self) -> str:
        return f"RAW    " \
            f"{self.interface.name or 'unbound': <23}" \
            f"{'raw': <23}" \
            f"{self.state: <16}" \
            f"{self.acquiring_process_pid}"
