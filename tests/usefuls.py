from NetSym.consts import OPCODES
from NetSym.packets.all import Ether, ARP, IP, DNS
from NetSym.packets.usefuls.dns import DNSQueryRecord, list_to_dns_query, list_to_dns_resource_record, DNSResourceRecord

MACS = [
    "00:11:22:33:44:55",
    "77:ab:cd:ef:11:22",
]

IPS = [
    "1.2.3.4",
    "4.3.2.1",
]


def example_ethernet():
    return Ether(
        src_mac=MACS[0],
        dst_mac="1a:bb:cc:43:5f:6e",
    )


def example_ip():
    return IP(
        src_ip="4.7.23.10",
        dst_ip=IPS[0],
        ttl=62,
    )


def example_arp():
    return ARP(
        opcode=OPCODES.ARP.REQUEST,
        dst_mac=MACS[0],
        src_mac="1a:bb:cc:43:5f:6e",
        dst_ip=IPS[0],
        src_ip="4.7.23.10",
    )


def example_dns(is_query=True):
    return DNS(
        transaction_id=0,
        is_response=not is_query,
        is_recursion_desired=False,

        queries=list_to_dns_query([
            DNSQueryRecord(
                query_name="www.facebook.com",
                query_type=OPCODES.DNS.TYPES.HOST_ADDRESS,
                query_class=OPCODES.DNS.CLASSES.INTERNET,
            ),
        ] if is_query else []),

        answer_records=list_to_dns_resource_record([
            DNSResourceRecord(
                record_name="www.facebook.com",
                time_to_live=6,
                record_data="19.168.1.2",
            )
        ] if not is_query else [])
    )
