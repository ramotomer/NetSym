import random
from collections import namedtuple
from typing import Tuple

from recordclass import recordclass

from address.ip_address import IPAddress
from address.mac_address import MACAddress
from computing.internals.arp_cache import ArpCache
from computing.internals.filesystem.filesystem import Filesystem
from computing.internals.interface import Interface
from computing.internals.processes.abstracts.process import PacketMetadata, ReturnedPacket
from computing.internals.processes.kernelmode_processes.arp_process import ARPProcess, SendPacketWithARPProcess
from computing.internals.processes.process_scheduler import ProcessScheduler
from computing.internals.processes.usermode_processes.daytime_process import DAYTIMEServerProcess
from computing.internals.processes.usermode_processes.dhcp_process import DHCPClient
from computing.internals.processes.usermode_processes.dhcp_process import DHCPServer
from computing.internals.processes.usermode_processes.ftp_process import ServerFTPProcess
from computing.internals.processes.usermode_processes.ping_process import SendPing
from computing.internals.processes.usermode_processes.sniffing_process import SniffingProcess
from computing.internals.routing_table import RoutingTable, RoutingTableItem
from computing.internals.sockets.raw_socket import RawSocket
from computing.internals.sockets.tcp_socket import TCPSocket
from computing.internals.sockets.udp_socket import ReturnedUDPPacket
from computing.internals.wireless_interface import WirelessInterface
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
from usefuls.funcs import get_the_one

ReceivedPacket = namedtuple("ReceivedPacket", "packet metadata")
# ^ a packet that was received in this computer  (packet object, receiving time, interface packet is received on)


