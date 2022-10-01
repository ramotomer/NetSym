from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Tuple, TYPE_CHECKING, Optional, Any, List

from address.ip_address import IPAddress
from computing.internals.processes.abstracts.process import WaitingFor, T_ProcessCode, WaitingForWithTimeout, Timeout
from consts import COMPUTER, T_Port, T_Time
from exceptions import SocketNotBoundError, SocketIsClosedError

if TYPE_CHECKING:
    from computing.computer import Computer


class Socket(metaclass=ABCMeta):
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

        self.received = []

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

    @abstractmethod
    def receive(self, count: Optional[int]) -> List[Any]:
        """
        receive the information from the other side of the socket
        :param count: how many bytes to receive
        :return:
        """

    @abstractmethod
    def bind(self, address: Tuple[IPAddress, T_Port]) -> None:
        """
        Binds the socket to a certain address and port on the computer
        :param address:
        :return:
        """

    def block_until_received(self, timeout: Optional[T_Time] = None) -> T_ProcessCode:
        """
        Like `self.receive` but is a generator that process can use `yield from` upon.
        takes in a list, appends it with the received data when the generator is over.
        :return:
        """
        if timeout is None:
            yield WaitingFor(lambda: self.has_data_to_receive)
        else:
            yield WaitingForWithTimeout((lambda: self.has_data_to_receive), Timeout(timeout))

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
