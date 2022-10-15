from __future__ import annotations

from typing import NamedTuple, TYPE_CHECKING, List

from computing.internals.interface import Interface
from computing.internals.processes.abstracts.process import Process, ReturnedPacket, T_ProcessCode, WaitingFor
from consts import *
from exceptions import *
from gui.main_loop import MainLoop

if TYPE_CHECKING:
    from packets.packet import Packet
    from computing.switch import Switch


class SwitchTableItem(NamedTuple):
    leg:  Interface
    time: T_Time


class SwitchingProcess(Process):
    """
    This is the process that is in charge of switching packets on a computer.
    """
    computer: Switch

    def __init__(self, pid: int, switch: Switch) -> None:
        """
        Initiates the process with a computer that runs it.
        """
        super(SwitchingProcess, self).__init__(pid, switch)
        self.switching_table = {}
        # ^ a dictionary mapping mac addresses to the corresponding leg (interface) they sit behind.

    def update_switch_table_from_packets(self, packets: ReturnedPacket) -> None:
        """
        Updates the switch table by looking at the packets that were received since
        the last time this function was called.|
        """
        for packet, packet_metadata in packets:
            try:
                src_mac = packet["Ether"].src_mac
            except KeyError:
                raise UnknownPacketTypeError("The packet contains no Ethernet layer!!!")
            self.switching_table[src_mac] = SwitchTableItem(leg=packet_metadata.interface, time=MainLoop.instance.time())

    def delete_old_switch_table_items(self) -> None:
        """
        Deletes the old items in the switch table. deletes from the switch table any item that was not updated in the
        last `SWITCH_TABLE_ITEM_LIFETIME` seconds.
        :return: None
        """
        for src_mac, switch_table_item in list(self.switching_table.items()):
            if MainLoop.instance.time_since(switch_table_item.time) > COMPUTER.SWITCH_TABLE.ITEM_LIFETIME:
                del self.switching_table[src_mac]

    def send_new_packets_to_destinations(self, packets: ReturnedPacket) -> None:
        """
        Checks all of the packets that were received since the last time this
        function was called and sends them down the correct leg.
        :param packets: a list of `ReceivedPackets` which are tuples (packet,time,leg)
        :return: None
        """
        for packet, packet_metadata in packets:
            if self.computer.is_directly_for_me(packet) or self.computer.is_arp_for_me(packet):
                continue  # do not switch packets that are for you!
            if self.computer.stp_enabled and "STP" in packet:
                continue   # do not switch STP packets (unless you do not know what STP is (== Hub))
            destination_legs = self.where_to_send(packet, source_leg=packet_metadata.interface)
            for leg in destination_legs:
                packet.graphics = None
                self.computer.send(packet.copy(), interface=leg)

    def where_to_send(self, packet: Packet, source_leg: Interface) -> List[Interface]:
        """
        Returns a list of legs that the packet needs to be sent to.
        Here it is decided whether to flood the packet or not.
        :param packet: a `Packet` object that was received.
        :param source_leg: the `Interface` object from which it was received.
        :return: a list of interface that the packet should be sent on.
        """
        dst_mac = packet["Ether"].dst_mac

        if self.computer.is_hub or dst_mac.is_broadcast() or (dst_mac not in self.switching_table):
            return [leg for leg in self.computer.interfaces if leg is not source_leg and leg.is_connected()]  # flood!!!
        destination_leg = self.switching_table[dst_mac].leg
        return [destination_leg] if destination_leg is not source_leg else []
        # ^ making sure the packet does not return on the destination leg

    @staticmethod
    def is_switchable_packet(packet: Packet) -> bool:
        """
        Receives a `Packet` object and returns whether or not it can be switched
        :return:
        """
        return "STP" not in packet

    def code(self) -> T_ProcessCode:
        """
        The main code of the process
        :return: yield WaitingFor-s
        """
        while True:
            new_packets = yield WaitingFor(self.is_switchable_packet, get_raw_packet=True)

            self.send_new_packets_to_destinations(new_packets)
            self.update_switch_table_from_packets(new_packets)
            self.delete_old_switch_table_items()

    def __repr__(self) -> str:
        return "[kswitch]"
