import random
from collections import namedtuple
from typing import Tuple, List, Union

from address.ip_address import IPAddress
from computing.internals.sockets.l4_socket import L4Socket
from consts import COMPUTER, PORTS
from exceptions import *

ReturnedUDPPacket = namedtuple("ReturnedUDPPacket", [
    "data",
    "src_ip",
    "src_port",
])


class UDPSocket(L4Socket):
    """
    A socket is an operation-system
    em object that allows for an abstraction of network access
    and sessions
    """

    def __init__(self, computer, address_family=COMPUTER.SOCKETS.ADDRESS_FAMILIES.AF_INET):
        """
        Generates a socket
        :param computer: the computer that contains the socket
        :param address_family: usually you need AF_INET - I think it means IP
        """
        super(UDPSocket, self).__init__(computer, address_family, COMPUTER.SOCKETS.TYPES.SOCK_DGRAM)
        self.allow_being_broken = True

    def sendto(self, data, address: Tuple[IPAddress, int]):
        """
        Sends down the socket some data
        """
        self.assert_is_bound()
        self.assert_is_not_closed()
        _, src_port = self.bound_address
        dst_ip, dst_port = address
        self.computer.start_sending_udp_packet(dst_ip, src_port, dst_port, data)

    def receivefrom(self) -> List[ReturnedUDPPacket]:
        self.assert_is_bound()
        self.assert_is_not_closed()
        return [self.received.pop(0) for _ in range(len(self.received))]

    def receive(self, count=1024) -> List[str]:
        self.assert_is_bound()
        self.assert_is_not_closed()
        self.assert_is_connected()
        return [self.received.pop(0).data for _ in range(len(self.received))]

    def send(self, data):
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

    def connect(self, address: Tuple[IPAddress, int]):
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

    def bind(self, address: Union[Tuple[IPAddress, int], None] = None):
        if address is None:
            try:
                address = self.computer.ips[0], random.randint(*PORTS.USERMODE_USABLE_RANGE)
            except IndexError:
                raise NoIPAddressError(
                    f"Cannot bind udp socket without an IP address! on socket: {self} computer: {self.computer} ips: {self.computer.ips}")

        ip, port = address
        if not self.computer.has_this_ip(ip) and ip != IPAddress.no_address():
            raise InvalidAddressError(f"computer {self.computer} does not have the address {ip} so socket {self} cannot be bound to it")
        super(UDPSocket, self).bind(address)
