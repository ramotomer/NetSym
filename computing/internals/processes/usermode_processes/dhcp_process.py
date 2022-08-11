from collections import namedtuple

from address.ip_address import IPAddress
from address.mac_address import MACAddress
from computing.internals.processes.abstracts.process import Process
from consts import OPCODES, COMPUTER, PORTS, PROTOCOLS
from exceptions import *
from packets.all import DHCP, BOOTP, IP, UDP
from usefuls.funcs import get_the_one

DHCPData = namedtuple("DHCPData", [
    "given_ip",
    "given_gateway",
    "given_dns_server",
])


class DHCPClient(Process):
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

    def __init__(self, pid, computer):
        super(DHCPClient, self).__init__(pid, computer)
        self.sockets = []

    def update_routing_table(self, session_interface, dhcp_pack):
        """
        Receive the interface that runs the session with the server and the DHCP pack packet that it sent,
        update the routing table accordingly.
        :param session_interface: an `Interface` object.
        :param dhcp_pack: a `Packet` object that contains DHCP.
        :return: None
        """
        given_ip = dhcp_pack["DHCP"].data.given_ip
        session_interface.ip = given_ip
        self.computer.update_routing_table()
        self.computer.set_default_gateway(dhcp_pack["DHCP"].data.given_gateway, given_ip)
        self.computer.graphics.update_text()

    # def validate_offer(self, dhcp_offer):
    #     """
    #     Receives a `Packet` parses it, validates it and returns the server MAC address.
    #     :return: a `MACAddress` object.
    #     """
    #     server_mac = dhcp_offer["Ethernet"].src_mac
    #     offered_ip = dhcp_offer["DHCP"].data.given_ip
    #     if not self.computer.validate_dhcp_given_ip(offered_ip):
    #         raise AddressError("did not validate IP from DHCP server!!! (probably two interfaces have the same address)")
    #     return server_mac

    @staticmethod
    def build_dhcp_discover(interface):
        return interface.ethernet_wrap(MACAddress.broadcast(),
                                       IP(src_ip=str(IPAddress.no_address()), dst_ip=str(IPAddress.broadcast()), ttl=PROTOCOLS.DHCP.DEFAULT_TTL) /
                                       UDP(src_port=PORTS.DHCP_CLIENT, dst_port=PORTS.DHCP_SERVER) /
                                       BOOTP(opcode=OPCODES.BOOTP.REQUEST, client_mac=interface.mac.as_bytes()) /
                                       DHCP(options=[('message-type', OPCODES.DHCP.DISCOVER)]))

    @staticmethod
    def build_dhcp_request(server_mac, session_interface, server_ip, requested_ip):
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

    def code(self):
        """
        This is main code of the DHCP client.
        :return: None
        """
        for interface in self.computer.interfaces:
            socket = self.computer.get_socket(self.pid, kind=COMPUTER.SOCKETS.TYPES.SOCK_RAW)
            socket.bind(lambda p: "DHCP" in p and p["Ethernet"].dst_mac in self.computer.macs, interface)
            self.sockets.append(socket)
        self.computer.print("Asking For DHCP...")
        for socket in self.sockets:
            socket.send(self.build_dhcp_discover(socket.interface))

        ready_socket = yield from self.computer.select(self.sockets)
        dhcp_offer, session_interface = ready_socket.receive()[0].packet_and_interface
        # TODO: validate offer
        session_socket = get_the_one(self.sockets, lambda s: s.interface == session_interface, ThisCodeShouldNotBeReached)

        session_socket.send(self.build_dhcp_request(
            server_mac=dhcp_offer["Ethernet"].src_mac,
            session_interface=session_interface,
            server_ip=dhcp_offer["IP"].src_ip,
            requested_ip=dhcp_offer["BOOTP"].your_ip
        ))
        yield from session_socket.block_until_received()
        dhcp_pack = session_socket.receive()[0]

        self.update_routing_table(session_interface, dhcp_pack.packet)
        self.computer.arp_grat(session_interface)
        self.computer.print("Got Address from DHCP!")

    def __repr__(self):
        """The string representation of the the process"""
        return "dhcpcd"


