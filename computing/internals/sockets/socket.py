from abc import ABCMeta, abstractmethod
from typing import Tuple

from address.ip_address import IPAddress
from computing.internals.processes.abstracts.process import WaitingFor
from consts import COMPUTER, T_Port
from exceptions import SocketNotBoundError, SocketIsClosedError


class Socket(metaclass=ABCMeta):
    """
    A socket is an operation-system object that allows for an abstraction of network access
    and sessions
    """
    def __init__(self, computer,
                 address_family=COMPUTER.SOCKETS.ADDRESS_FAMILIES.AF_INET,
                 kind=COMPUTER.SOCKETS.TYPES.SOCK_STREAM):
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
    def acquiring_process_pid(self):
        return self.computer.sockets[self].pid

    @property
    def state(self):
        return self.computer.sockets[self].state
    
    @property
    def has_data_to_receive(self):
        return bool(self.received)

    def assert_is_bound(self):
        if not self.is_bound:
            raise SocketNotBoundError("The socket is not bound to any address or port!!!")

    def assert_is_not_closed(self):
        if self.is_closed:
            raise SocketIsClosedError("The socket is closed and cannot be used!!!")

    @abstractmethod
    def send(self, data):
        """
        Sends down the socket some data
        :param data: string
        :return:
        """

    @abstractmethod
    def receive(self, count):
        """
        receive the information from the other side of the socket
        :param count: how many bytes to receive
        :return:
        """

    @abstractmethod
    def bind(self, address: Tuple[IPAddress, T_Port]):
        """
        Binds the socket to a certain address and port on the computer
        :param address:
        :return:
        """

    def block_until_received(self):
        """
        Like `self.receive` but is a generator that process can use `yield from` upon.
        takes in a list, appends it with the received data when the generator is over.
        :return:
        """
        yield WaitingFor(lambda: self.has_data_to_receive)

    def block_until_received_or_closed(self):
        """
        Like `self.block_until_received` - but the condition also matches if the socket is closed :)
        :return:
        """
        yield WaitingFor(lambda: self.has_data_to_receive or self.is_closed)

    def close(self):
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
