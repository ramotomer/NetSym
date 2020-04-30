from consts import *
from exceptions import NoIPAddressError
from processes.process import Process, WaitingForPacket, ReturnedPacket, WaitingForPacketWithTimeout, Timeout


def arp_reply_from(ip_address):
    """Returns a function that tests if the packet given to it is an ARP reply for the `ip_address`"""
    def tester(packet):
        return ("ARP" in packet) and (packet["ARP"].opcode == ARP_REPLY) and (packet["ARP"].src_ip == ip_address)
    return tester


def request_address(computer, address):
    """
    Handle the sending of ARPs from a computer to request a certain address.
    Knows to send a couple of ARPs and to give up if it does not get a reply.
    :param computer: the `Computer` object that sends the ARPs
    :param address: an `IPAddress` object that is requested.
    :return: yields the appropriate `WaitingForPacket` namedtuple-s.
    """
    if address is None:
        return

    if address in computer.arp_cache:
        return

    returned_packets = ReturnedPacket()
    for _ in range(ARP_RESEND_COUNT):
        computer.send_arp_to(address)
        yield WaitingForPacketWithTimeout(arp_reply_from(address), returned_packets, Timeout(ARP_RESEND_TIME))
        if returned_packets.has_packets():  # if this was not timed-out, so we got an arp reply.
            break


class SendPing(Process):
    """
    This is a process for sending a ping request to another computer and receiving the reply.
    """
    def __init__(self, computer, ip_address, opcode=ICMP_REQUEST):
        super(SendPing, self).__init__(computer)
        self.dst_ip = ip_address
        self.ping_opcode = opcode
        self.is_sending_to_gateway = False

    def _send_the_ping(self, ip_for_the_mac):
        """
        Does all things necessary to send the ping.
        (decides the interfaces, maps ip to mac and actually sends the ping)
        :param ip_for_the_mac: The `IPAddress` we use to get the MAC address we send the ping to.
            (will be of the destination if in the same LAN, otherwise, will be of the gateway)
        :return: None
        """
        if not self.computer.has_ip():
            raise NoIPAddressError("The sending computer has no IP address!!!")

        dst_mac = self.computer.arp_cache[ip_for_the_mac].mac
        self.computer.send_ping_to(dst_mac, self.dst_ip, self.ping_opcode)

    def ping_reply_from(self, ip_address):
        """
        Returns a function that tests if the packet given to it is a ping reply for the `ip_address`
        """
        def tester(packet):
            if "ICMP" in packet:
                if packet["ICMP"].opcode == ICMP_REPLY:
                    if packet["IP"].src_ip == ip_address:
                        return True
                    if self.computer.has_this_ip(self.dst_ip) and packet["IP"].src_ip == self.computer.loopback.ip:
                        return True
                if packet["ICMP"].opcode == ICMP_UNREACHABLE:
                    return True
            return False
        return tester

    def _print_output(self, returned_packet):
        """
        Receives the `ReturnedOutput` object that was received and prints out to the `Console` an appropriate message
        """
        packet = returned_packet.packet
        if packet["ICMP"].opcode == ICMP_UNREACHABLE:
            self.computer.print("destination unreachable :(")
        else:
            self.computer.print("ping reply!")

    def code(self):
        """
        This code sends a ping (request or reply).
        If the address is unknown, first it sends an ARP and waits for a reply.
        :return: a generator of `WaitingForPacket` namedtuple-s.
        """
        if self.ping_opcode == ICMP_REQUEST:
            self.computer.print(f"pinging {self.dst_ip} with some bytes")

        ip_for_the_mac = self.computer.routing_table[self.dst_ip].ip_address # the IP we use to get our destination MAC address

        yield from request_address(self.computer, ip_for_the_mac)

        if not ip_for_the_mac in self.computer.arp_cache:  # the ARPs were not answered
            self.computer.print("Destination unreachable :(")
            return

        self._send_the_ping(ip_for_the_mac)

        if self.ping_opcode == ICMP_REQUEST:
            returned_packet = ReturnedPacket()
            yield WaitingForPacket(self.ping_reply_from(self.dst_ip), returned_packet)
            self._print_output(returned_packet)

    def __repr__(self):
        """The string representation of the SendPing process"""
        return "SendPing process"

