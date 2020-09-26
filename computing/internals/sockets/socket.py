from abc import ABCMeta, abstractmethod
from functools import wraps
from typing import Tuple

from address.ip_address import IPAddress
from consts import COMPUTER
from exceptions import SocketNotBoundError, SocketNotConnectedError, SocketIsBrokenError, SocketIsClosedError


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

        self.pid = None

        self.to_send = []
        self.received = None

        self.is_connected = False
        self.is_closed = False

        self.listening_count = None

        self.send = self.check_connected(self.check_not_broken(self.check_not_closed(self.send)))
        self.recv = self.check_bound(self.check_connected(self.check_not_broken(self.check_not_closed(self.recv))))
        self.listen = self.check_bound(self.check_not_closed(self.listen))
        self.accept = self.check_bound(self.check_not_closed(self.accept))
        self.connect = self.check_not_closed(self.connect)
        # ^ decorators that survive inheritance

    @property
    def bound_address(self):
        return self.computer.sockets[self].local_ip_address, self.computer.sockets[self].local_port

    @property
    def process(self):
        return self.computer.process_scheduler.get_process(self.pid, raises=False)

    @staticmethod
    def check_bound(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if self.computer.sockets[self].local_port is not None:
                raise SocketNotBoundError("The socket is not bound to any address or port!!!")
            return func(self, *args, **kwargs)
        return wrapper

    @staticmethod
    def check_connected(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self.is_connected:
                raise SocketNotConnectedError("The socket is not connected!!!")
            return func(self, *args, **kwargs)
        return wrapper

    @staticmethod
    def check_not_broken(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if self.pid is None or \
                    self.process is None:
                raise SocketIsBrokenError("The socket is broken and cannot be used!!!")
            return func(self, *args, **kwargs)
        return wrapper

    @staticmethod
    def check_not_closed(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if self.is_closed:
                raise SocketIsClosedError("The socket is closed and cannot be used!!!")
            return func(self, *args, **kwargs)

        return wrapper

    @abstractmethod
    def send(self, data):
        """
        Sends down the socket some data
        :param data: string
        :return:
        """

    @abstractmethod
    def recv(self, count):
        """
        Recv the information from the other side of the socket
        :param count: how many bytes to receive
        :return:
        """

    @abstractmethod
    def connect(self, address: Tuple[IPAddress, int]):
        """
        Connect to a listening socket with the given address
        :param address:
        :return:
        """

    @abstractmethod
    def bind(self, address: Tuple[IPAddress, int]):
        """
        Binds the socket to a certain address and port on the computer
        :param address:
        :return:
        """

    @abstractmethod
    def listen(self, count: int):
        """
        Listen for connections to this socket.
        :param count:
        :return:
        """

    @abstractmethod
    def accept(self):
        """
        Accept connections to this socket.
        :return:
        """

    def close(self):
        """
        Closes the socket
        :return:
        """
        self.is_closed = True
        self.computer.send_process_signal(self.pid, COMPUTER.PROCESSES.SIGNALS.SIGTERM)
