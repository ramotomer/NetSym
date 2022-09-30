from __future__ import annotations

from typing import TYPE_CHECKING

from computing.internals.processes.abstracts.process import Process, T_ProcessCode
from computing.internals.processes.abstracts.tcp_server_process import TCPServerProcess
from consts import PORTS, T_Port
from exceptions import TCPSocketConnectionRefused
from packets.usefuls.dns import T_Hostname

if TYPE_CHECKING:
    from computing.internals.sockets.tcp_socket import TCPSocket
    from computing.computer import Computer


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

            with self.computer.filesystem.at_path(self.cwd, filename) as file:
                self.socket.send(file.read())

        yield from self.socket.close_when_done_transmitting()

    def __repr__(self) -> str:
        return "ftpsession"


class ClientFTPProcess(Process):
    """
    The client side process
    """
    def __init__(self,
                 pid: int,
                 computer: Computer,
                 server_hostname: T_Hostname,
                 filename: str = '/bin/cat',
                 server_port: T_Port = PORTS.FTP) -> None:
        super(ClientFTPProcess, self).__init__(pid, computer)
        self.socket = None
        self.server_host = server_hostname
        self.server_port = server_port
        self.filename = filename

    def code(self) -> T_ProcessCode:
        server_ip = yield from self.computer.resolve_domain_name(self, self.server_host)

        self.socket = self.computer.get_tcp_socket(self.pid)
        self.socket.bind()

        try:
            yield from self.socket.blocking_connect((server_ip, self.server_port))
        except TCPSocketConnectionRefused:
            self.computer.print(f"FTP process({self.pid}) ended unexpectedly :(")
            self.die()
            return

        self.socket.send(f"FTP: {self.filename}")

        data = b''
        while self.socket.is_connected and not self.socket.is_closed:
            data += self.socket.receive()
            yield from self.socket.block_until_received_or_closed()
        self.computer.filesystem.output_to_file(data.decode("ascii"), self.filename.split("/")[-1], self.cwd)

        yield from self.socket.close_when_done_transmitting()

    def __repr__(self) -> str:
        return "ftp"
