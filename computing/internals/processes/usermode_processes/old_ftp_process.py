from computing.internals.processes.abstracts.tcp_process import TCPProcess
from consts import *


class FTPProcess(TCPProcess):
    """
    A generic FTP process (Server or Client)
    """
    def __init__(self, pid, computer, is_client, server_ip=None):
        """
        Initiates the FTP process with a bool that tells it whether it is the server or the client
        """
        super(FTPProcess, self).__init__(pid, computer,
                                         is_client=is_client,
                                         dst_ip=server_ip,
                                         src_port=PORTS.FTP if not is_client else None,
                                         dst_port=PORTS.FTP if is_client else None)

    @staticmethod
    def create_ftp_layer(data, is_request=False):
        """
        Creates an FTP layer and returns it.
        :param data: The actual data that the packet will contain.
        :param is_request: whether or not the packet is a request to download or upload a file.
        :return: `FTP` object
        """
        return FTP(
            data,
            is_request=is_request,
        )

    def code(self):
        pass


class FTPServerProcess(FTPProcess):
    """
    This is a file transferring process. It is not really like FTP it is just something i made to test the TCP process.
    """
    def __init__(self, pid, computer, file_location=os.path.join(DIRECTORIES.FILES, TRANSFER_FILE)):
        """
        Initiates the process from a base TCP process.
        :param computer: The computer running the process
        :param file_location: the location of the file one wishes to transfer
        """
        super(FTPServerProcess, self).__init__(pid, computer, is_client=False)
        self.file_location = file_location
        self.file_content = open(self.file_location, 'r').read()

        # TODO: after computer filesystems were implemented, make it so the file is actually from the server!

    def code(self):
        """
        The code of the actual process
        :return:
        """
        while True:
            yield from self.hello_handshake()
            request = []
            started = False
            while not self.is_done_transmitting() or not request:
                yield from self.handle_tcp_and_receive(request)

                if request and not started:
                    if request[0].is_request:
                        self.send(self.file_content, packet_constructor=self.create_ftp_layer)
                        started = True
                    else:
                        self.reset_connection()
                        return
            yield from self.goodbye_handshake(initiate=True)

    def __repr__(self):
        return "FTP server process"
        
        
class FTPClientProcess(FTPProcess):
    """
    The client process side of the FTP
    """
    def __init__(self, pid, computer, dst_ip):
        """
        Initialize the process with a server_ip
        :param computer: 
        :param dst_ip: the IP address of the server
        """
        super(FTPClientProcess, self).__init__(pid, computer, is_client=True, server_ip=dst_ip)

    def code(self):
        """
        The actual code of the process
        :return:
        """
        self.computer.print(f"Downloading file from {self.dst_ip}...")
        yield from self.hello_handshake()
        self.send(self.create_ftp_layer(os.path.join(DIRECTORIES.FILES, TRANSFER_FILE), is_request=True))
        received_file = ""
        ftp_from_server = []
        while not (ftp_from_server and ftp_from_server[-1] is PROTOCOLS.TCP.DONE_RECEIVING):
            received_file += self.sum_packets_to_string(ftp_from_server)
            ftp_from_server.clear()
            yield from self.handle_tcp_and_receive(ftp_from_server)

    def sum_packets_to_string(self, ftp_list):
        """
        Receive a list of `FTP` objects, returns a string of the concat-ed data from them
        :param ftp_list: list of `FTP` objects
        :return: a string of the summed data from them
        """
        return ''.join(ftp.data for ftp in ftp_list)

    def __repr__(self):
        return "FTP client process"
