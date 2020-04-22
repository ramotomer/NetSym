from consts import *
from exceptions import *
import random
from usefuls import is_hex


class MACAddress:
    """
    This class represents a MAC address in the program.
    """

    generated_addresses = []

    def __init__(self, string_mac):
        """
        Initiates a MACAddress object from a data
        :param string_mac: The string mac ('aa:bb:cc:11:22:76' for example)
        """
        if not MACAddress.is_valid(string_mac):
            raise InvalidAddressError(INVALID_MAC_ADDRESS)
        self.string_mac = string_mac
        self.__class__.generated_addresses.append(string_mac)
        self.vendor = MAC_ADDRESS_SEPARATOR.join(string_mac.split(MAC_ADDRESS_SEPARATOR)[0:3])

    def is_broadcast(self):
        """Returns if a MAC address is the broadcast MAC or not"""
        return self.string_mac == BROADCAST_MAC

    @classmethod
    def broadcast(cls):
        """
        This is constructor that returns a broadcast MAC address object.
        :return: a MACAddress with the broadcast MAC.
        """
        return cls(BROADCAST_MAC)

    @classmethod
    def randomac(cls):
        """
        A constructor that returns a randomized mac address.
        Returns a different one each time.
        :return: A random string MAC address.
        """
        randomized_string = MAC_ADDRESS_SEPARATOR.join([hex(random.randint(0, 255))[2:].zfill(2) for _ in range(6)])
        if randomized_string in cls.generated_addresses:
            return cls.randomac()
        cls.generated_addresses.append(randomized_string)
        return randomized_string

    @staticmethod
    def is_valid(address):
        """
        Receives a data that is supposed to be a mac address and returns whether
        or not it is a valid address.
        :param address: The string address
        :return: Whether or not it is valid.
        """
        splitted_address = address.split(MAC_ADDRESS_SEPARATOR)
        return len(splitted_address) == 6 and \
               all([is_hex(part) and len(part) == 2 for part in splitted_address])

    @staticmethod
    def as_bytes(address):
        """
        Returns a byte representation of the MAC address
        :param mac_address_object: A MACAddress object.
        :return: a `bytes` object which is the representation of the mac address.
        """
        address_as_numbers = [int(hex_num, 16) for hex_num in address.string_mac.split(MAC_ADDRESS_SEPARATOR)]
        return bytes(address_as_numbers)

    def __eq__(self, other):
        """Determines whether two MAC addresses are equal or not"""
        return self.string_mac.lower() == other.string_mac.lower()

    def __hash__(self):
        """Determines the hash of the `MACAddress` object"""
        return hash(repr(self))

    def __repr__(self):
        """The data representation of the MAC address"""
        return self.string_mac
