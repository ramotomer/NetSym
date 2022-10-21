from __future__ import annotations

from typing import TYPE_CHECKING, List

import scapy

from NetSym.gui.tech.wireless_packet_graphics import WirelessPacketGraphics
from NetSym.packets.packet import Packet

if TYPE_CHECKING:
    from NetSym.computing.internals.frequency import Frequency
    from NetSym.computing.internals.wireless_interface import WirelessInterface


class WirelessPacket(Packet):
    """
    just like a regular packet but it is sent over a Frequency rather than a regular connection.
    """
    def __init__(self, data: scapy.packet.Packet) -> None:
        super(WirelessPacket, self).__init__(data)

    def init_graphics(self, frequency_object: Frequency, sending_interface: WirelessInterface) -> List[WirelessPacketGraphics]:
        """
        Starts the display of the object. (Creating the graphics object)
        """
        self.graphics = WirelessPacketGraphics(sending_interface.graphics.x, sending_interface.graphics.y, self.deepest_layer(), frequency_object)
        return [self.graphics]
