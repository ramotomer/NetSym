from computing.computer import Computer
from consts import *
from processes.process import Process, WaitingFor, NoNeedForPacket
import time
from gui.computer_graphics import ComputerGraphics
from processes.dhcp_process import DHCPServer
from computing.routing_table import RoutingTable


def arp_reply_from(source_ip):
    """
    returns a condition for a packet. the condition is a function that receives a packet and returns a boolean.
    The condition here checks if the packet is an arp reply from `source_ip`.
    :param source_ip: an `IPAddress` object.
    :return: a condition function.
    """
    return lambda p: ("ARP" in p) and (p["ARP"].opcode == ARP_REPLY) and (p["ARP"].src_ip == source_ip)


class RoutePacket(Process):
    """
    This is a process which when run, takes in a packet and routes over the running router, using the
    `decide_routing_interfaces` method.
    The process is of routing a single packet over the router.
    """
    def __init__(self, computer, packet):
        """
        Initiates the process with the given packet to route and the routing computer.
        """
        super(RoutePacket, self).__init__(computer)
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

        if "0.0.0.0" in [self.packet["IP"].dst_ip.string_ip, self.packet["IP"].src_ip.string_ip]:
            return False

        if self.packet["IP"].src_ip.is_broadcast():
            return False

        return True

    def _decrease_ttl(self):
        """
        Decrease the TTL of the packet, if it is 0, sends an ICMP Time Exceeded
        :return: a bool telling whether the time (TTL) of the packet was exceeded (reached 0).
        """
        sender_ip = self.packet["IP"].src_ip
        if self.packet["IP"].ttl == 0:
            self.computer.send_ping_to(self.computer.arp_cache[sender_ip].mac, sender_ip, ICMP_TIME_EXCEEDED)
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
        sender_ip = self.packet["IP"].src_ip

        if self.computer.routing_table[dst_ip].ip_address == self.computer.routing_table.default_gateway.ip_address and \
                self.computer.routing_table.default_gateway.ip_address is None:
            self.computer.send_ping_to(self.computer.arp_cache[sender_ip].mac,
                                       self.packet["IP"].src_ip,
                                       ICMP_UNREACHABLE,
                                       f"Unreachable: {dst_ip}")
            return True
        return False

    def code(self):
        """
        Receives the packet in the constructor, routes it to the correct subnet (the correct interface of the router).
        It has to send ARPs first sometimes. Does all of that.

        :return: a generator that yields `WaitingFor` namedtuple-s.
        """
        if not self._is_packet_routable():
            return

        if self._destination_unreachable():
            return

        dst_ip = self.packet["IP"].dst_ip
        time_exceeded = self._decrease_ttl()

        if not time_exceeded:
            while dst_ip not in self.computer.arp_cache:
                self.computer.send_arp_to(dst_ip)
                yield WaitingFor(arp_reply_from(dst_ip), NoNeedForPacket())

            dst_mac = self.computer.arp_cache[dst_ip].mac
            interface = self.computer.get_interface_with_ip(self.computer.routing_table[dst_ip].interface_ip)
            interface.send_with_ethernet(dst_mac, self.packet["IP"])

    def __repr__(self):
        """The string representation of the process"""
        return "Routing Process"


class Router(Computer):
    """
    This is a router class.
    It has one interface in each subnet that it routes.
    It has routing table which tells it where to route his packets to. It contains a subnet mask mapped to an interface
    (any packet that fits the subnet mask of the interface goes to that interface)
    """
    def __init__(self, name=None, interfaces=(), is_dhcp_server=True):
        """
        Initiates a router with no IP addresses.
        """
        super(Router, self).__init__(name, OS_SOLARIS, None, *interfaces)
        self.routing_table = RoutingTable.create_default(self, False)

        self.last_route_check = time.time()

        self.is_dhcp_server = is_dhcp_server

    def show(self, x, y):
        """
        overrides Computer.show and shows the same computer_graphics object only
        with a router's photo.
        :param x:
        :param y:
        :return: None
        """
        self.graphics = ComputerGraphics(x, y, self, ROUTER_IMAGE)

    def route_new_packets(self):
        """
        checks what are the new packets that arrived to this router, if they are not for it, routes them on.
        :return: None
        """
        new_packets = self._new_packets_since(self.last_route_check)
        self.last_route_check = time.time()

        for packet, _, _ in new_packets:
            if "IP" in packet and not self.has_this_ip(packet["IP"].dst_ip) and "DHCP" not in packet:
                self.start_process(RoutePacket, packet)

    def logic(self):
        """Adds to the original logic of the Computer the ability to route packets."""
        super(Router, self).logic()

        self.route_new_packets()

        if self.is_dhcp_server and not self._is_process_running(DHCPServer):
            self.print("Started serving DHCP...")
            self.start_process(DHCPServer, self)

    def __repr__(self):
        """The string representation of the Router"""
        return f"Router(name={self.name}, Interfaces={self.interfaces})"
