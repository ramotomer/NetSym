from __future__ import annotations

from abc import abstractmethod, ABC
from typing import TYPE_CHECKING, Optional, List

from NetSym.computing.internals.processes.abstracts.process import WaitingFor, T_ProcessCode, Timeout
from NetSym.consts import COMPUTER, T_Time
from NetSym.exceptions import SocketNotBoundError, SocketIsClosedError

if TYPE_CHECKING:
    from NetSym.computing.computer import Computer


class Socket(ABC):
    """
    A socket is an operation-system object that allows for an abstraction of network access
    and sessions
    """
    def __init__(self,
                 computer: Computer,
                 address_family: int = COMPUTER.SOCKETS.ADDRESS_FAMILIES.AF_INET,
                 kind: int = COMPUTER.SOCKETS.TYPES.SOCK_STREAM) -> None:
        """
        Generates a socket
        :param computer: the computer that contains the socket
        :param address_family: usually you need AF_INET
        :param kind: SOCK_STREAM is TCP, SOCK_DGRAM is udp.
        """
        self.computer = computer
        self.address_family = address_family
        self.kind = kind

        self.received: List[bytes] = []

        self.is_closed = False
        self.is_bound = False

    @property
    def acquiring_process_pid(self) -> int:
        return self.computer.sockets[self].pid

    @property
    def state(self) -> str:
        return self.computer.sockets[self].state
    
    @property
    def has_data_to_receive(self) -> bool:
        return bool(self.received)

    def assert_is_bound(self) -> None:
        if not self.is_bound:
            raise SocketNotBoundError("The socket is not bound to any address or port!!!")

    def assert_is_not_closed(self) -> None:
        if self.is_closed:
            raise SocketIsClosedError("The socket is closed and cannot be used!!!")

    @abstractmethod
    def send(self, data) -> None:
        """
        Sends down the socket some data
        :param data: string
        :return:
        """

    def block_until_received(self, timeout: Optional[T_Time] = None) -> T_ProcessCode:
        """
        Like `self.receive` but is a generator that process can use `yield from` upon.
        takes in a list, appends it with the received data when the generator is over.
        :return:
        """
        yield WaitingFor((lambda: self.has_data_to_receive), timeout=Timeout(timeout) if timeout is not None else None)

    def block_until_received_or_closed(self) -> T_ProcessCode:
        """
        Like `self.block_until_received` - but the condition also matches if the socket is closed :)
        :return:
        """
        yield WaitingFor(lambda: self.has_data_to_receive or self.is_closed)

    def close(self) -> None:
        """
        Closes the socket
        :return:
        """
        self.is_closed = True
        try:
            self.computer.sockets[self].state = COMPUTER.SOCKETS.STATES.CLOSED
        except KeyError:
            # If the process died
            pass
