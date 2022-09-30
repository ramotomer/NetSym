from __future__ import annotations

from typing import TYPE_CHECKING

from address.ip_address import IPAddress
from address.mac_address import MACAddress
from computing.internals.processes.abstracts.process import Process, WaitingFor, Timeout, T_ProcessCode
from consts import T_Time
from packets.all import UDP

if TYPE_CHECKING:
    from computing.computer import Computer


class DDOSProcess(Process):
    """
    A process that repeatedly sends udp packets in broadcast
    """
    def __init__(self,
                 pid: int,
                 computer: Computer,
                 count: int,
                 sending_interval: T_Time) -> None:
        """
        Initiates the process with a counter of packets to send and a sending interval
        between each packets
        """
        super(DDOSProcess, self).__init__(pid, computer)
        self.count = count
        self.sending_interval = sending_interval

    def code(self) -> T_ProcessCode:
        """
        The actual code of the DDOS process, send a packet, wait `self.sending_interval` seconds,
        then send again.
        :return: yield `WaitingFor` objects
        """
        if not self.computer.has_ip():
            return

        for _ in range(self.count):
            self.computer.send_to(
                MACAddress.broadcast(),
                IPAddress.broadcast(),
                UDP(
                    src_port=42069,
                    dst_port=42069,
                ) / "DDOS",
            )
            yield WaitingFor(Timeout(self.sending_interval).is_done)

    def __repr__(self) -> str:
        """A string representation of the process"""
        return f"python my_attack.py -c {self.count} -i {self.sending_interval}"
