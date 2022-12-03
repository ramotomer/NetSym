import pytest
from _pytest.monkeypatch import MonkeyPatch

from NetSym.address.ip_address import IPAddress
from NetSym.computing.internals.network_interfaces.cable_network_interface import CableNetworkInterface
from NetSym.exceptions import NoIPAddressError
from tests.usefuls import mock_mainloop_time


@pytest.fixture
def example_interfaces():
    return [
        CableNetworkInterface(
            "00:11:22:33:44:55",
            "1.2.3.4",
            "interfacename1",
        ),
        CableNetworkInterface(
            "00:11:22:33:44:56",
            "192.168.1.2",
            "interfacename2",
        ),
        CableNetworkInterface(
            "00:11:22:33:44:56",
            name="interfacename3",
        ),
    ]


def test_no_carrier(example_interfaces):
    with MonkeyPatch.context() as m:
        mock_mainloop_time(m)

        assert example_interfaces[0].no_carrier is True

        example_interfaces[0].connect(example_interfaces[1])
        assert example_interfaces[0].no_carrier is False


# def test_random_name(cls):
#     if cls.POSSIBLE_INTERFACE_NAMES is None:
#         cls.POSSIBLE_INTERFACE_NAMES = [line.strip() for line in open(FILE_PATHS.INTERFACE_NAMES_FILE_PATH).readlines()]
#
#     name = random.choice(cls.POSSIBLE_INTERFACE_NAMES) + str(random.randint(0, 10))
#     if name in cls.EXISTING_INTERFACE_NAMES:
#         name = cls.random_name()
#     cls.EXISTING_INTERFACE_NAMES.add(name)
#     return name


def test_with_ip():
    interface = CableNetworkInterface.with_ip("11.22.33.44")
    assert interface.ip == IPAddress("11.22.33.44")


def test_get_ip(example_interfaces):
    with pytest.raises(NoIPAddressError):
        example_interfaces[2].get_ip()

    assert example_interfaces[1].get_ip() == IPAddress("192.168.1.2")
    assert example_interfaces[0].get_ip() == IPAddress("1.2.3.4")


