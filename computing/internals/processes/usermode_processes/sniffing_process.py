from computing.internals.processes.abstracts.process import Process
from consts import COMPUTER, INTERFACES, OPCODES
from exceptions import SocketIsClosedError
from packets.usefuls import get_layer_opcode, get_original_layer_name_by_instance


class SniffingProcess(Process):
    """
    This is a process object. The process it represents is one that sniffs packets and prints the results to the screen.

    """
    def __init__(self, pid, computer, filter, interface=INTERFACES.ANY_INTERFACE, promisc=False):
        super(SniffingProcess, self).__init__(pid, computer)

        self.socket = self.computer.get_socket(self.pid, kind=COMPUTER.SOCKETS.TYPES.SOCK_RAW)
        self.socket.bind(filter, interface, promisc)

        self.packet_count = 0

        self.set_killing_signals_handler(self.close_socket)

    @property
    def interface_name(self):
        return getattr(self.socket.interface, 'name', '') or 'All interfaces'

    def close_socket(self, signum):
        self.computer.print(f"Stopped sniffing on {self.interface_name}")
        self.socket.close()

    @staticmethod
    def _get_sniffed_packet_info_line(returned_packet):
        """
        Return the line that is printed when the packet is sniffed.
        :param returned_packet: a `ReturnedPacket` object
        :return:
        """
        packet, packet_metadata = returned_packet.packet_and_metadata

        deepest = packet.deepest_layer()
        line = str(get_layer_opcode(deepest)) or get_original_layer_name_by_instance(deepest)
        if 'TCP' in packet:
            line = f"TCP {' '.join([f for f in OPCODES.TCP.FLAGS_DISPLAY_PRIORITY if f in packet['TCP'].flags])}"

        if 'IP' in packet:
            l3_protocol = 'IP'
        elif 'ARP' in packet:
            l3_protocol = 'ARP'
        else:
            return line

        src_ip, dst_ip = packet[l3_protocol].src_ip, packet[l3_protocol].dst_ip
        return f"{line} {packet_metadata.direction} {src_ip!s} > {dst_ip!s}"

    def code(self):
        self.computer.print(f"started sniffing on {self.interface_name}")
        while True:
            yield from self.socket.block_until_received()

            try:
                for returned_packet in self.socket.receive():
                    self.computer.print(f"({self.packet_count}) {self._get_sniffed_packet_info_line(returned_packet)}")
                    self.packet_count += 1
            except SocketIsClosedError:
                self.die()
                return

    def __repr__(self):
        return f"tcpdump " \
            f"{f'-A' if self.socket.interface == INTERFACES.ANY_INTERFACE else f'-i {self.socket.interface.name}'} " \
            f"{'-p' if self.socket.is_promisc else ''}"
