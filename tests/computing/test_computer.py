import os
import random
from typing import cast

import pytest
from _pytest.monkeypatch import MonkeyPatch

from NetSym.address.ip_address import IPAddress
from NetSym.address.mac_address import MACAddress
from NetSym.computing.computer import Computer
from NetSym.computing.internals.network_interfaces.cable_network_interface import CableNetworkInterface
from NetSym.computing.internals.network_interfaces.wireless_network_interface import WirelessNetworkInterface
from NetSym.computing.internals.processes.abstracts.process import ReturnedPacket, PacketMetadata
from NetSym.computing.internals.processes.usermode_processes.sniffing_process import SniffingProcess
from NetSym.consts import OS, FILE_PATHS, DIRECTORIES, COMPUTER, INTERFACES, PACKET
from NetSym.exceptions import NoSuchInterfaceError, PopupWindowWithThisError
from NetSym.gui.abstracts.graphics_object import GraphicsObject
from NetSym.gui.user_interface.popup_windows.popup_window import PopupWindow
from NetSym.packets.packet import Packet
from NetSym.usefuls.dotdict import DotDict
from tests.usefuls import MACS, IPS, example_ethernet, example_arp, mock_mainloop_time


def mock_for_computer_generation(patcher):
    """
    Mock all things to allow the instantiation of a new computer inside a test
    """
    patcher.setattr(FILE_PATHS,  'INTERFACE_NAMES_FILE_PATH', os.path.join("./src/NetSym/res/files", "interface_names.txt"))
    patcher.setattr(FILE_PATHS,  'COMPUTER_NAMES_FILE_PATH',  os.path.join("./src/NetSym/res/files", "computer_names.txt"))
    patcher.setattr(FILE_PATHS,  'WINDOW_INPUT_LIST_FILE',    os.path.join("./src/NetSym/res/files", "window_inputs.txt"))
    patcher.setattr(DIRECTORIES, 'IMAGES',                    "./src/NetSym/res/sprites")

    mock_mainloop_time(patcher)


def get_example_computers():
    with MonkeyPatch.context() as m:
        mock_for_computer_generation(m)

        return [
            Computer(
                "c1",
                OS.WINDOWS,
                None,
                *[CableNetworkInterface(mac, ip, f"c1i{i}") for i, (mac, ip) in enumerate(zip(MACS, IPS))],
            ),
        ]


@pytest.fixture
def example_computers():
    print("running fixture!")
    return get_example_computers()


@pytest.fixture
def example_computers_with_graphics():
    with MonkeyPatch.context() as m:
        mock_for_computer_generation(m)
        computers = get_example_computers()
        for computer in computers:
            computer.init_graphics(0, 0, (0, 0))
        return computers


@pytest.fixture
def example_computers_with_shells():
    with MonkeyPatch.context() as m:
        mock_for_computer_generation(m)
        computers = get_example_computers()
        for computer in computers:
            computer.create_shell(0, 0, PopupWindow(10, 10))
            computer.create_shell(1, 1, PopupWindow(20, 20))
            computer.create_shell(2, 2, PopupWindow(30, 30))
        return computers


def test_macs(example_computers):
    assert example_computers[0].macs == list(map(MACAddress, MACS))


def test_ips(example_computers):
    assert example_computers[0].ips == list(map(IPAddress, IPS))


def test_all_interfaces(example_computers):
    for computer in example_computers:
        assert len(computer.all_interfaces) == len(MACS) + 1


def test_dns_server(example_computers):
    for computer in example_computers:
        server = IPAddress("192.168.1.2")
        computer.dns_server = server
        assert computer.dns_server == server

        computer.dns_server = None
        assert computer.dns_server is None


def test_domain(example_computers):
    for computer in example_computers:
        domain = "hello.world."
        computer.domain = domain
        assert computer.domain == domain

        computer.domain = None
        assert computer.domain is None


def test_raw_sockets(example_computers):
    for computer in example_computers:
        raw_socket1 = computer.get_raw_socket(1)
        raw_socket2 = computer.get_raw_socket(1)
        udp_socket = computer.get_udp_socket(1)
        tcp_socket = computer.get_tcp_socket(1)
        expected_raw_socket_list = [raw_socket1, raw_socket2]

        assert (computer.raw_sockets == expected_raw_socket_list)


@pytest.mark.parametrize(
    "ip_address, name",
    [
        ("1.1.1.1",                "name1"),
        ("0.0.0.0",                "noip"),
        (IPAddress("192.168.1.2"), "tomernoyman"),
        ("1.2.3.4",                None),
    ]
)
def test_with_ip(ip_address, name):
    with MonkeyPatch.context() as m:
        mock_for_computer_generation(m)
        computer = Computer.with_ip(ip_address, name)

    assert isinstance(computer, Computer)
    assert len(computer.interfaces) == 1
    assert isinstance(computer.interfaces[0], CableNetworkInterface)
    assert computer.interfaces[0].ip == IPAddress(ip_address)

    if name is None:
        assert isinstance(computer.name, str)
    else:
        assert computer.name == name


@pytest.mark.parametrize(
    "ip_address, name",
    [
        ("1.1.1.1",                "name1"),
        ("0.0.0.0",                "noip"),
        (IPAddress("192.168.1.2"), "tomernoyman"),
        ("1.2.3.4",                None),
    ]
)
def test_wireless_with_ip(ip_address, name):
    with MonkeyPatch.context() as m:
        mock_for_computer_generation(m)
        computer = Computer.wireless_with_ip(ip_address, name)

    assert isinstance(computer, Computer)
    assert len(computer.interfaces) == 1
    assert isinstance(computer.interfaces[0], WirelessNetworkInterface)
    assert computer.interfaces[0].ip == IPAddress(ip_address)

    if name is None:
        assert isinstance(computer.name, str)
    else:
        assert computer.name == name


def test_random_name():
    with MonkeyPatch.context() as m:
        m.setattr(random, "choice",  lambda i:    "name")
        m.setattr(random, "randint", lambda s, e: 99)
        mock_for_computer_generation(m)

        assert Computer.random_name() == "name99"


@pytest.mark.parametrize(
    "x, y, console_location",
    [
        (100,      200,       (300,      500)),
        (0,        0,         (0,        0)),
        (10000000, 100000000, (10000000, 1000000))
    ]
)
def test_init_graphics(x, y, console_location, example_computers):
    with MonkeyPatch.context() as m:
        mock_for_computer_generation(m)

        for computer in example_computers:
            graphics_list = computer.init_graphics(x, y, console_location)

            assert isinstance(graphics_list, list)
            assert all(isinstance(object_, GraphicsObject) for object_ in graphics_list)
            assert computer.loopback.connection.graphics in graphics_list

            assert computer.graphics in graphics_list
            assert computer.graphics.x == x, computer.graphics.y == y
            assert computer.graphics.child_graphics_objects.console.location == console_location


def test_print_CONSOLE(example_computers_with_graphics):
    string = "Hello World!!! hi"
    for computer in example_computers_with_graphics:
        computer.output_method = COMPUTER.OUTPUT_METHOD.CONSOLE
        computer.print(string)
        assert computer.graphics.child_graphics_objects.console._text.splitlines()[-1] == string


def test_print_SHELL(example_computers_with_graphics):
    string = "Hello World!!! hi"
    for computer in example_computers_with_graphics:
        computer.output_method = COMPUTER.OUTPUT_METHOD.SHELL
        flag = DotDict(is_set=False)
        with MonkeyPatch.context() as m:
            m.setattr(Computer, '_print_on_all_shells', lambda *args: flag.set('is_set', True))
            computer.print(string)
        assert flag.is_set


