from consts import PACKET
from exceptions import *
from usefuls.attribute_renamer import define_attribute_aliases
from usefuls.funcs import temporary_attribute_values


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


class ScapyRenamedPacketField:
    def __init__(self, new_name, field_object):
        self.field_object = field_object
        self.new_name = new_name

    def __getattr__(self, item):
        if item == "name":
            return self.new_name
        return getattr(self.field_object, item)


def define_scapy_packet_attribute_aliases(class_, attribute_name_mapping):
    """
    Scapy has ugly attribute names                 (ciaddr, dport)
    We want to add our aliases that would work too (client_ip, dst_port)
    `define_attribute_aliases` allows us to do so - but the `show` method still prints with the bad names

    This method temporarily sets the field names to be our better names, calls the `show` method,
        and set field names back as they were
    """
    class_ = define_attribute_aliases(class_, attribute_name_mapping)
    attribute_value_mapping = {'fields_desc': [
        ScapyRenamedPacketField(attribute_name_mapping.get(field.name, field.name), field)
        for field in class_.fields_desc
    ]}

    class WithOverriddenShowMethod(class_):
        original_name = getattr(class_, 'original_name', class_.__name__)

        def show(self, *args, **kwargs):
            with temporary_attribute_values(self, attribute_value_mapping):
                super(WithOverriddenShowMethod, self).show(*args, **kwargs)

    return WithOverriddenShowMethod


def get_original_layer_name(layer):
    """

    :param layer:
    :return:
    """
    return getattr(layer, 'original_name', type(layer).__name__)


def get_layer_opcode(layer):
    """

    :param layer:
    :return:
    """
    try:
        return PACKET.TYPE_TO_OPCODE_FUNCTION[get_original_layer_name(layer)](layer)
    except KeyError:
        return None
