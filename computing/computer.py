import random
from collections import namedtuple

from address.ip_address import IPAddress
from address.mac_address import MACAddress
from computing.interface import Interface
from computing.routing_table import RoutingTable, RoutingTableItem
from consts import *
from exceptions import *
from gui.main_loop import MainLoop
from gui.tech.computer_graphics import ComputerGraphics
from packets.arp import ARP
from packets.dhcp import DHCP, DHCPData
from packets.icmp import ICMP
from packets.ip import IP
from packets.tcp import TCP
from packets.udp import UDP
from processes.arp_process import ARPProcess
from processes.daytime_process import DAYTIMEServerProcess
from processes.dhcp_process import DHCPClient
from processes.dhcp_process import DHCPServer
from processes.ftp_process import FTPServerProcess
from processes.ping_process import SendPing
from usefuls import get_the_one

ARPCacheItem = namedtuple("ARPCacheItem", "mac time")
# ^ the values of the ARP cache of the computer (MAC address and creation time)
ReceivedPacket = namedtuple("ReceivedPacket", "packet time interface")
# ^ a packet that was received in this computer  (packet object, receiving time, interface packet is received on)
WaitingProcess = namedtuple("WaitingProcess", "process waiting_for")
# ^ a process that is currently waiting for a certain packet.


