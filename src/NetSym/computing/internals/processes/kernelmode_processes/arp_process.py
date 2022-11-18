from __future__ import annotations

from typing import Callable, TYPE_CHECKING, Optional

import scapy

from NetSym.address.mac_address import MACAddress
from NetSym.computing.internals.processes.abstracts.process import Process, Timeout, \
    T_ProcessCode, WaitingFor
from NetSym.computing.internals.processes.abstracts.process_internal_errors import ProcessInternalError_NoResponseForARP
from NetSym.consts import OPCODES, PROTOCOLS
from NetSym.packets.usefuls.dns import T_Hostname
from NetSym.usefuls.funcs import my_range

if TYPE_CHECKING:
    from NetSym.address.ip_address import IPAddress
    from NetSym.packets.packet import Packet
    from NetSym.computing.computer import Computer


def arp_reply_from(ip_address: IPAddress) -> Callable[[Packet], bool]:
    """Returns a function that tests if the packet given to it is an ARP reply for the `ip_address`"""
    def tester(packet: Packet) -> bool:
        return ("ARP" in packet) and (packet["ARP"].opcode == OPCODES.ARP.REPLY) and (packet["ARP"].src_ip == ip_address)
    return tester


class ARPProcess(Process):
    """
    This is the process of the computer asking for an IP address using ARPs.
    """
    def __init__(self,
                 pid: int,
                 computer: Computer,
                 destination: T_Hostname,
                 send_even_if_known: bool = False,
                 resend_count: int = PROTOCOLS.ARP.RESEND_COUNT,
                 resend_even_on_success: bool = False,
                 override_process_name: Optional[str] = None) -> None:
        """
        Initiates the process with the address to request.
        """
        super(ARPProcess, self).__init__(pid, computer)
        self.destination = destination
        self.send_even_if_known = send_even_if_known
        self.resend_count = resend_count
        self.resend_even_on_success = resend_even_on_success
        self.override_process_name = override_process_name

    def code(self) -> T_ProcessCode:
        """The code of the process"""
        if self.destination is None:
            return

        dst_ip = yield from self.computer.resolve_domain_name(self, self.destination)
        if dst_ip in self.computer.arp_cache and not self.send_even_if_known:
            return

        for _ in my_range(self.resend_count):
            self.computer.send_arp_to(dst_ip)
            returned_packets = yield WaitingFor(arp_reply_from(dst_ip), timeout=Timeout(PROTOCOLS.ARP.RESEND_TIME))
            if not returned_packets.has_packets():
                self.computer.print("Destination is unreachable :(")
                continue
            if self.resend_even_on_success:
                continue
            return

        if not self.resend_even_on_success:
            self.die("ERROR! No response for ARP :(", raises=ProcessInternalError_NoResponseForARP)

    def __repr__(self) -> str:
        return self.override_process_name or f"[karp] {self.destination}"


class SendPacketWithARPProcess(Process):
    """
    This is a process that starts a complete sending of a packet.
    It checks the routing table and asks for the address and does whatever is necessary.
    """
    def __init__(self,
                 pid: int,
                 computer: Computer,
                 ip_layer: scapy.packet.Packet) -> None:
        """
        Initiates the process with the running computer
        the ip_layer will be wrapped in ethernet
        """
        super(SendPacketWithARPProcess, self).__init__(pid, computer)
        self.ip_layer = ip_layer

    def code(self) -> T_ProcessCode:
        """
        The code of the process
        :return:
        """
        dst_ip = self.ip_layer.dst_ip
        if not dst_ip.is_broadcast():
            _, dst_mac = yield from self.computer.resolve_ip_address(dst_ip, self)
        else:
            dst_mac = MACAddress.broadcast()

        self.computer.send_with_ethernet(
            dst_mac,
            dst_ip,
            self.ip_layer,
        )

    def __repr__(self) -> str:
        return f"[kwarp]"
