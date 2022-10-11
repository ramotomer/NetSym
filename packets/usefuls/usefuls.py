from __future__ import annotations

from typing import Any, TYPE_CHECKING, List, Type

import scapy
from scapy.packet import Raw

from exceptions import *
from packets.all import protocols
from usefuls.funcs import get_the_one

if TYPE_CHECKING:
    from packets.packet import Packet
    from address.ip_address import IPAddress


def scapy_layer_class_to_our_class(scapy_layer_class: Type[scapy.packet.Packet]) -> Type[scapy.packet.Packet]:
    """

    """
    return get_the_one(protocols, lambda p: issubclass(p, scapy_layer_class), default=scapy_layer_class)


def get_packet_attribute(packet: Packet, attribute_name: str, containing_protocols: List[str]) -> Any:
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


def get_src_ip(packet: Packet) -> IPAddress:
    return get_packet_attribute(packet, 'src_ip', ["IP", "ARP"])


def get_dst_ip(packet: Packet) -> IPAddress:
    return get_packet_attribute(packet, 'dst_ip', ["IP", "ARP"])


class ScapyRenamedPacketField:
    def __init__(self, new_name: str, field_object: scapy.fields.Field) -> None:
        self.field_object = field_object
        self.new_name = new_name

    def __getattr__(self, item: str) -> Any:
        if item == "name":
            return self.new_name
        return getattr(self.field_object, item)

    def __repr__(self) -> str:
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


def is_raw_layer(layer: Any) -> bool:
    """
    Return whether or not the layer is a layer that only contains raw information
    Can accept either an instance or a subclass - works anyway
    """
    return isinstance(layer, (Raw, str)) or issubclass(layer, (Raw, str))
