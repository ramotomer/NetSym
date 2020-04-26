from processes.process import Process, WaitingFor, NoNeedForPacket, ReturnedPacket
from exceptions import NoIPAddressError
from consts import ICMP_REQUEST, ICMP_REPLY, ARP_REPLY


def arp_reply_from(ip_address):
    """Returns a function that tests if the packet given to it is an ARP reply for the `ip_address`"""
    def tester(packet):
        return ("ARP" in packet) and (packet["ARP"].opcode == ARP_REPLY) and (packet["ARP"].src_ip == ip_address)
    return tester


def ping_reply_from(ip_address):
    """Returns a function that tests if the packet given to it is a ping reply for the `ip_address`"""
    return lambda p: ("ICMP" in p) and (p["ICMP"].opcode == ICMP_REPLY) and (p["IP"].src_ip == ip_address)



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

    def code(self):
        """
        This code sends a ping (request or reply).
        If the address is unknown, first it sends an ARP and waits for a reply.
        :return: a generator of `WaitingFor` namedtuple-s.
        """
        if not self.computer.is_reachable(self.dst_ip):
            self.is_sending_to_gateway = True
            if self.computer.gateway is None: # network is totally unreachable
                return

        ip_for_the_mac = self.computer.routing_table[self.dst_ip].ip_address
        # ^ the IP we use to get our destination MAC address

        while ip_for_the_mac not in self.computer.arp_cache:
            self.computer.send_arp_to(ip_for_the_mac)
            yield WaitingFor(arp_reply_from(ip_for_the_mac), NoNeedForPacket())

        self._send_the_ping(ip_for_the_mac)

        if self.ping_opcode == ICMP_REQUEST:
            self.computer.print(f"pinging {self.dst_ip} with some bytes")

            ping_reply_returned_packet = ReturnedPacket()
            yield WaitingFor(ping_reply_from(self.dst_ip), ping_reply_returned_packet)
            self.computer.print("ping reply!")

    def __repr__(self):
        """The string representation of the SendPing process"""
        return "SendPing process"

