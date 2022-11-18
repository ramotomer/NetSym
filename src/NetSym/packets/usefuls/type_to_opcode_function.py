from scapy.layers.dhcp import DHCPTypes

from NetSym.consts import OPCODES
from NetSym.packets.usefuls.dns import get_dns_opcode
from NetSym.packets.usefuls.ip import needs_reassembly
from NetSym.packets.usefuls.tcp import get_dominant_tcp_flag

TYPE_TO_OPCODE_FUNCTION = {
    "IP": needs_reassembly,
    "ARP":  lambda arp: arp.opcode,
    "ICMP": (lambda icmp: (icmp.type, icmp.code) if icmp.type == OPCODES.ICMP.TYPES.UNREACHABLE else icmp.type),
    "DHCP": (lambda dhcp: DHCPTypes.get(dhcp.parsed_options.message_type, dhcp.parsed_options.message_type)),
    "TCP":  get_dominant_tcp_flag,
    "DNS":  get_dns_opcode,
}
