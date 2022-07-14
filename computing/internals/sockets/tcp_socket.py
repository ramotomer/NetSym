from typing import Tuple

from address.ip_address import IPAddress
from computing.internals.processes.abstracts.process import WaitingFor
from computing.internals.processes.kernelmode_processes.tcp_socket_process import ListeningTCPSocketProcess, \
    ConnectingTCPSocketProcess
from computing.internals.sockets.l4_socket import L4Socket
from consts import COMPUTER
from exceptions import SocketIsBrokenError


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
        self.to_send = []

        self.listening_count = None

        self.socket_handling_kernelmode_pid = None

    @property
    def socket_handling_kernelmode_process(self):
        return self.computer.process_scheduler.get_process(self.socket_handling_kernelmode_pid, COMPUTER.PROCESSES.MODES.KERNELMODE, raises=False)

    def assert_is_not_broken(self):
        if self.socket_handling_kernelmode_pid is None or self.socket_handling_kernelmode_process is None:
            raise SocketIsBrokenError(f"The socket is broken and cannot be used!!! pid: {self.socket_handling_kernelmode_pid}, "
                                      f"process: {self.socket_handling_kernelmode_process}, computer: {self.computer}")

    def send(self, data):
        """
        Sends down the socket some data
        :param data: string
        :return:
        """
        self.assert_is_bound()
        self.assert_is_not_closed()
        self.assert_is_connected()
        self.assert_is_not_broken()
        self.to_send.append(data)

    def connect(self, address: Tuple[IPAddress, int]):
        """
        Connect to a listening socket with the given address
        :param address:
        :return:
        """
        self.assert_is_bound()
        self.assert_is_not_closed()
        self.socket_handling_kernelmode_pid = self.computer.process_scheduler.start_kernelmode_process(ConnectingTCPSocketProcess, self, address)

    def listen(self, count: int):
        """
        Listen for connections to this socket.
        :param count:
        :return:
        """
        self.assert_is_bound()
        self.assert_is_not_closed()
        self.computer.sockets[self].state = COMPUTER.SOCKETS.STATES.LISTENING
        self.computer.graphics.update_image()
        self.listening_count = count

    def accept(self):
        """
        Accept connections to this socket.
        :return:
        """
        self.assert_is_bound()
        self.assert_is_not_closed()
        self.assert_is_not_broken()
        self.socket_handling_kernelmode_pid = self.computer.process_scheduler.start_kernelmode_process(ListeningTCPSocketProcess, self,
                                                                                                       self.bound_address)

    def blocking_accept(self):
        """
        Just like `self.accept` - only processes can use `yield from` to block until the socket is connected :)
        :return:
        """
        self.accept()
        yield WaitingFor(lambda: self.is_connected)

    def close(self):
        self.assert_is_not_broken()
        super(TCPSocket, self).close()
        self.socket_handling_kernelmode_process.close_socket_when_done_transmitting = True
