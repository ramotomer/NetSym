from typing import Tuple

from address.ip_address import IPAddress
from computing.internals.processes.abstracts.process import WaitingFor
from computing.internals.processes.sockets.tcp_socket_process import ListeningTCPSocketProcess, \
    ConnectingTCPSocketProcess
from computing.internals.sockets.socket import Socket
from consts import COMPUTER
from exceptions import SocketIsClosedError


class TCPSocket(Socket):
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

    def send(self, data):
        """
        Sends down the socket some data
        :param data: string
        :return:
        """
        self.to_send.append(data)
        self.computer.send_process_signal(self.pid, COMPUTER.PROCESSES.SIGNALS.SIGSOCKSEND)
        return len(data)

    def recv(self, count=1024):
        """
        Recv the information from the other side of the socket
        :param count: how many bytes to receive
        :return:
        """
        data = ''.join(self.received) if self.received else None
        self.received.clear()
        return data

    def connect(self, address: Tuple[IPAddress, int]):
        """
        Connect to a listening socket with the given address
        :param address:
        :return:
        """
        self.pid = self.computer.start_process(ConnectingTCPSocketProcess, self, address)

    def bind(self, address: Tuple[IPAddress, int]):
        """
        Binds the socket to a certain address and port on the computer
        :param address:
        :return:
        """
        self.computer.bind_socket(self, address)

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
        self.pid = self.computer.start_process(ListeningTCPSocketProcess, self, self.bound_address)

    def blocking_recv(self, received_list):
        """
        Like `self.recv` but is a generator that process can use `yield from` upon.
        takes in a list, appends it with the received data when the generator is over.
        :return:
        """
        received = self.recv()
        try:
            while received is None:
                received = self.recv()
                yield WaitingFor(lambda: True)

            received_list.append(received)
        except SocketIsClosedError:
            return

    def blocking_accept(self):
        """
        Just like `self.accept` - only processes can use `yield from` to block until the socket is connected :)
        :return:
        """
        self.accept()
        yield WaitingFor(lambda: self.is_connected)

    def __str__(self):
        return f"socket of {self.computer.name}"

    def __repr__(self):
        return f"TCP    " \
            f"{':'.join(map(str, self.bound_address)): <23}" \
            f"{':'.join(map(str, self.foreign_address)): <23}" \
            f"{self.state: <16}" \
            f"{self.acquiring_process_pid}"