class Computer:
    """
    This is a base class for all of the machines that will operate on the screen
    in our little simulation.

    The computer mainly will be in charge of the logic in sending and receiving packets.
    (So answering ARPs and pings and Switching and Routing in the appropriate cases)
    The `logic` method is where all of this happens.

    The computer runs many `Process`-s that are all either currently running or waiting for a certain packet to arrive.
    """

    PORTS_TO_PROCESSES = {
        DAYTIME_PORT: DAYTIMEServerProcess,
        FTP_PORT: FTPServerProcess,
        SSH_PORT: None,
        HTTP_PORT: None,
        HTTPS_PORT: None,
    }

    def __init__(self, name=None, os=OS_WINDOWS, gateway=None, *interfaces):
        """
        Initiates a Computer object.
        :param name: the name of the computer which will be displayed next to it.
        :param os: The operation system of the computer.
        :param gateway: an IPAddress object which is the address of the computer's default gateway.
        :param interfaces: An interface list of the computer.
        """
        self.name = name if name is not None else self.random_name()
        self.os = os
        self.default_gateway = gateway  # an IPAddress object of the default gateway of this computer

        self.interfaces = list(interfaces)
        if not interfaces:
            self.interfaces = [Interface(MACAddress.randomac())]  # a list of all of the interfaces without the loopback
        self.packets_sniffed = 0
        self.loopback = Interface.loopback()

        self.arp_cache = {}  # a dictionary of {<ip address> : ARPCacheItem(<mac address>, <initiation time of this item>)
        self.routing_table = RoutingTable.create_default(self)  # a dictionary of {<ip address destination> : RoutingTableItem(<gateway IP>, <interface IP>)}
        self.received = []  # a list of the `ReceivedPacket` namedtuple-s that were received at this computer.

        self.waiting_processes = []  # a list of `WaitingProcess` namedtuple-s. If the process is new, its `WaitingProcess.waiting_for` should be None.
        self.process_last_check = MainLoop.instance.time()  # the last time that the waiting_processes were checked for 'can they run?'

        self.graphics = None
        # ^ The `GraphicsObject` of the computer, not initiated for now.

        self.is_powered_on = True

        self.packet_types_and_handlers = {
            "ARP": self._handle_arp,
            "ICMP": self._handle_ping,
            "TCP": self._handle_tcp,
        }

        self.open_ports = [] # a list of the ports that are open on this computer.

        MainLoop.instance.insert_to_loop_pausable(self.logic)
        # ^ the fact that it is 'pausable' means that when the space bar is pressed and the program pauses, this method does not run.

    @property
    def macs(self):
        """A list of all of the mac addresses this computer has (has a mac for each interfaces)"""
        return [interface.mac for interface in self.interfaces]

    @property
    def ips(self):
        """a list of all of the IP addresses this computer has (one for each interface)"""
        return [interface.ip for interface in self.interfaces if interface.ip is not None]

    @property
    def all_interfaces(self):
        """Returns the list of interfaces with the loopback"""
        return self.interfaces + [self.loopback]

    @classmethod
    def with_ip(cls, ip_address, name=None):
        """
        This is a constructor for a computer with a given IP address, defaults the rest of the properties.
        :param ip_address: an IP string that one wishes the new `Computer` to have.
        :return: a `Computer` object
        """
        computer = cls(name, OS_WINDOWS, None, Interface(MACAddress.randomac(), IPAddress(ip_address), "IHaveIP"))
        return computer

    @staticmethod
    def random_name():
        """
        Randomize a computer name based on his operating system.
        Theoretically can randomize the same name twice, but unlikely.
        :return: a random string that is the name.
        """
        return ''.join([random.choice(COMPUTER_NAMES), str(random.randint(0, 100))])

    def show(self, x, y):
        """
        This is called once to initiate the graphics of the computer.
        Gives it a `GraphicsObject`. (`ComputerGraphics`)
        :param x:
        :param y: Coordinates to initiate the `GraphicsObject` at.
        :return: None
        """
        self.graphics = ComputerGraphics(x, y, self, COMPUTER_IMAGE if not self.open_ports else SERVER_IMAGE)
        self.loopback.connection.connection.show(self.graphics)

    def print(self, string):
        """
        Prints out a string to the computer output.
        :param string: The string to print.
        :return: None
        """
        self.graphics.child_graphics_objects.console.write(string)

    def power(self):
        """Powers the computer on or off."""

        self.waiting_processes.clear()

        self.is_powered_on = not self.is_powered_on
        for interface in self.all_interfaces:
            interface.is_powered_on = self.is_powered_on
        self.graphics.toggle_opacity()

    def available_interface(self, ip_address=None):
        """
        Returns an interface of the computer that is disconnected and
        is available to connect to another computer.
        If the computer has no available interfaces, creates one and returns it.
        :param ip_address: a string which is the address the new interface will have if one is created.
        :return: an `Interface` object.
        """
        try:
            return get_the_one(self.interfaces, lambda i: not i.is_connected(), NoSuchInterfaceError)
        except NoSuchInterfaceError:
            new_interface = Interface.with_ip(ip_address)
            self.interfaces.append(new_interface)
            self.graphics.add_interface(new_interface)
            return new_interface

    def disconnect(self, connection):
        """
        Receives a `Connection` object and disconnects the appropriate interface from that connection.
        :param connection: a `Connection` object.
        :return: None
        """
        for interface in self.interfaces:
            if interface.connection is connection.left_side or interface.connection is connection.right_side:
                interface.disconnect()
                return

    def same_subnet_interfaces(self, ip_address):
        """
        Returns all of the interfaces of the computer that are in the same subnet as the given IP address.
        It is tested (naturally) using the subnet mask of the given `IPAddress` object.
        :param ip_address: The `IPAddress` object whose subnet we are talking about.
        :return: an `Interface` list of the Interface objects in the same subnet.
        """
        return[interface for interface in self.all_interfaces \
                if interface.has_ip() and interface.ip.is_same_subnet(ip_address)]

    def has_ip(self):
        """Returns whether or not this computer has an IP address at all (on any of its interfaces)"""
        return any(interface.has_ip() for interface in self.interfaces)

    def get_ip(self):
        """
        Returns one of the ip addresses of this computer. Currently - the first one, but this is not guaranteed and
        should not be relied upon.
        :return: `IPAddress` object.
        """
        if not self.has_ip():
            raise NoIPAddressError("This computer has no IP address!")
        return get_the_one(self.interfaces, lambda i: i.has_ip(), NoSuchInterfaceError).ip

    def get_mac(self):
        """Returns one of the computer's `MACAddresses`"""
        if not self.macs:
            raise NoSuchInterfaceError("The computer has no MAC address since it has no network interfaces!!!")
        return self.macs[0]

    def add_remove_interface(self, name):
        """
        Adds a new interface to this computer with a given name
        :param name: a string or None, if None, chooses random name.
        :return: None
        """
        interface = get_the_one(self.interfaces, lambda i: i.name == name)
        if interface is None:
            self.interfaces.append(Interface(MACAddress.randomac(), name=name))
            return

        if interface.is_connected():
            raise DeviceAlreadyConnectedError("Cannot remove a connected interface!!!")
        if interface.has_ip():
            self.routing_table.remove_interface(interface)
        self.interfaces.remove(interface)

    def has_this_ip(self, ip_address):
        """Returns whether or not this computer has a given IP address. (so whether or not if it is its address)"""
        if ip_address is None:
            # raise NoIPAddressError("The address that is given is None!!!")
            return
        return any(interface.has_ip() and interface.ip.string_ip == ip_address.string_ip for interface in self.all_interfaces)

    def is_arp_for_me(self, packet):
        """Returns whether or not the packet is an ARP request for one of your IP addresses"""
        return "ARP" in packet and packet["ARP"].opcode == ARP_REQUEST and self.has_this_ip(packet["ARP"].dst_ip)

    def get_interface_with_ip(self, ip_address=None):
        """
        Returns the interface that has this ip_address.
        If there is none that have that address, return None.

        If no IP address is given, returns one interface that has any IP address.
        :param ip_address: The `IPAddress` object.
        :return: Interface object or None.
        """
        if ip_address is None:
            return get_the_one(self.interfaces, lambda i: i.has_ip(), NoSuchInterfaceError)
        return get_the_one(self.all_interfaces, lambda i: i.has_this_ip(ip_address))

    def _handle_arp(self, packet, interface):
        """
        Receives a `Packet` object and if it contains an ARP request layer, sends back
        an ARP reply. If the packet contains no ARP layer raises `NoArpLayerError`.
        Anyway learns the IP and MAC from the ARP (even if it is a reply or a grat-arp).
        :param packet: the `Packet` that contains the ARP we handle
        :param interface: The `Interface` the packet was received on.
        :return: None
        """
        try:
            arp = packet["ARP"]
        except KeyError:
            raise NoARPLayerError("This function should only be called with an ARP packet!!!")

        self.arp_cache[arp.src_ip] = ARPCacheItem(arp.src_mac, MainLoop.instance.time())  # learn from the ARP

        if arp.opcode == ARP_REQUEST and interface.has_this_ip(arp.dst_ip):
            self.send_arp_reply(packet)                     # Answer if request

    def _handle_ping(self, packet, interface):
        """
        Receives a `Packet` object which contains an ICMP layer with ICMP request
        handles everything related to the ping and sends a ping reply.
        :param packet: a `Packet` object to reply on.
        :param interface: The `Interface` the packet was received on.
        :return: None
        """
        if (packet["ICMP"].opcode == ICMP_REQUEST) and (self.is_for_me(packet)):
            if interface.has_this_ip(packet["IP"].dst_ip) or (interface is self.loopback and self.has_this_ip(packet["IP"].dst_ip)):  # only if the packet is for me also on the third layer!
                dst_ip = packet["IP"].src_ip
                self.start_ping_process(dst_ip, ICMP_REPLY)

    def _handle_tcp(self, packet, interface):
        """
        Receives a TCP packet and decides if it is a TCP SYN to an open port, starts a server process or sends a TCP RST
        accordingly
        :param packet: a `Packet` object to test
        :param interface: the `Interface` that received it.
        :return: None
        """
        if not self.has_ip() or not self.has_this_ip(packet["IP"].dst_ip):
            return

        if {TCP_SYN} == packet["TCP"].flags:
            dst_port = packet["TCP"].dst_port
            if dst_port not in self.open_ports:
                self.send_to(packet["Ethernet"].src_mac, packet["IP"].src_ip,
                             TCP(packet["TCP"].dst_port, packet["TCP"].src_port, 0, {TCP_RST}))

    def _handle_special_packet(self, packet, receiving_interface):
        """
        Checks if the packet that was received is of some special type that requires handling (ARP, ICMP, TPC-SYN) and
        if so, calls the appropriate handler.
        :param packet: a `Packet` object that was received
        :param receiving_interface: an `Interface` object that received that packet.s
        :return: None
        """
        for packet_type in self.packet_types_and_handlers:
            if packet_type in packet:
                self.packet_types_and_handlers[packet_type](packet, receiving_interface)

    def start_ping_process(self, ip_address, opcode=ICMP_REQUEST):
        """
        Starts sending a ping to another computer.
        :param ip_address: an `IPAddress` object to ping.
        :param opcode: the opcode of the ping to send
        :return: None
        """
        self.start_process(SendPing, ip_address, opcode)

    def is_for_me(self, packet):
        """
        Takes in a packet and returns whether or not that packet is meant for this computer. (On the second layer)
        If broadcast, return True.
        :param packet: a `Packet` object.
        :return: boolean
        """
        return any([interface.is_for_me(packet) for interface in self.interfaces])

    def is_directly_for_me(self, packet):
        """
        Takes in a packet and returns whether or not that packet is meant for this computer directly (not broadcast).
        :param packet: a `Packet` object.
        :return: boolean
        """
        return any([interface.is_directly_for_me(packet) for interface in self.interfaces])

    def _forget_arp_cache(self):
        """
        Check through the ARP cache if any addresses should be forgotten and if so forget them. (removes from the arp cache)
        :return: None
        """
        for ip, arp_cache_item in list(self.arp_cache.items()):
            if MainLoop.instance.time_since(arp_cache_item.time) > ARP_CACHE_FORGET_TIME:
                del self.arp_cache[ip]

    def ask_dhcp(self):
        """
        Start a `DHCPClient` process to receive an IP address!
        One can read more at the 'dhcp_process.py' file.
        :return: None
        """
        self.kill_process(DHCPClient)  # if currently asking for dhcp, stop it
        self.start_process(DHCPClient)

    def open_port(self, port_number):
        """
        Opens a port on the computer. Starts the process that is behind it.
        :param port_number:
        :return:
        """
        if port_number not in self.PORTS_TO_PROCESSES:
            raise PopupWindowWithThisError(f"{port_number} is an unknown port!!!")

        process = self.PORTS_TO_PROCESSES[port_number]
        if port_number in self.open_ports:
            if process is not None:
                self.kill_process(process)
            self.open_ports.remove(port_number)
        else:
            if process is not None:
                self.start_process(self.PORTS_TO_PROCESSES[port_number])
            self.open_ports.append(port_number)

        self.graphics.update_image()

    def update_routing_table(self):
        """updates the routing table according to the interfaces at the moment"""
        self.routing_table = RoutingTable.create_default(self)

    def set_default_gateway(self, gateway_ip, interface_ip=None):
        """
        Sets the default gateway of the computer in the routing table with the interface IP that the packets to
        that gateway will be sent from.
        :param gateway_ip: The `IPAddress` of the default gateway.
        :param interface_ip: The `IPAddress` of the interface that will send the packets to the gateway.
        :return: None
        """
        interface_ip_address = interface_ip
        if interface_ip is None:
            interface_ip_address = self.same_subnet_interfaces(gateway_ip)[0].ip
        self.routing_table[IPAddress("0.0.0.0/0")] = RoutingTableItem(gateway_ip, interface_ip_address)

    def set_ip(self, interface, string_ip):
        """
        Sets the IP address of a given interface.
        Updates all relevant attributes of the computer (routing table, DHCP serving, etc...)
        If there is no interface with that name, `NoSuchInterfaceError` will be raised.
        :param interface: The `Interface` one wishes to change the IP of
        :param string_ip: a string IP which will be the new IP of the interface.
        :return: None
        """
        interface.ip = IPAddress(string_ip)
        if self.is_process_running(DHCPServer):
            dhcp_server_process = self.get_running_process(DHCPServer)
            dhcp_server_process.update_server_data()
        self.routing_table.add_interface(interface.ip)
        self.graphics.update_text()

    def toggle_sniff(self, interface_name=ANY_INTERFACE, is_promisc=False):
        """
        Starts sniffing on the interface with the given name.
        If no such interface exists, raises NoSuchInterfaceError.
        If the interface is sniffing already, stops sniffing on it.
        :param interface_name: ... the interface name
        :return: None
        """
        if interface_name == ANY_INTERFACE:
            for name in [interface.name for interface in self.interfaces]:
                self.toggle_sniff(name, is_promisc)
            return

        self.print(f"sniffing toggled on interface {interface_name}")
        interface = get_the_one(self.interfaces, lambda i: i.name == interface_name, NoSuchInterfaceError)
        interface.is_promisc = is_promisc
        interface.is_sniffing = not interface.is_sniffing

    def _sniff_packet(self, packet):
        """
        Receives a `Packet` and prints it out to the computer's console. should be called only if the packet was sniffed
        """
        deepest = packet.deepest_layer()
        packet_str = deepest.opcode if hasattr(deepest, "opcode") else type(deepest).__name__
        self.print(f"({self.packets_sniffed}) sniff: {packet_str}")
        self.packets_sniffed += 1

    def _new_packets_since(self, time_):
        """
        Returns a list of all the new `ReceivedPacket`s that were received in the last `seconds` seconds.
        :param seconds: a number of seconds.
        :return: a list of `ReceievedPacket`s
        """
        return list(filter(lambda rp: rp.time > time_, self.received))

