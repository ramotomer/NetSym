from __future__ import annotations

from typing import TYPE_CHECKING, Tuple, Optional

import scapy

from address.ip_address import IPAddress
from computing.internals.processes.abstracts.process import Process, T_ProcessCode
from consts import OPCODES, PROTOCOLS, T_Time, T_Port, PORTS
from packets.all import DNS
from packets.usefuls.dns import T_Hostname
from packets.usefuls.dns import list_to_dns_query, DNSQueryRecord

if TYPE_CHECKING:
    from computing.internals.sockets.udp_socket import UDPSocket
    from computing.computer import Computer


class DNSClientProcess(Process):
    """
    A Domain Name Server process - will resolve a display name to an IPAddress if a client requests
    """
    def __init__(self,
                 pid: int,
                 computer: Computer,
                 server_ip: Optional[IPAddress],
                 name_to_resolve: str,
                 default_query_timeout: T_Time = PROTOCOLS.DNS.CLIENT_QUERY_TIMEOUT,
                 default_retry_count: int = PROTOCOLS.DNS.DEFAULT_RETRY_COUNT,
                 server_port: T_Port = PORTS.DNS) -> None:
        """
        Creates the new process
        :param pid: The process ID of this process
        :param computer: The computer that runs this process
        :param server_ip: the IPAddress of the server
        """
        super(DNSClientProcess, self).__init__(pid, computer)
        self._server_address: Tuple[IPAddress, T_Port] = (server_ip, server_port)
        self._name_to_resolve = name_to_resolve

        self.socket: Optional[UDPSocket] = None
        self._query_timeout = default_query_timeout
        self._retry_count = default_retry_count

    def _dns_process_print(self, message):
        """
        Print to computer console with a DNS prefix
        """
        self.computer.print(f"DNS says: {message}")

    def _are_parameters_valid(self) -> bool:
        """
        Kill the process if any of the parameters are invalid!
        """
        if self._retry_count < 1:
            self._dns_process_print(f"Retry count must be at least 1, not {self._retry_count}")
            return False

        if not self._name_to_resolve:
            self._dns_process_print(f"Name invalid! '{self._name_to_resolve}'")
            return False

        if self._server_address[0] is None:
            self._dns_process_print(f"No DNS server configured!")
            return False

        return True

    def _build_dns_query(self, name_to_resolve: str, is_recursion_desired: bool = True) -> scapy.packet.Packet:
        """
        Builds the DNS layer of the packet to send to the server
        """
        if not is_recursion_desired:
            raise NotImplementedError(f"Only recursive DNS queries are currently supported")

        query = DNS(
            transaction_id=self.computer.dns_cache.transaction_counter,
            is_response=False,
            is_recursion_desired=is_recursion_desired,

            queries=list_to_dns_query([
                DNSQueryRecord(
                    query_name=name_to_resolve,
                    query_type=OPCODES.DNS.QUERY_TYPES.HOST_ADDRESS,
                    query_class=OPCODES.DNS.QUERY_CLASSES.INTERNET,
                ),
            ]),
        )
        self.computer.dns_cache.transaction_counter += 1
        return query

    def _extract_dns_answer(self, dns_answer: scapy.packet.Packet) -> Tuple[T_Hostname, IPAddress, int]:

        """
        Take in the answer packet that was sent from the server
        Return the interesting information to insert in the DNS cache of the computer
        """
        if dns_answer.answer_record_count > 1:
            raise NotImplementedError(f"Multiple answers in the packet!")

        answer_record, = dns_answer.answer_records
        return answer_record.record_name, answer_record.record_data, answer_record.time_to_live

    def code(self) -> T_ProcessCode:
        """
        The main code of the process
        """
        self.socket = self.computer.get_udp_socket(self.pid)
        self.socket.bind()
        self.socket.connect(self._server_address)

        if not self._are_parameters_valid():
            self.die("ERROR: DNS Process parameters invalid!")
            return

        self._dns_process_print(f"Resolving name '{self._name_to_resolve}'")
        for _ in range(self._retry_count):
            self.socket.send(self._build_dns_query(self._name_to_resolve))
            yield from self.socket.block_until_received(timeout=self._query_timeout)

            received = self.socket.receive()
            if received:
                dns_answer = received[0]
                _, ip_address, ttl = self._extract_dns_answer(dns_answer)
                self.computer.dns_cache.add_item(self._name_to_resolve, ip_address, ttl)
                break
        else:
            self.die(f"ERROR: DNS could not resolve name :(")
            return

    def __repr__(self) -> str:
        return "dnscd"
