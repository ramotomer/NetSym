from __future__ import annotations

from typing import TYPE_CHECKING

import scapy

from consts import OPCODES, TCPFlag
from packets.usefuls.usefuls import get_packet_attribute

if TYPE_CHECKING:
    from packets.packet import Packet


def get_dominant_tcp_flag(tcp: scapy.packet.Packet) -> TCPFlag:
    for flag in OPCODES.TCP.FLAGS_DISPLAY_PRIORITY:
        if int(tcp.flags) & int(flag):
            return flag
    return OPCODES.TCP.NO_FLAGS


def get_src_port(packet: Packet) -> int:
    """
    Return the src port of the packet
    Can be either UDP or TCP
    If it is neither - raise
    """
    return get_packet_attribute(packet, 'src_port', ["UDP", "TCP"])


def get_dst_port(packet: Packet) -> int:
    """
    Return the dst port of the packet
    Can be either UDP or TCP
    If it is neither - raise
    """
    return get_packet_attribute(packet, 'dst_port', ["UDP", "TCP"])
