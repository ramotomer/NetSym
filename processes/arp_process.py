from consts import OPCODES, PROTOCOLS
from processes.process import Process, ReturnedPacket, WaitingForPacketWithTimeout, Timeout, WaitingFor


def arp_reply_from(ip_address):
    """Returns a function that tests if the packet given to it is an ARP reply for the `ip_address`"""
    def tester(packet):
        return ("ARP" in packet) and (packet["ARP"].opcode == OPCODES.ARP.REPLY) and (packet["ARP"].src_ip == ip_address)
    return tester


class ARPProcess(Process):
    """
    This is the process of the computer asking for an IP address using ARPs.
    """
    def __init__(self, computer, address, requesting_process=None):
        """
        Initiates the process with the address to request.
        :param computer:
        :param address:
        """
        super(ARPProcess, self).__init__(computer)
        self.address = address
        self.requesting_process = requesting_process

    def code(self):
        """The code of the process"""
        if self.address is None:
            return

        if self.address in self.computer.arp_cache:
            return

        returned_packets = ReturnedPacket()
        for _ in range(PROTOCOLS.ARP.RESEND_COUNT):
            self.computer.send_arp_to(self.address)
            yield WaitingForPacketWithTimeout(arp_reply_from(self.address), returned_packets, Timeout(PROTOCOLS.ARP.RESEND_TIME))
            if returned_packets.has_packets():  # if this was not timed-out, so we got an arp reply.
                return
        self.computer.print("Destination unreachable :(")

        if self.requesting_process is not None:
            self.computer.kill_process(type(self.requesting_process))

    def __repr__(self):
        return "Address Resolution Process (ARP sending)"


class SendPacketWithArpsProcess(Process):
    """
    This is a process that starts a complete sending of a packet.
    It checks the routing table and asks for the address and does whatever is necessary.
    """
    def __init__(self, computer, ip_layer):
        """
        Initiates the process with the running computer
        the ip_layer will be wrapped in ethernet
        """
        super(SendPacketWithArpsProcess, self).__init__(computer)
        self.ip_layer = ip_layer

    def code(self):
        """
        The code of the process
        :return:
        """
        dst_ip = self.ip_layer.dst_ip
        ip_for_the_mac, done_searching = self.computer.request_address(dst_ip, self, True)
        yield WaitingFor(done_searching)

        self.computer.send_with_ethernet(
            self.computer.arp_cache[ip_for_the_mac],
            dst_ip,
            self.ip_layer,
        )
