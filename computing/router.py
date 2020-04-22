from computing.computer import Computer
from consts import *
from computing.process import Process, WaitingFor, NoNeedForPacket
import time
from gui.computer_graphics import ComputerGraphics
from computing.dhcp_process import DHCPServer


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

    def _packet_details(self):
        """
        Returns details about the packet;
        - is it routable? (does it have an IP layer, do we have where to route it to etc...)
        - what is the packet's dst IP address
        - what interfaces should it be sent on?

        :return: a tuple (is_routable, packet_dst_ip, interfaces_to_route_it_to) types: (bool, IPAddress, list of Interface objecs)
        """
        if "IP" not in self.packet:
            return False, None, None

        dst_ip = self.packet["IP"].dst_ip
        if self.computer.has_this_ip(dst_ip):
            return False, dst_ip, None  # packets that are for this router are not routable!

        sending_interfaces = self.computer.decide_routing_interface(self.packet["IP"].src_ip, dst_ip)
        return bool(sending_interfaces), dst_ip, sending_interfaces

    def _decrease_ttl(self):
        """
        Decrease the TTL of the packet, if it is 0, sends an ICMP Time Exceeded
        :return: a bool telling whether the time (TTL) of the packet was exceeded (reached 0).
        """
        sender_ip = self.packet["IP"].src_ip
        if self.packet["IP"].ttl == 0:
            for interface in self.computer.decide_sending_interface(sender_ip):
                interface.ping_to(self.computer.arp_cache[sender_ip].mac, sender_ip, ICMP_TIME_EXCEEDED)
            return True

        self.packet["IP"].ttl -= 1
        return False

    def code(self):
        """
        Receives the packet in the constructor, routes it to the correct subnet (the correct interface of the router).
        It has to send ARPs first sometimes. Does all of that.

        :return: a generator that yields `WaitingFor` namedtuple-s.
        """
        is_routable, dst_ip, sending_interfaces = self._packet_details()
        if not is_routable:
            return

        time_exceeded = self._decrease_ttl()

        if not time_exceeded:
            while dst_ip not in self.computer.arp_cache:
                self.computer.request_address(dst_ip)  # ARP
                yield WaitingFor(arp_reply_from(dst_ip), NoNeedForPacket())

            dst_mac = self.computer.arp_cache[dst_ip].mac
            for interface in sending_interfaces:
                interface.send(interface.ethernet_wrap(dst_mac, self.packet["IP"]))

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

        # self.routing_table = {IPAddress("0.0.0.0/0"): self.gateway}
        self.last_route_check = time.time()

        self.start_dhcp_server = is_dhcp_server

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
        new_packets = list(filter(lambda rp: rp.time > self.last_route_check, self.received))
        self.last_route_check = time.time()

        for packet, _, _ in new_packets:
            self.start_process(RoutePacket, packet)

    def decide_routing_interface(self, src_ip, dst_ip):
        """"""
        interfaces = self.decide_sending_interface(dst_ip)
        return [interface for interface in interfaces if not (interface.has_ip() and interface.ip.is_same_subnet(src_ip))]

    def logic(self):
        """Adds to the original logic of the Computer the ability to route packets."""
        super(Router, self).logic()

        self.route_new_packets()

        if self.start_dhcp_server:  # start the process of serving DHCP
            self.start_process(DHCPServer, self)
            self.start_dhcp_server = False

    def __repr__(self):
        """The string representation of the Router"""
        return f"Router(name={self.name}, Interfaces={self.interfaces})"
