from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Optional

from computing.internals.processes.abstracts.process import Process, ReturnedPacket, T_ProcessCode, WaitingFor
from consts import OPCODES, PROTOCOLS
from exceptions import NoIPAddressError
from packets.usefuls.dns import T_Hostname
from packets.usefuls.icmp import get_icmp_data
from usefuls.funcs import my_range

if TYPE_CHECKING:
    from address.mac_address import MACAddress
    from address.ip_address import IPAddress
    from packets.packet import Packet
    from computing.computer import Computer


class SendPing(Process):
    """
    This is a process for sending a ping request to another computer and receiving the reply.
    """
    def __init__(self,
                 pid: int,
                 computer: Computer,
                 destination: T_Hostname,
                 opcode: int = OPCODES.ICMP.TYPES.REQUEST,
                 count: int = 1,
                 length: int = PROTOCOLS.ICMP.DEFAULT_MESSAGE_LENGTH) -> None:
        super(SendPing, self).__init__(pid, computer)
        self.destination = destination
        self.ping_opcode = opcode
        self.is_sending_to_gateway = False
        self.count = count
        self.length = length

        self.dst_ip: Optional[IPAddress] = None

    def _send_the_ping(self, dst_mac: MACAddress) -> None:
        """
        Does all things necessary to send the ping.
        (decides the interfaces, maps ip to mac and actually sends the ping)
        """
        if not self.computer.has_ip():
            self.computer.print("Could not send ICMP packets without an IP address!")
            raise NoIPAddressError("The sending computer has no IP address!!!")

        self.computer.send_ping_to(dst_mac, self.dst_ip, self.ping_opcode, get_icmp_data(self.length))

    def ping_reply_from(self, ip_address: IPAddress) -> Callable[[Packet], bool]:
        """
        Returns a function that tests if the packet given to it is a ping reply for the `ip_address`
        """
        def tester(packet: Packet) -> bool:
            if "ICMP" in packet:
                if packet["ICMP"].type == OPCODES.ICMP.TYPES.REPLY:
                    if packet["IP"].src_ip == ip_address and self.computer.has_this_ip(packet["IP"].dst_ip):
                        return True
                    if self.computer.has_this_ip(self.dst_ip) and packet["IP"].src_ip == self.computer.loopback.ip:
                        return True
                if packet["ICMP"].type == OPCODES.ICMP.TYPES.UNREACHABLE:
                    return True
            return False
        return tester

    def _print_output(self, returned_packet: ReturnedPacket) -> None:
        """
        Receives the `ReturnedPacket` object that was received and prints out to the `OutputConsole` an appropriate message
        """
        packet = returned_packet.packet
        if packet["ICMP"].type == OPCODES.ICMP.TYPES.UNREACHABLE:
            self.computer.print("destination unreachable :(")
        else:
            self.computer.print("ping reply!")

    def code(self) -> T_ProcessCode:
        """
        This code sends a ping (request or reply).
        If the address is unknown, first it sends an ARP and waits for a reply.
        :return: a generator of `WaitingForPacket` namedtuple-s.
        """
        self.dst_ip = yield from self.computer.resolve_domain_name(self, self.destination)

        if self.ping_opcode == OPCODES.ICMP.TYPES.REQUEST:
            self.computer.print(f"pinging {self.dst_ip} with some bytes")

        for _ in my_range(self.count):
            _, dst_mac = yield from self.computer.resolve_ip_address(self.dst_ip, self)

            try:
                self._send_the_ping(dst_mac)
            except NoIPAddressError:
                return

            if self.ping_opcode == OPCODES.ICMP.TYPES.REQUEST:
                returned_packet = yield WaitingFor(self.ping_reply_from(self.dst_ip))
                self._print_output(returned_packet)

    def __repr__(self) -> str:
        """The string representation of the SendPing process"""
        return f"ping {self.destination} {f'-n {self.count}' if self.count != PROTOCOLS.ICMP.INFINITY else '-t'}"
