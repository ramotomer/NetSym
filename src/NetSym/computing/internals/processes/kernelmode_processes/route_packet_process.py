from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from NetSym.computing.internals.processes.abstracts.process import Process, \
    T_ProcessCode
from NetSym.computing.internals.processes.abstracts.process_internal_errors import ProcessInternalError_RoutedPacketTTLExceeded, \
    ProcessInternalError_NoResponseForARP, ProcessInternalError_PacketTooLongButDoesNotAllowFragmentation
from NetSym.consts import OPCODES, COMPUTER
from NetSym.packets.usefuls.ip import needs_fragmentation, allows_fragmentation

if TYPE_CHECKING:
    from NetSym.computing.computer import Computer
    from NetSym.packets.packet import Packet


class RoutePacket(Process):
    """
    This is a process which when run, takes in a packet and routes over the running router, using the
    `decide_routing_interfaces` method.
    The process is of routing a single packet over the router.
    """
    def __init__(self, pid: int, computer: Computer, packet: Packet) -> None:
        """
        Initiates the process with the given packet to route and the routing computer.
        """
        super(RoutePacket, self).__init__(pid, computer)
        self.packet: Packet = packet

    def _is_packet_routable(self) -> bool:
        """
        Checks the given packet and make sure that it is valid and can be routed.
        :return:
        """
        if not self.packet.is_valid() or ("IP" not in self.packet):
            return False

        if self.packet["IP"].dst_ip is None or self.packet["IP"].src_ip is None:
            return False

        if "0.0.0.0" in [str(self.packet["IP"].dst_ip), str(self.packet["IP"].src_ip)]:
            return False

        if self.packet["IP"].src_ip.is_broadcast() or self.packet["Ether"].dst_mac.is_broadcast():
            return False

        return True

    def _validate_ttl(self) -> T_ProcessCode:
        """
        Decrease the TTL of the packet, if it is 0, sends an ICMP Time Exceeded
        :return: a bool telling whether the time (TTL) of the packet was exceeded (reached 0).
        """
        if self.packet["IP"].ttl > 1:
            return

        sender_ip = self.packet["IP"].src_ip
        _, dst_mac = yield from self.computer.resolve_ip_address(sender_ip, self)
        self.computer.send_time_exceeded(dst_mac, sender_ip)
        raise ProcessInternalError_RoutedPacketTTLExceeded

    def _destination_unreachable(self) -> bool:
        """
        Tests if the destination of the packet is unreachable. If it is, send an `ICMP_UNREACHABLE` and return True.
        If not, return False
        :return: `bool`
        """
        dst_ip = self.packet["IP"].dst_ip

        if (dst_ip not in self.computer.routing_table) or \
           self.computer.get_sending_interface_by_routing_table(dst_ip).no_carrier:
            self._send_icmp_unreachable(OPCODES.ICMP.CODES.NETWORK_UNREACHABLE)
            return True
        return False

    def _send_icmp_unreachable(self, code: Optional[int] = None) -> None:
        """Sends to the sender of the routed packet, an ICMP unreachable"""
        sender_ip = self.packet["IP"].src_ip
        dst_ip = self.packet["IP"].dst_ip

        self.computer.send_ping_to(
            self.computer.arp_cache[sender_ip].mac,
            self.packet["IP"].src_ip,
            OPCODES.ICMP.TYPES.UNREACHABLE,
            f"Unreachable: {dst_ip}",
            code=code,
        )

    def code(self) -> T_ProcessCode:
        """
        Receives the packet in the constructor, routes it to the correct subnet (the correct interface of the router).
        It has to send ARPs first sometimes. Does all of that.

        :return: a generator that yields `WaitingForPacket` namedtuple-s.
        """
        if not self._is_packet_routable():
            return

        if self._destination_unreachable():
            return

        yield from self._validate_ttl()

        self.packet["IP"].ttl -= 1
        dst_ip = self.packet["IP"].dst_ip
        try:
            ip_for_the_mac, dst_mac = yield from self.computer.resolve_ip_address(dst_ip, self)
        except ProcessInternalError_NoResponseForARP:
            self._send_icmp_unreachable()
            raise

        interface = self.computer.get_sending_interface_by_routing_table(dst_ip)
        packet = interface.ethernet_wrap(dst_mac, self.packet["IP"])

        if needs_fragmentation(packet, interface.mtu) and not allows_fragmentation(packet):
            self._send_icmp_unreachable(OPCODES.ICMP.CODES.FRAGMENTATION_NEEDED)
            raise ProcessInternalError_PacketTooLongButDoesNotAllowFragmentation  # drop the packet

        self.computer.send_packet_stream(
            COMPUTER.PROCESSES.INIT_PID,
            COMPUTER.PROCESSES.MODES.KERNELMODE,
            [packet],
            COMPUTER.ROUTING.SENDING_INTERVAL,
        )

    def __repr__(self) -> str:
        """The string representation of the process"""
        return "[kroute]"
