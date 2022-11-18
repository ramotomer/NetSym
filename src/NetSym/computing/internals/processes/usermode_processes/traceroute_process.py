from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from NetSym.computing.internals.processes.abstracts.process import Process, ReturnedPacket, T_ProcessCode, WaitingFor
from NetSym.computing.internals.processes.abstracts.process_internal_errors import ProcessInternalError_NoIPAddressError
from NetSym.consts import OPCODES, PROTOCOLS
from NetSym.packets.usefuls.dns import T_Hostname

if TYPE_CHECKING:
    from NetSym.address.mac_address import MACAddress
    from NetSym.address.ip_address import IPAddress
    from NetSym.packets.packet import Packet
    from NetSym.computing.computer import Computer


class TraceRouteProcess(Process):
    """
    This is a process for sending a ping request to another computer and receiving the reply.
    """
    def __init__(self,
                 pid: int,
                 computer: Computer,
                 destination: T_Hostname) -> None:
        super(TraceRouteProcess, self).__init__(pid, computer)
        self.destination = destination

        self.dst_ip: Optional[IPAddress] = None

    def _send_the_ping(self, dst_mac: MACAddress, ttl: int) -> None:
        """
        Does all things necessary to send the ping.
        (decides the interfaces, maps ip to mac and actually sends the ping)
        """
        if not self.computer.has_ip():
            raise ProcessInternalError_NoIPAddressError("Could not send ICMP packets without an IP address!")

        self.computer.send_ping_to(dst_mac, self.dst_ip, ttl=ttl)

    def ttl_exceeded_reply(self, packet: Packet) -> bool:
        """
        Returns a function that tests if the packet given to it is a ping reply for the `ip_address`
        """
        if "ICMP" in packet:
            if packet["ICMP"].type in [OPCODES.ICMP.TYPES.TIME_EXCEEDED,
                                       OPCODES.ICMP.TYPES.REPLY,
                                       OPCODES.ICMP.TYPES.UNREACHABLE]:
                if self.computer.has_this_ip(packet["IP"].dst_ip):
                    return True
        return False

    def _print_midpoint(self, returned_packet: ReturnedPacket, is_final_stop: bool = False) -> None:
        """
        Receives the `ReturnedPacket` object that was received and prints out to the `OutputConsole` an appropriate message
        """
        packet = returned_packet.packet
        if packet["ICMP"].type == OPCODES.ICMP.TYPES.UNREACHABLE:
            self.computer.print("destination unreachable :(")
            return
        self.computer.print(f"{'MIDPOINT' if not is_final_stop else 'ENDPOINT'}: {packet['IP'].src_ip}")

    def code(self) -> T_ProcessCode:
        """
        This code sends a ping (request or reply).
        If the address is unknown, first it sends an ARP and waits for a reply.
        :return: a generator of `WaitingForPacket` namedtuple-s.
        """
        self.dst_ip = yield from self.computer.resolve_domain_name(self, self.destination)

        for ttl in range(1, PROTOCOLS.IP.MAX_TTL):
            _, dst_mac = yield from self.computer.resolve_ip_address(self.dst_ip, self)
            self._send_the_ping(dst_mac, ttl)
            returned_packet = yield WaitingFor(self.ttl_exceeded_reply)
            if self.dst_ip == returned_packet.packet["IP"].src_ip:
                self._print_midpoint(returned_packet, is_final_stop=True)
                return
            self._print_midpoint(returned_packet)
        self.computer.print(f"Traceroute could not find all midpoints! Destination is too far away or unreachable :(")

    def __repr__(self) -> str:
        """The string representation of the SendPing process"""
        return f"traceroute"
