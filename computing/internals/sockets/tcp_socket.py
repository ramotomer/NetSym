from typing import Tuple

from address.ip_address import IPAddress
from computing.internals.processes.abstracts.process import WaitingFor
from computing.internals.processes.kernelmode_processes.tcp_socket_process import ListeningTCPSocketProcess, \
    ConnectingTCPSocketProcess
from computing.internals.sockets.l4_socket import L4Socket
from consts import COMPUTER, debugp
from exceptions import TCPSocketConnectionRefused


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

        self.socket_handling_kernelmode_pid = None

    @property
    def socket_handling_kernelmode_process(self):
        return self.computer.process_scheduler.get_process(self.socket_handling_kernelmode_pid, COMPUTER.PROCESSES.MODES.KERNELMODE, raises=False)

    def send(self, data):
        """
        Sends down the socket some data
        :param data: string
        :return:
        """
        self.assert_is_bound()
        self.assert_is_not_closed()
        self.assert_is_connected()
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

    def blocking_connect(self, address: Tuple[IPAddress, int]):
        """
        Same as `accept` only yields a `WaitingFor` namedtuple that waits until the socket is connected
        """
        self.connect(address)
        yield WaitingFor(lambda: self.is_connected or self.is_closed)
        if self.is_closed:
            raise TCPSocketConnectionRefused

    def listen(self):
        """
        Listen for connections to this socket.
        :return:
        """
        self.assert_is_bound()
        self.assert_is_not_closed()
        self.computer.sockets[self].state = COMPUTER.SOCKETS.STATES.LISTENING

    def accept(self):
        """
        Accept connections to this socket.
        :return:
        """
        self.assert_is_bound()
        self.assert_is_not_closed()
        self.socket_handling_kernelmode_pid = self.computer.process_scheduler.start_kernelmode_process(ListeningTCPSocketProcess, self,
                                                                                                       self.bound_address)

    def blocking_accept(self, requesting_process_pid):
        """
        Just like `self.accept` - only processes can use `yield from` to block until the socket is connected :)
        :return:
        """
        self.accept()
        yield WaitingFor(lambda: self.is_connected)

        listening_socket = self.computer.get_socket(requesting_process_pid, address_family=self.address_family, kind=self.kind)
        listening_socket.bind(self.bound_address)
        listening_socket.listen()
        return listening_socket

    def close(self):
        super(TCPSocket, self).close()
        self.socket_handling_kernelmode_process.close_socket_when_done_transmitting = True

    def close_when_done_transmitting(self):
        """
        A generator to `yield from` inside processes.
        Waits until all of the data is sent and then closes the socket :)
        """
        debugp(f"is done: {self.socket_handling_kernelmode_process.is_done_transmitting} {self.socket_handling_kernelmode_process.is_done_transmitting()}")

        yield WaitingFor(self.socket_handling_kernelmode_process.is_done_transmitting)
        debugp(f"{self.computer} found what you're waiting for")
        self.close()
