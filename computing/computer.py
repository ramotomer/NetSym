from gui.graphics_object import NoGraphics
from gui.computer_graphics import ComputerGraphics
from address.mac_address import MACAddress
from exceptions import *
from computing.interface import Interface
from consts import *
import time
from collections import namedtuple
from computing.process import SendPing
from address.ip_address import IPAddress
import random
from usefuls import get_the_one
from computing.dhcp_process import DHCPClient
from gui.main_loop import MainLoop


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
            self.interfaces = [Interface(os, MACAddress.randomac())]  # interfaces need to know the os for TTL-s
        self.packets_sniffed = 0

        self.arp_cache = {}  # a dictionary of {<ip address> : ARPCacheItem(<mac address>, <initiation time of this item>)
        self.received = []  # a list of the `ReceivedPacket` namedtuple-s that were received at this computer.

        self.waiting_processes = []  # a list of `WaitingProcess` namedtuple-s. If the process is new, its `WaitingProcess.waiting_for` should be None.
        self.process_last_check = time.time()  # the last time that the waiting_processes were checked for 'can they run?'

        self.graphics = NoGraphics()
        # ^ The `GraphicsObject` of the computer.

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
    def gateway(self):
        """The IP address of the gateway of this computer. If there is none, returns the expected one"""
        if not self.has_ip():
            return None
        return self.default_gateway if self.default_gateway is not None else self.get_ip().expected_gateway()

    @classmethod
    def with_ip(cls, ip_address, name=None):
        """
        This is a constructor for a computer with a given IP address, defaults the rest of the properties.
        :param ip_address: an IP string that one wishes the new `Computer` to have.
        :return: a `Computer` object
        """
        computer = cls(name=name)
        computer.interfaces[0].ip = IPAddress(ip_address)
        return computer

    @staticmethod
    def random_name():
        """
        Randomize a computer name based on his operating system.
        Theoretically can randomize the same name twice, but unlikely.
        :param os: The `self.os` variable of the computer.
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
        self.graphics = ComputerGraphics(x, y, self)

    def print(self, string):
        """
        Prints out a string to the computer output.
        Should be to a CLI that will be on the side of the screen when a computer is viewed. (currently not implemented)
        :param string: The stirng to print.
        :return: None
        """
        print(f"{self.name}: {string}")
        # probably will be changed in the future

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
            new_interface = Interface(self.os, MACAddress.randomac(), ip_address)
            self.interfaces.append(new_interface)
            return new_interface

    def connect(self, other):
        """
        Connects this computer to another one.
        Use the `self.available_interface`.
        :param other: another `Computer` object.
        :return: None
        """
        return self.available_interface().connect(other.available_interface())

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
        return[interface for interface in self.interfaces \
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

    def has_this_ip(self, ip_address):
        """Returns whether or not this computer has a given IP address. (so whether or not if it is its address)"""
        if ip_address is None:
            # raise NoIPAddressError("The address that is given is None!!!")
            return
        return any(interface.has_ip() and interface.ip == ip_address for interface in self.interfaces)

    def is_arp_for_me(self, packet):
        """Returns whether or not the packet is an ARP request for one of your IP addresses"""
        return "ARP" in packet and packet["ARP"].opcode == ARP_REQUEST and self.has_this_ip(packet["ARP"].dst_ip)

    def get_interface_with_ip(self, ip_address):
        """
        Returns the interface that has this ip_address.
        If there is none that have that address, return None.
        :param ip_address: The `IPAddress` object.
        :return: Interface object or None.
        """
        return get_the_one(self.interfaces, lambda i: i.has_this_ip(ip_address))

    def decide_sending_interface(self, dst_ip):
        """
        Receives a packet and returns the Interface object it needs to be sent from. (according to IP and MAC addresses).
        :param packet: The `Packet` object to send.
        :return: A list of interfaces to send on.
        """
        if dst_ip.is_broadcast():
            return self.same_subnet_interfaces(dst_ip)
        return self.same_subnet_interfaces(dst_ip)[:1]

    def _handle_arp(self, packet, source_interface):
        """
        Receives a `Packet` object and if it contains an ARP request layer, sends back
        an ARP reply. If the packet contains no ARP layer raises `NoArpLayerError`.
        Anyway learns the IP and MAC from the ARP (even if it is a reply or a grat-arp).
        :param arp: The `Packet` object.
        :return: None
        """
        if not isinstance(source_interface, Interface):
            raise NotAnInterfaceError(f"This is not an interface! {source_interface!r}")

        arp = packet["ARP"]
        self.arp_cache[arp.src_ip] = ARPCacheItem(arp.src_mac, time.time())  # learn from the ARP

        if arp.opcode == ARP_REQUEST and self.has_this_ip(arp.dst_ip):
            source_interface.arp_reply(packet, arp.dst_ip)                     # Answer if request

    def _handle_ping(self, packet):
        """
        Receives a `Packet` object which contains an ICMP layer with ICMP request
        handles everything related to the ping and sends a ping reply.
        :param packet: a `Packet` object to reply on.
        :return: None
        """
        if packet["ICMP"].opcode == ICMP_REQUEST and self.is_for_me(packet):
            dst_ip = packet["IP"].src_ip
            if self.has_this_ip(packet["IP"].dst_ip):  # only if the packet is for me also on the third layer!
                self.ping_to(dst_ip, opcode=ICMP_REPLY)

    def is_for_me(self, packet):
        """
        Takes in a packet and returns whether or not that packet is meant for this computer.
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

    def is_reachable(self, ip_address):
        """Returns whether or not a given ip_address is in a subnet with me (and therefore is reachable)"""
        return any([interface.has_ip() and interface.ip.is_same_subnet(ip_address) for interface in self.interfaces])

    def request_address(self, ip_address):
        """
        Search the network using ARPs for a given IP address's MAC address.
        :param ip_address: an `IPAddress` object of the address you want to acquire
        :return: None
        """
        for interface in self.same_subnet_interfaces(ip_address):
            interface.arp_to(ip_address)

    def forget_arp_cache(self):
        """
        Check through the ARP cache if any addresses should be forgotten and if so forget them. (removes from the arp cache)
        :return: None
        """
        for ip, arp_cache_item in list(self.arp_cache.items()):
            if time.time() - arp_cache_item.time > ARP_CACHE_FORGET_TIME:
                del self.arp_cache[ip]

    def ping_to(self, ip_address, opcode=ICMP_REQUEST):
        """
        Send a ping to a given IP address.
        Starts a `SendPing` process.
        read the 'process.py' for documentation about that process.
        :param ip_address: a string IP address to send a ping to.
        :param opcode: the Ping opcode (request / reply)
        :return: None
        """
        # self.print(f"{self.get_ip()} is sending {opcode} to {ip_address}")
        self.start_process(SendPing, IPAddress(ip_address), opcode)

    def ask_dhcp(self):
        """
        Start a `DHCPClient` process to receive an IP address!
        One can read more at the 'dhcp_process.py' file.
        :return: None
        """
        self.kill_process(DHCPClient)  # if currently asking for dhcp, stop it
        self.start_process(DHCPClient)

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

    def run_process(self, process):
        """
        This function receives a process and runs it until yielding a `WaitingFor` namedtuple.
        Returns the yielded `WaitingFor`.
        :param process: a `Process` object.
        :return: a `WaitingFor` namedtuple or if the process is done, None.
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

    def _handle_processes(self):
        """
        Handles all of running the processes, runs the ones that should be run and puts them back to the `waiting_processes`
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
        :return: a list of `Process` objects that are ready to run. (they will run in the next call to `self._handle_processes`
        """
        new_packets = list(filter(lambda rp: rp.time > self.process_last_check, self.received))
        self.process_last_check = time.time()

        ready_processes = self._start_new_processes()

        for waiting_process in self.waiting_processes[:]:
            for received_packet in new_packets:
                self._decide_if_process_ready_by_packet(waiting_process, received_packet, ready_processes)
        return ready_processes

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

    def _decide_if_process_ready_by_packet(self, waiting_process, received_packet, ready_processes):
        """
        This method receives a waiting process, a possible packet that matches its `WaitingFor` condition and a list of
        already ready processes.
        If the packet matches the condition of the `WaitingFor` of the process, this adds the process to `ready_processes`
        and removes it from the `self.waiting_processes` list.
        It enables the same process to receive a number of different packets if the condition fits to a number of packets
        in the run. (mainly in DHCP Server when all of the computers send in the same time to the same process...)
        :param waiting_process: a `WaitingProcess` namedtuple.
        :param received_packet: a `ReceivedPacket` namedtuple.
        :param ready_processes: a list of already ready processes that will run in the next call to `self._handle_processes`.
        :return: None
        """
        process, waiting_for = waiting_process
        packet, _, receiving_interface = received_packet

        if waiting_for.condition(packet) == True:
            if process not in ready_processes:
                ready_processes.append(process)
                waiting_for.value.packets[packet] = receiving_interface  # this is the behaviour the `Process` object expects
                self.waiting_processes.remove((process, waiting_for))  # the process is about to run so we remove it from the waiting process list

            else:  # if the same process receives a couple of different packets
                waiting_for.value.packets[packet] = receiving_interface

    def logic(self):
        """
        This method operates the computer's sending and receiving logic.
        (ARPs, Pings, Switching, Routing and so on....)

        In the regular `Computer` class, it receives packets, sniffs them, handles arps, handles pings,
        handles processes and in the end handles the ARP cache. In that order.
        :return: None
        """
        for interface in self.interfaces:
            if not interface.is_connected():
                continue
            for packet in interface.receive():
                if packet is None:
                    continue
                self.received.append(ReceivedPacket(packet, time.time(), interface))

                if interface.is_sniffing:
                    self.print(f"({self.packets_sniffed}) {interface.name} got: {packet}")
                    self.packets_sniffed += 1

                if "ARP" in packet:
                    self._handle_arp(packet, interface)

                if "ICMP" in packet:
                    self._handle_ping(packet)

        self._handle_processes()
        self.forget_arp_cache()  # deletes just the required items in the arp cache naturally....

    def __repr__(self):
        """The string representation of the computer"""
        return f"Computer(name={self.name}, Interfaces={self.interfaces}" + (f", gateway={self.gateway})" if self.gateway is not None else ')')

    def __str__(self):
        """a simple string representation of the computer"""
        return f"{self.name}"
