from __future__ import annotations

from typing import NamedTuple, Dict, Optional, Union, Iterator

from address.ip_address import IPAddress
from address.mac_address import MACAddress
from consts import COMPUTER, T_Time
from exceptions import InvalidAddressError
from gui.main_loop import MainLoop


class ARPCacheItem(NamedTuple):
    """
    the values of the ARP cache of the computer (MAC address and creation time)
    """
    mac:  MACAddress
    time: T_Time
    type: str


class ArpCache:
    """
    Holds a computers mapping for an IP address to the MAC address.
    """
    def __init__(self, initial_dict: Optional[Dict[IPAddress, ARPCacheItem]] = None) -> None:
        """
        init it.
        The arp-cache is basically just a dictionary from an IPAddress object to an ARPCacheItem namedtuple that holds
        the info for that ip. (the mac, the time it was added, etc...)
        :param initial_dict:
        """
        self.__cache: Dict[IPAddress, ARPCacheItem] = initial_dict if initial_dict is not None else {}

    def forget_old_items(self, max_lifetime: T_Time = COMPUTER.ARP_CACHE.ITEM_LIFETIME) -> None:
        """
        Check through the ARP cache if any addresses should be forgotten and if so forget them.
        (removes from the arp cache)
        :return: None
        """
        for ip, arp_cache_item in list(self.__cache.items()):
            if MainLoop.instance.time_since(arp_cache_item.time) > max_lifetime:
                del self.__cache[ip]

    def add_dynamic(self, ip_address: Union[str, IPAddress], mac_address: Union[str, MACAddress]) -> None:
        """
        Adds a dynamic arp cache item
        :param ip_address: IPAddress or str
        :param mac_address: MACAddress or str
        :return:
        """
        self.__cache[IPAddress(ip_address)] = ARPCacheItem(MACAddress(mac_address),
                                                           MainLoop.instance.time(),
                                                           COMPUTER.ARP_CACHE.DYNAMIC)

    def add_static(self, ip_address: Union[str, IPAddress], mac_address: Union[str, MACAddress]) -> None:
        """
        Adds a static arp cache item
        :param ip_address: IPAddress or str
        :param mac_address: MACAddress or str
        :return:
        """
        self.__cache[IPAddress(ip_address)] = ARPCacheItem(mac_address,
                                                           MainLoop.instance.time(),
                                                           COMPUTER.ARP_CACHE.STATIC)

    def wipe(self) -> None:
        """
        Delete all dynamic items of the arp cache
        :return:
        """
        for key in [ip for ip in self.__cache if self.__cache[ip].type == COMPUTER.ARP_CACHE.DYNAMIC]:
            del self.__cache[key]

    def __contains__(self, item: IPAddress) -> bool:
        if not isinstance(item, IPAddress):
            raise InvalidAddressError(f"Key of an arp cache must be an IPAddress object!!! not {type(item)} like {repr(item)}")

        return item.string_ip in {ip.string_ip: value for ip, value in self.__cache.items()}

    def __getitem__(self, item: IPAddress) -> bool:
        if not isinstance(item, IPAddress):
            raise KeyError(f"Only search the arp cache for IPAddress! not {type(item)}!")
        return {ip.string_ip: value for ip, value in self.__cache.items()}[item.string_ip]

    def __iter__(self) -> Iterator:
        return iter(self.__cache)

    def __repr__(self) -> str:
        string = f"{'IP address': >19}{'mac': >22}\n"
        for ip, arp_cache_item in self.__cache.items():
            string += f"{str(ip): >19}{str(arp_cache_item.mac): >22}\n"
        return string
