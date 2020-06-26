from address.mac_address import MACAddress
from computing.computer import Computer
from computing.interface import Interface
from consts import *
from gui.tech.computer_graphics import ComputerGraphics
from packets.stp import STP, LogicalLinkControl
from processes.stp_process import STPProcess
from processes.switching_process import SwitchingProcess


class Switch(Computer):
    """
    This class represents a Switch (a device in charge of delivering packets and connection computers in the second layer).
    It switches packets, using flooding and a switching table.
    It has `legs` that are ports, or interfaces. In switch termination they are called legs.

    The switch has a table that helps it learn which MAC address sits behind which leg and so it knows where to send
    the packet (frame) it receives, this table is called the `switching_table`.
    """
    def __init__(self, name=None, priority=DEFAULT_SWITCH_PRIORITY):
        """
        Initiates the Switch with a given name.
        A switch has a variable `self.is_hub` that allows any switch to become a hub.

        :param name: a string that will be the name of the switch. If `None`, it is randomized.
        """
        super(Switch, self).__init__(name, OS_LINUX, None)

        self.is_hub = False

        self.stp_enabled = True
        self.priority = priority
        self.add_startup_process(SwitchingProcess)

    def show(self, x, y):
        """
        overrides `Computer.show` and shows the same `ComputerGraphics` object only with a switch's photo.
        :param x:
        :param y: coordinates of the computer image.
        :return: None
        """
        self.graphics = ComputerGraphics(x, y, self, SWITCH_IMAGE)

    def is_for_me(self, packet):
        """
        overrides the original `is_for_me` method of `Computer` and adds STP multicast-s.
        :param packet: a `Packet` to test
        :return: whether it is for me or not.
        """
        if self.stp_enabled:
            return (super(Switch, self).is_for_me(packet)) or (packet["Ethernet"].dst_mac == MACAddress.stp_multicast())
        return super(Switch, self).is_for_me(packet)

    def start_stp(self):
        """
        Starts the process of STP sending and receiving.
        :return: None
        """
        if not self.is_process_running(STPProcess) and self.interfaces:
            self.start_process(STPProcess)

    def send_stp(self, sender_bid, root_bid, distance_to_root, root_declaration_time):
        """
        Sends an STP packet with the given information on all interfaces. (should only be used on a switch)
        :param sender_bid: a `BID` object of the sending switch.
        :param root_bid: a `BID` object of the root switch.
        :param distance_to_root: The switch's distance to the root switch.
        :return: None
        """
        for interface in self.interfaces:
            interface.send_with_ethernet(MACAddress.stp_multicast(),
                                         LogicalLinkControl(
                                             STP(sender_bid, root_bid, distance_to_root, root_declaration_time)))

    @classmethod
    def from_dict_load(cls, dict_):
        """
        Load a computer from the dict that is saved into the files
        :param dict_:
        :return: Computer
        """
        returned = cls(dict_["name"])
        returned.interfaces = [Interface.from_dict_load(interface_dict) for interface_dict in dict_["interfaces"]],
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
        self.graphics = ComputerGraphics(x, y, self, HUB_IMAGE)


class Antenna(Switch):
    """
    This class represents an Antenna, which is just a Switch that can send things over radio waves.
    """
    def __init__(self, name=None):
        super(Antenna, self).__init__(name)
        self.stp_enabled = True
        self.is_supporting_wireless_connections = True

    def show(self, x, y):
        """
        Overrides `Switch.show` and shows the same `ComputerGraphics` object only with a antenna's photo.
        :param x:
        :param y:  coordinates that the image will have.
        :return: None
        """
        self.graphics = ComputerGraphics(x, y, self, ANTENNA_IMAGE)
