from exceptions import *


def get_packet_attribute(packet, attribute_name, containing_protocols):
    """
    Return the attribute of the packet that is named `attribute_name`
    Packet must contain one of `containing_protocols` - If it does not - raise
    Each of the `containing_protocols` must have an attribute named `attribute_name`
    """
    for protocol in containing_protocols:
        if protocol in packet:
            return getattr(packet[protocol], attribute_name)
    raise UnknownPacketTypeError(
        f"packet must include one of {containing_protocols} layers in order to have a `{attribute_name}`! packet: {packet}")


def get_src_port(packet):
    """
    Return the src port of the packet
    Can be either UDP or TCP
    If it is neither - raise
    """
    return get_packet_attribute(packet, 'src_port', ["UDP", "TCP"])


def get_dst_port(packet):
    """
    Return the dst port of the packet
    Can be either UDP or TCP
    If it is neither - raise
    """
    return get_packet_attribute(packet, 'dst_port', ["UDP", "TCP"])


def get_src_ip(packet):
    return get_packet_attribute(packet, 'src_ip', ["IP", "ARP"])


def get_dst_ip(packet):
    return get_packet_attribute(packet, 'dst_ip', ["IP", "ARP"])


class ScapyOptions:
    def __init__(self, options):
        self.options = options

    def __getitem__(self, item):
        for key, value in [option for option in self.options if isinstance(option, tuple)]:
            if key.replace('-', '_') == item:
                return value
        raise KeyError(f"This scapy options list: {self} has no option '{item}'!")

    def __getattr__(self, item):
        return self[item]

    def __setattr__(self, key, value):
        for existing_key, existing_value in [option for option in self.options if isinstance(option, tuple)]:
            if existing_key == key:
                self.options = [option for option in self.options if not (isinstance(option, tuple) and option[0] == key)] + [(key, value)]
                return
        self.options.append((key, value))

    def __repr__(self):
        return str(self.options)
