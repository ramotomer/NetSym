from __future__ import annotations

from operator import attrgetter
from os import linesep
from typing import NamedTuple, Optional, Union, Dict, List

from NetSym.address.ip_address import IPAddress
from NetSym.consts import ADDRESSES
from NetSym.exceptions import *


class RoutingTableItem(NamedTuple):
    """
    a routing table item.
    ip_address is the IP address to send the packet to (on the second layer) - the gateway
    interface is the IPAddress of the interface the packet should be sent on.
    """
    gateway_ip:   Union[str, IPAddress]  # can be 'On-link'
    interface_ip: IPAddress

    @property
    def ip_address(self):
        return self.gateway_ip  # TODO: IMPROVE: remove this alias please it is not as understandable


class TypeSafeRoutingTableItem(NamedTuple):
    """
    Just like RoutingTableItem - only it is guaranteed that the `ip_address` field is never 'On-link'
    """
    gateway_ip:   IPAddress
    interface_ip: IPAddress

    @property
    def ip_address(self):
        return self.gateway_ip  # TODO: IMPROVE: remove this alias please it is not as understandable


class RoutingTable:
    """
    This is a routing table, it acts like a dictionary except that the keys are not checking equality, but rather they
    are checking if the IPAddresses are in the same subnet. (so if the IPAddress that is given fits the network
    destination and netmask in the key)

    The class is based on an `OrderedDict` because the order matters in a routing table!
    """

    dictionary: Dict[IPAddress, RoutingTableItem]

    def __init__(self, initial_dict: Optional[Dict[IPAddress, RoutingTableItem]] = None) -> None:
        """
        Initiates the RoutingTable with some default entries.
        """
        if initial_dict is not None:
            self.dictionary = initial_dict
            return

        self.dictionary = {
            IPAddress("127.0.0.0/8"): RoutingTableItem(ADDRESSES.IP.ON_LINK, IPAddress.loopback()),
        }

    @property
    def default_gateway(self) -> Optional[TypeSafeRoutingTableItem]:
        """The default gateway in the routing table"""
        try:
            return self[IPAddress("0.0.0.0/0")]
        except RoutingTableCouldNotRouteToIPAddress:
            return None

    def set_default_gateway(self, gateway: IPAddress, interface_ip: IPAddress) -> None:
        """
        Sets the default gateway in the routing table, using a gateway and an IP of an interface to go out
        from the computer to it.
        :return: None
        """
        self.dictionary[IPAddress("0.0.0.0/0")]          = RoutingTableItem(gateway, interface_ip)
        self.dictionary[IPAddress("255.255.255.255/32")] = RoutingTableItem(gateway, interface_ip)

    @classmethod
    def create_default(cls, ips: List[IPAddress], expect_normal_gateway: bool = True) -> RoutingTable:
        """
        This is a constructor class method.
        Creates a default routing table for a given `Computer`.
        :param ips: A list of the ip addresses that the computer has that we need to note while creating the routing table.
        :param expect_normal_gateway: whether or not to set the gateway to be the expected one (192.168.1.1 for example)
        :return: a `RoutingTable` object.
        """
        table = cls()
        if not ips:
            return table

        if expect_normal_gateway:
            table.set_default_gateway(ips[0].expected_gateway(), ips[0])  # set the expected IP address of a gateway in that subnet.

        for ip in ips:
            table.add_interface(ip)
        return table

    def route_add(self, destination_ip: IPAddress, gateway_ip: Union[str, IPAddress], interface_ip: IPAddress) -> None:
        """
        Adds a route from all of the required ip_layer to do that
        :param destination_ip: an `IPAddress` of the destination.
        :param gateway_ip: an `IPAddress` of the gateway to send things to.
        :param interface_ip: an `IPAddress` of the interface to send through it things to the gateway.
        :return: None
        """
        if gateway_ip is not ADDRESSES.IP.ON_LINK:
            gateway_ip = IPAddress(gateway_ip)
        self.dictionary[IPAddress(destination_ip)] = RoutingTableItem(gateway_ip, IPAddress(interface_ip))

    def route_delete(self, destination_ip: IPAddress) -> None:
        """
        Deletes a route from the routing table
        :param destination_ip: The destination IP address and netmask
        :return: None
        """
        destination_ip = IPAddress(destination_ip)
        if destination_ip not in self.dictionary:
            raise RoutingTableError(f"Cannot remove route. it is not in the routing table {destination_ip}!!!")

        del self.dictionary[destination_ip]

    def add_interface(self, interface_ip: IPAddress) -> None:
        """
        Adds a new interface to the routing table in the default way.
        :param interface_ip: an `IPAddress` object of the IP address of the interface that one wishes to add to
        the routing table.
        :return: None
        """
        self.route_add(IPAddress(interface_ip.string_ip + "/32"), IPAddress.loopback(), IPAddress.loopback())
        self.route_add(interface_ip.subnet(), ADDRESSES.IP.ON_LINK, IPAddress(interface_ip))

    def delete_interface(self, interface_ip: IPAddress) -> None:
        """
        Removes an interface from the routing table.
        (This is also used when changing an interface's ip address)
        :param interface_ip: The ip of the interface to delete
        :return:
        """
        self.route_delete(interface_ip.subnet())
        self.route_delete(IPAddress(interface_ip.string_ip + "/32"))

    def __getitem__(self, item: Union[str, IPAddress]) -> TypeSafeRoutingTableItem:
        """
        allows the dictionary notation of dict[key].
        :param item: The key. Has to be an `IPAddress` object.
        :return: a `RoutingTableItem` object.
        """
        requested_address = IPAddress(item)
        possible_addresses = list(filter(lambda destination: destination.is_same_subnet(requested_address), self.dictionary))
        if not possible_addresses:
            raise RoutingTableCouldNotRouteToIPAddress(f"IP: {requested_address!r}... ")  # Routing Table: \n{self!r}")

        result = self.dictionary[max(possible_addresses, key=attrgetter("subnet_mask"))]
        if isinstance(result.gateway_ip, str):  # is ON_LINK
            return TypeSafeRoutingTableItem(requested_address, result.interface_ip)

        return TypeSafeRoutingTableItem(result.gateway_ip, result.interface_ip)

    def __contains__(self, item: Union[str, IPAddress]) -> bool:
        """
        Returns whether or not the routing table knows how to route to the supplied ip address.
        """
        try:
            self[item]
        except RoutingTableCouldNotRouteToIPAddress:
            return False
        return True

    def __str__(self) -> str:
        """string representation of the routing table"""
        return f"RoutingTable({self.dictionary}, default={self.default_gateway})"

    def __repr__(self) -> str:
        """allows a 'route print' """
        return f"""
====================================================================
Active Routes:
Network Destination             Gateway           Interface  
{linesep.join(''.join([repr(key).rjust(20, ' '), str(self.dictionary[key].gateway_ip).rjust(20, ' '), 
                       str(self.dictionary[key].interface_ip).rjust(20, ' ')]) for key in self.dictionary)}	

Default Gateway:        {getattr(self.default_gateway, "ip_address", None)}
===================================================================
"""

    def dict_save(self) -> Dict:
        """
        Save the routing table as a dict that can later be reassembled to a routing table
        :return:
        """
        return {
            "class": "RoutingTable",
            "dict": {
                repr(ip): list(map(str, routing_table_item))
                for ip, routing_table_item in self.dictionary.items()
            }
        }

    @classmethod
    def from_dict_load(cls, dict_: Dict) -> RoutingTable:
        """
        Load the routing table from a dictionary that was saved to a file
        :param dict_: the dict
        :return:
        """
        def ip_or_on_link(item: Union[str, IPAddress]) -> Union[str, IPAddress]:
            if isinstance(item, str) and (item.strip("'") == ADDRESSES.IP.ON_LINK):
                return ADDRESSES.IP.ON_LINK
            return IPAddress(item)

        return cls(
            {IPAddress(ip): RoutingTableItem(ip_or_on_link(item[0]), IPAddress(item[1]))
             for ip, item in dict_["dict"].items()}
        )
