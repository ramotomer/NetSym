from scapy.layers.dhcp import BOOTP
from scapy.layers.inet import IP, UDP, TCP, ICMP
from scapy.layers.l2 import Ether, ARP

from packets.usefuls import ScapyOptions, define_scapy_packet_attribute_aliases
from usefuls.attribute_renamer import with_parsed_attributes

Ether = define_scapy_packet_attribute_aliases(
    Ether,
    {
        "src_mac": "src",
        "dst_mac": "dst",
    }
)
ARP = define_scapy_packet_attribute_aliases(
    ARP,
    {
        "src_mac": "hwsrc",
        "dst_mac": "hwdst",
        "src_ip":  "psrc",
        "dst_ip":  "pdst",
    }
)
IP = define_scapy_packet_attribute_aliases(
    IP,
    {
        "src_ip":          "src",
        "dst_ip":          "dst",
        "length":          "len",
        "fragment_offset": "frag",
        "protocol":        "proto",
        "checksum":        "chksum",
    }
)
ICMP = define_scapy_packet_attribute_aliases(
    ICMP,
    {
        "sequence": "seq",
        "checksum": "chksum",
    }
)
UDP = define_scapy_packet_attribute_aliases(
    UDP,
    {
        "src_port": "sport",
        "dst_port": "dport",
        "length":   "len",
        "checksum": "chksum",
    }
)
TCP = define_scapy_packet_attribute_aliases(
    with_parsed_attributes(TCP, {"options": ScapyOptions}),
    {
        "src_port":        "sport",
        "dst_port":        "dport",
        "sequence_number": "seq",
        "ack_number":      "ack",
        "checksum":        "chksum",
        "urgent_pointer":  "urgptr",
        "window_size":     "window",
    }
)
BOOTP = define_scapy_packet_attribute_aliases(
    BOOTP,
    {
        "opcode":      "op",
        "client_mac":  "chaddr",
        "client_ip":   "ciaddr",
        "your_ip":     "yiaddr",
        "server_ip":   "siaddr",
        "server_name": "sname",
        "gateway_ip":  "giaddr",
    }
)
DHCP = with_parsed_attributes(TCP, {"options": ScapyOptions}),
