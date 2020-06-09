from address.ip_address import IPAddress
from consts import *
from exceptions import *
from packets.dhcp import DHCPData
from processes.process import Process, WaitingForPacket, ReturnedPacket


def dhcp_for(mac_addresses):
    """Returns a function that receives a packet and returns whether it is a dhcp packet for any of the `mac_addresses`"""
    def tester(packet):
        return ("DHCP" in packet) and any(packet["Ethernet"].dst_mac == mac for mac in mac_addresses)
    return tester


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

    def validate_offer(self, dhcp_offer):
        """
        Receives a `Packet` parses it, validates it and returns the server MAC address.
        :return: a `MACAddress` object.
        """
        server_mac = dhcp_offer["Ethernet"].src_mac
        offered_ip = dhcp_offer["DHCP"].data.given_ip
        if not self.computer.validate_dhcp_given_ip(offered_ip):
            raise AddressError("did not validate IP from DHCP server!!! (probably two interfaces have the same address)")
        return server_mac

    def code(self):
        """
        This is main code of the DHCP client.
        :return: None
        """
        self.computer.print("Asking For DHCP...")
        self.computer.send_dhcp_discover()
        dhcp_offer = ReturnedPacket()
        yield WaitingForPacket(dhcp_for(self.computer.macs), dhcp_offer)

        packet, session_interface = dhcp_offer.packet_and_interface
        server_mac = self.validate_offer(packet)

        self.computer.send_dhcp_request(server_mac, session_interface)
        dhcp_pack = ReturnedPacket()
        yield WaitingForPacket(dhcp_for([session_interface.mac]), dhcp_pack)

        self.update_routing_table(session_interface, dhcp_pack.packet)
        self.computer.arp_grat(session_interface)
        self.computer.print("Got Address from DHCP!")

    def __repr__(self):
        """The string representation of the the process"""
        return "DHCP client process"


class DHCPServer(Process):
    """
    This is the process of discovering the DHCP client, receiving an IP address,
    acknowledging the IP that it offers you is fine, receiving an IP, gateway and DNS servers and updating the computer
    accordingly.

    The stages of DHCP are: discover, offer, request and pack
    """
    def __init__(self, computer, default_gateway):
        """
        Initiates the process
        :param computer: The computer that runs this process.
        """
        super(DHCPServer, self).__init__(computer)

        self.default_gateway = default_gateway  # a `Computer` that is the default gateway of the subnets this server serves.

        self.interface_to_dhcp_data = {} # interface : DHCPData
        # ^ a mapping for each interface of the server to a ip_layer that it packs for its clients.
        self.update_server_data()

        self.in_session_with = {}  # {mac : offered_ip}

        self.actions = {DHCP_DISCOVER: self.send_offer, DHCP_REQUEST: self.send_pack}
        # ^ a dictionary of what to do with any packet that is received to this process.

    def update_server_data(self):
        """
        It updates the `self.interface_to_dhcp_data` dictionary according to this comptuer's interfaces.
        This is called if for example one of the computer's interfaces is updated in the middle of the process.
        :return: None
        """
        self.interface_to_dhcp_data = {
            interface: DHCPData(IPAddress.copy(interface.ip),
                                self.default_gateway.same_subnet_interfaces(interface.ip)[0].ip, None) \
            for interface in self.computer.interfaces if interface.has_ip()
        }

    def unknown_packet(self, packet, interface):
        """When a DHCP packet with an unknown opcode is received"""
        raise UnknownPacketTypeError("DHCP type unknown")

    def send_pack(self, request_packet, interface):
        """
        Sends the `DHCP_PACK` packet to the destination with all of the details the client had requested.
        :param request_packet: a `ReturnedPacket` with the packet.
        """
        client_mac = request_packet["Ethernet"].src_mac

        ip = self.in_session_with[client_mac]
        gateway = self.interface_to_dhcp_data[interface].given_gateway
        dns_server = None

        self.computer.send_dhcp_pack(client_mac, DHCPData(ip, gateway, dns_server), interface)
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
        self.computer.send_dhcp_offer(client_mac, offered, interface)

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
            self.interface_to_dhcp_data[interface] = DHCPData(IPAddress.copy(interface.ip), self.default_gateway.same_subnet_interfaces(interface.ip)[0].ip, None)
            return self.offer_ip(interface)

    def code(self):
        """
        This is main code of the DHCP server.
        Waits for a DHCP packet for the running computer and runs sthe appropriate command as a DHCP Server.
        :return: None
        """
        while True:
            received_packets = ReturnedPacket()
            yield WaitingForPacket(lambda p: "DHCP" in p, received_packets)

            if not self.computer.has_ip():
                self.computer.print("Cannot server DHCP without and IP address!")
                continue
            for packet, interface in received_packets.packets.items():
                self.actions.get(packet["DHCP"].opcode, self.unknown_packet)(packet, interface)

    def __repr__(self):
        """The string representation of the the process"""
        return "DHCP server process"
