from scapy.layers.dhcp import BOOTP
from scapy.layers.inet import IP, UDP, TCP
from scapy.layers.l2 import Ether, ARP

from usefuls.attribute_renamer import define_attribute_aliases

Ether = define_attribute_aliases(
    Ether,
    {
        "src_mac": "src",
        "dst_mac": "dst",
    }
)
ARP = define_attribute_aliases(
    ARP,
    {
        "src_mac": "hwsrc",
        "dst_mac": "hwdst",
        "src_ip": "psrc",
        "dst_ip": "pdst",
    }
)
UDP = define_attribute_aliases(
    UDP,
    {
        "src_port": "sport",
        "dst_port": "dport",
        "length": "len",
        "checksum": "chksum",
    }
)
IP = define_attribute_aliases(
    IP,
    {
        "src_ip": "src",
        "dst_ip": "dst",
        "length": "len",
        "fragment_offset": "frag",
        "protocol": "proto",
        "checksum": "chksum",
    }
)
TCP = define_attribute_aliases(
    TCP,
    {
        "src_port": "sport",
        "dst_port": "dport",
    }
)
BOOTP = define_attribute_aliases(
    BOOTP,
    {
        "opcode": "op",
        "client_mac": "chaddr",
        "client_ip": "ciaddr",
        "your_ip": "yiaddr",
        "server_ip": "siaddr",
        "server_name": "sname",
        "gateway_ip": "giaddr",
    }
)
