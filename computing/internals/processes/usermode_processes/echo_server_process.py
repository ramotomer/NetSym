from __future__ import annotations

from typing import Tuple, TYPE_CHECKING, Optional

from address.ip_address import IPAddress
from computing.internals.processes.abstracts.process import Process, T_ProcessCode
from consts import COMPUTER, PORTS, PROTOCOLS, T_Port

if TYPE_CHECKING:
    from computing.computer import Computer


class EchoServerProcess(Process):
    def __init__(self,
                 pid: int,
                 computer: Computer) -> None:
        super(EchoServerProcess, self).__init__(pid, computer)
        self.socket = None

    def code(self) -> T_ProcessCode:
        self.socket = self.computer.get_socket(kind=COMPUTER.SOCKETS.TYPES.SOCK_DGRAM, requesting_process_pid=self.pid)
        self.socket.bind((IPAddress.no_address(), PORTS.ECHO_SERVER))

        while True:
            yield from self.socket.block_until_received()
            udp_returned_packets = self.socket.receivefrom()
            for udp_returned_packet in udp_returned_packets:
                self.socket.sendto(udp_returned_packet.data, (udp_returned_packet.src_ip, udp_returned_packet.src_port))
                self.computer.print(f"server echoed: '{udp_returned_packet.data}' "
                                    f"to: {udp_returned_packet.src_ip}")

    def die(self, death_message: Optional[str] = None) -> None:
        if self.socket is not None:
            self.socket.close()
        super(EchoServerProcess, self).die(death_message)

    def __repr__(self) -> str:
        return "echosd"


class EchoClientProcess(Process):
    def __init__(self,
                 pid: int,
                 computer: Computer,
                 server_address: Tuple[IPAddress, T_Port],
                 data: str,
                 count: int = PROTOCOLS.ECHO_SERVER.DEFAULT_REQUEST_COUNT) -> None:
        super(EchoClientProcess, self).__init__(pid, computer)
        self.server_address = server_address
        self.data = data
        self.count = count

        self.socket = None

    def code(self) -> T_ProcessCode:
        if not self.computer.ips:
            self.computer.print(f"Cannot run `echocd` without an IP address :(")
            self.die()
            return

        self.socket = self.computer.get_socket(kind=COMPUTER.SOCKETS.TYPES.SOCK_DGRAM, requesting_process_pid=self.pid)
        self.socket.bind()
        self.socket.connect(self.server_address)

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

    def die(self, death_message: Optional[str] = None) -> None:
        if self.socket is not None:
            self.socket.close()
        super(EchoClientProcess, self).die(death_message)

    def __repr__(self) -> str:
        server_ip, server_port = self.server_address
        return f"echocd {server_ip} " \
            f"-p {server_port} " \
            f"{f'-c {self.count}' if self.count != PROTOCOLS.ECHO_SERVER.DEFAULT_REQUEST_COUNT else ''}"
