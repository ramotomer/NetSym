from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING, Optional

from consts import T_Time
from gui.main_loop import MainLoop

if TYPE_CHECKING:
    from computing.internals.sockets.raw_socket import RawSocket
    from computing.internals.interface import Interface
    from computing.computer import Computer


class PacketSendingQueue:
    """
    a set of packets that should be sent one after the other, with some gaps of time in between - for visual prettiness
    """
    def __init__(self,
                 computer: Computer,
                 requesting_usermode_pid: int,
                 process_mode: str,
                 packet_deque: deque,
                 interval: T_Time,
                 interface: Optional[Interface] = None,
                 sending_socket: Optional[RawSocket] = None) -> None:
        """
        :param computer: The computer the packets will be sent from
        :param packet_deque: a `collections.deque` object that contains in-order the packets that should be sent
        :param interval: How long to wait between packets (seconds)
        """
        self.computer = computer
        self.process_mode = process_mode
        self.pid = requesting_usermode_pid
        self.packets = packet_deque
        self.interval = interval
        self.interface = interface
        self.sending_socket = sending_socket

        self.last_packet_sending_time = MainLoop.instance.time()

    def send_packets_with_time_gaps(self) -> None:
        """
        Send the next packet - unless the last packet was sent recently
        """
        if MainLoop.instance.time_since(self.last_packet_sending_time) <= self.interval:
            return

        if not self.packets:
            return

        packet = self.packets.popleft()
        self.computer.send(packet, self.interface, self.sending_socket)
        self.last_packet_sending_time = MainLoop.instance.time()
