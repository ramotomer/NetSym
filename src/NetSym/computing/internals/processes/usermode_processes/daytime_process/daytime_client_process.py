from __future__ import annotations

from typing import TYPE_CHECKING

from NetSym.computing.internals.processes.abstracts.process import Process, T_ProcessCode
from NetSym.consts import T_Port, PORTS
from NetSym.exceptions import TCPSocketConnectionRefused
from NetSym.packets.usefuls.dns import T_Hostname

if TYPE_CHECKING:
    from NetSym.computing.computer import Computer


class DAYTIMEClientProcess(Process):
    """
    The client process of the DAYTIME protocol
    """
    def __init__(self, pid: int, computer: Computer, server_hostname: T_Hostname, server_port: T_Port = PORTS.DAYTIME) -> None:
        super(DAYTIMEClientProcess, self).__init__(pid, computer)
        self.server_hostname = server_hostname
        self.server_port = server_port
        self.socket = None

    def code(self) -> T_ProcessCode:
        """
        The actual code of the DAYTIME process
        :return: yields WaitingFor namedtuple-s like every process.
        """
        server_ip = yield from self.computer.resolve_domain_name(self, self.server_hostname)

        self.computer.print("Asking Daytime...")
        self.socket = self.computer.get_tcp_socket(self.pid)
        self.socket.bind()

        try:
            yield from self.socket.blocking_connect((server_ip, self.server_port))
        except TCPSocketConnectionRefused:
            self.computer.print(f"Daytime process ({self.pid}) ended unexpectedly :(")
            self.die()
            return

        yield from self.socket.block_until_received()
        self.computer.print(f"Got datetime! {self.socket.receive().decode('ascii')}")
        yield from self.socket.block_until_closed()

    def __repr__(self) -> str:
        return "daytimecd"
