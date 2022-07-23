from abc import ABCMeta

from address.ip_address import IPAddress
from computing.internals.processes.abstracts.process import Process, WaitingFor
from consts import PORTS


class FTPProcess(Process, metaclass=ABCMeta):
    """
    A process that allows for file downloading from another computer.
    """
    def __init__(self, pid, computer):
        super(FTPProcess, self).__init__(pid, computer)

        self.socket = self.computer.get_socket(self.pid)
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


class ServerFTPProcess(FTPProcess):
    """
    The server side process
    """

    def code(self):
        self.socket.bind((None, PORTS.FTP))
        self.socket.listen(1)
        yield from self.socket.blocking_accept()

        yield from self.socket.block_until_received()
        received = self.socket.receive()

        if received.startswith("FTP: "):
            filename = received.split()[received.split().index("FTP:") + 1]

            with self.computer.filesystem.at_path(self.cwd, filename) as file:
                self.socket.send(file.read())

        yield WaitingFor(lambda: self.socket.socket_handling_kernelmode_process.is_done_transmitting())
        self.socket.close()
        # TODO: once we connect once to a server - we cannot do it again because the socket is closed now :) LOL


class ClientFTPProcess(FTPProcess):
    """
    The client side process
    """
    def __init__(self, pid, computer, server_ip: IPAddress, filename='/bin/cat'):
        super(ClientFTPProcess, self).__init__(pid, computer)
        self.server_ip = server_ip
        self.filename = filename

    def code(self):
        self.socket.bind()
        self.socket.connect((self.server_ip, PORTS.FTP))
        yield WaitingFor(lambda: self.socket.is_connected or self.socket.is_closed)

        if self.socket.is_closed:
            self.computer.print(f"FTP process({self.pid}) ended unexpectedly :(")
            self.kill_me = True
            return

        self.socket.send(f"FTP: {self.filename}")

        data = ''
        while self.socket.is_connected and not self.socket.is_closed:
            yield from self.socket.block_until_received()
            data += self.socket.receive()

        self.computer.filesystem.output_to_file(data, self.filename.split("/")[-1], self.cwd)

        if not self.socket.is_closed:
            self.socket.close()
