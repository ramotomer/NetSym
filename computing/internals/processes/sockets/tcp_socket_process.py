from abc import ABCMeta
from typing import Tuple

from address.ip_address import IPAddress
from computing.internals.processes.abstracts.tcp_process import TCPProcess
from consts import COMPUTER


class TCPSocketProcess(TCPProcess, metaclass=ABCMeta):
    """
    A process to handle the actions of a socket of kind SOCK_STREAM
    """
    def __init__(self, socket):
        """
        Initiates the process with a src socket and the running computer
        :param socket:
        """
        self.socket = socket
        self.received = []

        self.signal_handlers[COMPUTER.PROCESSES.SIGNALS.SIGSOCKRECV] = self.handle_signal_for_receiving
        self.signal_handlers[COMPUTER.PROCESSES.SIGNALS.SIGSOCKSEND] = self.handle_signal_for_sending

        self.closing_the_socket = False
        self.set_killing_signals_handler(self.kill_signal_handler)

    def handle_signal_for_sending(self, signum):
        """
        When this signal is received, the process reads from the socket what it needs to send
        and sends it
        :param signum:
        :return:
        """
        for data in self.socket.to_send:
            self.send(data)

        self.socket.to_send.clear()

    def handle_signal_for_receiving(self, signum):
        """
        When this signal is received, the process writes to the socket what it received from
        the destination
        :param signum:
        :return:
        """
        self.socket.received = ''.join(packet["TCP"].data for packet in self.received)
        self.received.clear()

    def handle_process_kill(self, signum):
        """
        Handling of process being killed (closing the connection)
        :return:
        """
        self.closing_the_socket = True

    def code(self):
        """"""
        yield from self.hello_handshake()  # halts until receiving a syn to the port
        self.socket.is_connected = True

        while not (self.closing_the_socket and self.is_done_transmitting()):
            yield from self.handle_tcp_and_receive(self.received)

        yield from self.goodbye_handshake(initiate=True)
        self.socket.close()

    def __repr__(self):
        """
        The string representation of the process (also the process name in `ps`)
        :return:
        """
        return "[ksockworker]"


class ListeningTCPSocketProcess(TCPSocketProcess):
    """
    The process of a socket that is listening
    """
    def __init__(self, pid, computer, socket, bound_address):
        """
        Initiates the process with a src socket and the running computer
        :param computer:
        :param socket:
        """
        super(ListeningTCPSocketProcess, self).__init__(socket)
        super(TCPSocketProcess, self).__init__(pid, computer, src_port=bound_address[1], is_client=False)


class ConnectingTCPSocketProcess(TCPSocketProcess):
    """
    The process of a socket that is initiating the connection to the remote socket.
    """
    def __init__(self, pid, computer, socket, dst_address: Tuple[IPAddress, int]):
        """
        Initiates the process with a src socket and the running computer
        :param computer:
        :param socket:
        """
        dst_ip, dst_port = dst_address
        super(ConnectingTCPSocketProcess, self).__init__(socket)
        super(TCPSocketProcess, self).__init__(pid, computer, dst_ip=dst_ip, dst_port=dst_port, is_client=True)
