from consts import *
from processes.tcp_process import TCPProcess


class FTPServerProcess(TCPProcess):
    """

    """
    def __init__(self, computer, file_location=FILES.format(TRANSFER_FILE)):
        """

        :param computer:
        """
        super(FTPServerProcess, self).__init__(computer, is_client=False, src_port=FTP_PORT)
        self.file_location = file_location
        self.file_content = open(self.file_location, 'rb').read()

    def code(self):
        """

        :return:
        """
        while True:
            yield from self.hello_handshake()
            request = []
            started = False
            while not self.is_done_transmitting() or not request:
                yield from self.handle_tcp_and_receive(request)

                if request and not started:
                    if request[0] == FTP_REQUEST:
                        self.send(self.file_content)
                        started = True
                    else:
                        self.reset_connection()
                        return
            yield from self.goodbye_handshake(initiate=True)

    def __repr__(self):
        return "FTP server process"
        
        
class FTPClientProcess(TCPProcess):
    """
    
    """
    def __init__(self, computer, dst_ip):
        """
        
        :param computer: 
        :param dst_ip: 
        """
        super(FTPClientProcess, self).__init__(computer, dst_ip, FTP_PORT)

    def code(self):
        """

        :return:
        """
        self.computer.print(f"Downloading file from {self.dst_ip}...")
        yield from self.hello_handshake()
        self.send(FTP_REQUEST)
        all_data = []
        data_from_server = []
        while not (data_from_server and data_from_server[-1] is TCP_DONE_RECEIVING):
            if data_from_server:
                all_data[:] = data_from_server[:]
                data_from_server.clear()
                self.computer.print("got data!")
            yield from self.handle_tcp_and_receive(data_from_server)
        self.computer.print("Got the file!")

    def __repr__(self):
        return "FTP client process"
