from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Optional

from NetSym.computing.internals.processes.abstracts.process import Process, ReturnedPacket, T_ProcessCode
from NetSym.consts import INTERFACES
from NetSym.exceptions import SocketIsClosedError

if TYPE_CHECKING:
    from NetSym.packets.packet import Packet
    from NetSym.computing.internals.network_interfaces.interface import Interface
    from NetSym.computing.computer import Computer


class SniffingProcess(Process):
    """
    This is a process object. The process it represents is one that sniffs packets and prints the results to the screen.

    """
    def __init__(self,
                 pid: int,
                 computer: Computer,
                 filter: Callable[[Packet], bool],
                 interface: Optional[Interface] = INTERFACES.ANY_INTERFACE,
                 promisc: bool = False) -> None:
        super(SniffingProcess, self).__init__(pid, computer)

        self.socket = self.computer.get_raw_socket(self.pid)
        self.socket.bind(filter, interface, promisc)

        self.packet_count = 0

        self.set_killing_signals_handler(self.close_socket)

    @property
    def interface_name(self) -> str:
        return getattr(self.socket.interface, 'name', '') or 'All interfaces'

    def close_socket(self, signum: int) -> None:
        self.computer.print(f"Stopped sniffing on {self.interface_name}")
        self.socket.close()

    @staticmethod
    def _get_sniffed_packet_info_line(returned_packet: ReturnedPacket) -> str:
        """
        Return the line that is printed when the packet is sniffed.
        """
        packet, packet_metadata = returned_packet.packet_and_metadata
        return f"{packet_metadata.direction} {packet.summary()}"

    def code(self) -> T_ProcessCode:
        self.computer.print(f"started sniffing on {self.interface_name}")
        while True:
            yield from self.socket.block_until_received()

            try:
                for returned_packet in self.socket.receive():
                    self.computer.print(f"({self.packet_count}) {self._get_sniffed_packet_info_line(returned_packet)}")
                    self.packet_count += 1
            except SocketIsClosedError:
                self.die()
                return

    def __repr__(self) -> str:
        return f"tcpdump " \
            f"{f'-A' if self.socket.interface is None else f'-i {self.socket.interface.name}'} " \
            f"{'-p' if self.socket.is_promisc else ''}"
