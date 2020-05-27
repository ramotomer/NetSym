from collections import namedtuple
from os import linesep

from address.ip_address import IPAddress
from consts import *
from exceptions import *

RoutingTableItem = namedtuple("RoutingTableItem", "ip_address interface_ip")
"""
a routing table item.
ip_address is the IP address to send the packet to (on the second layer) - the gateway
interface is the IPAddress of the interface the packet should be sent on.
"""


class RoutingTable:
    """
    This is a routing table, it acts like a dictionary except that the keys are not checking equality, but rather they
    are checking if the IPAddresses are in the same subnet. (so if the IPAddress that is given fits the network
    destination and netmask in the key)

    The class is based on an `OrderedDict` because the order matters in a routing table!
    """
    def __init__(self):
        """
        Initiates the RoutingTable with some default entries.
        """
        dictionary = {
            IPAddress("0.0.0.0/0"): RoutingTableItem(None, None),
            IPAddress("255.255.255.255/32"): RoutingTableItem(None, None),
            IPAddress("127.0.0.0/8"): RoutingTableItem(ON_LINK, IPAddress.loopback()),
        }

        self.dictionary = dictionary

    @property
    def default_gateway(self):
        """The default gateway in the routing table"""
        return self[IPAddress("0.0.0.0/0")]

    def set_default_gateway(self, gateway, interface_ip):
        """
        Sets the default gateway in the routing table, using a gateway and an IP of an interface to go out
        from the computer to it.
        :return: None
        """
        self.dictionary[IPAddress("0.0.0.0/0")] = RoutingTableItem(gateway, interface_ip)
        self.dictionary[IPAddress("255.255.255.255/32")] = RoutingTableItem(gateway, interface_ip)

    @classmethod
    def create_default(cls, computer, expect_normal_gateway=True):
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
                returned.route_add(interface.ip.subnet(), ON_LINK, IPAddress.copy(interface.ip))
                returned.route_add(IPAddress(interface.ip.string_ip + "/32"),
                                   IPAddress.copy(computer.loopback.ip),
                                   IPAddress.copy(computer.loopback.ip))

        return returned

    def route_add(self, destination_ip, gateway_ip, interface_ip):
        """
        Adds a route from all of the required data to do that
        :param destination_ip: an `IPAddress` of the destination.
        :param gateway_ip: an `IPAddress` of the gateway to send things to.
        :param interface_ip: an `IPAddress` of the interface to send through it things to the gateway.
        :return: None
        """
        arguments = (destination_ip, gateway_ip, interface_ip)
        if any(not isinstance(address, IPAddress) for address in arguments) and gateway_ip is not ON_LINK:
            raise NoIPAddressError(
                f"One of the arguments to this function is not an IPAddress object!!!!! ({arguments})")

        if destination_ip in self.dictionary:
            raise RoutingTableError("Cannot add a route to a destination that already exists!!!")

        self.dictionary[destination_ip] = RoutingTableItem(gateway_ip, interface_ip)

    def route_delete(self, destination_ip):
        """
        Deletes a route from the routing table
        :param destination_ip: The destination IP address and netmask
        :return: None
        """
        if destination_ip not in self.dictionary:
            raise RoutingTableError(f"Cannot remove route. it is not in the routing table {destination_ip}!!!")
        del self.dictionary[destination_ip]

    def add_interface(self, interface_ip):
        """
        Adds a new interface to the routing table in the default way.
        :param interface_ip: an `IPAddress` object of the IP address of the interface that one wishes to add to
        the routing table.
        :return: None
        """
        send_to = self.default_gateway.ip_address
        if send_to is None or send_to.is_same_subnet(interface_ip):
            send_to = ON_LINK

        self.route_add(interface_ip.subnet(), send_to, interface_ip)
        self.route_add(IPAddress(interface_ip.string_ip + "/32"), IPAddress.loopback(), IPAddress.loopback())
        # TODO: BUG: when a computer doesn't have an IP and we give it one after it is created it cant send itself pings

    def __getitem__(self, item):
        """
        allows the dictionary notation of dict[key].
        :param item: The key. Has to be an `IPAddress` object.
        :return: a `RoutingTableItem` object.
        """
        if not isinstance(item, IPAddress):
            raise InvalidAddressError(f"Key of a routing table must be an IPAddress object!!! not {item}")

        possible_addresses = list(filter(lambda destination: destination.is_same_subnet(item), self.dictionary))
        most_fitting_destination = max(possible_addresses, key=lambda address: address.subnet_mask)

        result = self.dictionary[most_fitting_destination]
        if result.ip_address is ON_LINK:
            return RoutingTableItem(item, result.interface_ip)
        return result

    def __setitem__(self, key, value):
        """
        allows the dictionary notation of dict[key] = value
        :param key: has to be an `IPAddress` object.
        :param value: a `RoutingTableItem` object.
        :return: None
        """
        if not isinstance(key, IPAddress):
            raise InvalidAddressError("Key of a routing table must be an IPAddress object!!!")

        self.dictionary[key] = value

    def __str__(self):
        """string representation of the routing table"""
        return f"RoutingTable({self.dictionary}, default={self.default_gateway})"

    def __repr__(self):
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
