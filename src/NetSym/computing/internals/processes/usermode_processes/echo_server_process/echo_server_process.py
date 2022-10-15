from __future__ import annotations

from typing import TYPE_CHECKING

from NetSym.address.ip_address import IPAddress
from NetSym.computing.internals.processes.abstracts.process import Process, T_ProcessCode
from NetSym.consts import PORTS

if TYPE_CHECKING:
    from NetSym.computing.computer import Computer


class EchoServerProcess(Process):
    def __init__(self,
                 pid: int,
                 computer: Computer) -> None:
        super(EchoServerProcess, self).__init__(pid, computer)
        self.socket = None

    def code(self) -> T_ProcessCode:
        self.socket = self.computer.get_udp_socket(self.pid)
        self.socket.bind((IPAddress.no_address(), PORTS.ECHO_SERVER))

        while True:
            yield from self.socket.block_until_received()
            udp_returned_packets = self.socket.receivefrom()
            for udp_returned_packet in udp_returned_packets:
                self.socket.sendto(udp_returned_packet.data, (udp_returned_packet.src_ip, udp_returned_packet.src_port))
                self.computer.print(f"server echoed: '{udp_returned_packet.data.decode('ascii')}' "
                                    f"to: {udp_returned_packet.src_ip}")

    def __repr__(self) -> str:
        return "echosd"
