from __future__ import annotations

from typing import Tuple, TYPE_CHECKING, Optional

from NetSym.address.ip_address import IPAddress
from NetSym.computing.internals.processes.abstracts.process import Process, T_ProcessCode
from NetSym.consts import PROTOCOLS, T_Port
from NetSym.packets.usefuls.dns import T_Hostname

if TYPE_CHECKING:
    from NetSym.computing.internals.sockets.udp_socket import UDPSocket
    from NetSym.computing.computer import Computer


class EchoClientProcess(Process):
    def __init__(self,
                 pid: int,
                 computer: Computer,
                 server: Tuple[T_Hostname, T_Port],
                 data: str,
                 count: int = PROTOCOLS.ECHO_SERVER.DEFAULT_REQUEST_COUNT) -> None:
        super(EchoClientProcess, self).__init__(pid, computer)
        self.server_host, self.server_port = server
        self.data = data
        self.count = count

        self.socket: Optional[UDPSocket] = None
        self.server_ip: Optional[IPAddress] = None

    def code(self) -> T_ProcessCode:
        if not self.computer.ips:
            self.computer.print(f"Cannot run `echocd` without an IP address :(")
            self.die()
            return

        self.server_ip = yield from self.computer.resolve_domain_name(self, self.server_host)
        self.socket = self.computer.get_udp_socket(self.pid)
        self.socket.bind()
        self.socket.connect((self.server_ip, self.server_port))

        for _ in range(self.count):
            self.socket.send(self.data.encode("ascii"))
            self.computer.print(f"echoing: {self.data}")
            yield from self.socket.block_until_received()
            data = self.socket.receive()[0].decode("ascii")
            if data == self.data:
                self.computer.print(f"echo server: {data}\n:)")
                continue

            self.computer.print(f"ERROR: echo server echoed: '{data}'\n:(")
            self.die()
            return

    def __repr__(self) -> str:
        return f"echocd {self.server_host} " \
            f"-p {self.server_port} " \
            f"{f'-c {self.count}' if self.count != PROTOCOLS.ECHO_SERVER.DEFAULT_REQUEST_COUNT else ''}"
