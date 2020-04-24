from collections import namedtuple, OrderedDict
from exceptions import *
from address.ip_address import IPAddress
from os import linesep
from consts import ON_LINK


RoutingTableItem = namedtuple("RoutingTableItem", "ip_address interface_ip")
"""
a routing table item.
ip_address is the IP address to send the packet to (on the second layer) - the gateway
interface is the IPAddress of the interface the packet should be sent on.
"""


class RoutingTable:
    """
    This is a routing table, it acts like a dictionary except that the keys are not checking equlity, but rather they are
    checking if the IPAddresses are in the same subnet. (so if the IPAddress that is given fits the network destination and netmask in the key)

    The class is based on an `OrderedDict` because the order matters in a routing table!
    """
    def __init__(self, initial_dictionary, default_gateway=None):
        """
        Initiates the RoutingTable from a dictionary of {IPAddress: RoutingTableItem}
        :param initial_dictionary: `dict` or list of tuples.
        :param default_gateway: a default `RoutingTableItem` that
        """
        self.dictionary = OrderedDict(initial_dictionary)
        self.default_gateway = default_gateway

    @classmethod
    def create_default(cls, computer):
        """
        This is a constructor class method.
        Creates a default routing table for a given `Computer`.
        :param computer: a `Computer` object.
        :return: a `RoutingTable` object.
        """
        try:
            main_interface = computer.get_interface_with_ip()
        except NoSuchInterfaceError:
            return cls({}, RoutingTableItem(None, None))    # if there is no interface with an IP address
        gateway = main_interface.ip.expected_gateway()  # the expected IP address of a gateway in that subnet.
        dictionary = [
            (IPAddress("0.0.0.0/0"), RoutingTableItem(gateway, main_interface.ip)),
            *[
                (interface.ip.subnet(),RoutingTableItem(
                    ON_LINK,
                    IPAddress.copy(interface.ip)
                 )) for interface in computer.interfaces if interface.has_ip()
            ],
            (IPAddress("255.255.255.255/32"), RoutingTableItem(gateway, main_interface.ip)),
        ]
        return cls(OrderedDict(dictionary), RoutingTableItem(gateway, main_interface.ip))

    def __getitem__(self, item):
        """allows the dictionary notation of dict[key] """
        if not isinstance(item, IPAddress):
            raise InvalidAddressError("Key of a routing table must be an IPAddress object!!!")

        for destination_address in reversed(self.dictionary):  # the begging is the default and we use the first one (from the bottom) that fits for us.
            if destination_address.is_same_subnet(item):  # if the item (which is a dst ip) fits this subnet and subnet mask
                result = self.dictionary[destination_address]
                if result.ip_address is ON_LINK:
                    return RoutingTableItem(item, result.interface_ip)
                return result
        return self.default_gateway

    def __setitem__(self, key, value):
        """allows the dictionary notation of dict[key] = value """
        if not isinstance(key, IPAddress):
            raise InvalidAddressError("Key of a routing table must be an IPAddress object!!!")

        if key == IPAddress("0.0.0.0/0"):
            self.default_gateway = value

        self.dictionary[key] = value

    def __str__(self):
        """string representation of the routing table"""
        return f"RoutingTable({self.dictionary}, default={self.default_gateway})"

    def __repr__(self):
        """allows a route print"""
        return f"""
====================================================================
Active Routes:
Network Destination             Gateway           Interface  
{linesep.join(''.join([repr(key).rjust(20, ' '), str(self.dictionary[key].ip_address).rjust(20, ' '), str(self.dictionary[key].interface_ip).rjust(20, ' ')]) for key in self.dictionary)}	

Default Gateway:        {self.default_gateway.ip_address}
===================================================================
"""
