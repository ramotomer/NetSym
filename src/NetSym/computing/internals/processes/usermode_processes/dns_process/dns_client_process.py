from __future__ import annotations

import json
from typing import TYPE_CHECKING, Tuple, Optional, cast

import scapy
from scapy.layers.dns import dnstypes

from NetSym.address.ip_address import IPAddress
from NetSym.computing.internals.processes.abstracts.process import Process, T_ProcessCode
from NetSym.computing.internals.processes.abstracts.process_internal_errors import ProcessInternalError_DNSNameErrorFromServer, \
    ProcessInternalError_NoResponseForDNSQuery
from NetSym.consts import OPCODES, PROTOCOLS, T_Time, T_Port, PORTS
from NetSym.packets.all import DNS
from NetSym.packets.usefuls.dns import list_to_dns_query, DNSQueryRecord

if TYPE_CHECKING:
    from NetSym.computing.internals.sockets.udp_socket import UDPSocket
    from NetSym.computing.computer import Computer


SERVER_ADDRESS_IP_INDEX = 0


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
                 server_port: T_Port = PORTS.DNS,
                 output_result_to_path: Optional[str] = None) -> None:
        """
        Creates the new process
        :param pid: The process ID of this process
        :param computer: The computer that runs this process
        :param server_ip: the IPAddress of the server
        """
        super(DNSClientProcess, self).__init__(pid, computer)
        self._server_address = (server_ip, server_port)
        self._name_to_resolve = name_to_resolve

        self.socket: Optional[UDPSocket] = None
        self._query_timeout = default_query_timeout
        self._retry_count = default_retry_count

        self._output_file = output_result_to_path

    def _dns_format_print(self, message: str) -> None:
        """
        Print to computer console with a DNS prefix
        """
        self.computer.print(f"DNS says: {message}")

    def _are_parameters_valid(self) -> bool:
        """
        Kill the process if any of the parameters are invalid!
        """
        if self._retry_count < 1:
            self._dns_format_print(f"Retry count must be at least 1, not {self._retry_count}")
            return False

        if not self._name_to_resolve:
            self._dns_format_print(f"Name invalid! '{self._name_to_resolve}'")
            return False

        if self._server_address[SERVER_ADDRESS_IP_INDEX]:
            self._dns_format_print(f"No DNS server configured!")
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
                    query_type=OPCODES.DNS.TYPES.HOST_ADDRESS,
                    query_class=OPCODES.DNS.CLASSES.INTERNET,
                ),
            ]),
        )
        self.computer.dns_cache.transaction_counter += 1
        return query

    def _store_result_in_file(self, ip_address: IPAddress, ttl: int, record_type: str) -> None:
        """
        Write the output of the query to the file at `self._output_file`
        The format is json (so I have to write as little code as possible)
        """
        if self._output_file is None:
            return

        with self.computer.filesystem.make_empty_file_with_directory_tree(self._output_file, raise_on_exists=False) as f:
            f.write(json.dumps({
                "record_name": self._name_to_resolve,
                "record_type": record_type,
                "time_to_live": ttl,
                "record_data": str(ip_address),
            }))

    def _extract_dns_answer(self, dns_answer: bytes) -> Tuple[IPAddress, int, str]:

        """
        Take in the answer packet that was sent from the server
        Return the interesting information to insert in the DNS cache of the computer
        """
        parsed_dns_answer = DNS(dns_answer)

        if parsed_dns_answer.answer_record_count > 1:
            raise NotImplementedError(f"Multiple answers in the packet!")

        answer_record, = parsed_dns_answer.answer_records
        return answer_record.record_data, answer_record.time_to_live, answer_record.record_type

    def _validate_no_error_in_dns_answer(self, dns_answer: bytes) -> None:
        """
        Take in the packet bytes that were received from the socket
        Return whether or not they contain a DNS error return code
        """
        if DNS(dns_answer).return_code != OPCODES.DNS.RETURN_CODES.OK:
            self.die(
                "ERROR! DNS server sent an error! name not resolved :(",
                raises=ProcessInternalError_DNSNameErrorFromServer,
            )

    def _store_dns_answer(self, ip_address: IPAddress, ttl: int, record_type: str) -> None:
        """
        Take in the parsed DNS answer - and handle it
            Add to the DNS cache
            Store in tmp file (for recursive resolution) if necessary
            Print success message
        """
        self.computer.dns_cache.add_item(self._name_to_resolve, IPAddress(ip_address), ttl)
        self._store_result_in_file(ip_address, ttl, record_type)
        if dnstypes.get(record_type, record_type) == OPCODES.DNS.TYPES.HOST_ADDRESS:
            self._dns_format_print(f"\nAnswer:\n{ip_address}")

    def code(self) -> T_ProcessCode:
        """
        The main code of the process
        """
        if not self._are_parameters_valid():
            self.die("ERROR: DNS Process parameters invalid!")
            return

        self.socket = self.computer.get_udp_socket(self.pid)
        self.socket.bind()
        self.socket.connect(cast(Tuple[IPAddress, int], self._server_address))

        self._name_to_resolve = self.computer.add_default_domain_prefix_if_necessary(self._name_to_resolve)
        if self._name_to_resolve in self.computer.dns_cache:
            return  # name already in DNS cache - no need to resolve! :)
        self._dns_format_print(f"Resolving name '{self._name_to_resolve}'")

        for _ in range(self._retry_count):
            self.socket.send(self._build_dns_query(self._name_to_resolve))
            yield from self.socket.block_until_received(timeout=self._query_timeout)

            received = self.socket.receive()
            if received:  # if `received` is empty - that means the socket `block_until_received` was timed out
                dns_answer = received[0]
                self._validate_no_error_in_dns_answer(dns_answer)
                self._store_dns_answer(*self._extract_dns_answer(dns_answer))
                return

        self.die(
            f"ERROR: DNS server did not respond. name not resolved :(",
            raises=ProcessInternalError_NoResponseForDNSQuery,
        )

    def __repr__(self) -> str:
        return "dnscd"