# def test_get_graphics(self):
#     if self.graphics is None:
#         raise GraphicsObjectNotYetInitialized
#
#     return self.graphics
#
# def test_is_directly_for_me(self, packet: Packet):
#     return bool((self.mac == packet["Ether"].dst_mac) or packet["Ether"].dst_mac.is_no_mac())
#
# def test_is_for_me(self, packet: Packet):
#     return self.is_directly_for_me(packet) or (packet["Ether"].dst_mac.is_broadcast())
#
# def test_has_ip(self):
#     return self.ip is not None
#
# def test_has_this_ip(self, ip_address: Union[str, IPAddress]):
#     return self.has_ip() and self.get_ip() == IPAddress(ip_address)
#
# def test_is_connected(self):
#     """Returns whether the interface is connected or not"""
#
# def test_init_graphics(self, parent_computer: ComputerGraphics, x: Optional[float] = None, y: Optional[float] = None):
#     """
#     Initiate the GraphicsObject that represents the interface visually
#     """
#
# def test_set_mac(self, new_mac: MACAddress):
#     self.mac = new_mac
#
# def test_set_name(self, name: str):
#     if name == self.name:
#         raise PopupWindowWithThisError("new computer name is the same as the old one!!!")
#     elif len(name) < 2:
#         raise PopupWindowWithThisError("name too short!!!")
#     elif not any(char.isalpha() for char in name):
#         raise PopupWindowWithThisError("name must contain letters!!!")
#
#     self.name = name
#
# def test_set_mtu(self, mtu: int):
#     if not (PROTOCOLS.ETHERNET.MINIMUM_MTU < mtu <= PROTOCOLS.ETHERNET.MTU):
#         raise PopupWindowWithThisError(f"Invalid MTU {mtu}! valid range - between {PROTOCOLS.ETHERNET.MINIMUM_MTU} and {PROTOCOLS.ETHERNET.MTU}!")
#
#     self.mtu = mtu
#
# def test_disconnect(self):
#     if not self.is_connected():
#         raise InterfaceNotConnectedError("Cannot disconnect an interface that is not connected!")
#     self.connection_side = None
#
# def test_send(self, packet: Packet):
#     if not self.is_powered_on:
#         return False
#
#     if len(packet.data) > (self.mtu + PROTOCOLS.ETHERNET.HEADER_LENGTH):
#         print(f"{self!r} dropped a packet due to MTU being too large! packet is {len(packet.data) - PROTOCOLS.ETHERNET.HEADER_LENGTH} bytes long!"
#               f" MTU is only {self.mtu}")
#         return False
#
#     if self.is_connected() and (not self.is_blocked or (self.is_blocked and self.accepting in packet)):
#         self.connection_side.send(packet)
#         return True
#
# def test_receive(self):
#     if not self.is_powered_on:
#         return []
#
#     if not self.is_connected():
#         raise InterfaceNotConnectedError("The interface is not connected so it cannot receive packets!!!")
#
#     packets = self.connection_side.receive()
#     if self.is_blocked:
#         return list(filter((lambda packet: self.accepting in packet), packets))
#     if self.is_promisc:
#         return packets
#     return list(filter(lambda packet: self.is_for_me(packet), packets))
#
# def test_ethernet_wrap(self, dst_mac: MACAddress, data: scapy.packet.Packet):
#     return Packet(Ether(src_mac=str(self.mac), dst_mac=str(dst_mac)) / data)
#
# def test_send_with_ethernet(self, dst_mac: MACAddress, protocol: scapy.packet.Packet):
#     self.send(self.ethernet_wrap(dst_mac, protocol))
#
# def test_block(self, accept: Optional[str] = None):
#     self.is_blocked = True
#     self.accepting = accept
#
# def test_unblock(self):
#     self.is_blocked = False
#     self.accepting = None
#
# def test_toggle_block(self, accept: Optional[str] = None):
#     if self.is_blocked:
#         self.unblock()
#     else:
#         self.block(accept)
#
# def test___eq__(self, other: Any):
#     return self is other
#
# def test___hash__(self):
#     return hash(id(self))
#
# def test_generate_view_text(self):
#     linesep = '\n'
#     return f"""
# Interface:
# {self.name}
#
# {str(self.mac) if not self.mac.is_no_mac() else ""}
# {repr(self.ip) if self.has_ip() else ''}
# MTU: {self.mtu}
# {"Connected" if self.is_connected() else "Disconnected"}
# {f"Promisc{linesep}" if self.is_promisc else ""}{"Blocked" if
#     self.is_blocked else ""}
# """
#
# def test___init__(self,
#              mac: Optional[Union[str, MACAddress]] = None,
#              ip: Optional[Union[str, IPAddress]] = None,
#              name: Optional[str] = None,
#              connection_side: Optional[ConnectionSide] = None,
#              display_color: T_Color = INTERFACES.COLOR,
#              type_: str = INTERFACES.TYPE.ETHERNET,
#              mtu: int = PROTOCOLS.ETHERNET.MTU):
#     super(CableNetworkInterface, self).__init__(mac, ip, name, connection_side, display_color, type_, mtu)
#
# def test_connection(self):
#     if self.__connection is None:
#         raise NoSuchConnectionError(f"self: {self}, self.__connection: {self.__connection}")
#     return self.__connection
#
# def test_connection_side(self):
#     return self.__connection_side
#
# def test_connection_side(self, value: Optional[BaseConnectionSide]):
#     if (value is not None) and (not isinstance(value, ConnectionSide)):
#         raise WrongUsageError(f"Do not set the `connection_side` of an `CableNetworkInterface` with something that is not a `ConnectionSide` "
#                               f"You inserted {value!r} which is a {type(value)}...")
#
#     self.__connection = None
#     self.__connection_side = value
#
#     if value is not None:
#         self.__connection = value.connection
#
# def test_connection_length(self):
#     if not self.is_connected():
#         raise InterfaceNotConnectedError(repr(self))
#
#     return self.connection.deliver_time
#
# def test_init_graphics(self, parent_computer: ComputerGraphics, x: Optional[float] = None, y: Optional[float] = None):
#     self.graphics = CableNetworkInterfaceGraphics(x, y, self, parent_computer)
#     return self.graphics
#
# def test_is_connected(self):
#     return (self.__connection_side is not None) and (self.__connection is not None)
#
# def test_connect(self, other: CableNetworkInterface):
#     if self.is_connected() or other.is_connected():
#         raise DeviceAlreadyConnectedError("The interface is connected already!!!")
#     connection = Connection()
#     self.connection_side, other.connection_side = connection.get_sides()
#     return connection
#
# def test_disconnect(self):
#     if not self.is_connected():
#         raise InterfaceNotConnectedError("Cannot disconnect an interface that is not connected!")
#     self.connection_side = None
#
# def test_block(self, accept: Optional[str] = None):
#     super(CableNetworkInterface, self).block(accept)
#
#     if self.connection_side is not None:
#         self.connection_side.mark_as_blocked()
#
# def test_unblock(self):
#     super(CableNetworkInterface, self).unblock()
#
#     if self.connection_side is not None:
#         self.connection_side.mark_as_unblocked()
#
# def test___eq__(self, other: Any):
#     return self is other
#
# def test___hash__(self):
#     return hash(id(self))
#
# def test___str__(self):
#     mac = f"\n{self.mac}" if not self.mac.is_no_mac() else ""
#     return f"{self.name}: {mac}" + ('\n' + repr(self.ip) if self.has_ip() else '')
#
# def test___repr__(self):
#     return f"CableNetworkInterface(name={self.name}, mac={self.mac}, ip={self.ip})"
#
# def test_from_dict_load(cls, dict_: Dict):
#     loaded = cls(
#         mac=dict_["mac"],
#         ip=dict_["ip"],
#         name=dict_["name"],
#         type_=dict_["type_"],
#         mtu=dict_.get("mtu", PROTOCOLS.ETHERNET.MTU),
#     )
#
#     return loaded
