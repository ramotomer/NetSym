from __future__ import annotations

from typing import TYPE_CHECKING

from NetSym.address.ip_address import IPAddress
from NetSym.address.mac_address import MACAddress
from NetSym.computing.internals.processes.abstracts.process import Process, T_ProcessCode
from NetSym.consts import OPCODES, PORTS, PROTOCOLS
from NetSym.exceptions import *
from NetSym.packets.all import DHCP, BOOTP, IP, UDP
from NetSym.usefuls.funcs import get_the_one

if TYPE_CHECKING:
    from NetSym.packets.packet import Packet
    from NetSym.computing.internals.interface import Interface
    from NetSym.computing.computer import Computer


class DHCPClientProcess(Process):
    """
    This is the process of discovering the DHCP server, receiving an IP address,
    acknowledging the IP that it offers you is fine, receiving an IP, gateway and DNS servers and updating the computer
    accordingly.

    Reminder of how DHCP works:
    there are four stages:
        1) DHCP discover - the client sends a broadcast packet to know who is the DHCP server
        2) DHCP offer - the server offers the client an IP address
        3) DHCP request - the client accepts the IP address that was offered to it and requests it for itself.
        4) DHCP pack - the server sends the final IP address, default gateway and DNS server to the client.
    """

    # __init__ is inherited from the parent class

    def __init__(self, pid: int, computer: Computer) -> None:
        super(DHCPClientProcess, self).__init__(pid, computer)
        self.sockets = []

    def update_routing_table(self, session_interface: Interface, dhcp_pack: Packet) -> None:
        """
        Receive the interface that runs the session with the server and the DHCP pack packet that it sent,
        update the routing table accordingly.
        :param session_interface: an `Interface` object.
        :param dhcp_pack: a `Packet` object that contains DHCP.
        :return: None
        """
        given_ip = dhcp_pack["BOOTP"].your_ip
        session_interface.ip = given_ip
        self.computer.update_routing_table()
        self.computer.set_default_gateway(IPAddress(dhcp_pack["DHCP"].parsed_options.router), given_ip)

    @staticmethod
    def build_dhcp_discover(interface: Interface) -> Packet:
        return interface.ethernet_wrap(MACAddress.broadcast(),
                                       IP(src_ip=str(IPAddress.no_address()), dst_ip=str(IPAddress.broadcast()), ttl=PROTOCOLS.DHCP.DEFAULT_TTL) /
                                       UDP(src_port=PORTS.DHCP_CLIENT, dst_port=PORTS.DHCP_SERVER) /
                                       BOOTP(opcode=OPCODES.BOOTP.REQUEST, client_mac=interface.mac.as_bytes()) /
                                       DHCP(options=[('message-type', OPCODES.DHCP.DISCOVER)]))

    @staticmethod
    def build_dhcp_request(server_mac: MACAddress,
                           session_interface: Interface,
                           server_ip: IPAddress,
                           requested_ip: IPAddress) -> Packet:
        """
        Sends a `DHCP_REQUEST` that confirms the address that the server had offered.
        This is sent by the DHCP client.
        :param server_mac: The `MACAddress` of the DHCP server.
        :param session_interface: The `Interface` that is running the session with the server.
        :param server_ip: The `IPAddress` of the server
        :param requested_ip: The `IPAddress` the server has offered - and the client now requests
        """
        return session_interface.ethernet_wrap(server_mac,
                                               IP(src_ip=str(IPAddress.no_address()),
                                                  dst_ip=str(IPAddress.broadcast()),
                                                  ttl=PROTOCOLS.DHCP.DEFAULT_TTL) /
                                               UDP(src_port=PORTS.DHCP_CLIENT, dst_port=PORTS.DHCP_SERVER) /
                                               BOOTP(opcode=OPCODES.BOOTP.REQUEST, client_mac=session_interface.mac.as_bytes()) /
                                               DHCP(options=[('message-type', OPCODES.DHCP.REQUEST),
                                                             ('requested_addr', requested_ip),
                                                             ('server_id', server_ip)]))

    def code(self) -> T_ProcessCode:
        """
        This is main code of the DHCP client.
        :return: None
        """
        for interface in self.computer.interfaces:
            socket = self.computer.get_raw_socket(self.pid)
            socket.bind(lambda p: "DHCP" in p and p["Ether"].dst_mac in self.computer.macs, interface)
            self.sockets.append(socket)
        self.computer.print("Asking For DHCP...")
        for socket in self.sockets:
            socket.send(self.build_dhcp_discover(socket.interface))

        ready_socket = yield from self.computer.select(self.sockets)
        dhcp_offer, session_interface = ready_socket.receive()[0].packet_and_interface
        # TODO: validate offer
        session_socket = get_the_one(self.sockets, lambda s: s.interface == session_interface, ThisCodeShouldNotBeReached)

        session_socket.send(self.build_dhcp_request(
            session_interface= session_interface,
            server_mac=        dhcp_offer["Ether"].src_mac,
            server_ip=         dhcp_offer["IP"].src_ip,
            requested_ip=      dhcp_offer["BOOTP"].your_ip
        ))
        yield from session_socket.block_until_received()
        dhcp_pack = session_socket.receive()[0]

        self.update_routing_table(session_interface, dhcp_pack.packet)
        self.computer.dns_server = dhcp_pack.packet["DHCP"].parsed_options.get('name_server', None)
        self.computer.domain =     dhcp_pack.packet["DHCP"].parsed_options.get('domain', None)
        # TODO ^ this does not work if the router does not supply them :(
        self.computer.arp_grat(session_interface)
        self.computer.print("Got Address from DHCP!")

    def __repr__(self) -> str:
        """The string representation of the the process"""
        return "dhcpcd"
