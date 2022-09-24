from __future__ import annotations

import struct
from typing import TYPE_CHECKING

from address.ip_address import IPAddress
from computing.internals.processes.abstracts.process import Process, T_ProcessCode
from consts import COMPUTER, PORTS
from packets.all import DNS

if TYPE_CHECKING:
    from computing.computer import Computer


class DNSServerProcess(Process):
    """
    A Domain Name Server process - will resolve a display name to an IPAddress if a client requests
    """
    def __init__(self, pid: int, computer: Computer) -> None:
        """
        Creates the new process
        :param pid: The process ID of this process
        :param computer: The computer that runs this process
        """
        super(DNSServerProcess, self).__init__(pid, computer)
        self.socket = None
        self._active_sessions = []

    def _should_start_session(self, udp_packet_data: bytes) -> bool:
        """
        Whether or not the server should answer the request that was sent to it
        """
        try:
            parsed_dns_packet = DNS(udp_packet_data)
        except struct.error:
            return False
        return not parsed_dns_packet.opcode.is_response

    def code(self) -> T_ProcessCode:
        """
        The main code of the process
        """
        self.socket = self.computer.get_socket(kind=COMPUTER.SOCKETS.TYPES.SOCK_DGRAM, requesting_process_pid=self.pid)
        self.socket.bind((IPAddress.no_address(), PORTS.DNS))

        while True:
            yield from self.socket.block_until_received()
            returned_udp_packets = self.socket.receivefrom()
            for udp_packet_data, client_ip, client_port in returned_udp_packets:
                if (client_ip, client_port) in self._active_sessions:
                    self._handle_message_in_existing_session(udp_packet_data, client_ip, client_port)
                    break
                if self._should_start_session(udp_packet_data):
                    self._resolve_name()
