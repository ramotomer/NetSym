from address.mac_address import MACAddress
from computing.internals.processes.abstracts.process import Process, ReturnedPacket, WaitingForPacketWithTimeout, Timeout, \
    WaitingFor
from consts import OPCODES, PROTOCOLS
from usefuls.funcs import my_range


def arp_reply_from(ip_address):
    """Returns a function that tests if the packet given to it is an ARP reply for the `ip_address`"""
    def tester(packet):
        return ("ARP" in packet) and (packet["ARP"].opcode == OPCODES.ARP.REPLY) and (packet["ARP"].src_ip == ip_address)
    return tester


class ARPProcess(Process):
    """
    This is the process of the computer asking for an IP address using ARPs.
    """
    def __init__(self, pid, computer, address,
                 requesting_process=None,
                 send_even_if_known=False,
                 resend_count=PROTOCOLS.ARP.RESEND_COUNT,
                 resend_even_on_success=False):
        """
        Initiates the process with the address to request.
        :param computer:
        :param address:
        """
        super(ARPProcess, self).__init__(pid, computer)
        self.address = address
        self.requesting_process = requesting_process
        self.send_even_if_known = send_even_if_known
        self.resend_count = resend_count
        self.resend_even_on_success = resend_even_on_success

    def code(self):
        """The code of the process"""
        if self.address is None:
            return

        if self.address in self.computer.arp_cache and not self.send_even_if_known:
            return

        returned_packets = ReturnedPacket()
        for _ in my_range(self.resend_count):
            self.computer.send_arp_to(self.address)
            yield WaitingForPacketWithTimeout(arp_reply_from(self.address), returned_packets, Timeout(PROTOCOLS.ARP.RESEND_TIME))
            if not returned_packets.has_packets():
                self.computer.print("Destination is unreachable :(")
            elif not self.resend_even_on_success:
                return

        if self.requesting_process is not None:
            self.computer.process_scheduler.terminate_process(self.requesting_process, None)
            # TODO: what if we kill a process while it is ARP searching? this will try to kill it and crash the simulation

    def __repr__(self):
        return f"[karp] {self.address}"


class SendPacketWithARPProcess(Process):
    """
    This is a process that starts a complete sending of a packet.
    It checks the routing table and asks for the address and does whatever is necessary.
    """
    def __init__(self, pid, computer, ip_layer):
        """
        Initiates the process with the running computer
        the ip_layer will be wrapped in ethernet
        """
        super(SendPacketWithARPProcess, self).__init__(pid, computer)
        self.ip_layer = ip_layer

    def code(self):
        """
        The code of the process
        :return:
        """
        dst_ip = self.ip_layer.dst_ip
        if not dst_ip.is_broadcast():
            ip_for_the_mac, done_searching = self.computer.request_address(dst_ip, self, True)
            yield WaitingFor(done_searching)
        else:
            ip_for_the_mac = MACAddress.broadcast()

        self.computer.send_with_ethernet(
            self.computer.arp_cache[ip_for_the_mac].mac,
            dst_ip,
            self.ip_layer,
        )

    def __repr__(self):
        return f"[kwarp]"
