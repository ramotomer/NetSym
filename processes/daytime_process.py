import datetime

from consts import *
from processes.tcp_process import TCPProcess


class DAYTIMEServerProcess(TCPProcess):
    """
    This is a very simple TCP process where the client initiates a connection with the server and the server sends it
    the current time and day.
    """
    def __init__(self, computer):
        """
        Initiates the process of serving DAYTIME with the computer that run the process
        :param computer: the `Computer` that runs the process
        """
        super(DAYTIMEServerProcess, self).__init__(computer, src_port=PORTS.DAYTIME, is_client=False)

    def code(self):
        """
        The actual code of the DAYTIME process
        :return: yields WaitingFor namedtuple-s like every process.
        """
        self.computer.print("Serving DAYTIME...")
        while True:
            yield from self.hello_handshake()
            # ^ blocks the process until a client is connected.
            self.send(str(datetime.datetime.now()))  # sends the time
            while not self.is_done_transmitting():
                yield from self.handle_tcp_and_receive([])
            yield from self.goodbye_handshake(initiate=True)

    def __repr__(self):
        """String representation of the process"""
        return "DAYTIME server process"


class DAYTIMEClientProcess(TCPProcess):
    """
    The client process of the DAYTIME protocol
    """
    def __init__(self, computer, server_ip):
        """
        Initiates the process with the running computer and the IP address of the server
        :param computer:
        :param server_ip:
        """
        super(DAYTIMEClientProcess, self).__init__(computer, server_ip, PORTS.DAYTIME, is_client=True)

    def code(self):
        """
        The actual code of the DAYTIME process
        :return: yields WaitingFor namedtuple-s like every process.
        """
        self.computer.print("Asking Daytime...")
        yield from self.hello_handshake()
        daytime_data = []
        while not daytime_data:
            yield from self.handle_tcp_and_receive(daytime_data)
        self.computer.print(f"got daytime {daytime_data[0]}!")
        while not (daytime_data and daytime_data[-1] is PROTOCOLS.TCP.DONE_RECEIVING):
            yield from self.handle_tcp_and_receive(daytime_data)

    def __repr__(self):
        """String representation of the process"""
        return "DAYTIME client process"
