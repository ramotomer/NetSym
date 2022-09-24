from scapy.layers.dhcp import BOOTP, DHCP
from scapy.layers.dns import DNS
from scapy.layers.inet import IP, UDP, TCP, ICMP
from scapy.layers.l2 import Ether, ARP, LLC, STP

from packets.usefuls.dns import dns_resource_record_to_list, dns_query_record_to_list
from packets.usefuls.scapy_options import ScapyOptions
from usefuls.attribute_renamer import with_parsed_attributes, define_attribute_aliases, with_automatic_address_type_casting, \
    with_attribute_type_casting

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
            "opcode":          "op",
            "client_mac":      "chaddr",
            "client_ip":       "ciaddr",
            "your_ip":         "yiaddr",
            "server_ip":       "siaddr",
            "server_name":     "sname",
            "relay_agent_ip":  "giaddr",
        }
    )
)
DHCP = with_parsed_attributes(DHCP, {"options": ScapyOptions})
DNS = with_attribute_type_casting(
    define_attribute_aliases(
        DNS,
        {
            "transaction_id":                      "id",

            "is_response":                         "qr",
            "is_server_authority_for_domain":      "aa",
            "is_truncated":                        "tc",
            "is_recursive_desired":                "rd",
            "is_recursion_available":              "ra",
            "z__reserved":                         "z",
            "is_authenticated":                    "ad",
            "is_authentication_checking_disabled": "cd",

            "return_code":                         "rcode",

            "query_count":                         "qdcount",
            "answer_record_count":                 "ancount",
            "authority_record_count":              "nscount",
            "additional_record_count":             "arcount",

            "queries":                             "qd",
            "answer_records":                      "an",
            "authority_records":                   "ns",
            "additional_records":                  "ar",
        }
    ),
    {
        "queries":            dns_query_record_to_list,
        "answer_records":     dns_resource_record_to_list,
        "authority_records":  dns_resource_record_to_list,
        "additional_records": dns_resource_record_to_list,
    }
)


protocols = [
    Ether,
    ARP, IP, LLC,
    ICMP, UDP, TCP, BOOTP, STP,
    DHCP, DNS,
]
