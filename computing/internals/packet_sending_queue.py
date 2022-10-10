from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

from consts import T_Time
from gui.main_loop import MainLoop

if TYPE_CHECKING:
    from computing.computer import Computer


class PacketSendingQueue:
    """
    a set of packets that should be sent one after the other, with some gaps of time in between - for visual prettiness
    """
    def __init__(self, computer: Computer, requesting_usermode_pid: int, packet_deque: deque, interval: T_Time) -> None:
        """
        :param computer: The computer the packets will be sent from
        :param packet_deque: a `collections.deque` object that contains in-order the packets that should be sent
        :param interval: How long to wait between packets (seconds)
        """
        self.computer = computer
        self.pid = requesting_usermode_pid
        self.packets = packet_deque
        self.interval = interval
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
        self.computer.send(packet)
        self.last_packet_sending_time = MainLoop.instance.time()
