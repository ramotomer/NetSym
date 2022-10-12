from __future__ import annotations

from typing import TYPE_CHECKING

from computing.internals.processes.abstracts.process import Process, T_ProcessCode
from consts import PORTS, T_Port
from exceptions import TCPSocketConnectionRefused
from packets.usefuls.dns import T_Hostname

if TYPE_CHECKING:
    from computing.computer import Computer


# TODO: why do servers do not answer SYNs sometimes?????


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
