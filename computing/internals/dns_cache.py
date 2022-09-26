from dataclasses import dataclass
from typing import Dict

from address.ip_address import IPAddress
from consts import T_Time
from gui.main_loop import MainLoop
from packets.usefuls.dns import T_Hostname


@dataclass
class DNSCacheItem:
    ip_address: IPAddress
    ttl: int
    creation_time: T_Time


class DNSCache:
    """
    A cache that m aps a name to an IP address
    """
    def __init__(self) -> None:
        """
        Create an empty DNS cache
        """
        self.__cache: Dict[T_Hostname, DNSCacheItem] = {}
        self.transaction_counter = 0

    def __getitem__(self, item: T_Hostname) -> DNSCacheItem:
        """
        Resolve a DNS name
        """
        return self.__cache[item]

    def __contains__(self, item: T_Hostname) -> bool:
        """
        Whether or not the DNS cache contains the supplied name
        """
        return item in self.__cache

    def add_item(self, name: T_Hostname, ip_address: IPAddress, ttl: int) -> None:
        """
        Adds a new item to the cache
        """
        self.__cache[name] = DNSCacheItem(ip_address, ttl, MainLoop.instance.time())

    def forget_old_items(self) -> None:
        """
        Remove all items in the cache that their TTL (time to live) has expired
        """
        for item_name, dns_item in list(self.__cache.items()):
            if MainLoop.instance.time_since(dns_item.creation_time) > dns_item.ttl:
                del self.__cache[item_name]

    def wipe(self) -> None:
        """
        Clear the DNS cache of all entries
        """
        self.__cache.clear()

    def __repr__(self) -> str:
        """
        A textual representation of the cache
        Can be seen using the `dns -a` command
        """
        returned = "DNS Cache:\n" + ("-" * 30)
        for item_name, cache_item in self.__cache.items():
            returned += "\n"
            returned += f"""
{'Record Name':.<20}: {item_name}
{'Record Type':.<20}: A
{'Time To Live':.<20}: {cache_item.ttl}
{'A (Host) Record':.<20}: {cache_item.ip_address.string_ip}
"""
        return returned
