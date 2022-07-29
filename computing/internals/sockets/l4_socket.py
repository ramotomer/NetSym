import random
from abc import ABCMeta, abstractmethod
from typing import Tuple, Optional

from address.ip_address import IPAddress
from computing.internals.sockets.socket import Socket
from consts import COMPUTER, PORTS
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
        try:
            return COMPUTER.SOCKETS.L4_PROTOCOLS[self.kind]
        except KeyError:
            raise UnknownLayer4SocketTypeError(
                f"no such l4 protocol! socket: {self}, type: {self.kind} only known types are: {COMPUTER.SOCKETS.L4_PROTOCOLS}")

    @property
    def remote_address(self):
        return self.computer.sockets[self].remote_ip_address, self.computer.sockets[self].remote_port

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
        data = ''.join(self.received) if self.received else ''
        self.received.clear()
        return data

    @staticmethod
    def generate_port():
        return random.randint(*PORTS.USERMODE_USABLE_RANGE)

    def bind(self, address: Tuple[Optional[IPAddress], Optional[int]] = (None, None)):
        """
        Binds the socket to a certain address and port on the computer
        """
        ip, port = address
        port = port if port is not None else self.generate_port()
        ip = ip if ip is not None else IPAddress.no_address()

        if not self.computer.has_this_ip(ip) and ip != IPAddress.no_address():
            raise InvalidAddressError(f"computer {self.computer} does not have the address {ip} so socket {self} cannot be bound to it")

        self.computer.bind_socket(self, (ip, port))

    def get_str_representation(self,
                               proto_space_count=COMPUTER.SOCKETS.REPR.PROTO_SPACE_COUNT,
                               local_address_space_count=COMPUTER.SOCKETS.REPR.LOCAL_ADDRESS_SPACE_COUNT,
                               remote_address_space_count=COMPUTER.SOCKETS.REPR.REMOTE_ADDRESS_SPACE_COUNT,
                               state_space_count=COMPUTER.SOCKETS.REPR.STATE_SPACE_COUNT):

        return f"{self.protocol: <{proto_space_count}} " \
            f"{':'.join(map(str, self.bound_address)): <{local_address_space_count}} " \
            f"{':'.join(map(str, self.remote_address)): <{remote_address_space_count}} " \
            f"{self.state: <{state_space_count}} " \
            f"{self.acquiring_process_pid}"

    def __repr__(self):
        return self.get_str_representation(0, 0, 0, 0)
