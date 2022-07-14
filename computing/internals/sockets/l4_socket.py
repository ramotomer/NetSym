from abc import ABCMeta, abstractmethod
from typing import Tuple

from address.ip_address import IPAddress
from computing.internals.sockets.socket import Socket
from consts import COMPUTER
from exceptions import *


class L4Socket(Socket, metaclass=ABCMeta):
    """
    UDP/TCP sockets have many functions in common :)
    """
    def __init__(self, computer, address_family=COMPUTER.SOCKETS.ADDRESS_FAMILIES.AF_INET, kind=COMPUTER.SOCKETS.TYPES.SOCK_STREAM):
        super(L4Socket, self).__init__(computer, address_family=address_family, kind=kind)
        self.is_connected = False

    @property
    def protocol(self):
        if self.kind == COMPUTER.SOCKETS.TYPES.SOCK_STREAM:
            return "TCP"
        if self.kind == COMPUTER.SOCKETS.TYPES.SOCK_DGRAM:
            return "UDP"
        raise UnknownLayer4SocketTypeError(f"no such l4 protocol! socket: {self}, type: {self.kind}")

    @property
    def remote_address(self):
        address = self.computer.sockets[self].remote_ip_address
        port = self.computer.sockets[self].remote_port

        address = address if address is not None else IPAddress("0.0.0.0")
        port = port if port is not None else 0

        return address, port

    @property
    def bound_address(self):
        return self.computer.sockets[self].local_ip_address, self.computer.sockets[self].local_port

    def assert_is_connected(self):
        if not self.is_connected:
            raise SocketNotConnectedError("The socket is not connected!!!")

    @abstractmethod
    def connect(self, address: Tuple[IPAddress, int]):
        """
        Connect to a listening socket with the given address
        :param address:
        :return:
        """

    def receive(self, count=1024):
        """
        receive the information from the other side of the socket
        :param count: how many bytes to receive
        :return:
        """
        data = ''.join(self.received) if self.received else None
        self.received.clear()
        return data

    def bind(self, address: Tuple[IPAddress, int]):
        """
        Binds the socket to a certain address and port on the computer
        :param address:
        """
        self.computer.bind_socket(self, address)

    def __str__(self):
        return f"socket of {self.computer.name}"

    def __repr__(self):
        return f"{self.protocol}    " \
            f"{':'.join(map(str, self.bound_address)): <23}" \
            f"{':'.join(map(str, self.remote_address)): <23}" \
            f"{self.state: <16}" \
            f"{self.acquiring_process_pid}"