def test_print_STDOUT(example_computers_with_graphics, capsys):
    string = "Hello-MyGoodFriend World!!#@$@#$@ hi"
    for computer in example_computers_with_graphics:
        computer.output_method = COMPUTER.OUTPUT_METHOD.STDOUT
        capsys.readouterr()
        computer.print(string)
        assert capsys.readouterr().out.rstrip() == string


def test_print_on_all_shells(example_computers_with_shells):
    string = "Hello World!!!! HiHi"
    for computer in example_computers_with_shells:
        computer._print_on_all_shells(string)
        for shell in computer.active_shells:
            assert shell._text.splitlines()[-1] == string


def test_close_all_shells_NO_SHELLS(example_computers, capsys):
    for computer in example_computers:
        capsys.readouterr()
        computer._close_all_shells()
        assert not computer.active_shells
        assert capsys.readouterr().out.strip() == ""  # no message was printed


def test_close_all_shells(example_computers_with_shells, capsys):
    for computer in example_computers_with_shells:
        shells = computer.active_shells[:]
        capsys.readouterr()
        computer._close_all_shells()
        assert len(capsys.readouterr().out) > 0  # a message was printed

        for shell in shells:
            assert shell.carrying_window.unregister_this_window_from_user_interface


def test_get_mac(example_computers):
    for computer in example_computers:
        assert isinstance(computer.get_mac(), MACAddress)
        assert computer.get_mac() in computer.macs

        computer.interfaces.clear()
        with pytest.raises(NoSuchInterfaceError):
            computer.get_mac()


@pytest.mark.parametrize(
    "valid_name, invalid_name",
    [
        ("HelloWorld", ""),
        ("my_good_name", "h"),
        ("Computer Name 1234_3", "123213123"),
    ]
)
def test_set_name(example_computers_with_graphics, valid_name, invalid_name):
    for computer in example_computers_with_graphics:

        computer.set_name(valid_name)
        assert computer.name == valid_name

        with pytest.raises(PopupWindowWithThisError):
            computer.set_name(valid_name)

        with pytest.raises(PopupWindowWithThisError):
            computer.set_name(invalid_name)


@pytest.mark.parametrize(
    "interface_name, is_promisc",
    [
        ("c1i1", True),
        ("c1i0", False),
    ]
)
def test_start_sniffing_REGULAR(example_computers_with_graphics, interface_name, is_promisc):
    for computer in example_computers_with_graphics:
        computer.start_sniffing(interface_name, is_promisc)

        process = computer.process_scheduler.get_process_by_type(SniffingProcess)

        assert process.socket.interface.name == interface_name
        if is_promisc:
            assert process.socket.interface.is_promisc


def test_start_sniffing_ANY(example_computers_with_graphics):
    for computer in example_computers_with_graphics:
        computer.start_sniffing(INTERFACES.ANY_INTERFACE, False)

        process = computer.process_scheduler.get_process_by_type(SniffingProcess)

        assert process.socket.interface is INTERFACES.ANY_INTERFACE


# def test_stop_all_sniffing(self):
#     self.process_scheduler.kill_all_usermode_processes_by_type(SniffingProcess)


