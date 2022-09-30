from address.mac_address import MACAddress
from computing.computer import Computer, COMPUTER
from computing.internals.filesystem.filesystem import Filesystem
from computing.internals.processes.kernelmode_processes.switching_process import SwitchingProcess
from computing.internals.processes.usermode_processes.stp_process import STPProcess, BID
from computing.internals.routing_table import RoutingTable
from computing.internals.wireless_interface import WirelessInterface
from consts import OS, PROTOCOLS, IMAGES, CONNECTIONS, ADDRESSES
from gui.tech.computer_graphics import ComputerGraphics
from packets.all import LLC, STP


class Switch(Computer):
    """
    This class represents a Switch (a device in charge of delivering packets and connection computers in the second layer).
    It switches packets, using flooding and a switching table.
    It has `legs` that are ports, or interfaces. In switch termination they are called legs.

    The switch has a table that helps it learn which MAC address sits behind which leg and so it knows where to send
    the packet (frame) it receives, this table is called the `switching_table`.
    """
    def __init__(self, name=None, priority=PROTOCOLS.STP.DEFAULT_SWITCH_PRIORITY):
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

    def show(self, x, y):
        """
        overrides `Computer.show` and shows the same `ComputerGraphics` object only with a switch's photo.
        :param x:
        :param y: coordinates of the computer image.
        :return: None
        """
        self.graphics = ComputerGraphics(x, y, self, IMAGES.COMPUTERS.SWITCH)
        self.loopback.connection.connection.show(self.graphics)

    def is_for_me(self, packet):
        """
        overrides the original `is_for_me` method of `Computer` and adds STP multicast-s.
        :param packet: a `Packet` to test
        :return: whether it is for me or not.
        """
        if self.stp_enabled:
            return (super(Switch, self).is_for_me(packet)) or (packet["Ether"].dst_mac == MACAddress.stp_multicast())
        return super(Switch, self).is_for_me(packet)

    def start_stp(self):
        """
        Starts the process of STP sending and receiving.
        :return: None
        """
        if not self.process_scheduler.is_usermode_process_running_by_type(STPProcess) and self.interfaces:
            self.process_scheduler.start_usermode_process(STPProcess)

    def send_stp(self, sender_bid: BID, root_bid: BID, distance_to_root: int, age: int, sending_interval: int, root_max_age: int) -> None:
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
    def from_dict_load(cls, dict_):
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
    def __init__(self, name=None):
        super(Hub, self).__init__(name)
        self.is_hub = True
        self.stp_enabled = True

    def show(self, x, y):
        """
        Overrides `Switch.show` and shows the same `ComputerGraphics` object only with a hub's photo.
        :param x:
        :param y:  coordinates that the image will have.
        :return: None
        """
        self.graphics = ComputerGraphics(x, y, self, IMAGES.COMPUTERS.HUB)
        self.loopback.connection.connection.show(self.graphics)


class Antenna(Switch):
    """
    This class represents an Antenna, which is just a Switch that can send things over radio waves.
    """
    def __init__(self, name=None, *interfaces):
        super(Antenna, self).__init__(name)
        self.stp_enabled = False
        self.is_supporting_wireless_connections = True
        self.interfaces = [WirelessInterface(frequency=CONNECTIONS.WIRELESS.DEFAULT_FREQUENCY)] if not interfaces else list(interfaces)

    def show(self, x, y):
        """
        Overrides `Switch.show` and shows the same `ComputerGraphics` object only with a antenna's photo.
        :param x:
        :param y:  coordinates that the image will have.
        :return: None
        """
        self.graphics = ComputerGraphics(x, y, self, IMAGES.COMPUTERS.ANTENNA)
        self.loopback.connection.connection.show(self.graphics)

    @classmethod
    def from_dict_load(cls, dict_):
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
