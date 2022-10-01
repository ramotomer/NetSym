from __future__ import annotations

from os import linesep
from typing import NamedTuple, Optional, TYPE_CHECKING, Union, Dict, Any

from address.ip_address import IPAddress
from consts import ADDRESSES
from exceptions import *

if TYPE_CHECKING:
    from computing.internals.interface import Interface
    from computing.computer import Computer


class RoutingTableItem(NamedTuple):
    """
    a routing table item.
    ip_address is the IP address to send the packet to (on the second layer) - the gateway
    interface is the IPAddress of the interface the packet should be sent on.
    """
    ip_address:   Optional[IPAddress]
    interface_ip: Optional[IPAddress]


class RoutingTable:
    """
    This is a routing table, it acts like a dictionary except that the keys are not checking equality, but rather they
    are checking if the IPAddresses are in the same subnet. (so if the IPAddress that is given fits the network
    destination and netmask in the key)

    The class is based on an `OrderedDict` because the order matters in a routing table!
    """
    def __init__(self) -> None:
        """
        Initiates the RoutingTable with some default entries.
        """
        dictionary = {
            IPAddress("0.0.0.0/0"):          RoutingTableItem(None, None),
            IPAddress("255.255.255.255/32"): RoutingTableItem(None, None),
            IPAddress("127.0.0.0/8"):        RoutingTableItem(ADDRESSES.IP.ON_LINK, IPAddress.loopback()),
        }

        self.dictionary: Dict[IPAddress, RoutingTableItem] = dictionary

    @property
    def default_gateway(self) -> RoutingTableItem:
        """The default gateway in the routing table"""
        return self[IPAddress("0.0.0.0/0")]

    def set_default_gateway(self, gateway: IPAddress, interface_ip: IPAddress) -> None:
        """
        Sets the default gateway in the routing table, using a gateway and an IP of an interface to go out
        from the computer to it.
        :return: None
        """
        self.dictionary[IPAddress("0.0.0.0/0")] = RoutingTableItem(gateway, interface_ip)
        self.dictionary[IPAddress("255.255.255.255/32")] = RoutingTableItem(gateway, interface_ip)

    @classmethod
    def create_default(cls, computer: Computer, expect_normal_gateway: bool = True) -> RoutingTable:
        """
        This is a constructor class method.
        Creates a default routing table for a given `Computer`.
        :param computer: a `Computer` object.
        :param expect_normal_gateway: whether or not to set the gateway to be the expected one (192.168.1.1 for example)
        :return: a `RoutingTable` object.
        """
        try:
            main_interface = computer.get_interface_with_ip()
        except NoSuchInterfaceError:
            return cls()    # if there is no interface with an IP address

        returned = cls()

        if expect_normal_gateway:
            gateway = main_interface.ip.expected_gateway()  # the expected IP address of a gateway in that subnet.
            returned.set_default_gateway(gateway, main_interface.ip)

        for interface in computer.interfaces:
            if interface.has_ip():
                returned.route_add(interface.ip.subnet(), ADDRESSES.IP.ON_LINK, IPAddress.copy(interface.ip))
                returned.route_add(IPAddress(interface.ip.string_ip + "/32"),
                                   IPAddress.copy(computer.loopback.ip),
                                   IPAddress.copy(computer.loopback.ip))

        return returned

    def route_add(self, destination_ip: IPAddress, gateway_ip: IPAddress, interface_ip: IPAddress) -> None:
        """
        Adds a route from all of the required ip_layer to do that
        :param destination_ip: an `IPAddress` of the destination.
        :param gateway_ip: an `IPAddress` of the gateway to send things to.
        :param interface_ip: an `IPAddress` of the interface to send through it things to the gateway.
        :return: None
        """
        arguments = (destination_ip, gateway_ip, interface_ip)
        if any(not isinstance(address, (IPAddress, str)) for address in arguments) and gateway_ip is not ADDRESSES.IP.ON_LINK:
            raise NoIPAddressError(
                f"One of the arguments to this function is not a string or IPAddress object!!!!! ({arguments})")

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
        interface_ip = IPAddress(interface_ip)
        send_to = self.default_gateway.ip_address
        if send_to is None or send_to.is_same_subnet(interface_ip):
            send_to = ADDRESSES.IP.ON_LINK

        self.route_add(interface_ip.subnet(), send_to, interface_ip)
        self.route_add(IPAddress(interface_ip.string_ip + "/32"), IPAddress.loopback(), IPAddress.loopback())

    def delete_interface(self, interface: Interface) -> None:
        """
        Removes an interface from the routing table.
        (This is also used when changing an interface's ip address)
        :param interface:
        :return:
        """
        if not interface.has_ip():
            return
        self.route_delete(interface.ip.subnet())
        self.route_delete(IPAddress(interface.ip.string_ip + "/32"))

    def __getitem__(self, item: Union[str, IPAddress]) -> RoutingTableItem:
        """
        allows the dictionary notation of dict[key].
        :param item: The key. Has to be an `IPAddress` object.
        :return: a `RoutingTableItem` object.
        """
        if not isinstance(item, (IPAddress, str)):
            raise InvalidAddressError(f"Key of a routing table must be a string or an IPAddress object!!! not {type(item)} like {repr(item)}")
        item = IPAddress(item)

        possible_addresses = list(filter(lambda destination: destination.is_same_subnet(item), self.dictionary))
        most_fitting_destination = max(possible_addresses, key=lambda address: address.subnet_mask)

        result = self.dictionary[most_fitting_destination]
        if result.ip_address is ADDRESSES.IP.ON_LINK:
            return RoutingTableItem(item, result.interface_ip)
        return result

    def __setitem__(self, key: Union[str, IPAddress], value: RoutingTableItem) -> None:
        """
        allows the dictionary notation of dict[key] = value
        :param key: has to be an `IPAddress` object.
        :param value: a `RoutingTableItem` object.
        :return: None
        """
        if not isinstance(key, (IPAddress, str)):
            raise InvalidAddressError(f"Key of a routing table must be a string or an IPAddress object!!! not {type(key)} like {key}")

        self.dictionary[IPAddress(key)] = value

    def __str__(self) -> str:
        """string representation of the routing table"""
        return f"RoutingTable({self.dictionary}, default={self.default_gateway})"

    def __repr__(self) -> str:
        """allows a 'route print' """
        return f"""
====================================================================
Active Routes:
Network Destination             Gateway           Interface  
{linesep.join(''.join([repr(key).rjust(20, ' '), str(self.dictionary[key].ip_address).rjust(20, ' '), 
                       str(self.dictionary[key].interface_ip).rjust(20, ' ')]) for key in self.dictionary)}	

Default Gateway:        {self.default_gateway.ip_address}
===================================================================
"""

    def dict_save(self) -> Dict:
        """
        Save the routing table as a dict that can later be reassembled to a routing table
        :return:
        """
        def ip_str_or_none(item: Any) -> Optional[str]:
            if item is None:
                return None
            return str(item)

        return {
            "class": "RoutingTable",
            "dict": {
                repr(ip): list(map(ip_str_or_none, routing_table_item))
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
        def ip_or_none(item: Optional[Union[str, IPAddress]]) -> Optional[Union[str, IPAddress]]:
            if item is None:
                return item
            if item == f"'{ADDRESSES.IP.ON_LINK}'" or item == ADDRESSES.IP.ON_LINK:
                return ADDRESSES.IP.ON_LINK
            return IPAddress(item)

        returned = cls()
        new_dict = {IPAddress(ip): RoutingTableItem(*map(ip_or_none, item)) for ip, item in dict_["dict"].items()}
        returned.dictionary = new_dict
        return returned
