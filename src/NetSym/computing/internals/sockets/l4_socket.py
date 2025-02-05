from __future__ import annotations

import random
from abc import abstractmethod
from typing import Tuple, Optional, TYPE_CHECKING

from NetSym.address.ip_address import IPAddress
from NetSym.computing.internals.sockets.socket import Socket
from NetSym.consts import COMPUTER, PORTS, T_Port
from NetSym.exceptions import *

if TYPE_CHECKING:
    from NetSym.computing.computer import Computer


class L4Socket(Socket):
    """
    UDP/TCP sockets have many functions in common :)
    """

    def __init__(self,
                 computer: Computer,
                 address_family: int = COMPUTER.SOCKETS.ADDRESS_FAMILIES.AF_INET,
                 kind: int = COMPUTER.SOCKETS.TYPES.SOCK_STREAM) -> None:
        super(L4Socket, self).__init__(computer, address_family=address_family, kind=kind)
        self.is_connected = False

    @property
    def protocol(self) -> str:
        try:
            return COMPUTER.SOCKETS.L4_PROTOCOLS[self.kind]
        except KeyError:
            raise UnknownLayer4SocketTypeError(
                f"no such l4 protocol! socket: {self}, type: {self.kind} only known types are: {COMPUTER.SOCKETS.L4_PROTOCOLS}")

    @property
    def remote_address(self) -> Tuple[Optional[IPAddress], Optional[T_Port]]:
        return self.computer.sockets[self].remote_ip_address, self.computer.sockets[self].remote_port

    @property
    def bound_address(self) -> Tuple[IPAddress, T_Port]:
        ip = self.computer.sockets[self].local_ip_address
        port = self.computer.sockets[self].local_port
        if (ip is None) or (port is None):
            raise ThisValueShouldNeverBeNone(f"IP: {ip}, port: {port}")

        return ip, port

    def assert_is_connected(self) -> None:
        if not self.is_connected:
            raise SocketNotConnectedError("The socket is not connected!!!")

    @abstractmethod
    def connect(self, address: Tuple[IPAddress, T_Port]) -> None:
        """
        Connect to a listening socket with the given address
        :param address:
        :return:
        """

    @staticmethod
    def generate_port() -> int:
        return random.randint(*PORTS.USERMODE_USABLE_RANGE)

    def bind(self, address: Tuple[Optional[IPAddress], Optional[int]] = (None, None)) -> None:
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
                               proto_space_count: int = COMPUTER.SOCKETS.REPR.PROTO_SPACE_COUNT,
                               local_address_space_count: int = COMPUTER.SOCKETS.REPR.LOCAL_ADDRESS_SPACE_COUNT,
                               remote_address_space_count: int = COMPUTER.SOCKETS.REPR.REMOTE_ADDRESS_SPACE_COUNT,
                               state_space_count: int = COMPUTER.SOCKETS.REPR.STATE_SPACE_COUNT) -> str:

        return f"{self.protocol: <{proto_space_count}} " \
            f"{':'.join(map(str, self.bound_address)): <{local_address_space_count}} " \
            f"{':'.join(map(str, self.remote_address)): <{remote_address_space_count}} " \
            f"{self.state: <{state_space_count}} " \
            f"{self.acquiring_process_pid}"

    def __repr__(self) -> str:
        return self.get_str_representation(0, 0, 0, 0)
