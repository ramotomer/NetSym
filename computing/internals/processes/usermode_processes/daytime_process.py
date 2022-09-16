import datetime

from address.ip_address import IPAddress
from computing.internals.processes.abstracts.process import Process
from computing.internals.processes.abstracts.tcp_server_process import TCPServerProcess
from consts import *
from exceptions import TCPSocketConnectionRefused


class DAYTIMEServerProcess(TCPServerProcess):
    def __init__(self, pid, computer):
        super(DAYTIMEServerProcess, self).__init__(pid, computer, PORTS.DAYTIME, DAYTIMEServerSessionProcess)

    def __repr__(self):
        return "daytimesd"


class DAYTIMEServerSessionProcess(Process):
    """
    This is a very simple TCP process where the client initiates a connection with the server and the server sends it
    the current time and day.
    """
    def __init__(self, pid, computer, socket):
        super(DAYTIMEServerSessionProcess, self).__init__(pid, computer)
        self.socket = socket

    def code(self):
        """
        The actual code of the DAYTIME process
        :return: yields WaitingFor namedtuple-s like every process.
        """
        self.socket.send(str(datetime.datetime.now()))
        yield from self.socket.close_when_done_transmitting()

    def __repr__(self):
        """String representation of the process"""
        return "daytimesession"


class DAYTIMEClientProcess(Process):
    """
    The client process of the DAYTIME protocol
    """
    def __init__(self, pid, computer, server_address: IPAddress, server_port=PORTS.DAYTIME):
        super(DAYTIMEClientProcess, self).__init__(pid, computer)
        self.server_address = server_address
        self.server_port = server_port
        self.socket = None

    def code(self):
        """
        The actual code of the DAYTIME process
        :return: yields WaitingFor namedtuple-s like every process.
        """
        self.computer.print("Asking Daytime...")
        self.socket = self.computer.get_socket(self.pid)
        self.socket.bind()
        try:
            yield from self.socket.blocking_connect((self.server_address, self.server_port))
        except TCPSocketConnectionRefused:
            self.computer.print(f"Daytime process ({self.pid}) ended unexpectedly :(")
            self.die()
            return

        yield from self.socket.block_until_received()
        self.computer.print(f"Got datetime! {self.socket.receive().decode('ascii')}")
        yield from self.socket.block_until_closed()

    def __repr__(self):
        return "daytimecd"
