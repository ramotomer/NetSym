from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from computing.internals.processes.abstracts.process import Process, T_ProcessCode
from computing.internals.processes.abstracts.tcp_server_process import TCPServerProcess
from consts import *
from exceptions import TCPSocketConnectionRefused
from packets.usefuls.dns import T_Hostname

if TYPE_CHECKING:
    from computing.internals.sockets.tcp_socket import TCPSocket
    from computing.computer import Computer


class DAYTIMEServerProcess(TCPServerProcess):
    def __init__(self, pid: int, computer: Computer) -> None:
        super(DAYTIMEServerProcess, self).__init__(pid, computer, PORTS.DAYTIME, DAYTIMEServerSessionProcess)

    def __repr__(self) -> str:
        return "daytimesd"


class DAYTIMEServerSessionProcess(Process):
    """
    This is a very simple TCP process where the client initiates a connection with the server and the server sends it
    the current time and day.
    """
    def __init__(self, pid: int, computer: Computer, socket: TCPSocket) -> None:
        super(DAYTIMEServerSessionProcess, self).__init__(pid, computer)
        self.socket = socket

    def code(self) -> T_ProcessCode:
        """
        The actual code of the DAYTIME process
        :return: yields WaitingFor namedtuple-s like every process.
        """
        self.socket.send(str(datetime.datetime.now()))
        yield from self.socket.close_when_done_transmitting()

    def __repr__(self) -> str:
        """String representation of the process"""
        return "daytimesession"


class DAYTIMEClientProcess(Process):
    """
    The client process of the DAYTIME protocol
    """
    def __init__(self, pid: int, computer: Computer, server_hostname: T_Hostname, server_port: T_Port = PORTS.DAYTIME) -> None:
        super(DAYTIMEClientProcess, self).__init__(pid, computer)
        self.server_hostname = server_hostname
        self.server_port = server_port
        self.socket = None

    def code(self) -> T_ProcessCode:
        """
        The actual code of the DAYTIME process
        :return: yields WaitingFor namedtuple-s like every process.
        """
        server_ip = yield from self.computer.resolve_domain_name(self, self.server_hostname)

        self.computer.print("Asking Daytime...")
        self.socket = self.computer.get_tcp_socket(self.pid)
        self.socket.bind()

        try:
            yield from self.socket.blocking_connect((server_ip, self.server_port))
        except TCPSocketConnectionRefused:
            self.computer.print(f"Daytime process ({self.pid}) ended unexpectedly :(")
            self.die()
            return

        yield from self.socket.block_until_received()
        self.computer.print(f"Got datetime! {self.socket.receive().decode('ascii')}")
        yield from self.socket.block_until_closed()

    def __repr__(self) -> str:
        return "daytimecd"
