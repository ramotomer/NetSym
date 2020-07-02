from collections import namedtuple

from consts import *
from exceptions import *
from gui.main_loop import MainLoop
from processes.process import Process, WaitingForPacket, ReturnedPacket

SwitchTableItem = namedtuple("SwitchTableItem", [
    "leg",
    "time",
])


class SwitchingProcess(Process):
    """
    This is the process that is in charge of switching packets on a computer.
    """
    def __init__(self, switch):
        """
        Initiates the process with a computer that runs it.
        """
        super(SwitchingProcess, self).__init__(switch)
        self.switching_table = {}
        # ^ a dictionary mapping mac addresses to the corresponding leg (interface) they sit behind.

    def update_switch_table_from_packets(self, packets):
        """
        Updates the switch table by looking at the packets that were received since
        the last time this function was called.|
        :param packets: a list of `ReceivedPackets` which are tuples (packet,time,leg)
        :return: None
        """
        for packet, leg in packets:
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
            if MainLoop.instance.time_since(switch_table_item.time) > SWITCH_TABLE.ITEM_LIFETIME:
                del self.switching_table[src_mac]

    def send_new_packets_to_destinations(self, packets):
        """
        Checks all of the packets that were received since the last time this
        function was called and sends them down the correct leg.
        :param packets: a list of `ReceivedPackets` which are tuples (packet,time,leg)
        :return: None
        """
        for packet, source_leg in packets:
            if self.computer.is_directly_for_me(packet) or self.computer.is_arp_for_me(packet):
                continue  # do not switch packets that are for you!
            if self.computer.stp_enabled and "STP" in packet:
                continue   # do not switch STP packets (unless you do not know what STP is (== Hub))
            destination_legs = self.where_to_send(packet, source_leg)
            for leg in destination_legs:
                packet.graphics = None
                leg.send(packet.copy())

    def where_to_send(self, packet, source_leg):
        """
        Returns a list of legs that the packet needs to be sent to.
        Here it is decided whether to flood the packet or not.
        :param packet: a `Packet` object that was received.
        :param source_leg: the `Interface` object from which it was received.
        :return: a list of interface that the packet should be sent on.
        """
        dst_mac = packet["Ethernet"].dst_mac

        if self.computer.is_hub or dst_mac.is_broadcast() or (dst_mac not in self.switching_table):
            return [leg for leg in self.computer.interfaces if leg is not source_leg and leg.is_connected()] # flood!!!
        destination_leg = self.switching_table[dst_mac].leg
        return [destination_leg] if destination_leg is not source_leg else []
        # ^ making sure the packet does not return on the destination leg

    @staticmethod
    def is_switchable_packet(packet):
        """
        Receives a `Packet` object and returns whether or not it can be switched
        :return:
        """
        return "STP" not in packet

    def code(self):
        """
        The main code of the process
        :return: yield WaitingFor-s
        """
        while True:
            new_packets = ReturnedPacket()
            yield WaitingForPacket(self.is_switchable_packet, new_packets)

            self.send_new_packets_to_destinations(new_packets)
            self.update_switch_table_from_packets(new_packets)
            self.delete_old_switch_table_items()

    def __repr__(self):
        return "Switching process"
