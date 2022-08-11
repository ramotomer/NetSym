from computing.internals.processes.abstracts.process import Process, WaitingFor
from consts import OPCODES


class RoutePacket(Process):
    """
    This is a process which when run, takes in a packet and routes over the running router, using the
    `decide_routing_interfaces` method.
    The process is of routing a single packet over the router.
    """
    def __init__(self, pid, computer, packet):
        """
        Initiates the process with the given packet to route and the routing computer.
        """
        super(RoutePacket, self).__init__(pid, computer)
        self.packet = packet

    def _is_packet_routable(self):
        """
        Checks the given packet and make sure that it is valid and can be routed.
        :return:
        """
        if not self.packet.is_valid() or "IP" not in self.packet:
            return False

        if self.packet["IP"].dst_ip is None or self.packet["IP"].src_ip is None:
            return False

        if "0.0.0.0" in [str(self.packet["IP"].dst_ip), str(self.packet["IP"].src_ip)]:
            return False

        if self.packet["IP"].src_ip.is_broadcast() or self.packet["Ethernet"].dst_mac.is_broadcast():
            return False

        return True

    def _decrease_ttl(self):
        """
        Decrease the TTL of the packet, if it is 0, sends an ICMP Time Exceeded
        :return: a bool telling whether the time (TTL) of the packet was exceeded (reached 0).
        """
        sender_ip = self.packet["IP"].src_ip
        if self.packet["IP"].ttl == 0:
            self.computer.send_time_exceeded(self.computer.arp_cache[sender_ip].mac, sender_ip)
            return True

        self.packet["IP"].ttl -= 1
        return False

    def _destination_unreachable(self):
        """
        Tests if the destination of the packet is unreachable. If it is, send an `ICMP_UNREACHABLE` and return True.
        If not, return False
        :return: `bool`
        """
        dst_ip = self.packet["IP"].dst_ip
        routing_interface = self.computer.routing_table[dst_ip].ip_address
        gateway = self.computer.routing_table.default_gateway.ip_address

        if routing_interface == gateway and gateway is None:
            self._send_icmp_unreachable()
            return True
        return False

    def _send_icmp_unreachable(self):
        """Sends to the sender of the routed packet, an ICMP unreachable"""
        sender_ip = self.packet["IP"].src_ip
        dst_ip = self.packet["IP"].dst_ip

        self.computer.send_ping_to(self.computer.arp_cache[sender_ip].mac,
                                   self.packet["IP"].src_ip,
                                   OPCODES.ICMP.TYPES.UNREACHABLE,
                                   f"Unreachable: {dst_ip}")

    def code(self):
        """
        Receives the packet in the constructor, routes it to the correct subnet (the correct interface of the router).
        It has to send ARPs first sometimes. Does all of that.

        :return: a generator that yields `WaitingForPacket` namedtuple-s.
        """
        if not self._is_packet_routable():
            return

        if self._destination_unreachable():
            return

        dst_ip = self.packet["IP"].dst_ip
        time_exceeded = self._decrease_ttl()

        assert dst_ip is not None, "error!"

        if not time_exceeded:
            ip_for_the_mac, done_searching = self.computer.request_address(dst_ip, self, False)
            yield WaitingFor(done_searching)
            if ip_for_the_mac not in self.computer.arp_cache:          # if no one answered the arp
                self._send_icmp_unreachable()
                return

            self.computer.send_with_ethernet(self.computer.arp_cache[ip_for_the_mac].mac, dst_ip, self.packet["IP"])

    def __repr__(self):
        """The string representation of the process"""
        return "[kroute]"
