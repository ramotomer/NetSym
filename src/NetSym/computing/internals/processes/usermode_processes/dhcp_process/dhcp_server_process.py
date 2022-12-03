from __future__ import annotations

from typing import TYPE_CHECKING, Optional, NamedTuple, Dict, List

from NetSym.address.ip_address import IPAddress
from NetSym.address.mac_address import MACAddress
from NetSym.computing.internals.processes.abstracts.process import Process, T_ProcessCode
from NetSym.computing.internals.sockets.raw_socket import RawSocket
from NetSym.consts import OPCODES, PORTS, PROTOCOLS
from NetSym.exceptions import *
from NetSym.packets.all import DHCP, BOOTP, IP, UDP
from NetSym.packets.usefuls.dns import T_Hostname
from NetSym.usefuls.funcs import get_the_one_with_raise

if TYPE_CHECKING:
    from NetSym.packets.packet import Packet
    from NetSym.computing.internals.network_interfaces.interface import Interface
    from NetSym.computing.computer import Computer


class DHCPData(NamedTuple):
    given_ip:         IPAddress
    given_gateway:    IPAddress
    given_dns_server: Optional[IPAddress]


class DHCPServerProcess(Process):
    """
    This is the process of discovering the DHCP client, receiving an IP address,
    acknowledging the IP that it offers you is fine, receiving an IP, gateway and DNS servers and updating the computer
    accordingly.

    The stages of DHCP are: discover, offer, request and pack
    """

    def __init__(self,
                 pid: int,
                 computer: Computer,
                 default_gateway: Computer,
                 dns_server: Optional[IPAddress] = None,
                 domain: Optional[T_Hostname] = None) -> None:
        """
        Initiates the process
        :param computer: The computer that runs this process.
        """
        super(DHCPServerProcess, self).__init__(pid, computer)

        self.default_gateway = default_gateway
        # ^ a `Computer` that is the default gateway of the subnets this server serves.

        self.dns_server = dns_server
        self.domain = domain

        self.interface_to_dhcp_data: Dict[Interface, DHCPData] = {}
        # ^ a mapping for each interface of the server to a ip_layer that it packs for its clients.
        self.update_server_data()

        self.in_session_with: Dict[MACAddress, IPAddress] = {}  # {mac : offered_ip}

        self.sockets: List[RawSocket] = []

    def update_server_data(self) -> None:
        """
        It updates the `self.interface_to_dhcp_data` dictionary according to this computer's interfaces.
        This is called if for example one of the computer's interfaces is updated in the middle of the process.
        :return: None
        """
        self.interface_to_dhcp_data = {
            interface: DHCPData(IPAddress.copy(interface.get_ip()),
                                self.default_gateway.same_subnet_interfaces(interface.get_ip())[0].get_ip(), None)
            for interface in self.computer.interfaces if interface.has_ip()
        }

    def raise_on_unknown_packet(self, packet: Packet, interface: Interface) -> None:
        """When a DHCP packet with an unknown opcode is received"""
        raise UnknownPacketTypeError(f"DHCP type unknown, {packet['DHCP'].parsed_options.message_type}")

    @staticmethod
    def build_dhcp_offer(client_mac: MACAddress,
                         offered_ip: IPAddress,
                         interface: Interface) -> Packet:
        return interface.ethernet_wrap(client_mac,
                                       IP(src_ip=str(interface.ip), dst_ip=str(offered_ip), ttl=PROTOCOLS.DHCP.DEFAULT_TTL) /
                                       UDP(src_port=PORTS.DHCP_SERVER, dst_port=PORTS.DHCP_CLIENT) /
                                       BOOTP(opcode=OPCODES.BOOTP.REPLY,
                                             client_mac=client_mac.as_bytes(),
                                             your_ip=str(offered_ip),
                                             server_ip=str(interface.ip)) /
                                       DHCP(options=[
                                           ('message-type', OPCODES.DHCP.OFFER),
                                           ('subnet_mask', str(IPAddress.mask_from_number(interface.get_ip().subnet_mask))),
                                           ('server_id', str(interface.ip)),
                                       ]))

    @staticmethod
    def build_dhcp_pack(client_mac: MACAddress,
                        offered_ip: IPAddress,
                        offered_gateway: IPAddress,
                        session_interface: Interface,
                        dns_server: Optional[IPAddress] = None,
                        domain: Optional[T_Hostname] = None) -> Packet:
        """
        Sends a `DHCP_PACK` that tells the DHCP client all of the new ip_layer it needs to update (IP, gateway, DNS)
        :param domain:
        :param dns_server: the domain name server to be supplied to clients
        :param client_mac: The `MACAddress` of the client.
        :param session_interface: The `Interface` that is running the session with the client.
        :param offered_ip: The `IPAddress` offered to the client
        :param offered_gateway: The `IPAddress` of the gateway which is offered to the client
        :return:
        """
        options = [
            ('message-type',   OPCODES.DHCP.PACK),
            ('router',         str(offered_gateway)),
            *([('name_server', str(dns_server))] if dns_server is not None else []),
            *([('domain',      str(domain))] if domain is not None else []),
        ]

        return session_interface.ethernet_wrap(client_mac,
                                               IP(src_ip=str(session_interface.ip), dst_ip=str(offered_ip), ttl=PROTOCOLS.DHCP.DEFAULT_TTL) /
                                               UDP(src_port=PORTS.DHCP_SERVER, dst_port=PORTS.DHCP_CLIENT) /
                                               BOOTP(opcode=OPCODES.BOOTP.REPLY,
                                                     client_mac=client_mac.as_bytes(),
                                                     your_ip=str(offered_ip)) /
                                               DHCP(options=options))

    def send_pack(self, request_packet: Packet, interface: Interface) -> None:
        """
        Sends the `DHCP_PACK` packet to the destination with all of the details the client had requested.
        """
        client_mac = request_packet["Ether"].src_mac

        socket = get_the_one_with_raise(self.sockets, lambda s: bool(s.interface == interface), ThisCodeShouldNotBeReached)
        socket.send(self.build_dhcp_pack(
            client_mac,
            offered_ip=self.in_session_with[client_mac],
            offered_gateway=self.interface_to_dhcp_data[interface].given_gateway,
            session_interface=interface,
            dns_server=self.dns_server,
            domain=self.domain,
        ))
        del self.in_session_with[client_mac]

    def send_offer(self, discover_packet: Packet, interface: Interface) -> None:
        """
        This is called when a Discover was received, it sends a `DHCP_OFFER` to the asking computer.
        with an offer for an ip address.
        :param discover_packet: a `Packet` object which is a `DHCP_DISCOVER`
        :param interface: the `Interface` that is currently serving the DHCP.
        """
        client_mac = discover_packet["Ether"].src_mac
        offered = self.offer_ip(interface)

        self.in_session_with[client_mac] = IPAddress.copy(offered)
        socket = get_the_one_with_raise(self.sockets, lambda s: bool(s.interface == interface), ThisCodeShouldNotBeReached)
        socket.send(self.build_dhcp_offer(client_mac, offered, interface))

    def offer_ip(self, interface: Interface) -> IPAddress:
        """
        Offers the next available IP address for a new client, based on the `Interface` that is serving the DHCP.
        :param interface: the `Interface` that the request came from (to know the subnet)
        :return: The offered `IPAddress` object.
        """
        try:
            offered = self.interface_to_dhcp_data[interface].given_ip
            offered.increase()
            return IPAddress.copy(offered)
        except KeyError:  # if the interface was created after the start of this process.
            if not interface.has_ip():
                raise AddressError("The interface cannot serve DHCP because it has no IP address!")

            self.interface_to_dhcp_data[interface] = DHCPData(IPAddress.copy(interface.get_ip()),
                                                              self.default_gateway.same_subnet_interfaces(interface.get_ip())[0].get_ip(), None)
            self._bind_interface_to_socket(interface)
            return self.offer_ip(interface)

    def code(self) -> T_ProcessCode:
        """
        This is main code of the DHCP server.
        Waits for a DHCP packet for the running computer and runs the appropriate command as a DHCP Server.
        :return: None
        """
        for interface in self.computer.interfaces:
            self._bind_interface_to_socket(interface)

        while True:
            ready_socket = yield from self.computer.select_with_timeout(self.sockets, timeout=PROTOCOLS.DHCP.NEW_INTERFACE_DETECTION_TIMEOUT)
            self._detect_new_interfaces()
            if ready_socket is None:
                continue  # This means `select` ended due to timeout!

            received_packets = ready_socket.receive()

            for received_packet in received_packets:
                for packet, packet_metadata in received_packet.packets.items():
                    interface = packet_metadata.interface
                    if not interface.has_ip():
                        self.computer.print("Cannot server DHCP without an IP address!")
                        continue
                    {OPCODES.DHCP.DISCOVER: self.send_offer,
                     OPCODES.DHCP.REQUEST: self.send_pack}.get(
                        packet["DHCP"].parsed_options.message_type,
                        self.raise_on_unknown_packet
                    )(packet, interface)

    def _bind_interface_to_socket(self, interface: Interface) -> None:
        """
        Takes in an `Interface` and gets a raw socket from the operation system of the computer
        Binds the socket to the interface with a DHCP packet filter
        """
        socket = self.computer.get_raw_socket(self.pid)
        socket.bind(lambda p: "DHCP" in p, interface)
        self.sockets.append(socket)

    def _detect_new_interfaces(self) -> None:
        """
        Goes over the interfaces of the computer - if there is an interface
        that does not have a raw-socket bound to it, generate and bind one to it.
        """
        for interface in self.computer.interfaces:
            if not any(socket.interface == interface for socket in self.sockets):
                # the interface has no socket - it is new
                self._bind_interface_to_socket(interface)

    def __repr__(self) -> str:
        """The string representation of the the process"""
        return "dhcpsd"
