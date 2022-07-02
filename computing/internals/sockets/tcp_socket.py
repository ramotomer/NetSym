from typing import Tuple

from address.ip_address import IPAddress
from computing.internals.processes.abstracts.process import WaitingFor
from computing.internals.processes.kernelmode_processes.sockets.tcp_socket_process import ListeningTCPSocketProcess, \
    ConnectingTCPSocketProcess
from computing.internals.sockets.l4_socket import L4Socket
from consts import COMPUTER


class TCPSocket(L4Socket):
    """
    A socket is an operation-system object that allows for an abstraction of network access
    and sessions
    """
    def __init__(self, computer, address_family=COMPUTER.SOCKETS.ADDRESS_FAMILIES.AF_INET):
        """
        Generates a socket
        :param computer: the computer that contains the socket
        :param address_family: usually you need AF_INET
        """
        super(TCPSocket, self).__init__(computer, address_family, COMPUTER.SOCKETS.TYPES.SOCK_STREAM)
        self.protocol = 'TCP'

    def send(self, data):
        """
        Sends down the socket some data
        :param data: string
        :return:
        """
        self.to_send.append(data)

    def connect(self, address: Tuple[IPAddress, int]):
        """
        Connect to a listening socket with the given address
        :param address:
        :return:
        """
        self.pid = self.computer.process_scheduler.start_kernelmode_process(ConnectingTCPSocketProcess, self, address)

    def listen(self, count: int):
        """
        Listen for connections to this socket.
        :param count:
        :return:
        """
        self.computer.sockets[self].state = COMPUTER.SOCKETS.STATES.LISTENING
        self.computer.graphics.update_image()
        self.listening_count = count

    def accept(self):
        """
        Accept connections to this socket.
        :return:
        """
        self.pid = self.computer.process_scheduler.start_kernelmode_process(ListeningTCPSocketProcess, self, self.bound_address)

    def blocking_accept(self):
        """
        Just like `self.accept` - only processes can use `yield from` to block until the socket is connected :)
        :return:
        """
        self.accept()
        yield WaitingFor(lambda: self.is_connected)

    def close(self):
        super(TCPSocket, self).close()
        self.process.close_socket_when_done_transmitting = True
