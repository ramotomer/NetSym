from scapy.layers.dhcp import BOOTP, DHCP
from scapy.layers.inet import IP, UDP, TCP, ICMP
from scapy.layers.l2 import Ether, ARP, LLC, STP

from packets.usefuls import ScapyOptions
from usefuls.attribute_renamer import with_parsed_attributes, define_attribute_aliases, with_automatic_address_type_casting

Ether = with_automatic_address_type_casting(
    define_attribute_aliases(
        Ether,
        {
            "src_mac": "src",
            "dst_mac": "dst",
        }
    )
)
ARP = with_automatic_address_type_casting(
    define_attribute_aliases(
        ARP,
        {
            "hardware_type":           "hwtype",
            "protocol_type":           "ptype",
            "hardware_address_length": "hwlen",
            "protocol_address_length": "plen",
            "opcode":                  "op",
            "src_mac":                 "hwsrc",
            "src_ip":                  "psrc",
            "dst_mac":                 "hwdst",
            "dst_ip":                  "pdst",
        }
    )
)
IP = with_automatic_address_type_casting(
    define_attribute_aliases(
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
)
LLC = define_attribute_aliases(
    LLC,
    {
        "src_service_access_point": "ssap",
        "dst_service_access_point": "dsap",
        "control_field":            "ctrl",
    }
)
STP = with_automatic_address_type_casting(
    define_attribute_aliases(
        STP,
        {
            "protocol":      "proto",
            "bpdu_type":     "bpdutype",
            "bpdu_flags":    "bpduflags",
            "root_id":       "rootid",
            "root_mac":      "rootmac",
            "path_cost":     "pathcost",
            "bridge_id":     "bridgeid",
            "bridge_mac":    "bridgemac",
            "port_id":       "portid",
            "max_age":       "maxage",
            "hello_time":    "hellotime",
            "forward_delay": "fwddelay",
        }
    )
)
ICMP = define_attribute_aliases(
    ICMP,
    {
        "sequence": "seq",
        "checksum": "chksum",
    }
)
UDP = define_attribute_aliases(
    UDP,
    {
        "src_port": "sport",
        "dst_port": "dport",
        "length":   "len",
        "checksum": "chksum",
    }
)
TCP = define_attribute_aliases(
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
BOOTP = with_automatic_address_type_casting(
    define_attribute_aliases(
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
)
DHCP = with_parsed_attributes(DHCP, {"options": ScapyOptions})


protocols = [
    Ether,
    ARP, IP, LLC,
    ICMP, UDP, TCP, BOOTP, STP,
    DHCP,
]
