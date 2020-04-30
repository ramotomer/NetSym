import copy
from collections import namedtuple

from address.mac_address import MACAddress
from computing.computer import Computer
from computing.interface import Interface
from consts import *
from exceptions import *
from gui.computer_graphics import ComputerGraphics
from gui.main_loop import MainLoop
from packets.stp import STP, LogicalLinkControl
from processes.stp_process import STPProcess

SwitchTableItem = namedtuple("SwitchTableItem", "leg time")


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
        super(Switch, self).__init__(name, OS_LINUX, None, Interface(MACAddress.randomac(), name="eth0"))

        self.is_hub = False

        self.switching_table = {}  # a dictionary mapping mac addresses to the corresponding leg (interface) they sit behind.
        self.last_switch_table_update_time = MainLoop.instance.time()
        self.last_packet_sending_time = MainLoop.instance.time()

        self.stp_enabled = True
        self.priority = priority

    def show(self, x, y):
        """
        overrides `Computer.show` and shows the same `ComptuerGraphics` object only with a switch's photo.
        :param x:
        :param y: coordinates of the computer image.
        :return: None
        """
        self.graphics = ComputerGraphics(x, y, self, SWITCH_IMAGE)

    def is_for_me(self, packet):
        """
        overrides the original `is_for_me` method of `Computer` and adds STP multicasts.
        :param packet: a `Packet` to test
        :return: whether it is for me or not.
        """
        if self.stp_enabled:
            return (super(Switch, self).is_for_me(packet)) or (packet["Ethernet"].dst_mac == MACAddress.stp_multicast())
        return super(Switch, self).is_for_me(packet)

    def update_switch_table_from_packets(self):
        """
        Updates the switch table by looking at the packets that were received since
        the last time this function was called.
        :return: None
        """
        new_packets = self._new_packets_since(self.last_switch_table_update_time)
        self.last_switch_table_update_time = MainLoop.instance.time()
        for packet, _, leg in new_packets:
            try:
                src_mac = packet["Ethernet"].src_mac
            except KeyError:
                raise UnknownPacketTypeError("The packet contains no Ethernet layer!!!")
            self.switching_table[src_mac] = SwitchTableItem(leg, MainLoop.instance.time())

    def delete_old_switch_table_items(self):
        """
        Deletes the old items in the switch table. deletes from the switch table any item that was not updated in the
        last `SWITCH_TABLE_ITEM_LIFETIME` seconds.
        :return: None
        """
        for src_mac, switch_table_item in list(self.switching_table.items()):
            if MainLoop.instance.time_since(switch_table_item.time) > SWITCH_TABLE_ITEM_LIFETIME:
                del self.switching_table[src_mac]

    def send_new_packets_to_destinations(self):
        """
        Checks all of the packets that were received since the last time this
        function was called and sends them down the correct leg.
        :return: None
        """
        new_packets = self._new_packets_since(self.last_packet_sending_time)
        self.last_packet_sending_time = MainLoop.instance.time()

        for packet, _, source_leg in new_packets:
            if self.is_directly_for_me(packet) or self.is_arp_for_me(packet):
                continue  # do not switch packets that are for you!
            if self.stp_enabled and "STP" in packet:
                continue   # do not switch STP packets (unless you do not know what STP is (== Hub))
            destination_legs = self.where_to_send(packet, source_leg)
            for leg in destination_legs:
                packet.graphics = None
                leg.send(copy.deepcopy(packet))

    def where_to_send(self, packet, source_leg):
        """
        Returns a list of legs that the packet needs to be sent to.
        Here it is decided whether to flood the packet or not.
        :param packet: a `Packet` object that was received.
        :param source_leg: the `Interface` object from which it was received.
        :return: a list of interface that the packet should be sent on.
        """
        dst_mac = packet["Ethernet"].dst_mac

        if self.is_hub or dst_mac.is_broadcast() or (dst_mac not in self.switching_table):
            return [leg for leg in self.interfaces if leg is not source_leg and leg.is_connected()]   # flood!!!
        destination_leg = self.switching_table[dst_mac].leg
        return [destination_leg] if destination_leg is not source_leg else []
        # ^ making sure the packet does not return on the destination leg

    def start_stp(self):
        """
        Starts the process of STP sending and receiving.
        :return: None
        """
        if not self.is_process_running(STPProcess):
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

    def logic(self):
        """
        overrides the original `logic` function of `Computer`, but still calls the original and adds to it the switch logic.
        :return: None
        """
        super(Switch, self).logic()

        self.update_switch_table_from_packets()
        self.delete_old_switch_table_items()
        self.send_new_packets_to_destinations()


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
