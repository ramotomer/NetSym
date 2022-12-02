from __future__ import annotations

from typing import List, TYPE_CHECKING

from NetSym.consts import PROTOCOLS
from NetSym.exceptions import PacketAlreadyFragmentedError, InvalidFragmentsError, PacketTooLongToFragment
from NetSym.packets.all import IP
from NetSym.usefuls.funcs import split_by_size

if TYPE_CHECKING:
    from NetSym.packets.packet import Packet


def get_fragment_size(mtu: int) -> int:
    """
    Take in the ideal size the packet should be chopped up to
    Round it so it is divisible by 8 and return it
    """
    return mtu - (mtu % PROTOCOLS.IP.FRAGMENT_OFFSET_UNIT)


def validate_fragments(fragments: List[Packet]) -> None:
    """
    Take in a list of IP fragments - make sure they are valid. That means:
        0. There are fragments
        1. All fragments' lengths are divisible by 8 (except the last one)
        2. All fragments are of the same packet (with the same ip identification)
        3. All fragments except the last have the MORE_FRAGMENTS flag set
        4. Fragments match the lengths specified in their 'fragment offset's (the order does not matter)
    """
    fragments = sorted(fragments, key=lambda p: int(p["IP"].fragment_offset))

    if not fragments:
        raise InvalidFragmentsError(f"Cannot reassemble fragments if none are given... Stupid! fragment list: {fragments}")

    if not all(len(fragment["IP"].payload) % PROTOCOLS.IP.FRAGMENT_OFFSET_UNIT == 0 for fragment in fragments[:-1]):
        raise InvalidFragmentsError(f"Not all fragment lengths are divisible by 8!! fragment list: {fragments}")

    if not all(fragment["IP"].id == fragments[0]["IP"].id for fragment in fragments):
        raise InvalidFragmentsError(f"Not all fragments belong to the same packet! fragment list: {fragments}")

    if not all((fragment["IP"].flags & PROTOCOLS.IP.FLAGS.MORE_FRAGMENTS) for fragment in fragments[:-1]):
        raise InvalidFragmentsError(f"Not all fragments have MORE_FRAGMENTS flag set!!! fragment list: {fragments}")

    if fragments[-1]["IP"].flags & PROTOCOLS.IP.FLAGS.MORE_FRAGMENTS:
        raise InvalidFragmentsError(f"Last fragment must not have the MORE_FRAGMENTS flag set! fragment: {fragments[-1].multiline_repr()}")

    length_until_now = 0
    for fragment in fragments:
        if fragment["IP"].fragment_offset != length_until_now:
            raise InvalidFragmentsError(f"Fragment offset does not match sequence on fragment: {fragment.multiline_repr()}")
        length_until_now += (len(fragment["IP"].payload) // PROTOCOLS.IP.FRAGMENT_OFFSET_UNIT)


def are_fragments_valid(fragments: List[Packet]) -> bool:
    """
    The same as `validate_fragments` but instead of raising an exception - return the result
    """
    try:
        validate_fragments(fragments)
    except InvalidFragmentsError:
        return False
    return True


def reassemble_fragmented_packet(fragments: List[Packet]) -> Packet:
    """
    Take in a list of packets that are all of the fragments of a fragmented packet
    Reassemble them into one big packet and return it :)
    """
    validate_fragments(fragments)

    fragments =          sorted(fragments, key=lambda p: int(p["IP"].fragment_offset))
    ether_layer =        fragments[0].get_layer_by_name_no_payload("Ether")
    ip_layer =           fragments[0].get_layer_by_name_no_payload("IP")
    summed_ip_datas =    b''.join([fragment["IP"].payload.build() for fragment in fragments])

    packet =             fragments[0].copy()
    packet.data =        ether_layer / ip_layer / summed_ip_datas
    packet["IP"].flags = PROTOCOLS.IP.FLAGS.NO_FLAGS
    packet["IP"].frag  = 0
    # ^ TODO: this must stay 'frag' and not 'fragment_offset' for now - setting an aliased attribute does not yet work :(
    packet.reparse_layers()
    return packet


def fragment_packet(packet: Packet, mtu: int) -> List[Packet]:
    """
    Take in a packet and the max transfer unit (MTU)
    Chop the packet into small pieces that do not exceed the MTU. Set the appropriate flags in the IP header
    Return the small packets in a list
    """
    if needs_reassembly(packet):
        raise PacketAlreadyFragmentedError(f"mtu: {mtu}, packet: {packet.multiline_repr()}")

    ip_header_length = len(packet.get_layer_by_name_no_payload("IP"))
    ip_datas = split_by_size(packet.data.getlayer(IP).payload.build(), get_fragment_size(mtu - ip_header_length))

    if sum(map(len, ip_datas)) > PROTOCOLS.IP.LONGEST_FRAGMENTATIONABLE_PACKET:
        raise PacketTooLongToFragment(f"Max size is {PROTOCOLS.IP.LONGEST_FRAGMENTATIONABLE_PACKET} and {sum(map(len, ip_datas))} is too big :(")

    length_until_now = 0
    packet_slices = []
    for i, ip_data in enumerate(ip_datas):
        packet_slice = packet.copy()
        packet_slice.data = packet.get_layer_by_name_no_payload("Ether") / packet.get_layer_by_name_no_payload("IP") / ip_data

        if i < (len(ip_datas) - 1):
            packet_slice["IP"].flags = PROTOCOLS.IP.FLAGS.MORE_FRAGMENTS
        packet_slice["IP"].frag = length_until_now
        # ^ TODO: this must stay 'frag' and not 'fragment_offset' for now - setting an aliased attribute does not yet work :(
        length_until_now += (len(ip_data) // PROTOCOLS.IP.FRAGMENT_OFFSET_UNIT)

        packet_slice.reparse_layers()
        # ^ This is to make sure the ip_data is parsed only if necessary (It should not be parsed if the fragment offset is not 0
        packet_slices.append(packet_slice)

    return packet_slices


def needs_fragmentation(packet: Packet, mtu: int) -> bool:
    """
    Returns whether or not the packet needs to be fragmented with the given MTU
    """
    return ("IP" in packet) and (len(packet.data) > (mtu + PROTOCOLS.ETHERNET.HEADER_LENGTH))


def needs_reassembly(packet: Packet) -> bool:
    """
    Returns whether or not the supplied packet is part of a larger fragmented packet
    """
    return ("IP" in packet) and ((packet["IP"].fragment_offset != 0) or (packet["IP"].flags & PROTOCOLS.IP.FLAGS.MORE_FRAGMENTS))


def allows_fragmentation(packet: Packet) -> bool:
    """
    Whether or not the packet can be fragmented if needed
    """
    return not (packet["IP"].flags & PROTOCOLS.IP.FLAGS.DONT_FRAGMENT)
