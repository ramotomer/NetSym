from dataclasses import dataclass
from typing import Dict, Optional

from NetSym.address.ip_address import IPAddress
from NetSym.consts import T_Time
from NetSym.exceptions import WrongUsageError
from NetSym.gui.main_loop import MainLoop
from NetSym.packets.usefuls.dns import T_Hostname


@dataclass
class DNSCacheItem:
    ip_address: IPAddress
    ttl: int
    creation_time: T_Time


class DNSCache:
    """
    A cache that m aps a name to an IP address
    """
    def __init__(self, initial_dict: Optional[Dict[T_Hostname, DNSCacheItem]] = None) -> None:
        """
        Create an empty DNS cache
        """
        self._cache: Dict[T_Hostname, DNSCacheItem] = initial_dict if initial_dict is not None else {}
        self.transaction_counter = 0

    def __getitem__(self, item: T_Hostname) -> DNSCacheItem:
        """
        Resolve a DNS name
        """
        return self._cache[item]

    def __contains__(self, item: T_Hostname) -> bool:
        """
        Whether or not the DNS cache contains the supplied name
        """
        return item in self._cache

    def __len__(self):
        return len(self._cache)

    def add_item(self, name: T_Hostname, ip_address: IPAddress, ttl: int) -> None:
        """
        Adds a new item to the cache
        """
        if ttl is None:
            raise WrongUsageError("Do not add a DNS item with TTL (Time to live) which is `None`!!!!")

        self._cache[name] = DNSCacheItem(ip_address, ttl, MainLoop.get_time())

    def forget_old_items(self) -> None:
        """
        Remove all items in the cache that their TTL (time to live) has expired
        """
        for item_name, dns_item in list(self._cache.items()):
            if MainLoop.get_time_since(dns_item.creation_time) > dns_item.ttl:
                del self._cache[item_name]

    def wipe(self) -> None:
        """
        Clear the DNS cache of all entries
        """
        self._cache.clear()

    def __repr__(self) -> str:
        """
        A textual representation of the cache
        Can be seen using the `dns -a` command
        """
        returned = "DNS Cache:\n" + ("-" * 30)
        for item_name, cache_item in self._cache.items():
            returned += "\n"
            returned += f"""
{'Record Name':.<20}: {item_name}
{'Record Type':.<20}: A
{'Time To Live':.<20}: {cache_item.ttl}
{'A (Host) Record':.<20}: {cache_item.ip_address.string_ip}
"""
        return returned
