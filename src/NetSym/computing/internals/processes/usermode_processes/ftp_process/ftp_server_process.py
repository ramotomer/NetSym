from __future__ import annotations

from typing import TYPE_CHECKING

from NetSym.computing.internals.processes.abstracts.process import Process, T_ProcessCode
from NetSym.computing.internals.processes.abstracts.tcp_server_process import TCPServerProcess
from NetSym.consts import PORTS

if TYPE_CHECKING:
    from NetSym.computing.internals.sockets.tcp_socket import TCPSocket
    from NetSym.computing.computer import Computer


class ServerFTPProcess(TCPServerProcess):
    """
    The server side process
    Waits for new connections and starts the `ServerFTPSessionProcess` for each one of them
    """
    def __init__(self, pid: int, computer: Computer) -> None:
        super(ServerFTPProcess, self).__init__(pid, computer, PORTS.FTP, ServerFTPSessionProcess)

    def __repr__(self) -> str:
        return "ftpd"


class ServerFTPSessionProcess(Process):
    """
    This process represents a single session of the server with a client.
    This allows the server to continue listening for new connections
    """
    def __init__(self, pid: int, computer: Computer, socket: TCPSocket) -> None:
        super(ServerFTPSessionProcess, self).__init__(pid, computer)
        self.socket = socket

    def code(self) -> T_ProcessCode:
        """
        The actual code of the process
        """
        yield from self.socket.block_until_received()
        received = self.socket.receive().decode("ascii")

        if received.startswith("FTP: "):
            # TODO: actually implement the FTP protocol with a layer - as it should behave
            filename = received.split()[received.split().index("FTP:") + 1]

            with self.computer.filesystem.file_at_path(self.cwd, filename) as file:
                self.socket.send(file.read())

        yield from self.socket.close_when_done_transmitting()

    def __repr__(self) -> str:
        return "ftpsession"
