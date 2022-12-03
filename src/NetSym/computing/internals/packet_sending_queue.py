from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional, Deque

from NetSym.consts import T_Time
from NetSym.gui.main_loop import MainLoop

if TYPE_CHECKING:
    from NetSym.packets.packet import Packet
    from NetSym.computing.internals.sockets.raw_socket import RawSocket
    from NetSym.computing.internals.network_interfaces.interface import Interface
    from NetSym.computing.computer import Computer


@dataclass
class PacketSendingQueue:
    """
    a set of packets that should be sent one after the other, with some gaps of time in between - for visual prettiness
    """
    computer:                 Computer
    pid:                      int
    process_mode:             str
    packets:                  Deque[Packet]
    interval:                 T_Time
    interface:                Optional[Interface] = None
    sending_socket:           Optional[RawSocket] = None
    last_packet_sending_time: T_Time              = field(default_factory=MainLoop.get_time)

    def send_packets_with_time_gaps(self) -> None:
        """
        Send the next packet - unless the last packet was sent recently
        """
        if MainLoop.get_time_since(self.last_packet_sending_time) <= self.interval:
            return

        if not self.packets:
            return

        packet = self.packets.popleft()
        self.computer.send(packet, self.interface, self.sending_socket)
        self.last_packet_sending_time = MainLoop.get_time()