# def test_toggle_sniff(self, interface_name: Optional[str] = INTERFACES.ANY_INTERFACE, is_promisc: bool = False):
#     """
#     Toggles sniffing.
#     TODO: if the sniffing is already on - the toggle will turn off ALL sniffing on the computer :( - not only on the specific interface requested
#     """
#     if self.process_scheduler.is_usermode_process_running_by_type(SniffingProcess):
#         self.stop_all_sniffing()
#     else:
#         self.start_sniffing(interface_name, is_promisc)
#
# def test_new_packets_since(self, time_: T_Time, is_raw: bool = False):
#     """
#     Returns a list of all the new `ReturnedPacket`s that were received in the last `seconds` seconds.
#     :param is_raw: Whether or not the operation system is allowed to perform some actions on the packets before handing them over to processes
#     :param time_: a number of seconds.
#     """
#     return list(filter(lambda rp: rp.metadata.time > time_, (self.received_raw if is_raw else self.received)))
#
# # --------------------------------------- v  Computer power  v ------------------------------------------------
#
# def test_power(self):
#     """
#     Powers the computer on or off.
#     """
#     self.is_powered_on = not self.is_powered_on
#
#     for interface in self.all_interfaces:
#         interface.is_powered_on = self.is_powered_on
#         # TODO: add UP and DOWN for interfaces.
#
#     if self.is_powered_on:
#         self.on_startup()
#     else:
#         self.on_shutdown()
#
# def test_on_shutdown(self):
#     """
#     Things the computer should perform as it is shut down.
#     :return:
#     """
#     self.boot_time = None
#     self.process_scheduler.on_shutdown()
#     self.filesystem.wipe_temporary_directories()
#     self.arp_cache.wipe()
#     self.dns_cache.wipe()
#     self._remove_all_sockets()
#     self._close_all_shells()
#
#     self._active_packet_fragments.clear()
#     self._packet_sending_queues.clear()
#     self.received.clear()
#     self.received_raw.clear()
#
# def test_on_startup(self):
#     """
#     Things the computer should do when it is turned on
#     :return:
#     """
#     self.boot_time = self.main_loop.time()
#     self.process_scheduler.run_startup_processes()
#
#     self.icmp_sequence_number = 0
#     self._latest_ip_id = random.randint(0, PROTOCOLS.IP.MAX_IP_ID)
#
# def test_garbage_cleanup(self):
#     """
#     This method runs continuously and removes unused resources on the computer (sockets, processes, etc...)
#     """
#     self._cleanup_unused_sockets()
#     self._cleanup_unused_packet_sending_queues()
#     self._forget_old_ip_fragments()
#     self.arp_cache.forget_old_items()
#     self.dns_cache.forget_old_items()
#
# # --------------------------------------- v  Interface and Connections  v ------------------------------------------------
#
# def test_add_interface(self,
#                   name: Optional[str] = None,
#                   mac: Optional[Union[str, MACAddress]] = None,
#                   type_: str = INTERFACES.TYPE.ETHERNET):
#     """
#     Adds an interface to the computer with a given name.
#     If the name already exists, raise a DeviceNameAlreadyExists.
#     If no name is given, randomize.
#     """
#     interface_type_to_object = {
#         INTERFACES.TYPE.ETHERNET: Interface,
#         INTERFACES.TYPE.WIFI: WirelessNetworkInterface,
#     }
#
#     if any(interface.name == name for interface in self.all_interfaces):
#         raise DeviceNameAlreadyExists("Cannot have two interfaces with the same name!!!")
#
#     interface_class = interface_type_to_object[type_]
#
#     new_interface = interface_class((MACAddress.randomac() if mac is not None else mac), name=name)
#     self.interfaces.append(new_interface)
#     self.graphics.add_interface(new_interface)
#     return new_interface
#
# def test_remove_interface(self, name: str):
#     """
#     Removes a computer interface that is named `name`
#     """
#     interface = get_the_one(self.interfaces, lambda i: i.name == name)
#     if interface.is_connected():
#         raise DeviceAlreadyConnectedError("Cannot remove a connected interface!!!")
#     if interface.has_ip():
#         self.routing_table.delete_interface(interface)
#     self.interfaces.remove(interface)
#     self.main_loop.unregister_graphics_object(interface.graphics)
#     self.graphics.update_text()
#
# def test_available_interface(self):
#     """
#     Returns an interface of the computer that is disconnected and
#     is available to connect to another computer.
#     If the computer has no available interfaces, creates one and returns it.
#     """
#     try:
#         return get_the_one(self.interfaces, lambda i: not i.is_connected(), NoSuchInterfaceError)
#     except NoSuchInterfaceError:
#         interface = self.add_interface()
#         self.main_loop.register_graphics_object(interface.graphics)
#         return interface
#
# def test_disconnect(self, connection: Connection):
#     """
#     Receives a `Connection` object and disconnects the appropriate interface from that connection.
#     """
#     for interface in self.interfaces:
#         if interface.connection is connection.left_side or interface.connection is connection.right_side:
#             interface.disconnect()
#             return
#
# def test_same_subnet_interfaces(self, ip_address: IPAddress):
#     """
#     Returns all of the interfaces of the computer that are in the same subnet as the given IP address.
#     It is tested (naturally) using the subnet mask of the given `IPAddress` object.
#     :param ip_address: The `IPAddress` object whose subnet we are talking about.
#     :return: an `Interface` list of the Interface objects in the same subnet.
#     """
#     return [interface for interface in self.all_interfaces
#             if interface.has_ip() and interface.ip.is_same_subnet(ip_address)]
#
# def test_interface_by_name(self, name: str):
#     """
#     Receives an interface name and returns the `Interface`
#     """
#     return get_the_one(
#         self.all_interfaces,
#         lambda c: c.name == name,
#         NoSuchInterfaceError
#     )
#
# # --------------------------------------- v  IP and routing  v -----------------------------------------------------------
#
# def test_has_ip(self):
#     """Returns whether or not this computer has an IP address at all (on any of its interfaces)"""
#     return any(interface.has_ip() for interface in self.interfaces)
#
# def test_get_ip(self):
#     """
#     Returns one of the ip addresses of this computer. Currently - the first one, but this is not guaranteed and
#     should not be relied upon.
#     """
#     if not self.has_ip():
#         raise NoIPAddressError("This computer has no IP address!")
#     return get_the_one(self.interfaces, lambda i: i.has_ip(), NoSuchInterfaceError).ip
#
# def test_has_this_ip(self, ip_address: Optional[Union[str, IPAddress]]):
#     """Returns whether or not this computer has a given IP address. (so whether or not if it is its address)"""
#     if ip_address is None:
#         # raise NoIPAddressError("The address that is given is None!!!")
#         return False
#
#     if isinstance(ip_address, str):
#         ip_address = IPAddress(ip_address)
#
#     return any(interface.has_ip() and interface.ip.string_ip == ip_address.string_ip
#                for interface in self.all_interfaces)
#
# def test_get_interface_with_ip(self, ip_address: Optional[IPAddress] = None):
#     """
#     Returns the interface that has this ip_address.
#     If there is none that have that address, return None.
#
#     If no IP address is given, returns one interface that has any IP address.
#     """
#     if ip_address is None:
#         return get_the_one(self.interfaces, lambda i: i.has_ip(), NoSuchInterfaceError)
#     return get_the_one(self.all_interfaces, lambda i: i.has_this_ip(ip_address))
#
# def test_is_arp_for_me(self, packet: Packet):
#     """Returns whether or not the packet is an ARP request for one of your IP addresses"""
#     return "ARP" in packet and \
#            packet["ARP"].opcode == OPCODES.ARP.REQUEST and \
#            self.has_this_ip(packet["ARP"].dst_ip)
#
# def test_is_for_me(self, packet: Packet):
#     """
#     Takes in a packet and returns whether or not that packet is meant for this computer. (On the second layer)
#     If broadcast, return True.
#     """
#     return any([interface.is_for_me(packet) for interface in self.interfaces])
#
# def test_is_directly_for_me(self, packet: Packet):
#     """
#     Takes in a packet and returns whether or not that packet is meant for this computer directly (not broadcast).
#     :param packet: a `Packet` object.
#     :return: boolean
#     """
#     return any([interface.is_directly_for_me(packet) for interface in self.interfaces])
#
# def test_update_routing_table(self):
#     """updates the routing table according to the interfaces at the moment"""
#     self.routing_table = RoutingTable.create_default(self)
#
# def test_set_default_gateway(self, gateway_ip: IPAddress, interface_ip: Optional[IPAddress] = None):
#     """
#     Sets the default gateway of the computer in the routing table with the interface IP that the packets to
#     that gateway will be sent from.
#     :param gateway_ip: The `IPAddress` of the default gateway.
#     :param interface_ip: The `IPAddress` of the interface that will send the packets to the gateway.
#     :return: None
#     """
#     interface_ip_address = interface_ip
#     if interface_ip is None:
#         interface_ip_address = self.same_subnet_interfaces(gateway_ip)[0].ip
#     self.routing_table[IPAddress("0.0.0.0/0")] = RoutingTableItem(gateway_ip, interface_ip_address)
#     self.routing_table[IPAddress("255.255.255.255/32")] = RoutingTableItem(gateway_ip, interface_ip_address)
#
# def test_set_ip(self, interface: Interface, string_ip: str):
#     """
#     Sets the IP address of a given interface.
#     Updates all relevant attributes of the computer (routing table, DHCP serving, etc...)
#     If there is no interface with that name, `NoSuchInterfaceError` will be raised.
#     :param interface: The `Interface` one wishes to change the IP of
#     :param string_ip: a string IP which will be the new IP of the interface.
#     """
#     if interface is None:
#         raise PopupWindowWithThisError("The computer does not have interfaces!!!")
#
#     self.remove_ip(interface)
#     interface.ip = IPAddress(string_ip)
#
#     if self.process_scheduler.is_usermode_process_running_by_type(DHCPServerProcess):
#         dhcp_server_process = self.process_scheduler.get_usermode_process_by_type(DHCPServerProcess)
#         dhcp_server_process.update_server_data()
#
#     self.routing_table.add_interface(interface.ip)
#     self.graphics.update_text()
#
# def test_remove_ip(self, interface: Interface):
#     """
#     Removes the ip of an interface.
#     """
#     if not interface.has_ip():
#         return
#
#     self.routing_table.delete_interface(interface)
#     interface.ip = None
#
# # --------------------------------------- v  Specific protocol handling  v -------------------------------------------

def test_handle_arp(example_computers):
    with MonkeyPatch.context() as m:
        mock_mainloop_time(m)

        for computer in example_computers:
            cast(CableNetworkInterface, computer.interfaces[0]).connect(CableNetworkInterface())
            packet = Packet(example_ethernet() / example_arp())
            computer._handle_arp(ReturnedPacket(packet, PacketMetadata(computer.interfaces[0], 1.0, PACKET.DIRECTION.INCOMING)))
            to_send = computer.interfaces[0].connection_side._packets_to_send

            assert len(to_send) == 1
            reply, = to_send

            assert packet["ARP"].src_ip in computer.arp_cache
            assert computer.arp_cache[packet["ARP"].src_ip].mac == packet["ARP"].src_mac
            assert "ARP" in reply
            assert reply["ARP"].dst_ip == packet["ARP"].src_ip

