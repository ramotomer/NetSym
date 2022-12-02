from __future__ import annotations

from typing import Tuple, List, Union, Optional, TYPE_CHECKING, NamedTuple

import scapy

from NetSym.address.ip_address import IPAddress
from NetSym.computing.internals.sockets.l4_socket import L4Socket
from NetSym.consts import COMPUTER, T_Port
from NetSym.exceptions import *

if TYPE_CHECKING:
    from NetSym.computing.computer import Computer


class ReturnedUDPPacket(NamedTuple):
    """
    A UDP packet which is received from a UDP socket, with its metadata
    """
    data:     bytes
    src_ip:   IPAddress
    src_port: T_Port


class UDPSocket(L4Socket):
    """
    A socket is an operation-system object that allows for an abstraction of network access and sessions
    """

    def __init__(self,
                 computer: Computer,
                 address_family: int = COMPUTER.SOCKETS.ADDRESS_FAMILIES.AF_INET) -> None:
        """
        Generates a socket
        :param computer: the computer that contains the socket
        :param address_family: usually you need AF_INET - I think it means IP
        """
        super(UDPSocket, self).__init__(computer, address_family, COMPUTER.SOCKETS.TYPES.SOCK_DGRAM)

    def sendto(self, data: Union[str, bytes, scapy.packet.Packet], address: Tuple[IPAddress, T_Port]) -> None:
        """
        Sends down the socket some data
        """
        self.assert_is_bound()
        self.assert_is_not_closed()
        _, src_port = self.bound_address
        dst_ip, dst_port = address
        self.computer.start_sending_udp_packet(dst_ip, src_port, dst_port, data)

    def send(self, data: Union[str, bytes, scapy.packet.Packet]) -> None:
        """
        Send data to the other party. Only works for connected sockets
        :param data:
        :return:
        """
        self.assert_is_bound()
        self.assert_is_not_closed()
        self.assert_is_connected()
        dst_ip, dst_port = self.remote_address
        self.sendto(data, (dst_ip, dst_port))

    def receivefrom(self) -> List[ReturnedUDPPacket]:
        self.assert_is_bound()
        self.assert_is_not_closed()
        return [self.received.pop(0) for _ in range(len(self.received))]

    def receive(self, count: Optional[int] = 1024) -> List[bytes]:
        self.assert_is_bound()
        self.assert_is_not_closed()
        self.assert_is_connected()
        return [self.received.pop(0).data for _ in range(len(self.received))]

    def connect(self, address: Tuple[IPAddress, T_Port]) -> None:
        """
        Connect to a listening socket with the given address
        :param address:
        :return:
        """
        dst_ip, dst_port = self.remote_address
        if dst_ip is not None:
            raise SocketAlreadyConnectedError(f"{self} is already connected to {dst_ip, dst_port}")

        self.computer.sockets[self].remote_ip_address, self.computer.sockets[self].remote_port = address
        self.computer.sockets[self].state = COMPUTER.SOCKETS.STATES.ESTABLISHED
        self.is_connected = True
