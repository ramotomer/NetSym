from computing.internals.processes.abstracts.process import Process, WaitingFor
from consts import COMPUTER, INTERFACES, OPCODES


class SniffingProcess(Process):
    """

    """
    def __init__(self, pid, computer, filter, interface=INTERFACES.ANY_INTERFACE, promisc=False):
        super(SniffingProcess, self).__init__(pid, computer)

        self.socket = self.computer.get_socket(self.pid, kind=COMPUTER.SOCKETS.TYPES.SOCK_RAW)
        self.socket.bind(filter, interface, promisc)

        self.packet_count = 0

        self.set_killing_signals_handler(self.close_socket)

    def close_socket(self, signum):
        self.computer.print(f"Stopped sniffing on {self.socket.interface.name or 'All interfaces'}")
        self.socket.close()

    @staticmethod
    def _get_sniffed_packet_info_line(packet):
        """
        Return the line that is printed when the packet is sniffed.
        :param packet:
        :return:
        """
        deepest = packet.deepest_layer()
        line = deepest.opcode if hasattr(deepest, "opcode") else type(deepest).__name__
        if 'TCP' in packet:
            line = f"TCP {' '.join([f for f in OPCODES.TCP.FLAGS_DISPLAY_PRIORITY if f in packet['TCP'].flags])}"

        if 'IP' in packet:
            l3_protocol = 'IP'
        elif 'ARP' in packet:
            l3_protocol = 'ARP'
        else:
            return line

        src_ip, dst_ip = packet[l3_protocol].src_ip, packet[l3_protocol].dst_ip
        return f"{line} {src_ip!s} > {dst_ip!s}"

    def code(self):
        """

        :return:
        """
        self.computer.print(f"started sniffing on {self.socket.interface.name or 'All interfaces'}")
        while True:
            yield WaitingFor(lambda: bool(self.socket.received))

            for packet in self.socket.recv():
                self.computer.print(f"({self.packet_count}) {self._get_sniffed_packet_info_line(packet)}")
                self.packet_count += 1

    def __repr__(self):
        return "sniffing"
