from typing import Tuple

from address.ip_address import IPAddress
from computing.internals.processes.abstracts.process import Process
from consts import COMPUTER, PORTS, PROTOCOLS


class EchoServerProcess(Process):
    def __init__(self, pid, computer):
        super(EchoServerProcess, self).__init__(pid, computer)
        self.socket = None

    def code(self):
        self.socket = self.computer.get_socket(kind=COMPUTER.SOCKETS.TYPES.SOCK_DGRAM, requesting_process_pid=self.pid)
        self.socket.bind((IPAddress.no_address(), PORTS.ECHO_SERVER))

        while True:
            yield from self.socket.block_until_received()
            udp_returned_packets = self.socket.receivefrom()
            for udp_returned_packet in udp_returned_packets:
                self.socket.sendto(udp_returned_packet.data, (udp_returned_packet.src_ip, udp_returned_packet.src_port))
                self.computer.print(f"server echoed: '{udp_returned_packet.data}' "
                                    f"to: {udp_returned_packet.src_ip}")

    def die(self):
        super(EchoServerProcess, self).die()
        if self.socket is not None:
            self.socket.close()

    def __repr__(self):
        return "echosd"


class EchoClientProcess(Process):
    def __init__(self, pid, computer, server_address: Tuple[IPAddress, int], data,
                 count=PROTOCOLS.ECHO_SERVER.DEFAULT_REQUEST_COUNT):
        super(EchoClientProcess, self).__init__(pid, computer)
        self.server_address = server_address
        self.data = data
        self.count = count

        self.socket = None

    def code(self):
        if not self.computer.ips:
            self.computer.print(f"Cannot run `echocd` without an IP address :(")
            self.die()
            return

        self.socket = self.computer.get_socket(kind=COMPUTER.SOCKETS.TYPES.SOCK_DGRAM, requesting_process_pid=self.pid)
        self.socket.bind((self.computer.ips[0], PORTS.ECHO_CLIENT))
        self.socket.connect(self.server_address)

        for _ in range(self.count):
            self.socket.send(self.data)
            self.computer.print(f"echoing: {self.data}")
            yield from self.socket.block_until_received()
            data = self.socket.receive()[0]
            if data == self.data:
                self.computer.print(f"echo server: {data}\n:)")
                continue

            self.computer.print(f"ERROR: echo server echoed: '{data}'\n:(")
            self.die()
            return

    def die(self):
        super(EchoClientProcess, self).die()
        if self.socket is not None:
            self.socket.close()

    def __repr__(self):
        server_ip, server_port = self.server_address
        return f"echocd {server_ip} " \
            f"-p {server_port} " \
            f"{f'-c {self.count}' if self.count != PROTOCOLS.ECHO_SERVER.DEFAULT_REQUEST_COUNT else ''}"
