from typing import Tuple

from address.ip_address import IPAddress
from computing.internals.sockets.l4_socket import L4Socket
from consts import COMPUTER


class UDPSocket(L4Socket):
    """
    A socket is an operation-system object that allows for an abstraction of network access
    and sessions
    """
    def __init__(self, computer, address_family=COMPUTER.SOCKETS.ADDRESS_FAMILIES.AF_INET):
        """
        Generates a socket
        :param computer: the computer that contains the socket
        :param address_family: usually you need AF_INET - I think it means IP
        """
        super(UDPSocket, self).__init__(computer, address_family, COMPUTER.SOCKETS.TYPES.SOCK_DGRAM)
        self.protocol = 'UDP'
        self.is_connected = True
        self.allow_being_broken = True

    def send(self, data):
        """
        Sends down the socket some data
        :param data: string
        :return:
        """
        _, src_port = self.bound_address
        dst_ip, dst_port = self.foreign_address
        self.computer.start_sending_udp_packet(dst_ip, src_port, dst_port, data)

    def connect(self, address: Tuple[IPAddress, int]):
        """
        Connect to a listening socket with the given address
        :param address:
        :return:
        """
        raise NotImplementedError

    def listen(self, count: int):
        """
        Listen for connections to this socket.
        :param count:
        :return:
        """
        raise NotImplementedError

    def accept(self):
        """
        Accept connections to this socket.
        :return:
        """
        raise NotImplementedError
