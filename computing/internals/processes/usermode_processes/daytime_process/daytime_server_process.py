from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from computing.internals.processes.abstracts.process import Process, T_ProcessCode
from computing.internals.processes.abstracts.tcp_server_process import TCPServerProcess
from consts import *

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