# def test__handle_icmp(self, returned_packet: ReturnedPacket):
#     """
#     Receives a `Packet` object which contains an ICMP layer with ICMP request
#     handles everything related to the ping and sends a ping reply.
#     :param returned_packet: the `ReturnedPacket` that contains the ICMP we handle and its metadata
#     :return: None
#     """
#     packet, packet_metadata = returned_packet.packet_and_metadata
#     if (packet["ICMP"].type != OPCODES.ICMP.TYPES.REQUEST) or (not self.is_for_me(packet)):
#         return
#
#     if packet_metadata.interface.has_this_ip(packet["IP"].dst_ip) or (
#             packet_metadata.interface is self.loopback and self.has_this_ip(packet["IP"].dst_ip)):
#         # ^ only if the packet is for me also on the third layer!
#         dst_ip = packet["IP"].src_ip.string_ip
#         self.start_ping_process(
#             dst_ip,
#             OPCODES.ICMP.TYPES.REPLY,
#             mode=COMPUTER.PROCESSES.MODES.KERNELMODE,
#             data=packet["ICMP"].payload.build(),
#             sequence_number=packet["IP"].sequence_number,
#         )
#
# def test__handle_tcp(self, returned_packet: ReturnedPacket):
#     """
#     Receives a TCP packet and decides if it is a TCP SYN to an open port, starts a server process or sends a TCP RST
#     accordingly
#     :param returned_packet: the `ReturnedPacket` that contains the TCP we handle and its metadata
#     :return: None
#     """
#     packet, packet_metadata = returned_packet.packet_and_metadata
#     if not self.has_ip() or not self.has_this_ip(packet["IP"].dst_ip):
#         return
#
#     if not any(self._does_packet_match_tcp_socket_fourtuple(socket, packet)
#                for socket in self.sockets if socket.kind == COMPUTER.SOCKETS.TYPES.SOCK_STREAM) and \
#             not (OPCODES.TCP.RST & packet["TCP"].flags):
#         self.send_to(packet["Ether"].src_mac,
#                      packet["IP"].src_ip,
#                      TCP(dst_port=packet["TCP"].src_port,
#                          src_port=packet["TCP"].dst_port,
#                          sequence_number=0,
#                          flags=OPCODES.TCP.RST))
#
# def test__handle_udp(self, returned_packet: ReturnedPacket):
#     """
#     Handles a UDP packet that is received on the computer
#     :param returned_packet: the `ReturnedPacket` that contains the UDP we handle and its metadata
#     """
#     packet, packet_metadata = returned_packet.packet_and_metadata
#     if not self.has_ip() or not packet_metadata.interface.has_this_ip(packet["IP"].dst_ip):
#         return
#
#     if packet["UDP"].dst_port not in self.get_open_ports("UDP"):
#         self.send_to(packet["Ether"].src_mac, packet["IP"].src_ip, ICMP(
#             type=OPCODES.ICMP.TYPES.UNREACHABLE,
#             code=OPCODES.ICMP.CODES.PORT_UNREACHABLE))
#         # TODO: add the original packet to the ICMP port unreachable packet
#         return
#
#     self._sniff_packet_on_relevant_udp_sockets(packet)
#
# def test__handle_special_packet(self, returned_packet: ReturnedPacket):
#     """
#     Checks if the packet that was received is of some special type that requires handling (ARP, ICMP, TPC-SYN) and
#     if so, calls the appropriate handler.
#     :param returned_packet: a `ReturnedPacket` of a packet object that was received with its metadata
#     :return: None
#     """
#     packet, packet_metadata = returned_packet.packet_and_metadata
#     for packet_type in self.packet_types_and_handlers:
#         if packet_type in packet:
#             self.packet_types_and_handlers[packet_type](returned_packet)
#             continue
#
# def test_start_ping_process(self,
#                        destination: T_Hostname,
#                        opcode: int = OPCODES.ICMP.TYPES.REQUEST,
#                        count: int = 1,
#                        *args: Any,
#                        mode: str = COMPUTER.PROCESSES.MODES.USERMODE,
#                        **kwargs: Any):
#     """
#     Starts sending a ping to another computer.
#     :param mode: The mode in which to run the ping process (usermode / kernelmode)
#     :param destination:
#     :param opcode: the opcode of the ping to send
#     :param count: how many pings to send
#     """
#     self.process_scheduler.start_process(mode, SendPing, destination, opcode, count, *args, **kwargs)
#
# # --------------------------------------- v  IP fragmentation  v -----------------------------------------------------------
#
# def test__send_fragment_ttl_exceeded(self, dst_mac: MACAddress, dst_ip: IPAddress):
#     """
#     Send an ICMP TTL exceeded for a fragmented packet that could be reassembled
#     """
#     self.send_packet_stream_to(
#         COMPUTER.PROCESSES.INIT_PID, COMPUTER.PROCESSES.MODES.KERNELMODE,
#         PROTOCOLS.IP.FRAGMENT_SENDING_INTERVAL,
#         dst_mac,
#         dst_ip,
#         ICMP(
#             type=OPCODES.ICMP.TYPES.TIME_EXCEEDED,
#             code=OPCODES.ICMP.CODES.FRAGMENT_TTL_EXCEEDED,
#         )
#     )
#
# def test__pop_fragments(self, fragments: Iterable[Packet]):
#     """
#     Remove from the `_active_packet_fragments` list all of the fragments supplied
#     """
#     for active_fragment in self._active_packet_fragments[:]:
#         for fragment in fragments:
#             if active_fragment.packet == fragment:
#                 self._active_packet_fragments.remove(active_fragment)
#
# def test__handle_ip_fragments(self, returned_packet: ReturnedPacket):
#     """
#     Takes in a `ReturnedPacket` that maybe needs to be reassembled from IP fragments, and reassemble all fragments of it.
#         If the packet is not really a fragment - do nothing and return it
#         If it has more fragments coming, store it and do nothing - return None
#         If it is the last one - reassemble all fragments and return the new `ReturnedPacket` object that contains the united packet
#     """
#     last_fragment, last_fragment_metadata = returned_packet.packet_and_metadata
#     if not needs_reassembly(last_fragment) or not self.has_this_ip(get_dst_ip(returned_packet.packet)):
#         return returned_packet
#
#     self._active_packet_fragments.append(returned_packet)
#     same_packet_fragments = [fragment.packet for fragment in self._active_packet_fragments if fragment.packet["IP"].id == last_fragment["IP"].id]
#     if not are_fragments_valid(same_packet_fragments):
#         return None
#
#     self._pop_fragments(same_packet_fragments)
#     return ReturnedPacket(reassemble_fragmented_packet(same_packet_fragments), last_fragment_metadata)
#
# def test__forget_old_ip_fragments(self):
#     """
#     Check all active ip fragments in the computer
#     Delete the ones that are too old
#     Send an ICMP fragment TTL exceeded for them
#     """
#     active_ip_ids = {fragment.packet["IP"].id for fragment in self._active_packet_fragments}
#     for ip_id in active_ip_ids:
#         latest_sibling_fragment = max(
#             [rp for rp in self._active_packet_fragments if rp.packet["IP"].id == ip_id],
#             key=lambda rp: rp.metadata.time,
#         )
#         if self.main_loop.time_since(latest_sibling_fragment.metadata.time) > PROTOCOLS.IP.FRAGMENT_DROP_TIMEOUT:
#             fragment = None
#             for fragment in self._active_packet_fragments[:]:
#                 if fragment.packet["IP"].id == ip_id:
#                     self._active_packet_fragments.remove(fragment)
#             self._send_fragment_ttl_exceeded(fragment.packet["Ether"].src_mac, fragment.packet["IP"].src_ip)
#
# # --------------------------------------- v  DHCP and DNS  v -----------------------------------------------------------
#
# def test_ask_dhcp(self):
#     """
#     Start a `DHCPClientProcess` process to receive an IP address!
#     One can read more at the 'dhcp_process.py' file.
#     :return: None
#     """
#     self.process_scheduler.kill_all_usermode_processes_by_type(DHCPClientProcess)  # if currently asking for dhcp, stop it
#     self.process_scheduler.start_usermode_process(DHCPClientProcess)
#
# def test_set_dns_server_for_dhcp_server(self, dns_server: IPAddress):
#     """
#     Assumes that the computer is a DHCP server
#     Sets the address of the DNS server that the DHCPServerProcess give new clients
#     """
#     self.process_scheduler.get_usermode_process_by_type(DHCPServerProcess).dns_server = dns_server
#
# def test_set_domain_for_dhcp_server(self, domain: T_Hostname):
#     """
#     Assumes that the computer is a DHCP server
#     Sets the default name of the domain that the DHCPServerProcess give new clients
#     """
#     self.process_scheduler.get_usermode_process_by_type(DHCPServerProcess).domain = domain
#
# def test_resolve_domain_name(self,
#                         requesting_process: Process,
#                         name: T_Hostname,
#                         dns_server: Optional[IPAddress] = None):
#     """
#     A generator to `yield from` inside processes
#     The generator eventually will return the IPAddress that matches the supplied domain hostname
#     Can be used like this:
#         >>> ip_address = yield from self.resolve_domain_name(...)
#
#     If the name is a valid IPAddress - just cast it and return :)
#     """
#     if IPAddress.is_valid(name):
#         return IPAddress(name)
#
#     validate_domain_hostname(name)
#     yield from DNSClientProcess(requesting_process.pid, self, (dns_server if dns_server is not None else self.dns_server), name).code()
#     return self.dns_cache[self.add_default_domain_prefix_if_necessary(name)].ip_address
#
# def test_add_dns_entry(self, user_inserted_dns_entry_format: str):
#     """
#     Adds a new mapping between a hostname and an ip address in the computer's DNS zone file
#     :param user_inserted_dns_entry_format: "{hostname} {ipaddress}"
#     """
#     hostname, ip_address = user_inserted_dns_entry_format.split()
#     self.process_scheduler.get_usermode_process_by_type(DNSServerProcess).add_dns_record(
#         canonize_domain_hostname(hostname),
#         IPAddress(ip_address),
#     )
#
# def test_add_remove_dns_zone(self, zone_name: T_Hostname):
#     """
#     Add a new zone for the DNS server
#     If it exists - deletes it
#     """
#     self.process_scheduler.get_usermode_process_by_type(DNSServerProcess).add_or_remove_zone(zone_name)
#
# def test_add_default_domain_prefix_if_necessary(self, name_to_resolve: T_Hostname):
#     """
#     If the name to resolve was `Hello` and the default domain of the computer was `tomer.noyman.`
#         then the process's name to resolve will be set to `Hello.tomer.noyman.`
#     """
#     if ('.' in name_to_resolve) or (self.domain is None):
#         return name_to_resolve  # no need for the prefix
#     return canonize_domain_hostname(name_to_resolve, self.domain)
#
# # ------------------------- v  Packet sending and wrapping  v ---------------------------------------------
#
# def test_send(self, packet: Packet, interface: Optional[Interface] = None, sending_socket: Optional[RawSocket] = None):
#     """
#     Every sent packet from the computer should pass through this function!!!!!!!
#
#     Takes a full and ready packet and sends it
#         Sniffs the packet on the relevant RawSocket-s
#         Fragments the packet if necessary
#
#     :param packet: a valid `Packet` object.
#     :param interface: the `Interface` to send the packet on. If None - calculate by routing table
#     :param sending_socket: the `RawSocket` object that sent the packet (if was sent using a raw socket
#         it should not be sniffed on that same one as outgoing)
#     """
#     if interface is None:
#         interface = self.get_interface_with_ip(self.routing_table[packet["IP"].dst_ip].interface_ip)
#
#     if not packet.is_valid():
#         return
#
#     if needs_fragmentation(packet, interface.mtu):
#         if not allows_fragmentation(packet):
#             raise PacketTooLongButDoesNotAllowFragmentation("Packet is too long and should be fragmented, but DONT_FRAGMENT flag is set!!!")
#
#         self.send_packet_stream(
#             COMPUTER.PROCESSES.INIT_PID,
#             COMPUTER.PROCESSES.MODES.KERNELMODE,
#             fragment_packet(packet, interface.mtu),
#             PROTOCOLS.IP.FRAGMENT_SENDING_INTERVAL,
#             interface,
#             sending_socket,
#         )
#         return
#
#     if not interface.send(packet):
#         return  # interface decided to drop packet :(
#
#     self._sniff_packet_on_relevant_raw_sockets(
#         ReturnedPacket(
#             packet,
#             PacketMetadata(
#                 interface,
#                 self.main_loop.time(),
#                 PACKET.DIRECTION.OUTGOING
#             )
#         ),
#         sending_socket=sending_socket,
#     )
#
# def test_send_with_ethernet(self, dst_mac: MACAddress, dst_ip: IPAddress, data: Union[str, bytes, scapy.packet.Packet]):
#     """
#     Just like `send_to` only does not add the IP layer.
#     """
#     interface = self.get_interface_with_ip(self.routing_table[dst_ip].interface_ip)
#     self.send(
#         interface.ethernet_wrap(dst_mac, data),
#         interface=interface,
#     )
#
# def test_send_packet_stream_with_ethernet(self,
#                                      pid: int,
#                                      mode: str,
#                                      interval_between_packets: T_Time,
#                                      dst_mac: MACAddress,
#                                      dst_ip: IPAddress,
#                                      datas: List[Union[str, bytes, scapy.packet.Packet]]):
#     """
#     Just like `send_packet_stream` only applies `ethernet_wrap` on each of the packets
#     """
#     interface = self.get_interface_with_ip(self.routing_table[dst_ip].interface_ip)
#     self.send_packet_stream(
#         pid, mode,
#         (interface.ethernet_wrap(dst_mac, data) for data in datas),
#         interval_between_packets,
#         interface,
#     )
#
# def test_send_to(self, dst_mac: MACAddress, dst_ip: IPAddress, packet: Packet, **kwargs: Any):
#     """
#     Receives destination addresses and a packet, wraps the packet with IP
#     and Ethernet as required and sends it out.
#     :param dst_mac: destination `MACAddress` of the packet
#     :param dst_ip: destination `IPAddress` of the packet
#     :param packet: packet to wrap. Could be anything, should be something the destination computer expects.
#     """
#     self.send(self.ip_wrap(dst_mac, dst_ip, packet, id=self._latest_ip_id, **kwargs))
#     self._latest_ip_id = (self._latest_ip_id + 1) % (PROTOCOLS.IP.MAX_IP_ID + 1)
#
# def test_send_packet_stream_to(self,
#                           pid: int,
#                           mode: str,
#                           interval_between_packets: T_Time,
#                           dst_mac: MACAddress,
#                           dst_ip: IPAddress,
#                           datas: List[Union[str, bytes, scapy.packet.Packet]]):
#     """
#     Just like `send_packet_stream` only applies `ethernet_wrap` on each of the packets
#     """
#     self.send_packet_stream(
#         pid, mode,
#         (self.ip_wrap(dst_mac, dst_ip, data) for data in datas),
#         interval_between_packets,
#     )
#
# def test_ip_wrap(self, dst_mac: MACAddress, dst_ip: IPAddress, protocol: scapy.packet.Packet, ttl: Optional[int] = None, **kwargs: Any):
#     """
#     Takes in some protocol and wraps it up in Ethernet and IP with the appropriate MAC and IP addresses and TTL all
#     ready to be sent.
#     :param ttl:
#     :param dst_mac:
#     :param dst_ip:
#     :param protocol:  The thing to wrap in IP
#     """
#     interface = self.get_interface_with_ip(self.routing_table[dst_ip].interface_ip)
#     return interface.ethernet_wrap(dst_mac, IP(
#         src_ip=str(interface.ip),
#         dst_ip=str(dst_ip),
#         ttl=ttl or TTL.BY_OS[self.os],
#         **kwargs,
#     ) / protocol)
#
# def test_udp_wrap(self, dst_mac: MACAddress, dst_ip: IPAddress, src_port: T_Port, dst_port: T_Port, protocol: scapy.packet.Packet):
#     """
#     Takes in some protocol and wraps it up in Ethernet and IP with the appropriate MAC and IP addresses and TTL and UDP with the supplied ports
#     all ready to be sent
#     """
#     return self.ip_wrap(dst_mac, dst_ip, UDP(sport=src_port, dport=dst_port) / protocol)
#
# def test_start_sending_udp_packet(self, dst_ip: IPAddress, src_port: T_Port, dst_port: T_Port, data: Union[str, bytes, scapy.packet.Packet]):
#     """
#     Takes in some protocol and wraps it up in IP with the appropriate IP addresses and TTL.
#     Starts a process to resolve the MAC and once resolved - construct the packet and send it.
#     :param dst_ip:
#     :param dst_port:
#     :param src_port:
#     :param data: The thing to wrap in IP
#     """
#     interface = self.get_interface_with_ip(self.routing_table[dst_ip].interface_ip)
#     self.process_scheduler.start_kernelmode_process(SendPacketWithARPProcess,
#                                                     IP(src=str(interface.ip), dst=str(dst_ip),
#                                                        ttl=TTL.BY_OS[self.os]) / UDP(sport=src_port,
#                                                                                      dport=dst_port) / data)
#
# def test_send_arp_to(self, ip_address: IPAddress):
#     """
#     Constructs and sends an ARP request to a given IP address.
#     :param ip_address: a ip_layer of the IP address you want to find the MAC for.
#     :return: None
#     """
#     interface_ip = self.routing_table[ip_address].interface_ip
#     interface = self.get_interface_with_ip(interface_ip)
#     arp = ARP(opcode=OPCODES.ARP.REQUEST,
#               src_ip=str(interface.ip),
#               dst_ip=str(ip_address),
#               src_mac=str(interface.mac))
#     if interface.ip is None:
#         arp = ARP.create_probe(ip_address, interface.mac)
#     self.send(interface.ethernet_wrap(MACAddress.broadcast(), arp), interface)
#
# def test_send_arp_reply(self, request: Packet):
#     """
#     Receives a `Packet` object that is the ARP request you answer for.
#     Sends back an appropriate ARP reply.
#     This should only called if the ARP is for this computer (If not raises an exception!)
#     If the packet does not contain an ARP layer, raise NoARPLayerError.
#     :param request: a Packet object that contains an ARP layer.
#     :return: None
#     """
#     try:
#         sender_ip, requested_ip = request["ARP"].src_ip, request["ARP"].dst_ip
#     except KeyError:
#         raise NoARPLayerError("The packet has no ARP layer!!!")
#
#     if not self.has_this_ip(requested_ip):
#         raise WrongUsageError("Do not call this method if the ARP is not for me!!!")
#
#     interface = self.get_interface_with_ip(requested_ip)
#     arp = ARP(op=OPCODES.ARP.REPLY, psrc=str(request["ARP"].dst_ip), pdst=str(sender_ip), hwsrc=str(interface.mac),
#               hwdst=str(request["ARP"].src_mac))
#     self.send(interface.ethernet_wrap(request["ARP"].src_mac, arp), interface)
#
# def test_arp_grat(self, interface: Interface):
#     """
#     Send a gratuitous ARP from a given interface.
#     If the interface has no IP address, do nothing.
#     :param interface: an `Interface` object.
#     :return: None
#     """
#     if self.has_ip() and SENDING_GRAT_ARPS:
#         if interface.has_ip():
#             self.send(
#                 interface.ethernet_wrap(MACAddress.broadcast(),
#                                         ARP(op=OPCODES.ARP.GRAT, psrc=str(interface.ip), pdst=str(interface.ip), hwsrc=str(interface.mac))),
#                 interface
#             )
#
# def test_send_ping_to(self,
#                  mac_address: MACAddress,
#                  ip_address: IPAddress,
#                  type_: int = OPCODES.ICMP.TYPES.REQUEST,
#                  data: Union[str, bytes] = '',
#                  code: Optional[int] = None,
#                  sequence_number: Optional[int] = None,
#                  **kwargs: Any):
#     """
#     Send an ICMP packet to the a given ip address.
#     """
#     if sequence_number is None:
#         self.icmp_sequence_number += 1
#
#     self.send_to(
#         mac_address,
#         ip_address,
#         (ICMP(type=type_, code=code, sequence_number=(sequence_number if sequence_number is not None else self.icmp_sequence_number)) / data),
#         **kwargs,
#     )
#
# def test_send_time_exceeded(self, dst_mac: MACAddress, dst_ip: IPAddress, data: Union[str, bytes] = ''):
#     """
#     Sends an ICMP time exceeded packet.
#     It has the maximum time to live (must be more than the original packet it sends a time exceeded for)
#     :return: None
#     """
#     interface = self.get_interface_with_ip(self.routing_table[dst_ip].interface_ip)
#     self.send(
#         interface.ethernet_wrap(dst_mac,
#                                 IP(src=str(interface.ip), dst=str(dst_ip), ttl=TTL.MAX) /
#                                 ICMP(type=OPCODES.ICMP.TYPES.TIME_EXCEEDED, code=OPCODES.ICMP.CODES.TRANSIT_TTL_EXCEEDED) /
#                                 data),
#         interface
#     )
#
# def test_validate_dhcp_given_ip(self, ip_address: IPAddress):
#     """
#     This is for future implementation if you want, for now it is not doing anything, just making sure that no two
#     interfaces get the same IP address.
#     :return: theoretically, whether or not the interface approves of the address given to it by DHCP server.
#     """
#     return not any(interface.has_this_ip(ip_address) for interface in self.interfaces)
#
# def test_resolve_ip_address(self,
#                        ip_address: IPAddress,
#                        requesting_process: Process):
#     """
#     Receives an `IPAddress` and sends ARPs to it until it finds it or it did not answer for a long time.
#     This function actually starts a process that does that.
#     :param ip_address: an `IPAddress` object to look for
#     :param requesting_process: the process that is sending the ARP request.
#     :return: The actual IP address it is looking for (The IP of your gateway (or the original if in the same subnet))
#     and a condition to test whether or not the process is done looking for the IP.
#     """
#     ip_for_the_mac = self.routing_table[ip_address].ip_address
#     yield from ARPProcess(requesting_process.pid, self, ip_for_the_mac.string_ip).code()
#     return ip_for_the_mac, self.arp_cache[ip_for_the_mac].mac
#
# def test_send_packet_stream(self,
#                        pid: int,
#                        mode: str,
#                        packets: Iterator[Packet],
#                        interval_between_packets: T_Time,
#                        interface: Optional[Interface] = None,
#                        sending_socket: Optional[RawSocket] = None):
#     """
#     Send a large amount of packets that should be sent in quick succession one after the other
#     This will make sure they are sent with the appropriate time gaps - in order to allow the user to see them
#     """
#     existing_sending_queue = self.get_packet_sending_queue(pid, mode)
#     if existing_sending_queue is not None:
#         existing_sending_queue.packets.extend(packets)
#         return
#
#     self._packet_sending_queues.append(
#         PacketSendingQueue(
#             self,
#             pid,
#             mode,
#             deque(packets),
#             interval_between_packets,
#             interface,
#             sending_socket,
#         )
#     )
#
# def test__handle_packet_streams(self):
#     """
#     Allows all of the PacketSendingQueue-s to perform their actions (send their packets with time gaps)
#     Deletes the queues that are done sending.
#     """
#     for packet_sending_queue in self._packet_sending_queues[:]:
#         packet_sending_queue.send_packets_with_time_gaps()
#
# def test__cleanup_unused_packet_sending_queues(self):
#     """
#     Remove PacketSendingQueues that have no running process attached to them
#     """
#     for packet_sending_queue in self._packet_sending_queues[:]:
#         if not self.process_scheduler.is_process_running(packet_sending_queue.pid, packet_sending_queue.process_mode) and \
#            packet_sending_queue.pid != COMPUTER.PROCESSES.INIT_PID:
#             self._packet_sending_queues.remove(packet_sending_queue)
#
# def test_get_packet_sending_queue(self, pid: int, mode: str):
#     """
#     Get the PacketSendingQueue object of the process with the given ID
#     """
#     return get_the_one(self._packet_sending_queues, lambda psq: (psq.pid == pid and psq.process_mode == mode))
#
# # ------------------------------- v  Sockets  v ----------------------------------------------------------------------
#
# def test_get_socket(self,
#                requesting_process_pid: int,
#                address_family: int = COMPUTER.SOCKETS.ADDRESS_FAMILIES.AF_INET,
#                kind: int = COMPUTER.SOCKETS.TYPES.SOCK_STREAM):
#     """
#     Allows programs on the computer to acquire a network socket.
#     """
#     socket = {
#         COMPUTER.SOCKETS.TYPES.SOCK_STREAM: TCPSocket,
#         COMPUTER.SOCKETS.TYPES.SOCK_RAW: RawSocket,
#         COMPUTER.SOCKETS.TYPES.SOCK_DGRAM: UDPSocket,
#     }[kind](self, address_family)
#
#     self.sockets[socket] = SocketData(
#         kind=kind,
#         local_ip_address=None,
#         local_port=None,
#         remote_ip_address=None,
#         remote_port=None,
#         state=COMPUTER.SOCKETS.STATES.UNBOUND,
#         pid=requesting_process_pid,
#     )
#     return socket
#
# def test_get_udp_socket(self, requesting_process_pid: int):
#     """
#     Allows programs on the computer to acquire a UDP network socket.
#     """
#     returned = self.get_socket(requesting_process_pid, kind=COMPUTER.SOCKETS.TYPES.SOCK_DGRAM)
#     if isinstance(returned, UDPSocket):
#         return returned
#
#     raise ThisCodeShouldNotBeReached(f"Socket {returned} is not a UDPSocket!!! it is a {type(returned)}. "
#                                      f"This means `get_socket` returned the wrong type")
#
# def test_get_tcp_socket(self, requesting_process_pid: int):
#     """
#     Allows programs on the computer to acquire a TCP network socket.
#     """
#     returned = self.get_socket(requesting_process_pid)
#     if isinstance(returned, TCPSocket):
#         return returned
#
#     raise ThisCodeShouldNotBeReached(f"Socket {returned} is not a TCPSocket!!! it is a {type(returned)}. "
#                                      f"This means `get_socket` returned the wrong type")
#
# def test_get_raw_socket(self, requesting_process_pid: int):
#     """
#     Allows programs on the computer to acquire a raw network socket.
#     """
#     returned = self.get_socket(requesting_process_pid, kind=COMPUTER.SOCKETS.TYPES.SOCK_RAW)
#     if isinstance(returned, RawSocket):
#         return returned
#
#     raise ThisCodeShouldNotBeReached(f"Socket {returned} is not a RawSocket!!! it is a {type(returned)}. "
#                                      f"This means `get_socket` returned the wrong type")
#
# def test__is_port_taken(self, port: T_Port, kind: int = COMPUTER.SOCKETS.TYPES.SOCK_STREAM):
#     """
#     Returns whether or not a port is already bound to a socket.
#     """
#
#     def is_registered_on_port(socket_data: SocketData):
#         return socket_data.local_port == port and \
#                socket_data.kind == kind and \
#                socket_data.state == COMPUTER.SOCKETS.STATES.LISTENING
#
#     return any(map(is_registered_on_port, self.sockets.values()))
#
# def test_get_open_ports(self, protocol: Optional[str] = None):
#     """
#     Returns a list of the ports that are open on the computer.
#     Can filter by protocol ("TCP" / "UDP") if supplied
#     """
#     if protocol is None:
#         return reduce(concat, [self.get_open_ports(protocol) for protocol in COMPUTER.SOCKETS.L4_PROTOCOLS.values()])
#
#     return [socket_data.local_port for socket, socket_data in self.sockets.items()
#             if socket_data.state in [COMPUTER.SOCKETS.STATES.BOUND,
#                                      COMPUTER.SOCKETS.STATES.LISTENING,
#                                      COMPUTER.SOCKETS.STATES.ESTABLISHED] and
#             isinstance(socket, L4Socket) and socket.protocol == protocol]
#
# def test_bind_socket(self, socket: Socket, address: Tuple[IPAddress, T_Port]):
#     """
#     bind a socket you acquired from the computer to a specific port and address.
#     :param socket: a return value of `self.get_socket`
#     :param address: (IPAddress, int)
#     """
#     ip_address, port = address
#
#     if self._is_port_taken(port, socket.kind):
#         raise PortAlreadyBoundError(f"The socket cannot be bound, since another socket is listening on port {port}")
#
#     try:
#         self.sockets[socket].local_ip_address = ip_address
#         self.sockets[socket].local_port = port
#         self.sockets[socket].state = COMPUTER.SOCKETS.STATES.BOUND
#     except KeyError:
#         raise SocketNotRegisteredError(f"The socket that was provided is not known to the operation system! "
#                                        f"It was probably not acquired using the `computer.get_socket` method! "
#                                        f"The socket: {socket}")
#
#     socket.is_bound = True
#
# def test_remove_socket(self, socket: Socket):
#     """
#     Remove a socket from the operation system's management
#     """
#     try:
#         self.sockets.pop(socket)
#     except KeyError:
#         raise SocketNotRegisteredError(f"The socket that was provided is not known to the operation system! "
#                                        f"It was probably not acquired using the `computer.get_socket` method! "
#                                        f"The socket: {socket}")
#
# def test__remove_all_sockets(self):
#     """
#     Unregisters all of the sockets of the computer
#     :return:
#     """
#     for socket in list(self.sockets):
#         self.remove_socket(socket)
#
# def test__sniff_packet_on_relevant_raw_sockets(self, returned_packet: ReturnedPacket, sending_socket: Optional[RawSocket] = None):
#     """
#     Receive a packet on all raw sockets that this packet fits their filter
#
#     :param returned_packet:    The ReturnedPacket object that is sniffed
#     :param sending_socket the `RawSocket` object the packet was sent from (if it wasn't sent
#         through a raw socket - this will be None)
#     """
#     packet, packet_metadata = returned_packet.packet_and_metadata
#     for raw_socket in self.raw_sockets:
#         if raw_socket != sending_socket and \
#                 raw_socket.is_bound and \
#                 raw_socket.filter(packet) and \
#                 (raw_socket.interface == packet_metadata.interface or
#                  raw_socket.interface is INTERFACES.ANY_INTERFACE):
#             raw_socket.received.append(returned_packet)
#
# def test__sniff_packet_on_relevant_udp_sockets(self, packet: Packet):
#     """
#     Takes in a packet that was received on the computer
#     Hands it over to the sockets it is relevant to.
#     """
#     for socket in self.sockets:
#         if self._does_packet_match_udp_socket_fourtuple(socket, packet):
#             socket.received.append(ReturnedUDPPacket(packet["UDP"].payload.build(), packet["IP"].src_ip, packet["UDP"].src_port))
#
# def test_open_port(self, port_number: int, protocol: str = "TCP"):
#     """
#     Opens a port on the computer. Starts the process that is behind it.
#     """
#     if protocol not in self.PORTS_TO_PROCESSES:
#         raise UnknownPacketTypeError(f"Protocol type must be one of {list(self.PORTS_TO_PROCESSES.keys())} not {protocol!r}")
#
#     if port_number not in self.PORTS_TO_PROCESSES[protocol]:
#         raise PopupWindowWithThisError(f"{port_number} is an unknown {protocol} port!!!")
#
#     process = self.PORTS_TO_PROCESSES[protocol][port_number]
#     if process is not None:
#         if port_number in self.get_open_ports(protocol):
#             self.process_scheduler.kill_all_usermode_processes_by_type(process, force=True)
#         else:
#             self.process_scheduler.start_usermode_process(self.PORTS_TO_PROCESSES[protocol][port_number])
#
# def test__does_packet_match_socket_fourtuple(self, socket: Socket, packet: Packet):
#     """
#     Validates that the packet matches the bound fourtuple of the socket
#     """
#     socket_metadata = self.sockets[socket]
#     if not isinstance(socket, L4Socket):
#         return False
#
#     if socket_metadata.remote_ip_address is not None:  # if socket is connected
#         if socket_metadata.remote_port != get_src_port(packet) or \
#                 socket_metadata.remote_ip_address != packet["IP"].src_ip:
#             return False
#
#     if socket_metadata.local_port != get_dst_port(packet):
#         return False
#
#     if socket_metadata.local_ip_address != IPAddress.no_address() and \
#             socket_metadata.local_ip_address != packet["IP"].dst_ip:
#         return False
#
#     if socket_metadata.local_ip_address == IPAddress.no_address() and \
#             packet["IP"].dst_ip not in self.ips:
#         return False
#     return True
#
# def test__does_packet_match_udp_socket_fourtuple(self, socket: Socket, packet: Packet):
#     """
#     Validates that the packet matches the bound fourtuple of the UDP socket
#     Needs to operate on connected and disconnected sockets as well.
#     """
#     return self.sockets[socket].kind == COMPUTER.SOCKETS.TYPES.SOCK_DGRAM and \
#            "UDP" in packet and \
#            self._does_packet_match_socket_fourtuple(socket, packet)
#
# def test__does_packet_match_tcp_socket_fourtuple(self, socket: Socket, packet: Packet):
#     """
#     Validates that the packet matches the bound fourtuple of the TCP socket
#     Needs to operate on connected and disconnected sockets as well.
#     :param socket: `Socket` object to test
#     :param packet: `Packet` object to test
#     :return: `bool`
#     """
#     return self.sockets[socket].kind == COMPUTER.SOCKETS.TYPES.SOCK_STREAM and \
#            "TCP" in packet and \
#            self._does_packet_match_socket_fourtuple(socket, packet)
#
# def test__cleanup_unused_sockets(self):
#     """
#     Remove sockets that have no process that is using them
#     """
#     for socket, socket_metadata in list(self.sockets.items()):
#         if not self.process_scheduler.is_usermode_process_running(socket_metadata.pid):
#             self.remove_socket(socket)
#
# def test_select(self, socket_list: List[Socket], timeout: Optional[Union[int, float]] = None):
#     """
#     Similar to the `select` syscall of linux
#     Loops over all sockets until one of them has something to receive
#     The selected socket will later be returned. Use in the format:
#         >>> ready_socket = yield from self.select([socket], timeout)
#
#     This is a generator that yields `WaitingFor` objects
#     To use in a computer `Process` - yield from this
#     If the command ended due to a timeout - None will be returned
#     :param socket_list: List[Socket]
#     :param timeout: the amount of seconds to wait before returning without a selected socket
#     """
#     start_time = self.main_loop.time()
#     while True:
#         for socket in socket_list:
#             if socket.has_data_to_receive:
#                 return socket
#         if (timeout is not None) and (start_time + timeout < self.main_loop.time()):
#             return None
#         yield WaitingFor.nothing()
#
# # ------------------------------- v  The main `logic` method of the computer's main loop  v --------------------------
#
# def test_logic(self):
#     """
#     This method operates the computer's sending and receiving logic.
#     (ARPs, Pings, Switching, Routing and so on....)
#
#     In the regular `Computer` class, it receives packets, sniffs them, handles arps, handles pings,
#     handles processes and in the end handles the ARP cache. In that order.
#     :return: None
#     """
#     if not self.is_powered_on:
#         return
#
#     self.received.clear()
#     for interface in self.all_interfaces:
#         if not interface.is_connected():
#             continue
#         for packet in interface.receive():
#             packet_with_metadata = ReturnedPacket(packet, PacketMetadata(interface, self.main_loop.time(), PACKET.DIRECTION.INCOMING))
#             self.received_raw.append(packet_with_metadata)
#             self._sniff_packet_on_relevant_raw_sockets(packet_with_metadata)
#
#             packet_with_metadata = self._handle_ip_fragments(packet_with_metadata)
#             if packet_with_metadata is not None:
#                 self.received.append(packet_with_metadata)
#                 self._handle_special_packet(packet_with_metadata)
#
#     self._handle_packet_streams()
#     self.process_scheduler.handle_processes()
#     self.garbage_cleanup()
#
# def test___repr__(self):
#     """The string representation of the computer"""
#     return f"Computer(name={self.name}, Interfaces={self.interfaces}"
#
# def test___str__(self):
#     """a simple string representation of the computer"""
#     return f"{self.name}"
#
# # ----------------------------------------- v  File Saving  v ----------------------------------------
#
# def test__interfaces_from_dict(cls, dict_: Dict):
#     """
#     Receives a dict from a json file and return a list of interfaces
#     :param dict_:
#     :return:
#     """
#     interface_classes = {INTERFACES.TYPE.ETHERNET: Interface, INTERFACES.TYPE.WIFI: WirelessNetworkInterface}
#     return [interface_classes[iface_dict["type_"]].from_dict_load(iface_dict) for iface_dict in dict_["interfaces"]]
#
# def test_from_dict_load(cls, dict_: Dict):
#     """
#     Load a computer from the dict that is saved into the files
#     :param dict_:
#     :return: Computer
#     """
#     returned = cls(
#         dict_["name"],
#         dict_["os"],
#         None,
#         *cls._interfaces_from_dict(dict_)
#     )
#     returned.routing_table = RoutingTable.from_dict_load(dict_["routing_table"])
#     returned.filesystem = Filesystem.from_dict_load(dict_["filesystem"])
#     # returned.scale_factor = dict_["scale_factor"]
#     return returned
