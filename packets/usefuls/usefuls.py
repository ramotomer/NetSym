from typing import Any

import scapy
from scapy.packet import Raw

from consts import PACKET
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
        if item == 'options':
            return super(ScapyOptions, self).__getattribute__(item)

        try:
            return self[item]
        except KeyError as e:
            raise AttributeError(*e.args)

    def __setattr__(self, key, value):
        if key == 'options':
            super(ScapyOptions, self).__setattr__(key, value)
            return

        for existing_key, existing_value in [option for option in self.options if isinstance(option, tuple)]:
            if existing_key == key:
                self.options = [option for option in self.options if not (isinstance(option, tuple) and option[0] == key)] + [(key, value)]
                return
        self.options.append((key, value))

    def __repr__(self):
        return str(self.options)


class ScapyRenamedPacketField:
    def __init__(self, new_name, field_object):
        self.field_object = field_object
        self.new_name = new_name

    def __getattr__(self, item):
        if item == "name":
            return self.new_name
        return getattr(self.field_object, item)

    def __repr__(self):
        return f"new_name: '{self.new_name}' of Renamed({self.field_object!r})"

# TODO: make this vvvvvv Work! (for a `multiline_repr` method with more indicative attribute names :)
# def define_scapy_packet_attribute_aliases(class_, attribute_name_mapping):
#     """
#     Scapy has ugly attribute names                 (ciaddr, dport)
#     We want to add our aliases that would work too (client_ip, dst_port)
#     `define_attribute_aliases` allows us to do so - but the `show` method still prints with the bad names
#
#     This method temporarily sets the field names to be our better names, calls the `show` method,
#         and set field names back as they were
#     """
#     class_ = define_attribute_aliases(class_, attribute_name_mapping)
#     scapy_names_to_good_names = reverse_dict(attribute_name_mapping)
#
#     class WithOverriddenShowMethod(class_):
#         original_name = getattr(class_, 'original_name', class_.__name__)
#
#         def _show_or_dump(self, *args, **kwargs):
#             with temporary_attribute_values(
#                 self,
#                 {
#                     'fields_desc': [
#                         ScapyRenamedPacketField(scapy_names_to_good_names.get(field.name, field.name), field)
#                         for field in class_.fields_desc
#                     ],
#                     'fields': change_dict_key_names(self.fields, scapy_names_to_good_names),
#                     'default_fields': change_dict_key_names(self.default_fields, scapy_names_to_good_names),
#                 }
#             ):
#                 return super(WithOverriddenShowMethod, self)._show_or_dump(*args, **kwargs)
#
#     return WithOverriddenShowMethod


def get_original_layer_name_by_instance(layer: scapy.packet.Packet) -> str:
    """
    Returns the name of the protocol - regardless of the `AttributeRenamer` encapsulation
    """
    return getattr(layer, 'original_name', type(layer).__name__)


def get_layer_opcode(layer: scapy.packet.Packet):
    """
    Take in a layer of a packet and return the most dominant value of the packet
        that can be considered as an "opcode" (arp.opcode, icmp.type, one of tcp.flags, etc...)
    """
    try:
        return PACKET.TYPE_TO_OPCODE_FUNCTION[get_original_layer_name_by_instance(layer)](layer)
    except KeyError:
        return None


def is_raw_layer(layer: Any) -> bool:
    """
    Return whether or not the layer is a layer that only contains raw information
    Can accept either an instance or a subclass - works anyway
    """
    return isinstance(layer, (Raw, str)) or issubclass(layer, (Raw, str))
