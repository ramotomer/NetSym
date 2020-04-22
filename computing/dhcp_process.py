from computing.process import Process, WaitingFor, ReturnedPacket
from usefuls import get_the_one
from exceptions import *
from consts import *
from packets.dhcp import DHCPData
from address.ip_address import IPAddress


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

    def update_interface_from_dhcp_pack(self, interface, dhcp_pack_returned_packet):
        """
        Receives a `ReturnedPacket` object with a DHCP_PACK packet and receives an interface. updates the details of the
        interface by the information of the DHCP_PACK (ip, gateway and dns server)
        :param interface: The interface of the computer that operated the communication to the server
        :param dhcp_pack_returned_packet: a `ReturnedPacket` obejct with the DHCP_PACK packet inside
        :return: None
        """
        dhcp_pack = dhcp_pack_returned_packet.packet
        interface.ip, self.computer.default_gateway, _ = dhcp_pack["DHCP"].data
        self.computer.graphics.update_text()
        # TODO: when implementing dns servers, change the _ to something like `sending_interface.dns_server`

    def validate_offer(self, dhcp_offer_packet):
        """
        Receives a `ReturnedPacket` namedtuple (from the 'process.py' file), parses it, validates it and returns the details about it.
        :return: a tuple with the following details: (<the mac of the server>, <the interface the packet was received from>)
        """
        dhcp_offer = dhcp_offer_packet.packet
        server_mac = dhcp_offer["Ethernet"].src_mac
        offered_ip = dhcp_offer["DHCP"].data.given_ip
        sending_interface = get_the_one(self.computer.interfaces, lambda i: i.mac == dhcp_offer["Ethernet"].dst_mac,
                                        NoSuchInterfaceError)
        if not sending_interface.validate_DHCP_given_ip(offered_ip):
            # if in the future you add actually `validate_DHCP_given_ip`, maybe change this raising (so you wont crash)
            raise AddressError("did not validate IP from DHCP server!")
        return server_mac, sending_interface

    def code(self):
        """
        This is main code of the DHCP client.
        :return: None
        """
        for interface in self.computer.interfaces:
            interface.send_dhcp_discover()
        dhcp_offer_packet = ReturnedPacket()
        yield WaitingFor(dhcp_for(self.computer.macs), dhcp_offer_packet)

        server_mac, sending_interface = self.validate_offer(dhcp_offer_packet)

        sending_interface.send_dhcp_request(server_mac)
        dhcp_pack_packet = ReturnedPacket()
        yield WaitingFor(dhcp_for([sending_interface.mac]), dhcp_pack_packet)

        self.update_interface_from_dhcp_pack(sending_interface, dhcp_pack_packet)
        sending_interface.arp_grat()

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

        self.interface_to_dhcp_data = {interface: DHCPData(IPAddress.copy(interface.ip), default_gateway.same_subnet_interfaces(interface.ip)[0].ip, None) \
                                       for interface in self.computer.interfaces if interface.has_ip()}  # interface : DHCPData
        # ^ a mapping for each interface of the server to a data that it packs for its clients.

        self.default_gateway = default_gateway  # a `Computer` that is the default gateway of the subnets this server serves.
        self.in_session_with = {}  # mac : offered_ip

        self.actions = {DHCP_DISCOVER: self.send_offer, DHCP_REQUEST: self.send_pack}
        # ^ a dictionary of what to do with any packet that is received to this process.

    def unknown_packet(self, packet, interface):
        """When a DHCP packet with an unknown opcode is received"""
        raise UnknownPacketTypeError("DHCP type unknown")

    def send_pack(self, request_packet, interface):
        """
        Sends the `DHCP_PACK` packet to the destination with all of the details the client had requested.
        :param request_packet: a `ReturnedPacket` with the packet.
        """
        client_mac = request_packet["Ethernet"].src_mac
        sending_interface = interface

        ip = self.in_session_with[client_mac]
        gateway = self.default_gateway.same_subnet_interfaces(sending_interface.ip)[0].ip
        dns_server = None   # TODO: change this for serving DNS in the future!

        sending_interface.send_dhcp_pack(client_mac, DHCPData(ip, gateway, dns_server))
        del self.in_session_with[client_mac]

    def send_offer(self, discover_packet, interface):
        """
        This is called when a Discover was received, it sends a `DHCP_OFFER` to the asking computer.
        with an offer for an ip address.
        :param discover_packet: a `Packet` object which is a `DHCP_DISCOVER`
        :param interface: the `Interface` that is currently serving the DHCP.
        """
        client_mac, dst_mac = discover_packet["Ethernet"].src_mac, discover_packet["Ethernet"].dst_mac
        offered = self.offer_ip(interface)

        self.in_session_with[client_mac] = IPAddress.copy(offered)
        interface.send_dhcp_offer(client_mac, offered)

    def offer_ip(self, interface):
        """
        Offers the next available IP address for a new client, based on the `Interface` that is serving the DHCP.
        :param interface: the `Interface` that the request came from (to know the subnet)
        :return: The offered `IPAddress` object.
        """
        try:
            offered = self.interface_to_dhcp_data[interface].given_ip
            offered.increase()
            return offered
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
            yield WaitingFor(lambda p: "DHCP" in p, received_packets)
            counter = 0
            for packet, interface in received_packets.packets.items():
                self.actions.get(packet["DHCP"].opcode, self.unknown_packet)(packet, interface)
                counter += 1

    def __repr__(self):
        """The string representation of the the process"""
        return "DHCP server process"
