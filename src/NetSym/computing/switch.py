from __future__ import annotations

from typing import Optional, TYPE_CHECKING, Dict

from NetSym.address.mac_address import MACAddress
from NetSym.computing.computer import Computer, COMPUTER
from NetSym.computing.internals.filesystem.filesystem import Filesystem
from NetSym.computing.internals.network_data_structures.routing_table import RoutingTable
from NetSym.computing.internals.network_interfaces.wireless_network_interface import WirelessNetworkInterface
from NetSym.computing.internals.processes.kernelmode_processes.switching_process import SwitchingProcess
from NetSym.computing.internals.processes.usermode_processes.stp_process import STPProcess, BID
from NetSym.consts import OS, PROTOCOLS, ADDRESSES
from NetSym.packets.all import LLC, STP

if TYPE_CHECKING:
    from NetSym.packets.packet import Packet
    from NetSym.computing.internals.network_interfaces.network_interface import NetworkInterface


class Switch(Computer):
    """
    This class represents a Switch (a device in charge of delivering packets and connection computers in the second layer).
    It switches packets, using flooding and a switching table.
    It has `legs` that are ports, or interfaces. In switch termination they are called legs.

    The switch has a table that helps it learn which MAC address sits behind which leg and so it knows where to send
    the packet (frame) it receives, this table is called the `switching_table`.
    """
    def __init__(self,
                 name: Optional[str] = None,
                 priority: int = PROTOCOLS.STP.DEFAULT_SWITCH_PRIORITY) -> None:
        """
        Initiates the Switch with a given name.
        A switch has a variable `self.is_hub` that allows any switch to become a hub.

        :param name: a string that will be the name of the switch. If `None`, it is randomized.
        """
        super(Switch, self).__init__(name, OS.LINUX, None)

        self.is_hub = False

        self.stp_enabled = True
        self.priority = priority
        self.process_scheduler.add_startup_process(COMPUTER.PROCESSES.MODES.KERNELMODE, SwitchingProcess)

    def is_for_me(self, packet: Packet) -> bool:
        """
        overrides the original `is_for_me` method of `Computer` and adds STP multicast-s.
        :param packet: a `Packet` to test
        :return: whether it is for me or not.
        """
        if self.stp_enabled:
            return (super(Switch, self).is_for_me(packet)) or (packet["Ether"].dst_mac == MACAddress.stp_multicast())
        return super(Switch, self).is_for_me(packet)

    def start_stp(self) -> None:
        """
        Starts the process of STP sending and receiving.
        :return: None
        """
        if not self.process_scheduler.is_usermode_process_running_by_type(STPProcess) and self.interfaces:
            self.process_scheduler.start_usermode_process(STPProcess)

    def send_stp(self, sender_bid: BID, root_bid: BID, distance_to_root: float, age: int, sending_interval: float, root_max_age: float) -> None:
        """
        Sends an STP packet with the given information on all interfaces. (should only be used on a switch)
        """
        for interface in self.interfaces:
            interface.send_with_ethernet(MACAddress.stp_multicast(),
                                         LLC(src_service_access_point=ADDRESSES.LLC.STP_SAP,
                                             dst_service_access_point=ADDRESSES.LLC.STP_SAP,
                                             control_field=ADDRESSES.LLC.STP_CONTROL_FIELD) /
                                         STP(
                                            root_id=root_bid.priority,
                                            root_mac=str(root_bid.mac),
                                            path_cost=distance_to_root,
                                            bridge_id=sender_bid.priority,
                                            bridge_mac=str(sender_bid.mac),
                                            age=age,
                                            max_age=root_max_age,
                                            hello_time=sending_interval,
                                         ))

    @classmethod
    def from_dict_load(cls, dict_: Dict) -> Switch:
        """
        Load a computer from the dict that is saved into the files
        :param dict_:
        :return: Computer
        """
        returned = cls(dict_["name"])
        returned.interfaces = cls._interfaces_from_dict(dict_)
        returned.routing_table = RoutingTable.from_dict_load(dict_["routing_table"])
        returned.filesystem = Filesystem.from_dict_load(dict_["filesystem"])
        # returned.scale_factor = dict_["scale_factor"]
        return returned


class Hub(Switch):
    """
    This class represents a Hub, which is just a Switch that floods every time.
    It operates in the exact same way except that it is very stupid and just
    floods every time and sends all packets to everyone.
    """
    def __init__(self, name: Optional[str] = None) -> None:
        super(Hub, self).__init__(name)
        self.is_hub = True
        self.stp_enabled = True


class Antenna(Switch):
    """
    This class represents an Antenna, which is just a Switch that can send things over radio waves.
    """
    def __init__(self, name: Optional[str] = None, *interfaces: NetworkInterface) -> None:
        super(Antenna, self).__init__(name)
        self.stp_enabled = False
        self.interfaces = [WirelessNetworkInterface()] if not interfaces else list(interfaces)

    @classmethod
    def from_dict_load(cls, dict_: Dict) -> Switch:
        """
        Load a computer from the dict that is saved into the files
        :param dict_:
        :return: Computer
        """
        returned = cls(dict_["name"], *cls._interfaces_from_dict(dict_))
        returned.routing_table = RoutingTable.from_dict_load(dict_["routing_table"])
        returned.filesystem = Filesystem.from_dict_load(dict_["filesystem"])
        # returned.initial_size = dict_["scale_factor"]
        return returned
