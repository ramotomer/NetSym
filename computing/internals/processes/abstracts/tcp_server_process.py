from abc import ABCMeta

from computing.internals.processes.abstracts.process import Process


class TCPServerProcess(Process, metaclass=ABCMeta):
    """
    A process that waits for TCP connections.
    For each connection it starts a child process with the connection's `Socket` object
    """
    def __init__(self, pid, computer, src_port, connection_process_type):
        super(TCPServerProcess, self).__init__(pid, computer)
        self.src_port = src_port
        self.connection_process_type = connection_process_type
        self.socket = None
        self.set_killing_signals_handler(self.handle_killing_signals)

    def handle_killing_signals(self, signum):
        """
        Close the socket and die.
        :param signum:
        :return:
        """
        if self.socket is not None:
            self.socket.close()
        self.die()

    def code(self):
        self.socket = self.computer.get_socket(self.pid)
        self.socket.bind((None, self.src_port))
        self.socket.listen()
        while True:
            server_socket = yield from self.socket.blocking_accept(self.pid)
            self.computer.process_scheduler.start_usermode_process(self.connection_process_type, self.socket)
            self.socket = server_socket
