from __future__ import annotations

from typing import Type, TYPE_CHECKING

from NetSym.computing.internals.processes.abstracts.process import Process, T_ProcessCode
from NetSym.consts import T_Port

if TYPE_CHECKING:
    from NetSym.computing.computer import Computer


class TCPServerProcess(Process):
    """
    A process that waits for TCP connections.
    For each connection it starts a child process with the connection's `Socket` object
    """
    def __init__(self,
                 pid: int,
                 computer: Computer,
                 src_port: T_Port,
                 connection_process_type: Type[Process]) -> None:
        super(TCPServerProcess, self).__init__(pid, computer)
        self.src_port = src_port
        self.connection_process_type = connection_process_type
        self.socket = None
        self.set_killing_signals_handler(self.handle_killing_signals)

    def handle_killing_signals(self, signum: int) -> None:
        """
        Close the socket and die.
        :param signum:
        :return:
        """
        if self.socket is not None:
            self.socket.close()
        self.die()

    def code(self) -> T_ProcessCode:
        self.socket = self.computer.get_tcp_socket(self.pid)
        self.socket.bind((None, self.src_port))
        self.socket.listen()

        while True:
            server_socket = yield from self.socket.blocking_accept(self.pid)
            self.computer.process_scheduler.start_usermode_process(self.connection_process_type, self.socket)
            self.socket = server_socket
