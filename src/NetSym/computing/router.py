from __future__ import annotations

from typing import Optional, Iterable, Dict, TYPE_CHECKING

from NetSym.computing.computer import Computer
from NetSym.computing.internals.filesystem.filesystem import Filesystem
from NetSym.computing.internals.network_data_structures.routing_table import RoutingTable
from NetSym.computing.internals.network_interfaces.cable_network_interface import CableNetworkInterface
from NetSym.computing.internals.processes.kernelmode_processes.route_packet_process import RoutePacket
from NetSym.computing.internals.processes.usermode_processes.dhcp_process.dhcp_server_process import DHCPServerProcess
from NetSym.consts import OS
from NetSym.gui.main_loop import MainLoop

if TYPE_CHECKING:
    from NetSym.computing.internals.network_interfaces.network_interface import NetworkInterface


class Router(Computer):
    """
    This is a router class.
    It has one interface in each subnet that it routes.
    It has routing table which tells it where to route his packets to. It contains a subnet mask mapped to an interface
    (any packet that fits the subnet mask of the interface goes to that interface)
    """
    def __init__(self,
                 name: Optional[str] = None,
                 interfaces: Optional[Iterable[NetworkInterface]] = None,
                 is_dhcp_server: bool = True) -> None:
        """
        Initiates a router with no IP addresses.
        """
        if interfaces is None:
            interfaces = [CableNetworkInterface(ip='192.168.1.1')]

        super(Router, self).__init__(name, OS.SOLARIS, None, *interfaces)
        self.routing_table = RoutingTable.create_default(self.ips, False)

        self.last_route_check = MainLoop.get_time()

        self.is_dhcp_server = is_dhcp_server

    def route_new_packets(self) -> None:
        """
        checks what are the new packets that arrived to this router, if they are not for it, routes them on.
        :return: None
        """
        new_packets = self.new_packets_since(self.last_route_check, is_raw=True)
        self.last_route_check = MainLoop.get_time()

        for received_packet in new_packets:
            packet, interface = received_packet.packet_and_interface
            if "IP" in packet and \
                    not self.has_this_ip(packet["IP"].dst_ip) and \
                    "DHCP" not in packet and \
                    packet["Ether"].dst_mac == interface.mac:
                self.process_scheduler.start_kernelmode_process(RoutePacket, packet)

    def logic(self) -> None:
        """Adds to the original logic of the Computer the ability to route packets."""
        super(Router, self).logic()

        self.route_new_packets()

        if self.is_dhcp_server and not self.process_scheduler.is_usermode_process_running_by_type(DHCPServerProcess):
            self.print("Started serving DHCP...")
            self.process_scheduler.start_usermode_process(DHCPServerProcess, self)

    def __repr__(self) -> str:
        """The string representation of the Router"""
        return f"Router(name={self.name}, Interfaces={self.interfaces})"

    @classmethod
    def from_dict_load(cls, dict_: Dict) -> Router:
        """
        Load a computer from the dict that is saved into the files
        :param dict_:
        :return: Computer
        """
        returned = cls(
            dict_["name"],
            tuple(cls._interfaces_from_dict(dict_)),
            is_dhcp_server=dict_["is_dhcp_server"],
        )
        returned.routing_table = RoutingTable.from_dict_load(dict_["routing_table"])
        returned.filesystem = Filesystem.from_dict_load(dict_["filesystem"])
        # returned.scale_factor = dict_["scale_factor"]
        return returned
