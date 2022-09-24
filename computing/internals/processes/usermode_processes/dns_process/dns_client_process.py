from __future__ import annotations

from typing import TYPE_CHECKING, Tuple

import scapy

from address.ip_address import IPAddress
from computing.internals.processes.abstracts.process import Process, T_ProcessCode
from consts import COMPUTER, OPCODES
from packets.all import DNS
from packets.usefuls.dns import list_to_dns_query, DNSQueryRecord

if TYPE_CHECKING:
    from computing.computer import Computer


class DNSClientProcess(Process):
    """
    A Domain Name Server process - will resolve a display name to an IPAddress if a client requests
    """
    def __init__(self, pid: int, computer: Computer, server_address: IPAddress, name_to_resolve: str) -> None:
        """
        Creates the new process
        :param pid: The process ID of this process
        :param computer: The computer that runs this process
        :param server_address: the IPAddress of the server
        """
        super(DNSClientProcess, self).__init__(pid, computer)
        self._server_address = server_address
        self._name_to_resolve = name_to_resolve

        self.socket = None

    def _build_dns_query(self, name_to_resolve: str, is_recursion_desired: bool = True) -> scapy.packet.Packet:
        """
        Builds the DNS layer of the packet to send to the server
        """
        query = DNS(
            transaction_id=self.computer.dns_table.transaction_counter,
            is_response=False,
            is_recursion_desired=is_recursion_desired,

            queries=list_to_dns_query([
                DNSQueryRecord(
                    query_name=name_to_resolve,
                    query_type=OPCODES.DNS.QUERY_TYPES.HOST_ADDRESS,
                    query_class=OPCODES.DNS.QUERY_CLASSES.INTERNET,
                )
            ]),
        )
        self.computer.dns_table.transaction_counter += 1
        return query

    def _extract_dns_answer(self, dns_answer: scapy.packet.Packet) -> Tuple[str, IPAddress, int]:
        """
        Take in the answer packet that was sent from the server
        Return the interesting information to insert in the DNS table of the computer
        """
        return

    def code(self) -> T_ProcessCode:
        """
        The main code of the process
        """
        self.socket = self.computer.get_socket(kind=COMPUTER.SOCKETS.TYPES.SOCK_DGRAM, requesting_process_pid=self.pid)
        self.socket.bind()
        self.socket.connect(self._server_address)

        self.socket.send(self._build_dns_query(self._name_to_resolve))
        self.computer.print(f"Resolving name '{self._name_to_resolve}'")
        yield from self.socket.block_until_received()

        dns_answer = self.socket.receive()[0]
        name, ip_address, ttl = self._extract_dns_answer(dns_answer)
        self.computer.dns_table.add_item(name, ip_address, ttl)
