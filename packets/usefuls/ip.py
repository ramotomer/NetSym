from __future__ import annotations

from typing import List

from consts import PROTOCOLS
from packets.all import IP
from packets.packet import Packet
from usefuls.funcs import split_by_size


def fragment_packet(packet: Packet, mtu: int) -> List[Packet]:
    """
    Take in a packet and the max transfer unit (MTU)
    Chop the packet into small pieces that do not exceed the MTU. Set the appropriate flags in the IP header
    Return the small packets in a list
    """
    ip_header_length = len(packet.get_layer_by_name_no_payload("IP"))
    ip_datas = split_by_size(packet.data.getlayer(IP).payload.build(), (mtu - ip_header_length))

    length_until_now = 0
    packet_slices = []
    for i, ip_data in enumerate(ip_datas):
        packet_slice = Packet(packet.get_layer_by_name_no_payload("Ether") / packet.get_layer_by_name_no_payload("IP") / ip_data)

        if i < (len(ip_datas) - 1):
            packet_slice["IP"].flags = PROTOCOLS.IP.FLAGS.MORE_FRAGMENTS
        packet_slice["IP"].frag = length_until_now
        # ^ TODO: this must stay 'frag' and not 'fragment_offset' for now - setting an aliased attribute does not yet work :(
        length_until_now += len(packet_slice["IP"].payload)

        packet_slice.reparse_layers()
        # ^ This is to make sure the ip_data is parsed only if necessary (It should not be parsed if the fragment offset is not 0
        packet_slices.append(packet_slice)

    return packet_slices


def needs_fragmentation(packet: Packet, mtu: int) -> bool:
    """
    Returns whether or not the packet needs to be fragmented with the given MTU
    """
    return len(packet.data) > (mtu + PROTOCOLS.ETHERNET.HEADER_LENGTH)
