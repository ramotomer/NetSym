from abc import ABCMeta

from address.ip_address import IPAddress
from computing.internals.processes.abstracts.process import Process
from computing.internals.processes.abstracts.tcp_server_process import TCPServerProcess
from consts import PORTS
from exceptions import TCPSocketConnectionRefused


class FTPProcess(Process, metaclass=ABCMeta):
    """
    A process that allows for file downloading from another computer.
    Implements the logic required for both client and server
    """
    def __init__(self, pid, computer):
        super(FTPProcess, self).__init__(pid, computer)

        self.socket = None
        self.set_killing_signals_handler(self.handle_killing_signals)

    def handle_killing_signals(self, signum):
        """
        Close the socket and die.
        :param signum:
        :return:
        """
        self.socket.close()
        self.die()

    def __repr__(self):
        return "ftp"


class ServerFTPProcess(TCPServerProcess, FTPProcess):
    """
    The server side process
    Waits for new connections and starts the `ServerFTPSessionProcess` for each one of them
    """
    def __init__(self, pid, computer):
        super(ServerFTPProcess, self).__init__(pid, computer, PORTS.FTP, ServerFTPSessionProcess)


class ServerFTPSessionProcess(FTPProcess):
    """
    This process represents a single session of the server with a client.
    This allows the server to continue listening for new connections
    """
    def __init__(self, pid, computer, socket):
        super(ServerFTPSessionProcess, self).__init__(pid, computer)
        self.socket = socket

    def code(self):
        """
        The actual code of the process
        """
        yield from self.socket.block_until_received()
        received = self.socket.receive()

        if received.startswith("FTP: "):
            filename = received.split()[received.split().index("FTP:") + 1]

            with self.computer.filesystem.at_path(self.cwd, filename) as file:
                self.socket.send(file.read())

        yield from self.socket.close_when_done_transmitting()

    def __repr__(self):
        return "ftpsession"


class ClientFTPProcess(FTPProcess):
    """
    The client side process
    """
    def __init__(self, pid, computer, server_ip: IPAddress, filename='/bin/cat', server_port=PORTS.FTP):
        super(ClientFTPProcess, self).__init__(pid, computer)
        self.server_ip = server_ip
        self.server_port = server_port
        self.filename = filename

    def code(self):
        self.socket = self.computer.get_socket(self.pid)
        self.socket.bind()
        try:
            yield from self.socket.blocking_connect((self.server_ip, self.server_port))
        except TCPSocketConnectionRefused:
            self.computer.print(f"FTP process({self.pid}) ended unexpectedly :(")
            self.die()
            return

        self.socket.send(f"FTP: {self.filename}")

        data = ''
        while self.socket.is_connected and not self.socket.is_closed:
            yield from self.socket.block_until_received()
            data += self.socket.receive()

        self.computer.filesystem.output_to_file(data, self.filename.split("/")[-1], self.cwd)

        if not self.socket.is_closed:
            self.socket.close()
