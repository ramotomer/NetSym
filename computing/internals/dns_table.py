from dataclasses import dataclass
from typing import Dict

from address.ip_address import IPAddress
from consts import T_Time
from gui.main_loop import MainLoop


@dataclass
class DNSTableItem:
    ip_address: IPAddress
    ttl: int
    creation_time: T_Time


class DNSTable:
    """
    A table that m aps a name to an IP address
    """
    def __init__(self) -> None:
        """
        Create an empty DNS TAble
        """
        self.__table: Dict[str, DNSTableItem] = {}

    def __getitem__(self, item: str) -> DNSTableItem:
        """
        Resolve a DNS name
        """
        return self.__table[item]

    def remove_expired_items(self) -> None:
        """
        Remove all items in the table that their TTL (time to live) has expired
        """
        for domain_name, dns_item in list(self.__table.items()):
            if MainLoop.instance.time_since(dns_item.creation_time) > dns_item.ttl:
                del self.__table[domain_name]
