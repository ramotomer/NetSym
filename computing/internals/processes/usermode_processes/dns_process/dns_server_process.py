from __future__ import annotations

import json
import struct
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict

import scapy

from address.ip_address import IPAddress
from computing.internals.filesystem.file import File
from computing.internals.processes.abstracts.process import Process, T_ProcessCode, WaitingFor
from computing.internals.processes.usermode_processes.dns_process.dns_client_process import DNSClientProcess
from computing.internals.processes.usermode_processes.dns_process.zone import Zone, ZoneRecord
from consts import PORTS, T_Port, OPCODES
from exceptions import DNSRouteNotFound, WrongUsageError, NoSuchFileError
from packets.all import DNS
from packets.usefuls.dns import *
from usefuls.funcs import get_the_one, with_args

if TYPE_CHECKING:
    from computing.internals.sockets.udp_socket import UDPSocket
    from computing.computer import Computer


@dataclass
class ActiveQueryData:
    client_ip: IPAddress
    client_port: T_Port
    active_query_process_id: Optional[int] = None


T_QueryDict = Dict[T_Hostname, ActiveQueryData]


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

        self.__initial_domain_names = list(map(canonize_domain_hostname, (domain_names or [])))

    @property
    def domain_names(self) -> List[T_Hostname]:
        try:
            return [canonize_domain_hostname(file.name.rsplit('.', 1)[0])
                    for file in self.computer.filesystem.at_absolute_path(COMPUTER.FILES.CONFIGURATIONS.DNS_ZONE_FILES).files.values()]
        except NoSuchFileError:
            return []

    @property
    def _zone_file_paths(self):
        return [self._zone_file_path_by_domain_name(domain_name) for domain_name in self.domain_names]

    @property
    def _zone_files(self):
        return [self.computer.filesystem.at_absolute_path(path) for path in self._zone_file_paths]

    @staticmethod
    def _zone_file_path_by_domain_name(domain_name: T_Hostname) -> str:
        return COMPUTER.FILES.CONFIGURATIONS.DNS_ZONE_FILES + "/" + decanonize_domain_hostname(domain_name) + '.zone'

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
        return not parsed_dns_packet.is_response

    def _build_dns_answer(self, record_name: Optional[T_Hostname], time_to_live: Optional[int]) -> scapy.packet.Packet:
        """
        Takes in a name and TTL and builds a DNS packet that can be sent to the client as an answer to his query
        """
        is_ok = (record_name is not None) and (time_to_live is not None)
        dns_answer = DNS(
            transaction_id=self.computer.dns_cache.transaction_counter,
            is_response=True,
            return_code=OPCODES.DNS.RETURN_CODES.OK if is_ok else OPCODES.DNS.RETURN_CODES.NAME_ERROR,
            is_recursion_desired=True,
            is_recursion_available=True,
            answer_records=(list_to_dns_resource_record([
                DNSResourceRecord(
                    record_name=record_name,
                    time_to_live=time_to_live,
                    record_data=self.computer.dns_cache[record_name].ip_address.string_ip,
                )
            ]) if is_ok else None)
        )
        # TODO: add the Query object itself to the DNS answer packet
        self.computer.dns_cache.transaction_counter += 1
        return dns_answer

    def _build_dns_error(self) -> scapy.packet.Packet:
        """
        Builds a DNS answer to a client query. This answer signals that the name could sadly not be resolved :(
        """
        return self._build_dns_answer(None, None)

    def _is_active_client(self, client_ip: IPAddress, client_port: T_Port) -> bool:
        """Returns whether or not a client with this IP and port currently has an active query """
        return any(client.client_ip == client_ip and client.client_port == client_port for client in self._active_queries.values())

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
        for item_name, client in query_dict.items():
            del self._active_queries[item_name]
            self.socket.sendto(self._build_dns_answer(item_name, self.computer.dns_cache[item_name].ttl), (client.client_ip, client.client_port))

    def _send_error_messages_to_timed_out_clients(self) -> None:
        """
        Send error messages to the clients whose queries could sadly not be resolved :(
        """
        timed_out_clients = {hostname: client for hostname, client in self._active_queries.items()
                             if client.active_query_process_id is not None and
                                not self.computer.process_scheduler.is_usermode_process_running(client.active_query_process_id) and
                                not self.computer.filesystem.exists(default_tmp_query_output_file_path(hostname))}

        for hostname, client in timed_out_clients.items():
            del self._active_queries[hostname]
            self.socket.sendto(self._build_dns_error(), (client.client_ip, client.client_port))

    def _start_single_dns_query(self, name: T_Hostname, dns_server: IPAddress) -> None:
        """
        Start a process of a `DNSClientProcess` that will try another iteration of resolving the supplied name
        """
        pid = self.computer.process_scheduler.start_usermode_process(
            DNSClientProcess,
            dns_server if dns_server is not None else self.computer.dns_server,
            name,
            output_result_to_path=default_tmp_query_output_file_path(name),
        )
        self._active_queries[name].active_query_process_id = pid

    def _continue_sending_my_unfinished_queries(self) -> None:
        """
        When resolving a name, the process may be iterative; You ask one server and he passes you to the next and so on...
        Each of these queries you send is a separate process.
        When each one of them is done (if it was successful) it leaves behind a file to lead us to the next server

        This function checks for these files, and runs the new processes to continue the search
        """
        tmp_query_files_dir = self.computer.filesystem.at_absolute_path(COMPUTER.FILES.CONFIGURATIONS.DNS_TMP_QUERY_RESULTS_DIR_PATH)

        for file in list(tmp_query_files_dir.files.values()):
            with file as f:
                file_contents = json.loads(f.read())
            del tmp_query_files_dir.files[file.name]  # file was handled and is no longer necessary - delete!

            record_name,  record_type = file_contents["record_name"],  file_contents["record_type"]
            time_to_live, record_data = file_contents["time_to_live"], file_contents["record_data"]

            if record_type == OPCODES.DNS.TYPES.HOST_ADDRESS:
                relevant_domain_name = get_the_one(self.domain_names, with_args(does_domain_hostname_end_with, record_name), DNSRouteNotFound)
                self.computer.dns_cache.add_item(
                    record_name,
                    IPAddress(record_data),
                    time_to_live or self._zone_by_domain_name(relevant_domain_name).default_ttl,
                )
                continue

            if record_type == OPCODES.DNS.TYPES.AUTHORITATIVE_NAME_SERVER:
                self._start_single_dns_query(record_name, IPAddress(record_data))

    @staticmethod
    def _find_longest_matching_ns_record(name: T_Hostname, zone: Zone) -> Optional[ZoneRecord]:
        """
        Goes over all of the zone records which are A-s or CNAME-s
        Finds the one that is most fitting for the name supplied

        Returns (longest_record, longest_record_data) - the data is returned separately because if record is an alias -
            the data will be different than in the original record!

        If no sufficient records are found - returns (None, None)
        """
        longest_record: Optional[ZoneRecord] = None

        for record in zone:
            if does_domain_hostname_end_with(name, record.record_name, zone_origin=zone.origin):
                if longest_record is None:
                    longest_record = record
                    continue

                if (len(canonize_domain_hostname(record.record_name,        zone.origin)) >
                   len(canonize_domain_hostname(longest_record.record_name, zone.origin))):
                    if record.record_type in [OPCODES.DNS.TYPES.CANONICAL_NAME_FOR_AN_ALIAS,
                                              OPCODES.DNS.TYPES.AUTHORITATIVE_NAME_SERVER]:
                        longest_record = record
        return longest_record

    @staticmethod
    def _get_exact_host_record(name: T_Hostname, zone: Zone) -> Optional[ZoneRecord]:
        """
        Goes over the Zone file and returns the record that fits the supplied name exactly
        If one does not exist - return None
        """
        for record in zone:
            if (canonize_domain_hostname(record.record_name, zone.origin) == canonize_domain_hostname(name)) and \
                    (record.record_type in [OPCODES.DNS.TYPES.CANONICAL_NAME_FOR_AN_ALIAS,
                                            OPCODES.DNS.TYPES.HOST_ADDRESS]):
                return record
        return None

    def _resolve_name(self, name: T_Hostname, client_ip: IPAddress, client_port: T_Port) -> None:
        """
        Start doing everything that is required in order to resolve the supplied domain name
        """
        self._active_queries[name] = ActiveQueryData(client_ip, client_port)

        if name in self.computer.dns_cache:
            return  # name is known - no need to resolve :)

        domain_name = get_the_one(self.domain_names, with_args(does_domain_hostname_end_with, name), DNSRouteNotFound)
        zone = self._zone_by_domain_name(domain_name)

        exact_host_record = self._get_exact_host_record(name, zone)                  # A and CNAME records
        if exact_host_record is not None:
            self.computer.dns_cache.add_item(
                canonize_domain_hostname(exact_host_record.record_name, zone.origin),
                IPAddress(zone.resolve_aliasing(exact_host_record)),
                (exact_host_record.ttl or zone.default_ttl),
            )
            return

        longest_matching_record = self._find_longest_matching_ns_record(name, zone)  # NS records
        if longest_matching_record is not None:
            dst_ip = IPAddress(zone.resolve_aliasing(longest_matching_record))
            if self.computer.has_this_ip(dst_ip):
                # ^ This means the desired zone is local on this computer - but a sufficient 'A' record was not found :(
                self._decline_client_query(client_ip, client_port)
            else:
                self._start_single_dns_query(name, dst_ip)

    @staticmethod
    def _parse_dns_query(query_bytes: bytes) -> scapy.packet.Packet:
        """
        Take in raw bytes and return out `DNS` object
        The query should be valid, after it was tested in the `_is_query_valid` method
        """
        return DNS(query_bytes)

    def _init_socket(self):
        self.socket = self.computer.get_udp_socket(self.pid)
        self.socket.bind((IPAddress.no_address(), PORTS.DNS))

    def _init_zone_file(self, domain_name: T_Hostname) -> None:
        """
        Generate all zone files with default values
        And create the tmp directory in which DNS query results will be saved from other `DNSClientProcess`-s
        """
        zone_file = self.computer.filesystem.make_empty_file_with_directory_tree(self._zone_file_path_by_domain_name(domain_name),
                                                                                 raise_on_exists=False)
        with zone_file as f:
            if len(f.read()) == 0:
                f.write(Zone.with_default_values(domain_name, self.computer).to_file_format())

    def _init_tmp_query_result_files(self):
        """
        And create the tmp directory in which DNS query results will be saved from other `DNSClientProcess`-s
        """
        self.computer.filesystem.create_directory_tree(COMPUTER.FILES.CONFIGURATIONS.DNS_TMP_QUERY_RESULTS_DIR_PATH)

    def code(self) -> T_ProcessCode:
        """
        The main code of the process
        """
        self._init_tmp_query_result_files()
        self._init_socket()

        for domain_name in self.__initial_domain_names:
            self._init_zone_file(domain_name)

        while True:
            self._send_query_answers_to_clients(self._get_resolved_names())
            self._send_error_messages_to_timed_out_clients()
            self._continue_sending_my_unfinished_queries()

            yield WaitingFor.nothing()
            if not self.socket.has_data_to_receive:
                continue

            for udp_packet_data, client_ip, client_port in self.socket.receivefrom():
                if self._is_active_client(client_ip, client_port):
                    break  # The client has requested the same address again from the same port! ignore...

                if not self._is_query_valid(query_bytes=udp_packet_data):
                    break  # Query is invalid! ignore...

                dns_query = self._parse_dns_query(query_bytes=udp_packet_data)
                if dns_query.query_count > 1:
                    raise NotImplementedError(f"multiple queries in the same packet! count: {dns_query.query_count}")
                self._resolve_name(dns_query.queries[0].query_name.decode("ascii"), client_ip, client_port)

    def __repr__(self) -> str:
        return "dnssd"

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
                    OPCODES.DNS.CLASSES.INTERNET,
                    OPCODES.DNS.TYPES.HOST_ADDRESS,
                    ip_address.string_ip
                )
            )
            zone_file.write(parsed_zone_file.to_file_format())

    def add_or_remove_zone(self, domain_name: T_Hostname) -> None:
        """
        Add a new zone for the DNS server
        If it exists - deletes it
        """
        domain_name = canonize_domain_hostname(domain_name)

        if domain_name in self.domain_names:
            # remove
            self.domain_names.remove(domain_name)
            self.computer.filesystem.delete_file(self._zone_file_path_by_domain_name(domain_name))

        else:
            # add
            self.domain_names.append(domain_name)
            self._init_zone_file(domain_name)

    def _decline_client_query(self, client_ip: IPAddress, client_port: T_Port) -> None:
        """

        """
        hostname = [hostname for hostname, client in self._active_queries.items()
                    if client.client_ip == client_ip and client.client_port == client_port][0]

        self._active_queries[hostname].active_query_process_id = 0
        # ^ This PID does not exist - This is considered a timed out process - so they will be sent an error message
