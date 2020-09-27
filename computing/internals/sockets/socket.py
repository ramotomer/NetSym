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
        self.received = []

        self.is_connected = False
        self.is_closed = False

        self.listening_count = None

        self.__class__.send = self.check_not_closed(self.check_connected(self.check_not_broken(self.__class__.send)))
        self.__class__.recv = self.check_not_closed(self.check_bound(self.check_connected(self.check_not_broken(self.__class__.recv))))
        self.__class__.listen = self.check_bound(self.check_not_closed(self.__class__.listen))
        self.__class__.accept = self.check_bound(self.check_not_closed(self.__class__.accept))
        self.__class__.connect = self.check_not_closed(self.__class__.connect)
        # ^ decorators that survive inheritance

    @property
    def bound_address(self):
        return self.computer.sockets[self].local_ip_address, self.computer.sockets[self].local_port

    @property
    def process(self):
        return self.computer.process_scheduler.get_process(self.pid, raises=False)

    @property
    def acquiring_process_pid(self):
        return self.computer.sockets[self].pid

    @property
    def state(self):
        return self.computer.sockets[self].state
    
    @property
    def foreign_address(self):
        address = self.computer.sockets[self].remote_ip_address
        port = self.computer.sockets[self].remote_port

        address = address if address is not None else IPAddress("0.0.0.0")
        port = port if port is not None else 0

        return address, port

    @staticmethod
    def check_bound(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if self.computer.sockets[self].local_port is None:
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
                raise SocketIsBrokenError(f"The socket is broken and cannot be used!!! pid: {self.pid}, process: {self.process}")
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
        self.is_connected = False
        self.computer.send_process_signal(self.pid, COMPUTER.PROCESSES.SIGNALS.SIGTERM)
        self.computer.sockets[self].state = COMPUTER.SOCKETS.STATES.CLOSED
        # self.computer.remove_socket(self)

    def __repr__(self):
        return f"       " \
            f"{':'.join(map(str, self.bound_address)): <23}" \
            f"{':'.join(map(str, self.foreign_address)): <23}" \
            f"{self.state: <16}" \
            f"{self.acquiring_process_pid}"
