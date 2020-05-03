from consts import *
from processes.process import Process, ReturnedPacket, WaitingForPacketWithTimeout, Timeout


def arp_reply_from(ip_address):
    """Returns a function that tests if the packet given to it is an ARP reply for the `ip_address`"""
    def tester(packet):
        return ("ARP" in packet) and (packet["ARP"].opcode == ARP_REPLY) and (packet["ARP"].src_ip == ip_address)
    return tester


class ARPProcess(Process):
    """
    This is the process of the computer asking for an IP address using ARPs.
    """
    def __init__(self, computer, address):
        """
        Initiates the process with the address to request.
        :param computer:
        :param address:
        """
        super(ARPProcess, self).__init__(computer)
        self.address = address

    def code(self):
        """The code of the process"""
        if self.address is None:
            return

        if self.address in self.computer.arp_cache:
            return

        returned_packets = ReturnedPacket()
        for _ in range(ARP_RESEND_COUNT):
            self.computer.send_arp_to(self.address)
            yield WaitingForPacketWithTimeout(arp_reply_from(self.address), returned_packets, Timeout(ARP_RESEND_TIME))
            if returned_packets.has_packets():  # if this was not timed-out, so we got an arp reply.
                return
        self.computer.print("Destination unreachable :(")