class DHCPServer(Process):
    """
    This is the process of discovering the DHCP client, receiving an IP address,
    acknowledging the IP that it offers you is fine, receiving an IP, gateway and DNS servers and updating the computer
    accordingly.

    The stages of DHCP are: discover, offer, request and pack
    """

    def __init__(self, pid, computer, default_gateway):
        """
        Initiates the process
        :param computer: The computer that runs this process.
        """
        super(DHCPServer, self).__init__(pid, computer)

        self.default_gateway = default_gateway
        # ^ a `Computer` that is the default gateway of the subnets this server serves.

        self.interface_to_dhcp_data = {}  # interface : DHCPData
        # ^ a mapping for each interface of the server to a ip_layer that it packs for its clients.
        self.update_server_data()

        self.in_session_with = {}  # {mac : offered_ip}

        self.sockets = []

    def update_server_data(self):
        """
        It updates the `self.interface_to_dhcp_data` dictionary according to this computer's interfaces.
        This is called if for example one of the computer's interfaces is updated in the middle of the process.
        :return: None
        """
        self.interface_to_dhcp_data = {
            interface: DHCPData(IPAddress.copy(interface.ip),
                                self.default_gateway.same_subnet_interfaces(interface.ip)[0].ip, None) \
            for interface in self.computer.interfaces if interface.has_ip()
        }

    def raise_on_unknown_packet(self, packet, interface):
        """When a DHCP packet with an unknown opcode is received"""
        raise UnknownPacketTypeError("DHCP type unknown")

    @staticmethod
    def build_dhcp_offer(client_mac, offered_ip, interface):
        return interface.ethernet_wrap(client_mac,
                                       IP(interface.ip, offered_ip, PROTOCOLS.DHCP.DEFAULT_TTL) /
                                       UDP(PORTS.DHCP_SERVER, PORTS.DHCP_CLIENT) /
                                       BOOTP(opcode=OPCODES.BOOTP.REPLY,
                                             client_mac=client_mac.as_bytes(),
                                             your_ip=offered_ip,
                                             server_ip=interface.ip) /
                                       DHCP(options=[
                                           ('message-type', OPCODES.DHCP.PACK),
                                           ('subnet_mask', IPAddress.mask_from_number(interface.ip.subnet_mask)),
                                           ('server_id', str(interface.ip)),
                                       ]))

    @staticmethod
    def build_dhcp_pack(client_mac, offered_ip, offered_gateway, session_interface):
        """
        Sends a `DHCP_PACK` that tells the DHCP client all of the new ip_layer it needs to update (IP, gateway, DNS)
        :param client_mac: The `MACAddress` of the client.
        :param session_interface: The `Interface` that is running the session with the client.
        :param offered_ip: The `IPAddress` offered to the client
        :param offered_gateway: The `IPAddress` of the gateway which is offered to the client
        :return:
        """
        return session_interface.ethernet_wrap(client_mac,
                                               IP(src_ip=session_interface.ip, dst_ip=str(offered_ip), ttl=PROTOCOLS.DHCP.DEFAULT_TTL) /
                                               UDP(PORTS.DHCP_SERVER, PORTS.DHCP_CLIENT) /
                                               BOOTP(opcode=OPCODES.BOOTP.REPLY,
                                                     client_mac=client_mac.as_bytes(),
                                                     your_ip=str(offered_ip),
                                                     gateway_ip=str(offered_gateway)) /
                                               DHCP(options=[
                                                   ('message-type', OPCODES.DHCP.PACK)
                                               ]))

    def send_pack(self, request_packet, interface):
        """
        Sends the `DHCP_PACK` packet to the destination with all of the details the client had requested.
        """
        client_mac = request_packet["Ethernet"].src_mac

        socket = get_the_one(self.sockets, lambda s: s.interface == interface, ThisCodeShouldNotBeReached)
        socket.send(self.build_dhcp_pack(client_mac,
                                         offered_ip=self.in_session_with[client_mac],
                                         offered_gateway=self.interface_to_dhcp_data[interface].given_gateway,
                                         session_interface=interface)
                    )
        del self.in_session_with[client_mac]

    def send_offer(self, discover_packet, interface):
        """
        This is called when a Discover was received, it sends a `DHCP_OFFER` to the asking computer.
        with an offer for an ip address.
        :param discover_packet: a `Packet` object which is a `DHCP_DISCOVER`
        :param interface: the `Interface` that is currently serving the DHCP.
        """
        client_mac = discover_packet["Ethernet"].src_mac
        offered = self.offer_ip(interface)

        self.in_session_with[client_mac] = IPAddress.copy(offered)
        socket = get_the_one(self.sockets, lambda s: s.interface == interface, ThisCodeShouldNotBeReached)
        socket.send(self.build_dhcp_offer(client_mac, offered, interface))

    def offer_ip(self, interface):
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
            self.interface_to_dhcp_data[interface] = DHCPData(IPAddress.copy(interface.ip),
                                                              self.default_gateway.same_subnet_interfaces(interface.ip)[0].ip, None)
            self._bind_interface_to_socket(interface)
            return self.offer_ip(interface)

    def code(self):
        """
        This is main code of the DHCP server.
        Waits for a DHCP packet for the running computer and runs the appropriate command as a DHCP Server.
        :return: None
        """
        for interface in self.computer.interfaces:
            self._bind_interface_to_socket(interface)

        while True:
            ready_socket = yield from self.computer.select(self.sockets, timeout=0.5)
            self._detect_new_interfaces()
            if ready_socket is None:
                continue

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

    def _bind_interface_to_socket(self, interface):
        """
        Takes in an `Interface` and gets a raw socket from the operation system of the computer
        Binds the socket to the interface with a DHCP packet filter
        """
        socket = self.computer.get_socket(self.pid, kind=COMPUTER.SOCKETS.TYPES.SOCK_RAW)
        socket.bind(lambda p: "DHCP" in p, interface)
        self.sockets.append(socket)

    def _detect_new_interfaces(self):
        """
        Goes over the interfaces of the computer - if there is an interface
        that does not have a raw-socket bound to it, generate and bind one to it.
        """
        for interface in self.computer.interfaces:
            if not any(socket.interface == interface for socket in self.sockets):
                # the interface has no socket - it is new
                self._bind_interface_to_socket(interface)

    def __repr__(self):
        """The string representation of the the process"""
        return "dhcpsd"