SocketData = recordclass("SocketData", [
    "kind",
    "local_ip_address",
    "local_port",
    "remote_ip_address",
    "remote_port",
    "state",
    "pid",
])


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
        "TCP": {
            PORTS.DAYTIME: DAYTIMEServerProcess,
            PORTS.FTP: ServerFTPProcess,
            PORTS.SSH: None,
            PORTS.HTTP: None,
            PORTS.HTTPS: None,
        },
        "UDP": {
            PORTS.DHCP_SERVER: DHCPServer,
        },
    }

    def __init__(self, name=None, os=OS.WINDOWS, gateway=None, *interfaces):
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
            self.interfaces = []  # a list of all of the interfaces without the loopback
        self.loopback = Interface.loopback()
        self.boot_time = MainLoop.instance.time()

        self.received = []
        self.arp_cache = ArpCache()
        # ^ a dictionary of {<ip address> : ARPCacheItem(<mac address>, <initiation time of this item>)
        self.routing_table = RoutingTable.create_default(self)
        self.filesystem = Filesystem.with_default_dirs()
        self.process_scheduler = ProcessScheduler(self)

        self.graphics = None
        # ^ The `GraphicsObject` of the computer, not initiated for now.

        self.is_powered_on = True

        self.packet_types_and_handlers = {
            "ARP": self._handle_arp,
            "ICMP": self._handle_ping,
            "TCP": self._handle_tcp,
            "UDP": self._handle_udp,
        }

        self.open_udp_ports = []

        self.sockets = {}

        self.is_supporting_wireless_connections = False

        self.output_method = COMPUTER.OUTPUT_METHOD.CONSOLE
        self.active_shells = []

        self.initial_size = IMAGES.SCALE_FACTORS.SPRITES, IMAGES.SCALE_FACTORS.SPRITES

        MainLoop.instance.insert_to_loop_pausable(self.logic)
        # ^ method does not run when program is paused

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

    @property
    def open_tcp_ports(self):
        return [socket_data.local_port for socket, socket_data in self.sockets.items()
                if socket_data.state == COMPUTER.SOCKETS.STATES.LISTENING]

    @property
    def raw_sockets(self):
        return [socket for socket in self.sockets if self.sockets[socket].kind == COMPUTER.SOCKETS.TYPES.SOCK_RAW]

    @classmethod
    def with_ip(cls, ip_address, name=None):
        """
        This is a constructor for a computer with a given IP address, defaults the rest of the properties.
        :param ip_address: an IP string that one wishes the new `Computer` to have.
        :param name: a name that the computer will have.
        :return: a `Computer` object
        """
        computer = cls(name, OS.WINDOWS, None, Interface(MACAddress.randomac(), IPAddress(ip_address)))
        return computer

    @classmethod
    def wireless_with_ip(cls, ip_address, frequency=CONNECTIONS.WIRELESS.DEFAULT_FREQUENCY, name=None):
        return cls(name, OS.WINDOWS, None, WirelessInterface(MACAddress.randomac(), IPAddress(ip_address), frequency=frequency))

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
        self.graphics = ComputerGraphics(x, y, self, IMAGES.COMPUTERS.COMPUTER if not self.open_tcp_ports else IMAGES.COMPUTERS.SERVER)
        self.loopback.connection.connection.show(self.graphics)

    def print(self, string):
        """
        Prints out a string to the computer output.
        :param string: The string to print.
        :return: None
        """
        {
            COMPUTER.OUTPUT_METHOD.CONSOLE: self.graphics.child_graphics_objects.console.write,
            COMPUTER.OUTPUT_METHOD.SHELL: self._print_on_all_shells,
            COMPUTER.OUTPUT_METHOD.STDOUT: print,
            COMPUTER.OUTPUT_METHOD.NONE: lambda s: None
        }[self.output_method](string)

    def _print_on_all_shells(self, string):
        """
        print a string on all of the active shells that the computer has
        :param string:
        :return:
        """
        for shell in self.active_shells:
            shell.write(string)

    def _close_all_shells(self):
        """
        Close all shells of the computer.
        Occurs on shutdown
        """
        deleted_any_shells = False
        for shell in self.active_shells[:]:
            deleted_any_shells = True
            shell.exit()

        if deleted_any_shells:
            message = f"{self.name} was shutdown! Relevant shells were closed"
            # PopupError(message, user_interface)  # Impossible - you need the UserInterface object
            print(message)

    def power(self):
        """
        Powers the computer on or off.
        """
        self.is_powered_on = not self.is_powered_on

        for interface in self.all_interfaces:
            interface.is_powered_on = self.is_powered_on
            # TODO: add UP and DOWN for interfaces.
        self.graphics.toggle_opacity()

        if self.is_powered_on:
            self.on_startup()
        else:
            self.on_shutdown()
            # TODO: delete all sockets

    def on_shutdown(self):
        """
        Things the computer should perform as it is shut down.
        :return:
        """
        self.boot_time = None
        self.process_scheduler.terminate_all()
        self.filesystem.wipe_temporary_directories()
        self._close_all_shells()

    def on_startup(self):
        """
        Things the computer should do when it is turned on
        :return:
        """
        self.boot_time = MainLoop.instance.time()
        self.process_scheduler.terminate_all()
        self.process_scheduler.run_startup_processes()

    def add_interface(self, name=None, mac=None, type_=INTERFACES.TYPE.ETHERNET):
        """
        Adds an interface to the computer with a given name.
        If the name already exists, raise a DeviceNameAlreadyExists.
        If no name is given, randomize.
        :param name:
        :param mac:
        :param type_:
        :return:
        """
        interface_type_to_object = {
            INTERFACES.TYPE.ETHERNET: Interface,
            INTERFACES.TYPE.WIFI: WirelessInterface,
        }

        if any(interface.name == name for interface in self.all_interfaces):
            raise DeviceNameAlreadyExists("Cannot have two interfaces with the same name!!!")

        interface_class = interface_type_to_object[type_]

        new_interface = interface_class((MACAddress.randomac() if mac is not None else mac), name=name)
        self.interfaces.append(new_interface)
        self.graphics.add_interface(new_interface)
        return new_interface

    def remove_interface(self, name):
        """
        Removes a computer interface that is named `name`
        :param name: `str`
        :return:
        """
        interface = get_the_one(self.interfaces, lambda i: i.name == name)
        if interface.is_connected():
            raise DeviceAlreadyConnectedError("Cannot remove a connected interface!!!")
        if interface.has_ip():
            self.routing_table.delete_interface(interface)
        self.interfaces.remove(interface)
        MainLoop.instance.unregister_graphics_object(interface.graphics)
        self.graphics.update_text()

    def add_remove_interface(self, name):
        """
        Adds a new interface to this computer with a given name
        :param name: a string or None, if None, chooses random name.
        :return: None
        """
        try:
            self.add_interface(name)
        except DeviceNameAlreadyExists:
            self.remove_interface(name)

    def available_interface(self):
        """
        Returns an interface of the computer that is disconnected and
        is available to connect to another computer.
        If the computer has no available interfaces, creates one and returns it.
        :return: an `Interface` object.
        """
        try:
            return get_the_one(self.interfaces, lambda i: not i.is_connected(), NoSuchInterfaceError)
        except NoSuchInterfaceError:
            return self.add_interface()

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
        return [interface for interface in self.all_interfaces
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

    def has_this_ip(self, ip_address):
        """Returns whether or not this computer has a given IP address. (so whether or not if it is its address)"""
        if ip_address is None:
            # raise NoIPAddressError("The address that is given is None!!!")
            return
        return any(interface.has_ip() and interface.ip.string_ip == ip_address.string_ip
                   for interface in self.all_interfaces)

    def is_arp_for_me(self, packet):
        """Returns whether or not the packet is an ARP request for one of your IP addresses"""
        return "ARP" in packet and \
               packet["ARP"].opcode == OPCODES.ARP.REQUEST and \
               self.has_this_ip(packet["ARP"].dst_ip)

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

    def interface_by_name(self, name):
        """
        Receives an interface name and returns the `Interface`
        :param name:
        :return:
        """
        return get_the_one(
            self.all_interfaces,
            lambda c: c.name == name,
            NoSuchInterfaceError
        )

    def _handle_arp(self, returned_packet):
        """
        Receives a `Packet` object and if it contains an ARP request layer, sends back
        an ARP reply. If the packet contains no ARP layer raises `NoArpLayerError`.
        Anyway learns the IP and MAC from the ARP (even if it is a reply or a grat-arp).
        :param returned_packet: the `ReturnedPacket` that contains the ARP we handle and its metadata
        :return: None
        """
        packet, packet_metadata = returned_packet.packet_and_metadata
        try:
            arp = packet["ARP"]
        except KeyError:
            raise NoARPLayerError("This function should only be called with an ARP packet!!!")

        self.arp_cache.add_dynamic(arp.src_ip, arp.src_mac)

        if arp.opcode == OPCODES.ARP.REQUEST and packet_metadata.interface.has_this_ip(arp.dst_ip):
            self.send_arp_reply(packet)                     # Answer if request

    def _handle_ping(self, returned_packet):
        """
        Receives a `Packet` object which contains an ICMP layer with ICMP request
        handles everything related to the ping and sends a ping reply.
        :param returned_packet: the `ReturnedPacket` that contains the ICMP we handle and its metadata
        :return: None
        """
        packet, packet_metadata = returned_packet.packet_and_metadata
        if (packet["ICMP"].opcode == OPCODES.ICMP.REQUEST) and (self.is_for_me(packet)):
            if packet_metadata.interface.has_this_ip(packet["IP"].dst_ip) or (packet_metadata.interface is self.loopback and self.has_this_ip(packet["IP"].dst_ip)):
                # ^ only if the packet is for me also on the third layer!
                dst_ip = packet["IP"].src_ip
                self.start_ping_process(dst_ip, OPCODES.ICMP.REPLY)

    def _handle_tcp(self, returned_packet):
        """
        Receives a TCP packet and decides if it is a TCP SYN to an open port, starts a server process or sends a TCP RST
        accordingly
        :param returned_packet: the `ReturnedPacket` that contains the TCP we handle and its metadata
        :return: None
        """
        packet, packet_metadata = returned_packet.packet_and_metadata
        if not self.has_ip() or not self.has_this_ip(packet["IP"].dst_ip):
            return

        if {OPCODES.TCP.SYN} == packet["TCP"].flags:
            dst_port = packet["TCP"].dst_port
            if dst_port not in self.open_tcp_ports:
                self.send_to(packet["Ethernet"].src_mac, packet["IP"].src_ip,
                             TCP(packet["TCP"].dst_port, packet["TCP"].src_port, 0,
                                 {OPCODES.TCP.RST}))

    def _handle_udp(self, returned_packet):
        """
        Handles a UDP packet that is received on the computer
        :param returned_packet: the `ReturnedPacket` that contains the UDP we handle and its metadata
        :return:
        """
        packet, packet_metadata = returned_packet.packet_and_metadata
        if not self.has_ip() or not packet_metadata.interface.has_this_ip(packet["IP"].dst_ip):
            return

        if packet["UDP"].dst_port not in self.open_udp_ports:
            self.send_to(packet["Ethernet"].src_mac, packet["IP"].src_ip, ICMP(OPCODES.ICMP.PORT_UNREACHABLE))
            # TODO: add the original packet to the ICMP port unreachable packet
            return

        for socket, socket_metadata in self.sockets.items():
            if socket_metadata.kind == COMPUTER.SOCKETS.TYPES.SOCK_DGRAM and \
                    socket_metadata.local_port == packet["UDP"].dst_port and \
                    socket_metadata.remote_port == packet["UDP"].src_port and \
                    socket_metadata.remote_ip == packet["IP"].src_ip and \
                    socket_metadata.local_ip == packet["IP"].dst_ip:
                socket.received.append(ReturnedUDPPacket(packet["UDP"].data, packet["IP"].src_ip, packet["UDP"].src_port))

    def _handle_special_packet(self, returned_packet):
        """
        Checks if the packet that was received is of some special type that requires handling (ARP, ICMP, TPC-SYN) and
        if so, calls the appropriate handler.
        :param returned_packet: a `ReturnedPacket` of a packet object that was received with its metadata
        :return: None
        """
        packet, packet_metadata = returned_packet.packet_and_metadata
        for packet_type in self.packet_types_and_handlers:
            if packet_type in packet:
                self.packet_types_and_handlers[packet_type](returned_packet)
                continue

    def start_ping_process(self, ip_address, opcode=OPCODES.ICMP.REQUEST, count=1):
        """
        Starts sending a ping to another computer.
        :param ip_address: an `IPAddress` object to ping.
        :param opcode: the opcode of the ping to send
        :param count: how many pings to send
        :return: None
        """
        self.process_scheduler.start_usermode_process(SendPing, ip_address, opcode, count)

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

    def ask_dhcp(self):
        """
        Start a `DHCPClient` process to receive an IP address!
        One can read more at the 'dhcp_process.py' file.
        :return: None
        """
        self.process_scheduler.kill_all_usermode_processes_by_type(DHCPClient)  # if currently asking for dhcp, stop it
        self.process_scheduler.start_usermode_process(DHCPClient)

    def open_port(self, port_number, protocol="TCP"):
        """
        Opens a port on the computer. Starts the process that is behind it.
        :param port_number:
        :param protocol:
        :return:
        """
        if protocol not in self.PORTS_TO_PROCESSES:
            raise UnknownPacketTypeError(f"Protocol type must be one of {list(self.PORTS_TO_PROCESSES.keys())} not {protocol!r}")

        if port_number not in self.PORTS_TO_PROCESSES[protocol]:
            raise PopupWindowWithThisError(f"{port_number} is an unknown port!!!")

        process = self.PORTS_TO_PROCESSES[protocol][port_number]
        if port_number in self.open_tcp_ports:
            if process is not None:
                self.process_scheduler.kill_all_usermode_processes_by_type(process)
        else:
            if process is not None:
                self.process_scheduler.start_usermode_process(self.PORTS_TO_PROCESSES[port_number])

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
        self.routing_table[IPAddress("255.255.255.255/32")] = RoutingTableItem(gateway_ip, interface_ip_address)

    def set_ip(self, interface, string_ip):
        """
        Sets the IP address of a given interface.
        Updates all relevant attributes of the computer (routing table, DHCP serving, etc...)
        If there is no interface with that name, `NoSuchInterfaceError` will be raised.
        :param interface: The `Interface` one wishes to change the IP of
        :param string_ip: a string IP which will be the new IP of the interface.
        :return: None
        """
        if interface is None:
            raise PopupWindowWithThisError("The computer does not have interfaces!!!")

        self.remove_ip(interface)
        interface.ip = IPAddress(string_ip)

        if self.process_scheduler.is_usermode_process_running_by_type(DHCPServer):
            dhcp_server_process = self.process_scheduler.get_usermode_process_by_type(DHCPServer)
            dhcp_server_process.update_server_data()

        self.routing_table.add_interface(interface.ip)
        self.graphics.update_text()

    # TODO: deleting an interface and then connecting the device does not work well

    def remove_ip(self, interface):
        """
        Removes the ip of an interface.
        :param interface:
        :return:
        """
        if not interface.has_ip():
            return

        self.routing_table.delete_interface(interface)
        interface.ip = None

    def set_name(self, name):
        """
        Sets the name of the computer and updates the text under it.
        :param name: the new name for the computer
        :return: None
        """
        if name == self.name:
            raise PopupWindowWithThisError("new computer name is the same as the previous one!!!")
        if len(name) < 2:
            raise PopupWindowWithThisError("name too short!!!")
        if not any(char.isalpha() for char in name):
            raise PopupWindowWithThisError("name must contain letters!!!")
        self.name = name
        self.graphics.update_text()

    def start_sniffing(self, interface_name=INTERFACES.ANY_INTERFACE, is_promisc=False):
        """
        Starts a sniffing process on a supplied interface
        """
        self.process_scheduler.start_usermode_process(
            SniffingProcess,
            lambda packet: True,
            self.interface_by_name(interface_name) if interface_name != INTERFACES.ANY_INTERFACE else INTERFACES.ANY_INTERFACE,
            is_promisc
        )

    def stop_all_sniffing(self):
        """
        Kill all tcpdump processes currently running on the computer
        """
        self.process_scheduler.kill_all_usermode_processes_by_type(SniffingProcess)

    def toggle_sniff(self, interface_name=INTERFACES.ANY_INTERFACE, is_promisc=False):
        """
        Toggles sniffing.
        TODO: if the sniffing is already on - the toggle will turn off ALL sniffing on the computer :( - not only on the specific interface requested
        """
        if self.process_scheduler.is_usermode_process_running_by_type(SniffingProcess):
            self.stop_all_sniffing()
        else:
            self.start_sniffing(interface_name, is_promisc)

    def new_packets_since(self, time_):
        """
        Returns a list of all the new `ReceivedPacket`s that were received in the last `seconds` seconds.
        :param time_: a number of seconds.
        :return: a list of `ReceivedPacket`s
        """
        return list(filter(lambda rp: rp.packets[rp.packet].time > time_, self.received))

# -------------------------v packet sending and wrapping related methods v ---------------------------------------------

    def _sniff_packet_on_relevant_raw_sockets(self, returned_packet):
        """
        Receive a packet on all raw sockets that this packet fits their filter

        :param returned_packet:    The ReturnedPacket object that is sniffed
        """
        packet, packet_metadata = returned_packet.packet_and_metadata
        for raw_socket in self.raw_sockets:
            if raw_socket.is_bound and raw_socket.filter(packet) and \
                    (raw_socket.interface == packet_metadata.interface or raw_socket.interface is INTERFACES.ANY_INTERFACE):
                raw_socket.received.append(returned_packet)

    def send(self, packet, interface=None):
        """
        Takes a full and ready packet and just sends it.
        :param packet: a valid `Packet` object.
        :param interface: the `Interface` to send the packet on.
        :return: None
        """
        if interface is None:
            interface = self.get_interface_with_ip(self.routing_table[packet["IP"].dst_ip].interface_ip)

        if packet.is_valid():
            interface.send(packet)

            self._sniff_packet_on_relevant_raw_sockets(
                ReturnedPacket(packet, PacketMetadata(
                    interface,
                    MainLoop.instance.time(),
                    PACKET.DIRECTION.OUTGOING
                ))
            )

    def send_with_ethernet(self, dst_mac, dst_ip, data):
        """
        Just like `send_to` only does not add the IP layer.
        :param dst_mac:
        :param dst_ip:
        :param data:
        :return:
        """
        interface = self.get_interface_with_ip(self.routing_table[dst_ip].interface_ip)
        self.send(
            interface.ethernet_wrap(dst_mac, data),
            interface=interface,
        )

    def send_to(self, dst_mac, dst_ip, packet):
        """
        Receives destination addresses and a packet, wraps the packet with IP
        and Ethernet as required and sends it out.
        :param dst_mac: destination `MACAddress` of the packet
        :param dst_ip: destination `IPAddress` of the packet
        :param packet: packet to wrap. Could be anything, should be something the destination computer expects.
        :return: None
        """
        self.send(self.ip_wrap(dst_mac, dst_ip, packet))

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
        return interface.ethernet_wrap(dst_mac, IP(interface.ip, dst_ip, TTL.BY_OS[self.os], protocol))

    def udp_wrap(self, dst_mac, dst_ip, src_port, dst_port, protocol):
        """
        Takes in some protocol and wraps it up in Ethernet and IP with the appropriate MAC and IP addresses and TTL and UDP with the supplied ports
        all ready to be sent
        """
        return self.ip_wrap(dst_mac, dst_ip, UDP(src_port, dst_port, protocol))

    def start_sending_udp_packet(self, dst_ip, src_port, dst_port, data):
        """
        Takes in some protocol and wraps it up in IP with the appropriate IP addresses and TTL.
        Starts a process to resolve the MAC and once resolved - construct the packet and send it.
        :param dst_ip:
        :param dst_port:
        :param src_port:
        :param data: The thing to wrap in IP
        """
        interface = self.get_interface_with_ip(self.routing_table[dst_ip].interface_ip)
        self.process_scheduler.start_kernelmode_process(SendPacketWithARPProcess,
                                                        IP(interface.ip, dst_ip, TTL.BY_OS[self.os],
                                                           UDP(src_port, dst_port, data)))

    def send_arp_to(self, ip_address):
        """
        Constructs and sends an ARP request to a given IP address.
        :param ip_address: a ip_layer of the IP address you want to find the MAC for.
        :return: None
        """
        interface_ip = self.routing_table[ip_address].interface_ip
        interface = self.get_interface_with_ip(interface_ip)
        arp = ARP(OPCODES.ARP.REQUEST, interface.ip, ip_address, interface.mac)
        if interface.ip is None:
            arp = ARP.create_probe(ip_address, interface.mac)
        self.send(interface.ethernet_wrap(MACAddress.broadcast(), arp), interface)

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
            raise WrongUsageError("Do not call this method if the ARP is not for me!!!")

        interface = self.get_interface_with_ip(requested_ip)
        arp = ARP(OPCODES.ARP.REPLY, request["ARP"].dst_ip, sender_ip, interface.mac, request["ARP"].src_mac)
        self.send(interface.ethernet_wrap(request["ARP"].src_mac, arp), interface)

    def arp_grat(self, interface):
        """
        Send a gratuitous ARP from a given interface.
        If the interface has no IP address, do nothing.
        :param interface: an `Interface` object.
        :return: None
        """
        if self.has_ip() and SENDING_GRAT_ARPS:
            if interface.has_ip():
                self.send(
                    interface.ethernet_wrap(MACAddress.broadcast(),
                                            ARP(OPCODES.ARP.GRAT, interface.ip, interface.ip, interface.mac)),
                    interface
                )

    def send_ping_to(self, mac_address, ip_address, opcode=OPCODES.ICMP.REQUEST, data=''):
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
        self.send(
            interface.ethernet_wrap(dst_mac,
                                    IP(interface.ip, dst_ip, TTL.MAX,
                                       ICMP(OPCODES.ICMP.TIME_EXCEEDED, data))),
            interface
        )

    def send_dhcp_discover(self):
        """Sends out a `DHCP_DISCOVER` packet (This is sent by a DHCP client)"""
        dst_ip = IPAddress.broadcast()
        src_ip = IPAddress.no_address()
        for interface in self.interfaces:
            self.send(
                interface.ethernet_wrap(MACAddress.broadcast(),
                                        IP(src_ip, dst_ip, TTL.BY_OS[self.os],
                                           UDP(PORTS.DHCP_CLIENT, PORTS.DHCP_SERVER,
                                               DHCP(OPCODES.DHCP.DISCOVER, DHCPData(None, None, None))))),
                interface
            )

    def send_dhcp_offer(self, client_mac, offer_ip, session_interface):
        """
        Sends a `DHCP_OFFER` request with an `offer_ip` offered to the `dst_mac`. (This is sent by the DHCP server)
        :param client_mac: the `MACAddress` of the client computer.
        :param offer_ip: The `IPAddress` that is offered in the DHCP offer.
        :param session_interface: the `Interface` that runs the session with the Client
        :return: None
        """
        dst_ip = offer_ip
        self.send(
            session_interface.ethernet_wrap(client_mac,
                                                 IP(session_interface.ip, dst_ip, TTL.BY_OS[self.os],
                                                    UDP(PORTS.DHCP_SERVER, PORTS.DHCP_CLIENT,
                                                        DHCP(OPCODES.DHCP.OFFER, DHCPData(offer_ip, None, None))))),
            session_interface
        )

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
        self.send(
            session_interface.ethernet_wrap(server_mac,
                                            IP(src_ip, dst_ip, TTL.BY_OS[self.os],
                                               UDP(PORTS.DHCP_CLIENT, PORTS.DHCP_SERVER,
                                                   DHCP(OPCODES.DHCP.REQUEST, DHCPData(None, None, None))))),
            session_interface
        )

    def send_dhcp_pack(self, client_mac, dhcp_data, session_interface):
        """
        Sends a `DHCP_PACK` that tells the DHCP client all of the new ip_layer it needs to update (IP, gateway, DNS)
        :param client_mac: The `MACAddress` of the client.
        :param dhcp_data:  a `DHCPData` namedtuple (from 'dhcp_process.py') that is sent in the DHCP pack.
        :param session_interface: The `Interface` that is running the session with the client.
        :return: None
        """
        dst_ip = dhcp_data.given_ip
        self.send(
            session_interface.ethernet_wrap(client_mac,
                                            IP(session_interface.ip, dst_ip, TTL.BY_OS[self.os],
                                               UDP(PORTS.DHCP_SERVER, PORTS.DHCP_CLIENT,
                                                   DHCP(OPCODES.DHCP.PACK, dhcp_data)))),
            session_interface
        )

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
        self.process_scheduler.start_kernelmode_process(ARPProcess, ip_for_the_mac, kill_process)
        return ip_for_the_mac, lambda: ip_for_the_mac in self.arp_cache

    # ------------------------------- v Sockets v ----------------------------------------------------------------------

    def get_socket(self, requesting_process_pid,
                   address_family=COMPUTER.SOCKETS.ADDRESS_FAMILIES.AF_INET,
                   kind=COMPUTER.SOCKETS.TYPES.SOCK_STREAM):
        """
        Allows programs on the computer to acquire a network socket.
        """
        socket = {
            COMPUTER.SOCKETS.TYPES.SOCK_STREAM: TCPSocket,
            COMPUTER.SOCKETS.TYPES.SOCK_RAW: RawSocket,
            # COMPUTER.SOCKETS.MODES.SOCK_DGRAM:
        }[kind](self, address_family)
        self.sockets[socket] = SocketData(kind=kind,
                                          local_ip_address=None,
                                          local_port=None,
                                          remote_ip_address=None,
                                          remote_port=None,
                                          state=COMPUTER.SOCKETS.STATES.UNBOUND,
                                          pid=requesting_process_pid)
        return socket

    def _is_port_taken(self, port, kind=COMPUTER.SOCKETS.TYPES.SOCK_STREAM):
        """
        Returns whether or not a port is already bound to a socket.
        :param port:
        :param kind:
        :return:
        """
        def is_registered_on_port(socket_data):
            return socket_data.local_port == port and socket_data.kind == kind

        return any(map(is_registered_on_port, self.sockets.values()))

    def bind_socket(self, socket, address: Tuple[IPAddress, int]):
        """
        bind a socket you acquired from the computer to a specific port and address.
        :param socket: a return value of `self.get_socket`
        :param address: (IPAddress, int)
        :return:
        """
        ip_address, port = address

        if self._is_port_taken(port, socket.kind):
            raise PortAlreadyBoundError(f"The socket cannot be bound, since another socket is bound to port {port}")

        try:
            self.sockets[socket].local_ip_address = ip_address
            self.sockets[socket].local_port = port
            self.sockets[socket].state = COMPUTER.SOCKETS.STATES.BOUND
        except KeyError:
            raise SocketNotRegisteredError(f"The socket that was provided is not known to the operation system! "
                                           f"It was probably not acquired using the `computer.get_socket` method! "
                                           f"The socket: {socket}")

        socket.is_bound = True
        
    def remove_socket(self, socket):
        """
        Remove a socket from the operation system's management
        :param socket:
        :return:
        """
        try:
            self.sockets.pop(socket)
        except KeyError:
            raise SocketNotRegisteredError(f"The socket that was provided is not known to the operation system! "
                                           f"It was probably not acquired using the `computer.get_socket` method! "
                                           f"The socket: {socket}")

    # ------------------------------- v The main `logic` method of the computer's main loop v --------------------------

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
                packet_with_metadata = ReturnedPacket(packet, PacketMetadata(interface, MainLoop.instance.time(), PACKET.DIRECTION.INCOMING))
                self.received.append(packet_with_metadata)
                self._handle_special_packet(packet_with_metadata)
                self._sniff_packet_on_relevant_raw_sockets(packet_with_metadata)

        self.process_scheduler.handle_processes()
        self.arp_cache.forget_old_items()  # deletes just the required items in the arp cache....

    def __repr__(self):
        """The string representation of the computer"""
        return f"Computer(name={self.name}, Interfaces={self.interfaces}"

    def __str__(self):
        """a simple string representation of the computer"""
        return f"{self.name}"

# ----------------------------------------- Other methods  ----------------------------------------

    @classmethod
    def _interfaces_from_dict(cls, dict_):
        """
        Receives a dict from a json file and return a list of interfaces
        :param dict_:
        :return:
        """
        interface_classes = {INTERFACES.TYPE.ETHERNET: Interface, INTERFACES.TYPE.WIFI: WirelessInterface}
        return [interface_classes[iface_dict["type_"]].from_dict_load(iface_dict) for iface_dict in dict_["interfaces"]]

    @classmethod
    def from_dict_load(cls, dict_):
        """
        Load a computer from the dict that is saved into the files
        :param dict_:
        :return: Computer
        """
        returned = cls(
            dict_["name"],
            dict_["os"],
            None,
            *cls._interfaces_from_dict(dict_)
        )
        returned.routing_table = RoutingTable.from_dict_load(dict_["routing_table"])
        returned.filesystem = Filesystem.from_dict_load(dict_["filesystem"])
        returned.initial_size = dict_["size"]
        return returned