# -------------------------v packet sending and wrapping related methods v ---------------------------------------------

    def send(self, packet):
        """
        Takes a full and ready packet and just sends it.
        :param packet: a valid `Packet` object.
        :return: None
        """
        if packet.is_valid():
            interface = self.get_interface_with_ip(self.routing_table[packet["IP"].dst_ip].interface_ip)
            interface.send(packet)

    def send_to(self, dst_mac, dst_ip, packet):
        """
        Receives destination addresses and a packet, wraps the packet with IP
        and Ethernet as required and sends it out.
        :param dst_mac: destination `MACAddress` of the packet
        :param dst_ip: destination `IPAddress` of the packet
        :param packet: packet to wrap. Could be anything, should be something the destination computer expects.
        :return: None
        """
        full_packet = self.ip_wrap(dst_mac, dst_ip, packet)
        interface = self.get_interface_with_ip(self.routing_table[dst_ip].interface_ip)
        interface.send(full_packet)

    def ip_wrap(self, dst_mac, dst_ip, protocol):
        """
        Takes in some protocol and wraps it up in Ethernet and IP with the appropriate MAC and IP addresses and TTL all
        ready to be sent.
        :param dst_mac:
        :param dst_ip:
        :param protocol:  The thing to wrap in IP
        :return: a valid `Packet` object.
        """
        interface = self.get_interface_with_ip(self.routing_table[dst_ip].interface_ip)
        return interface.ethernet_wrap(dst_mac, IP(interface.ip, dst_ip, TTLS[self.os], protocol))

    def send_arp_to(self, ip_address):
        """
        Constructs and sends an ARP request to a given IP address.
        :param ip_address: a data of the IP address you want to find the MAC for.
        :return: None
        """
        interface = self.get_interface_with_ip(self.routing_table[ip_address].interface_ip)
        arp = ARP(ARP_REQUEST, interface.ip, ip_address, interface.mac)
        if interface.ip is None:
            arp = ARP.create_probe(ip_address, interface.mac)
        interface.send_with_ethernet(MACAddress.broadcast(), arp)

    def send_arp_reply(self, request):
        """
        Receives a `Packet` object that is the ARP request you answer for.
        Sends back an appropriate ARP reply.
        This should only called if the ARP is for this computer (If not raises an exception!)
        If the packet does not contain an ARP layer, raise NoARPLayerError.
        :param request: a Packet object that contains an ARP layer.
        :return: None
        """
        try:
            sender_ip, requested_ip = request["ARP"].src_ip, request["ARP"].dst_ip
        except KeyError:
            raise NoARPLayerError("The packet has no ARP layer!!!")

        if not self.has_this_ip(requested_ip):
            raise SomethingWentTerriblyWrongError("Do not call this method if the ARP is not for me!!!")

        interface = self.get_interface_with_ip(requested_ip)
        arp = ARP(ARP_REPLY, request["ARP"].dst_ip, sender_ip, interface.mac, request["ARP"].src_mac)
        interface.send_with_ethernet(request["ARP"].src_mac, arp)

    def arp_grat(self, interface):
        """
        Send a gratuitous ARP from a given interface.
        If the interface has no IP address, do nothing.
        :param interface: an `Interface` object.
        :return: None
        """
        if self.has_ip() and SENDING_GRAT_ARPS:
            if interface.has_ip():
                interface.send_with_ethernet(MACAddress.broadcast(), ARP(ARP_GRAT, interface.ip, interface.ip, interface.mac))

    def send_ping_to(self, mac_address, ip_address, opcode=ICMP_REQUEST, data=''):
        """
        Send an ICMP packet to the a given ip address.
        :param ip_address: The destination `IPAddress` object of the ICMP packet
        :param mac_address: The destination `MACAddress` object of the ICMP packet
        :param opcode: the ICMP opcode (reply / request / time exceeded)
        :return: None
        """
        self.send_to(mac_address, ip_address, ICMP(opcode, data))

    def send_time_exceeded(self, dst_mac, dst_ip, data=''):
        """
        Sends an ICMP time exceeded packet.
        It has the maximum time to live (must be more than the original packet it sends a time exceeded for)
        :return: None
        """
        interface = self.get_interface_with_ip(self.routing_table[dst_ip].interface_ip)
        interface.send_with_ethernet(dst_mac,
                                     IP(interface.ip, dst_ip, MAX_TTL,
                                        ICMP(ICMP_TIME_EXCEEDED, data)))

    def send_dhcp_discover(self):
        """Sends out a `DHCP_DISCOVER` packet (This is sent by a DHCP client)"""
        dst_ip = IPAddress.broadcast()
        src_ip = IPAddress.no_address()
        for interface in self.interfaces:
            interface.send_with_ethernet(MACAddress.broadcast(),
                                         IP(src_ip, dst_ip, TTLS[self.os],
                                            UDP(DHCP_CLIENT_PORT, DHCP_SERVER_PORT,
                                                DHCP(DHCP_DISCOVER, DHCPData(None, None, None)))))

    def send_dhcp_offer(self, client_mac, offer_ip, session_interface):
        """
        Sends a `DHCP_OFFER` request with an `offer_ip` offered to the `dst_mac`. (This is sent by the DHCP server)
        :param client_mac: the `MACAddress` of the client computer.
        :param offer_ip: The `IPAddress` that is offered in the DHCP offer.
        :param session_interface: the `Interface` that runs the session with the Client
        :return: None
        """
        dst_ip = offer_ip
        session_interface.send_with_ethernet(client_mac,
                                             IP(session_interface.ip, dst_ip, TTLS[self.os],
                                                UDP(DHCP_SERVER_PORT, DHCP_CLIENT_PORT,
                                                    DHCP(DHCP_OFFER, DHCPData(offer_ip, None, None)))))

    def send_dhcp_request(self, server_mac, session_interface):
        """
        Sends a `DHCP_REQUEST` that confirms the address that the server had offered.
        This is sent by the DHCP client.
        :param server_mac: The `MACAddress` of the DHCP server.
        :param session_interface: The `Interface` that is running the session with the server.
        :return: None
        """
        dst_ip = IPAddress.broadcast()
        src_ip = IPAddress.no_address()
        session_interface.send_with_ethernet(server_mac,
                                             IP(src_ip, dst_ip, TTLS[self.os],
                                                UDP(DHCP_CLIENT_PORT, DHCP_SERVER_PORT,
                                                    DHCP(DHCP_REQUEST, DHCPData(None, None, None)))))

    def send_dhcp_pack(self, client_mac, dhcp_data, session_interface):
        """
        Sends a `DHCP_PACK` that tells the DHCP client all of the new data it needs to update (IP, gateway, DNS)
        :param client_mac: The `MACAddress` of the client.
        :param dhcp_data:  a `DHCPData` namedtuple (from 'dhcp_process.py') that is sent in the DHCP pack.
        :param session_interface: The `Interface` that is running the session with the client.
        :return: None
        """
        dst_ip = dhcp_data.given_ip
        session_interface.send_with_ethernet(client_mac,
                                             IP(session_interface.ip, dst_ip, TTLS[self.os],
                                                UDP(DHCP_SERVER_PORT, DHCP_CLIENT_PORT,
                                                    DHCP(DHCP_PACK, dhcp_data))))

    def validate_dhcp_given_ip(self, ip_address):
        """
        This is for future implementation if you want, for now it is not doing anything, just making sure that no two
        interfaces get the same IP address.
        :param ip_address: an IPAddress object.
        :return: theoretically, whether or not the interface approves of the address given to it by DHCP server.
        """
        return not any(interface.has_this_ip(ip_address) for interface in self.interfaces)

    def request_address(self, ip_address, requesting_process, kill_process_if_not_found=True):
        """
        Receives an `IPAddress` and sends ARPs to it until it finds it or it did not answer for a long time.
        This function actually starts a process that does that.
        :param ip_address: an `IPAddress` object to look for
        :param requesting_process: the process that is sending the ARP request.
        :param kill_process_if_not_found: whether or not to kill the process if the arp was not answered
        :return: The actual IP address it is looking for (The IP of your gateway (or the original if in the same subnet))
        and a condition to test whether or not the process is done looking for the IP.
        """
        ip_for_the_mac = self.routing_table[ip_address].ip_address
        kill_process = requesting_process if kill_process_if_not_found else None
        self.start_process(ARPProcess, ip_for_the_mac, kill_process)
        return ip_for_the_mac, lambda: ip_for_the_mac in self.arp_cache

    # ------------------------- v process related methods v ----------------------------------------------------

    def start_process(self, process_type, *args):
        """
        Receive a `Process` subclass class, and the arguments for it
        (not including the default Computer argument that all processes receive.)

        for example: start_process(SendPing, '1.1.1.1/24')

        For more information about processes read the documentation at 'process.py'
        :param process_type: The `type` of the process to run.
        :param args: The arguments that the `Process` subclass constructor requires.
        :return: None
        """
        self.waiting_processes.append((process_type(self, *args), None))

    @staticmethod
    def run_process(process):
        """
        This function receives a process and runs it until yielding a `WaitingForPacket` namedtuple.
        Returns the yielded `WaitingForPacket`.
        :param process: a `Process` object.
        :return: a `WaitingForPacket` namedtuple or if the process is done, None.
        """
        try:
            return next(process.process)
        except StopIteration:
            return None

    def kill_process(self, process_type):
        """
        Takes in a process type and kills all of the waiting processes of that type in this `Computer`.
        :param process_type: a `Process` subclass type (for example `SendPing` or `DHCPClient`)
        :return: None
        """
        for waiting_process in self.waiting_processes:
            if isinstance(waiting_process.process, process_type):
                self.waiting_processes.remove(waiting_process)

    def is_process_running(self, process_type):
        """
        Receives a type of a `Process` subclass and returns whether or not there is a process of that type that
        is running.
        :param process_type: a `Process` subclass (for example `SendPing` or `DHCPClient`)
        :return: `bool`
        """
        for process, _ in self.waiting_processes:
            if isinstance(process, process_type):
                return True
        return False

    def get_running_process(self, process_type):
        """
        Receives a type of a `Process` subclass and returns the process object of the `Process` that is currently
        running in the computer.
        If no such process is running in the computer, raise NoSuchProcessError
        :param process_type: a `Process` subclass (for example `SendPing` or `DHCPClient`)
        :return: `bool`
        """
        for process, _ in self.waiting_processes:
            if isinstance(process, process_type):
                return process
        raise NoSuchProcessError(f"'{process_type}' is not currently running!")

    def _start_new_processes(self):
        """
        Goes over the waiting processes list and returns a list of new processes that are ready to run.
        Also removes them from the waiting processes list.
        New processes - that means that they were started by `start_process` but did not run at all yet.
        :return: a list of ready `Process`-s.
        """
        new_processes = []
        for process, waiting_for in self.waiting_processes[:]:
            if waiting_for is None:
                # ^ if waiting for is None the process was not yet run.
                new_processes.append(process)
                self.waiting_processes.remove((process, None))
        return new_processes

    def _handle_processes(self):
        """
        Handles all of running the processes, runs the ones that should be run and puts them back to the
         `waiting_processes`
        list if they are now waiting.
        Read more about processes at 'process.py'
        :return: None
        """
        ready_processes = self._get_ready_processes()
        for process in ready_processes:
            waiting_for = self.run_process(process)
            if waiting_for is not None:  # only None if the process is done!
                self.waiting_processes.append(WaitingProcess(process, waiting_for))

    def _get_ready_processes(self):
        """
        Returns a list of the waiting processes that finished waiting and are ready to run.
        :return: a list of `Process` objects that are ready to run. (they will run in the next call to
        `self._handle_processes`
        """
        new_packets = self._new_packets_since(self.process_last_check)
        self.process_last_check = MainLoop.instance.time()

        self._kill_dead_processes()
        ready_processes = self._start_new_processes()
        self._decide_ready_processes_no_packet(ready_processes)

        waiting_processes_copy = self.waiting_processes[:]
        for received_packet in new_packets[:]:
            for waiting_process in waiting_processes_copy:
                self._decide_if_process_ready_by_packet(waiting_process, received_packet, ready_processes)

        self._check_process_timeouts(ready_processes)
        return ready_processes

    def _kill_dead_processes(self):
        """
        Kills all of the process that have the `kill_me` attribute set.
        This allows them to terminate themselves from anywhere inside them
        :return: None
        """
        for waiting_process in self.waiting_processes[:]:
            process, _ = waiting_process
            if process.kill_me:
                self.waiting_processes.remove(waiting_process)
    
    def _decide_ready_processes_no_packet(self, ready_processes):
        """
        Receives a list of the already ready processes,
        Goes over the waiting processes and sees if one of them is waiting for a certain condition without a packet (if
        its `WaitingForPacket` object is actually `WaitingFor`.
        If so, it tests its condition. If the condition is true, appends the process to the `ready_processes` list and 
        removes it from the `waiting_processes` list.
        :return: None
        """
        for waiting_process in self.waiting_processes[:]:
            if not hasattr(waiting_process.waiting_for, "value"):
                if waiting_process.waiting_for.condition():
                    self.waiting_processes.remove(waiting_process)
                    ready_processes.append(waiting_process.process)

    def _decide_if_process_ready_by_packet(self, waiting_process, received_packet, ready_processes):
        """
        This method receives a waiting process, a possible packet that matches its `WaitingForPacket` condition
        and a list of already ready processes.
        If the packet matches the condition of the `WaitingForPacket` of the process, this adds the process
        to `ready_processes` and removes it from the `self.waiting_processes` list.
        It enables the same process to receive a number of different packets if the condition fits to a
        number of packets in the run. (mainly in DHCP Server when all of the computers send in the same time to the same
        process...)
        :param waiting_process: a `WaitingProcess` namedtuple.
        :param received_packet: a `ReceivedPacket` namedtuple.
        :param ready_processes: a list of already ready processes that will run in the next call to
        `self._handle_processes`.
        :return: whether or not the process is ready and was added to `ready_processes`
        """
        process, waiting_for = waiting_process
        packet, _, receiving_interface = received_packet

        if not hasattr(waiting_for, "value"):
            return False

        if waiting_for.condition(packet) == True:
            waiting_for.value.packets[packet] = receiving_interface  # this is the behaviour the `Process` object expects

            if process not in ready_processes:    # if this is the first packet that the process received in this loop
                ready_processes.append(process)
                self.waiting_processes.remove(waiting_process)  # the process is about to run so we remove it from the waiting process list
            return True
        return False

    def _check_process_timeouts(self, ready_processes):
        """
        Tests if the waiting processes have a timeout and if so, continues them, without any packets. (inserts to the
        `ready_processes` list)
        :param waiting_process: a `WaitingProcess`
        :param ready_processes: a list of the ready processes to run.
        :return: None
        """
        for waiting_process in self.waiting_processes:
            if hasattr(waiting_process.waiting_for, "timeout"):
                if waiting_process.waiting_for.timeout:
                    ready_processes.append(waiting_process.process)
                    self.waiting_processes.remove(waiting_process)

# ------------------------------- v The main `logic` method of the computer's main loop v ---------------------------

    def logic(self):
        """
        This method operates the computer's sending and receiving logic.
        (ARPs, Pings, Switching, Routing and so on....)

        In the regular `Computer` class, it receives packets, sniffs them, handles arps, handles pings,
        handles processes and in the end handles the ARP cache. In that order.
        :return: None
        """
        if not self.is_powered_on:
            return

        self.received.clear()
        for interface in self.all_interfaces:
            if not interface.is_connected():
                continue
            for packet in interface.receive():
                self.received.append(ReceivedPacket(packet, MainLoop.instance.time(), interface))

                if interface.is_sniffing:
                    self._sniff_packet(packet)

                self._handle_special_packet(packet, interface)

        self._handle_processes()
        self._forget_arp_cache()  # deletes just the required items in the arp cache....

    def __repr__(self):
        """The string representation of the computer"""
        return f"Computer(name={self.name}, Interfaces={self.interfaces}"

    def __str__(self):
        """a simple string representation of the computer"""
        return f"{self.name}"
