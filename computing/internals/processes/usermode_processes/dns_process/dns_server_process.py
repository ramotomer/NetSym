from __future__ import annotations

import struct
from typing import TYPE_CHECKING, Dict, Tuple, Optional

import scapy

from address.ip_address import IPAddress
from computing.internals.dns_table import T_DomainName
from computing.internals.processes.abstracts.process import Process, T_ProcessCode
from consts import PORTS, T_Port, PROTOCOLS
from packets.all import DNS
from packets.usefuls.dns import *

if TYPE_CHECKING:
    from computing.internals.sockets.udp_socket import UDPSocket
    from computing.computer import Computer


T_QueryDict = Dict[T_DomainName, Tuple[IPAddress, T_Port]]


class DNSServerProcess(Process):
    """
    A Domain Name Server process - will resolve a display name to an IPAddress if a client requests
    """
    def __init__(self, pid: int, computer: Computer, default_time_to_live: int = PROTOCOLS.DNS.DEFAULT_TIME_TO_LIVE) -> None:
        """
        Creates the new process
        :param pid: The process ID of this process
        :param computer: The computer that runs this process
        """
        super(DNSServerProcess, self).__init__(pid, computer)
        self.socket: Optional[UDPSocket] = None
        self._active_queries: T_QueryDict = {}

        self._default_time_to_live = default_time_to_live

    def _is_query_valid(self, query_bytes: bytes) -> bool:
        """
        Whether or not the server should answer the request that was sent to it
        """
        try:
            parsed_dns_packet = self._parse_dns_query(query_bytes)
        except struct.error:
            return False
        return not parsed_dns_packet.opcode.is_response

    def _build_dns_answer(self, domain_name: T_DomainName) -> scapy.packet.Packet:
        """

        :param domain_name:
        :return:
        """
        dns_answer = DNS(
            transaction_id=self.computer.dns_table.transaction_counter,
            is_response=True,
            is_recursion_desired=True,
            is_recursion_available=True,
            answer_records=list_to_dns_resource_record([
                DNSResourceRecord(
                    record_name=domain_name,
                    time_to_live=self._default_time_to_live,
                    record_data=self.computer.dns_table[domain_name].ip_address.string_ip,
                )
            ])
        )
        self.computer.dns_table.transaction_counter += 1
        return dns_answer

    def _get_resolved_names(self) -> T_QueryDict:
        """
        Check if any of the names you should have resolved have been resolved already
        Return them as a list
        """
        return {name_to_resolve: client for name_to_resolve, client in self._active_queries.items() if name_to_resolve in self.computer.dns_table}

    def _send_query_answers_to_clients(self, query_dict: T_QueryDict) -> None:
        """
        Take in all of the queries that are ready to be sent back to the clients
        Send them back to the clients
        """
        for domain_name, client_address in query_dict.items():
            self.socket.sendto(self._build_dns_answer(domain_name), client_address)

    def _send_error_messages_to_timed_out_clients(self) -> None:
        """
        Send error messages to the clients whose queries could sadly not be resolved :(
        """

    def _resolve_name(self, domain_name: T_DomainName) -> None:
        """
        Start doing everything that is required in order to resolve the supplied domain name
        """
        if domain_name in self.computer.dns_table:
            return  # name is known - no need to resolve :)

        # ...

    @staticmethod
    def _parse_dns_query(query_bytes: bytes) -> scapy.packet.Packet:
        """
        Take in raw bytes and return out `DNS` object
        The query should be valid, after it was tested in the `_is_query_valid` method
        """
        return DNS(query_bytes)

    def code(self) -> T_ProcessCode:
        """
        The main code of the process
        """
        self.socket = self.computer.get_udp_socket(self.pid)
        self.socket.bind((IPAddress.no_address(), PORTS.DNS))

        while True:
            yield from self.socket.block_until_received()
            returned_udp_packets = self.socket.receivefrom()
            for udp_packet_data, client_address in returned_udp_packets:
                if client_address in self._active_queries.values():
                    break  # The client has requested the same address again from the same port! ignore...

                if not self._is_query_valid(query_bytes=udp_packet_data):
                    break  # Query is invalid! ignore...

                dns_query = self._parse_dns_query(query_bytes=udp_packet_data)
                if dns_query.query_count > 1:
                    raise NotImplementedError(f"multiple queries in the same packet! count: {dns_query.query_count}")
                self._resolve_name(dns_query.queries[0].query_name)

            self._send_query_answers_to_clients(self._get_resolved_names())
            self._send_error_messages_to_timed_out_clients()
