from abc import ABCMeta
from typing import Tuple

from address.ip_address import IPAddress
from computing.internals.processes.abstracts.tcp_process import TCPProcess
from consts import COMPUTER


class TCPSocketProcess(TCPProcess, metaclass=ABCMeta):
    """
    A process to handle the actions of a socket of kind SOCK_STREAM
    """
    def __init__(self, pid, computer, socket, dst_ip=None, dst_port=None, src_port=None, is_client=True):
        """
        Initiates the process with a src socket and the running computer
        :param socket:
        """
        super(TCPSocketProcess, self).__init__(pid, computer, dst_ip, dst_port, src_port, is_client)
        self.socket = socket
        self.received = []
        self.close_socket_when_done_transmitting = False

    def __unload_socket_sending_queue(self):
        """
        reads from the socket what it needs to send
        and sends it
        """
        if not self.socket.to_send:
            return

        for data in self.socket.to_send:
            self.send(data)
        self.socket.to_send.clear()

    def __set_socket_connected(self):
        """
        Sets the connection of the socket as established, defines the foreign address and port etc...
        :return:
        """
        self.socket.is_connected = True
        self.computer.sockets[self.socket].remote_ip_address = self.dst_ip
        self.computer.sockets[self.socket].remote_port = self.dst_port
        self.computer.sockets[self.socket].state = COMPUTER.SOCKETS.STATES.ESTABLISHED

    def on_connection_reset(self):
        self.socket.close()

    def code(self):
        """"""
        yield from self.hello_handshake()  # halts until receiving a syn to the port
        if self.kill_me:
            return
        self.__set_socket_connected()

        while not (self.close_socket_when_done_transmitting and self.is_done_transmitting()):
            self.__unload_socket_sending_queue()
            yield from self.handle_tcp_and_receive(self.socket.received)

    def _end_session(self):
        super(TCPSocketProcess, self)._end_session()
        self.socket.close()

    def __repr__(self):
        """
        The string representation of the process (also the process name in `ps`)
        :return:
        """
        return "[ktcpsock]"


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
        super(ListeningTCPSocketProcess, self).__init__(pid, computer, socket,
                                                        src_port=bound_address[1], is_client=False)

    def code(self):
        yield from super(ListeningTCPSocketProcess, self).code()
        yield from self.goodbye_handshake(initiate=True)
        self.socket.close()


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
        self.socket = socket
        super(ConnectingTCPSocketProcess, self).__init__(pid, computer, socket,
                                                         dst_ip=dst_ip, dst_port=dst_port, is_client=True)

    def code(self):
        self.socket.bind((self.computer.get_ip(), self.src_port))
        yield from super(ConnectingTCPSocketProcess, self).code()
