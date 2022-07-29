from address.ip_address import IPAddress
from computing.internals.processes.abstracts.process import Process
from computing.internals.processes.abstracts.tcp_server_process import TCPServerProcess
from consts import PORTS
from exceptions import TCPSocketConnectionRefused


class ServerFTPProcess(TCPServerProcess):
    """
    The server side process
    Waits for new connections and starts the `ServerFTPSessionProcess` for each one of them
    """
    def __init__(self, pid, computer):
        super(ServerFTPProcess, self).__init__(pid, computer, PORTS.FTP, ServerFTPSessionProcess)

    def __repr__(self):
        return "ftpd"


class ServerFTPSessionProcess(Process):
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


class ClientFTPProcess(Process):
    """
    The client side process
    """
    def __init__(self, pid, computer, server_ip: IPAddress, filename='/bin/cat', server_port=PORTS.FTP):
        super(ClientFTPProcess, self).__init__(pid, computer)
        self.socket = None
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
            data += self.socket.receive()
            yield from self.socket.block_until_received_or_closed()
        self.computer.filesystem.output_to_file(data, self.filename.split("/")[-1], self.cwd)

        yield from self.socket.close_when_done_transmitting()

    def __repr__(self):
        return "ftp"
