from __future__ import annotations

from abc import ABCMeta
from typing import Tuple, TYPE_CHECKING, Optional

from NetSym.address.ip_address import IPAddress
from NetSym.computing.internals.processes.abstracts.process import T_ProcessCode
from NetSym.computing.internals.processes.abstracts.tcp_process import TCPProcess
from NetSym.consts import COMPUTER, T_Port

if TYPE_CHECKING:
    from NetSym.computing.internals.sockets.tcp_socket import TCPSocket
    from NetSym.computing.computer import Computer


class TCPSocketProcess(TCPProcess, metaclass=ABCMeta):
    """
    A process to handle the actions of a socket of kind SOCK_STREAM
    """
    def __init__(self,
                 pid: int,
                 computer: Computer,
                 socket: TCPSocket,
                 dst_ip: Optional[IPAddress] = None,
                 dst_port: Optional[T_Port] = None,
                 src_port: Optional[T_Port] = None,
                 is_client: bool = True) -> None:
        """
        Initiates the process with a src socket and the running computer
        :param socket:
        """
        super(TCPSocketProcess, self).__init__(pid, computer, dst_ip, dst_port, src_port, is_client)
        self.socket = socket
        self.received = []
        self.close_socket_when_done_transmitting = False

    def _unload_socket_sending_queue(self) -> None:
        """
        reads from the socket what it needs to send
        and sends it
        """
        if not self.socket.to_send:
            return

        for data in self.socket.to_send:
            self.send(data)
        self.socket.to_send.clear()

    def _set_socket_connected(self) -> None:
        """
        Sets the connection of the socket as established, defines the foreign address and port etc...
        :return:
        """
        self.socket.is_connected = True
        self.computer.sockets[self.socket].remote_ip_address = self.dst_ip
        self.computer.sockets[self.socket].remote_port = self.dst_port
        self.computer.sockets[self.socket].state = COMPUTER.SOCKETS.STATES.ESTABLISHED

    def on_connection_reset(self) -> None:
        self.socket.close()
        super(TCPSocketProcess, self).on_connection_reset()

    def code(self) -> T_ProcessCode:
        """"""
        yield from self.hello_handshake()  # blocks until receiving a syn to the port
        self._set_socket_connected()

        while not (self.close_socket_when_done_transmitting and self.is_done_transmitting()):
            self._unload_socket_sending_queue()
            yield from self.handle_tcp_and_receive(self.socket.received)

    def _end_session(self) -> None:
        super(TCPSocketProcess, self)._end_session()
        self.socket.close()

    def is_done_transmitting(self) -> bool:
        return super(TCPSocketProcess, self).is_done_transmitting() and not self.socket.to_send

    def __repr__(self) -> str:
        """
        The string representation of the process (also the process name in `ps`)
        """
        _, local_port = self.socket.bound_address
        return f"[ktcpsock] {local_port}"


class ListeningTCPSocketProcess(TCPSocketProcess):
    """
    The process of a socket that is listening
    """
    def __init__(self,
                 pid: int,
                 computer: Computer,
                 socket: TCPSocket,
                 bound_address: Tuple[IPAddress, T_Port]) -> None:
        """
        Initiates the process with a src socket and the running computer
        :param computer:
        :param socket:
        """
        super(ListeningTCPSocketProcess, self).__init__(pid, computer, socket,
                                                        src_port=bound_address[1], is_client=False)

    def code(self) -> T_ProcessCode:
        yield from super(ListeningTCPSocketProcess, self).code()
        yield from self.goodbye_handshake(initiate=True)
        self.socket.close()


class ConnectingTCPSocketProcess(TCPSocketProcess):
    """
    The process of a socket that is initiating the connection to the remote socket.
    """
    def __init__(self,
                 pid: int,
                 computer: Computer,
                 socket: TCPSocket,
                 dst_address: Tuple[IPAddress, T_Port]) -> None:
        """
        Initiates the process with a src socket and the running computer
        :param computer:
        :param socket:
        """
        dst_ip, dst_port = dst_address
        self.socket = socket
        super(ConnectingTCPSocketProcess, self).__init__(pid, computer, socket,
                                                         dst_ip=dst_ip, dst_port=dst_port, is_client=True)

    def code(self) -> T_ProcessCode:
        self.socket.bind((self.computer.get_ip(), self.src_port))
        yield from super(ConnectingTCPSocketProcess, self).code()
