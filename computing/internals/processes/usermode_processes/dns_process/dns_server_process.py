from __future__ import annotations

import os
import struct
from typing import TYPE_CHECKING, Dict, Tuple

import scapy

from address.ip_address import IPAddress
from computing.internals.filesystem.file import File
from computing.internals.processes.abstracts.process import Process, T_ProcessCode, WaitingFor
from computing.internals.processes.usermode_processes.dns_process.zone import Zone, ZoneRecord
from consts import PORTS, T_Port, COMPUTER, OPCODES, PROTOCOLS
from exceptions import DNSRouteNotFound, WrongUsageError
from packets.all import DNS
from packets.usefuls.dns import *
from usefuls.funcs import get_the_one

if TYPE_CHECKING:
    from computing.internals.sockets.udp_socket import UDPSocket
    from computing.computer import Computer


T_QueryDict = Dict[T_Hostname, Tuple[IPAddress, T_Port]]


class DNSServerProcess(Process):
    """
    A Domain Name Server process - will resolve a display name to an IPAddress if a client requests
    """
    def __init__(self, pid: int, computer: Computer, domain_names: Optional[List[T_Hostname]] = None) -> None:
        """
        Creates the new process
        :param pid: The process ID of this process
        :param computer: The computer that runs this process
        """
        super(DNSServerProcess, self).__init__(pid, computer)
        self.socket: Optional[UDPSocket] = None
        self._active_queries: T_QueryDict = {}

        self.domain_names = domain_names or PROTOCOLS.DNS.DEFAULT_DOMAIN_NAMES

    @property
    def _zone_file_paths(self):
        return [self._zone_file_path_by_domain_name(domain_name) for domain_name in self.domain_names]

    @property
    def _zone_files(self):
        return [self.computer.filesystem.at_absolute_path(path) for path in self._zone_file_paths]

    @staticmethod
    def _zone_file_path_by_domain_name(domain_name: T_Hostname) -> str:
        return os.path.join(COMPUTER.FILES.CONFIGURATIONS.DNS_ZONE_FILES, decanonize_domain_hostname(domain_name) + '.zone')

    def _zone_file_by_domain_name(self, domain_name: T_Hostname) -> File:
        return self.computer.filesystem.at_absolute_path(self._zone_file_path_by_domain_name(domain_name))

    def _zone_by_domain_name(self, domain_name: T_Hostname) -> Zone:
        with self._zone_file_by_domain_name(domain_name) as zone_file:
            return Zone.from_file_format(zone_file.read())

    def _is_query_valid(self, query_bytes: bytes) -> bool:
        """
        Whether or not the server should answer the request that was sent to it
        """
        try:
            parsed_dns_packet = self._parse_dns_query(query_bytes)
        except struct.error:
            return False
        return not parsed_dns_packet.opcode.is_response

    def _build_dns_answer(self, record_name: T_Hostname, time_to_live: int) -> scapy.packet.Packet:
        """

        :param record_name:
        :return:
        """
        dns_answer = DNS(
            transaction_id=self.computer.dns_cache.transaction_counter,
            is_response=True,
            is_recursion_desired=True,
            is_recursion_available=True,
            answer_records=list_to_dns_resource_record([
                DNSResourceRecord(
                    record_name=record_name,
                    time_to_live=time_to_live,
                    record_data=self.computer.dns_cache[record_name].ip_address.string_ip,
                )
            ])
        )
        self.computer.dns_cache.transaction_counter += 1
        return dns_answer

    def _get_resolved_names(self) -> T_QueryDict:
        """
        Check if any of the names you should have resolved have been resolved already
        Return them as a list
        """
        return {name_to_resolve: client for name_to_resolve, client in self._active_queries.items() if name_to_resolve in self.computer.dns_cache}

    def _send_query_answers_to_clients(self, query_dict: T_QueryDict) -> None:
        """
        Take in all of the queries that are ready to be sent back to the clients
        Send them back to the clients
        """
        for item_name, client_address in query_dict.items():
            self.socket.sendto(self._build_dns_answer(item_name), client_address)
            del self._active_queries[item_name]

    def _send_error_messages_to_timed_out_clients(self) -> None:
        """
        Send error messages to the clients whose queries could sadly not be resolved :(
        """

    def _resolve_name(self, name: T_Hostname) -> None:
        """
        Start doing everything that is required in order to resolve the supplied domain name
        """
        if name in self.computer.dns_cache:
            return  # name is known - no need to resolve :)

        domain_name = get_the_one(self.domain_names, DomainHostname(name).endswith, DNSRouteNotFound)
        zone = self._zone_by_domain_name(domain_name)

        for record in zone.alias_records:
            pass  # TODO: add this

        for record in zone.host_records:
            if DomainHostname(name).endswith(record.record_name):
                self.computer.dns_cache.add_item(record.record_name, record.record_data)
                return

        for record in zone.name_server_records:
            if DomainHostname(name).endswith(record.record_name):
                self.computer.resolve_name(name, dns_server=IPAddress(record.record_data))

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
        self._init_zone_files()
        self._init_socket()

        while True:
            self._send_query_answers_to_clients(self._get_resolved_names())
            self._send_error_messages_to_timed_out_clients()

            yield WaitingFor.nothing()
            if not self.socket.has_data_to_receive:
                continue

            for udp_packet_data, client_ip, client_port in self.socket.receivefrom():
                if (client_ip, client_port) in self._active_queries.values():
                    break  # The client has requested the same address again from the same port! ignore...

                if not self._is_query_valid(query_bytes=udp_packet_data):
                    break  # Query is invalid! ignore...

                dns_query = self._parse_dns_query(query_bytes=udp_packet_data)
                if dns_query.query_count > 1:
                    raise NotImplementedError(f"multiple queries in the same packet! count: {dns_query.query_count}")
                self._resolve_name(dns_query.queries[0].query_name)

    def __repr__(self) -> str:
        return "dnssd"

    def _init_socket(self):
        self.socket = self.computer.get_udp_socket(self.pid)
        self.socket.bind((IPAddress.no_address(), PORTS.DNS))

    def _init_zone_files(self):
        """
        Generate all zone files with default values
        """
        for domain_name in self.domain_names:
            zone_file = self.computer.filesystem.make_empty_file_with_directory_tree(self._zone_file_path_by_domain_name(domain_name))
            with zone_file as f:
                if len(f.read()) == 0:
                    f.write(Zone.with_default_values(domain_name, self.computer).to_file_format())

    def add_dns_record(self, name: T_Hostname, ip_address: IPAddress, domain_name: Optional[T_Hostname] = None) -> None:
        """
        Add a mapping between an ip and a name in the supplied domain's zone file
        """
        if domain_name is None:
            if len(self.domain_names) > 1:
                raise WrongUsageError(f"Must supply domain_name if server hosts multiple zones")
            domain_name, = self.domain_names

        with self._zone_file_by_domain_name(domain_name) as zone_file:
            parsed_zone_file = Zone.from_file_format(zone_file.read())
            parsed_zone_file.records.append(
                ZoneRecord(
                    name,
                    OPCODES.DNS.QUERY_CLASSES.INTERNET,
                    OPCODES.DNS.QUERY_TYPES.HOST_ADDRESS,
                    ip_address.string_ip
                )
            )
            zone_file.write(parsed_zone_file.to_file_format())
