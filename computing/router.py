from computing.computer import Computer
from computing.interface import Interface
from computing.internals.routing_table import RoutingTable
from consts import *
from gui.main_loop import MainLoop
from gui.tech.computer_graphics import ComputerGraphics
from processes.dhcp_process import DHCPServer
from processes.process import Process, WaitingFor


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
                                   OPCODES.ICMP.UNREACHABLE,
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
        return "Routing Process"


class Router(Computer):
    """
    This is a router class.
    It has one interface in each subnet that it routes.
    It has routing table which tells it where to route his packets to. It contains a subnet mask mapped to an interface
    (any packet that fits the subnet mask of the interface goes to that interface)
    """
    def __init__(self, name=None, interfaces=None, is_dhcp_server=True):
        """
        Initiates a router with no IP addresses.
        """
        if interfaces is None:
            interfaces = [Interface(ip='1.1.1.1')]

        super(Router, self).__init__(name, OS.SOLARIS, None, *interfaces)
        self.routing_table = RoutingTable.create_default(self, False)

        self.last_route_check = MainLoop.instance.time()

        self.is_dhcp_server = is_dhcp_server

    def show(self, x, y):
        """
        overrides Computer.show and shows the same computer_graphics object only
        with a router's photo.
        :param x:
        :param y:
        :return: None
        """
        self.graphics = ComputerGraphics(x, y, self, IMAGES.COMPUTERS.ROUTER)
        self.loopback.connection.connection.show(self.graphics)

    def route_new_packets(self):
        """
        checks what are the new packets that arrived to this router, if they are not for it, routes them on.
        :return: None
        """
        new_packets = self.new_packets_since(self.last_route_check)
        self.last_route_check = MainLoop.instance.time()

        for packet, _, _ in new_packets:
            if "IP" in packet and not self.has_this_ip(packet["IP"].dst_ip) and "DHCP" not in packet:
                self.start_process(RoutePacket, packet)

    def logic(self):
        """Adds to the original logic of the Computer the ability to route packets."""
        super(Router, self).logic()

        self.route_new_packets()

        if self.is_dhcp_server and not self.is_process_running(DHCPServer):
            self.print("Started serving DHCP...")
            self.start_process(DHCPServer, self)

    def __repr__(self):
        """The string representation of the Router"""
        return f"Router(name={self.name}, Interfaces={self.interfaces})"

    @classmethod
    def from_dict_load(cls, dict_):
        """
        Load a computer from the dict that is saved into the files
        :param dict_:
        :return: Computer
        """
        returned = cls(
            dict_["name"],
            [Interface.from_dict_load(interface_dict) for interface_dict in dict_["interfaces"]],
            is_dhcp_server=dict_["is_dhcp_server"],
        )
        returned.routing_table = RoutingTable.from_dict_load(dict_["routing_table"])
        return returned
