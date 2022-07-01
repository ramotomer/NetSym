from computing.computer import Computer
from computing.interface import Interface
from computing.internals.filesystem.filesystem import Filesystem
from computing.internals.processes.kernelmode_processes.route_packet_process import RoutePacket
from computing.internals.processes.usermode_processes.dhcp_process import DHCPServer
from computing.internals.routing_table import RoutingTable
from consts import *
from gui.main_loop import MainLoop
from gui.tech.computer_graphics import ComputerGraphics


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
                self.process_scheduler.start_kernelmode_process(RoutePacket, packet)

    def logic(self):
        """Adds to the original logic of the Computer the ability to route packets."""
        super(Router, self).logic()

        self.route_new_packets()

        if self.is_dhcp_server and not self.process_scheduler.is_usermode_process_running_by_type(DHCPServer):
            self.print("Started serving DHCP...")
            self.process_scheduler.start_usermode_process(DHCPServer, self)

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
            tuple([Interface.from_dict_load(interface_dict) for interface_dict in dict_["interfaces"]]),
            is_dhcp_server=dict_["is_dhcp_server"],
        )
        returned.routing_table = RoutingTable.from_dict_load(dict_["routing_table"])
        returned.filesystem = Filesystem.from_dict_load(dict_["filesystem"])
        returned.initial_size = dict_["size"]
        return returned
