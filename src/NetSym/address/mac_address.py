from __future__ import annotations

import random
from typing import Union, List

from NetSym.consts import ADDRESSES
from NetSym.exceptions import *
from NetSym.usefuls.funcs import is_hex


class MACAddress:
    """
    This class represents a MAC address in the program.
    """

    generated_addresses: List[str] = []

    string_mac: str

    def __init__(self, string_mac: Union[MACAddress, str]) -> None:
        """
        Initiates a MACAddress object from a ip_layer
        :param string_mac: The string mac ('aa:bb:cc:11:22:76' for example)
        """
        if isinstance(string_mac, self.__class__):
            self.string_mac = string_mac.string_mac
            return

        if not isinstance(string_mac, str):
            raise InvalidAddressError(f"Input of `MACAddress` must be a string! or another `MACAddress`! but not {type(string_mac)}")

        if not MACAddress.is_valid(string_mac):
            raise InvalidAddressError(f"This address is not a valid MAC address: {string_mac}")

        self.string_mac = string_mac
        self.__class__.generated_addresses.append(string_mac)

    @property
    def vendor(self) -> str:
        return ADDRESSES.MAC.SEPARATOR.join(self.string_mac.split(ADDRESSES.MAC.SEPARATOR)[0:3])

    def is_broadcast(self) -> bool:
        """Returns if a MAC address is the broadcast MAC or not"""
        return bool(self.string_mac.lower() == ADDRESSES.MAC.BROADCAST.lower())

    @classmethod
    def broadcast(cls) -> MACAddress:
        """
        This is constructor that returns a broadcast MAC address object.
        :return: a MACAddress with the broadcast MAC.
        """
        return cls(ADDRESSES.MAC.BROADCAST)

    @classmethod
    def randomac(cls) -> str:
        """
        A constructor that returns a randomized mac address.
        Returns a different one each time.
        :return: A random string MAC address.
        """
        randomized_string = ADDRESSES.MAC.SEPARATOR.join([hex(random.randint(0, 255))[2:].zfill(2) for _ in range(6)])
        if randomized_string in cls.generated_addresses:
            return cls.randomac()
        cls.generated_addresses.append(randomized_string)
        return randomized_string

    @classmethod
    def stp_multicast(cls) -> MACAddress:
        """
        a constructor.
        The STP multicast address.
        :return: `MACAddress` object
        """
        return cls(ADDRESSES.MAC.STP_MULTICAST)

    @classmethod
    def no_mac(cls) -> MACAddress:
        """a constructor that Returns the MAC of 0s"""
        return cls("00:00:00:00:00:00")

    def is_no_mac(self) -> bool:
        """Returns whether or not this mac is the 0s mac"""
        return bool(self.string_mac == "00:00:00:00:00:00")

    @classmethod
    def copy(cls, mac_address: MACAddress) -> MACAddress:
        """
        Copy the mac address and return a new different object.
        :param mac_address: a `MACAddress` object.
        :return: a `MACAddress` object.
        """
        return cls(mac_address.string_mac)

    @staticmethod
    def is_valid(address: str) -> bool:
        """
        Receives a ip_layer that is supposed to be a mac address and returns whether
        or not it is a valid address.
        """
        splitted_address = address.split(ADDRESSES.MAC.SEPARATOR)
        return bool((len(splitted_address) == 6) and (all([is_hex(part) and len(part) == 2 for part in splitted_address])))

    def as_bytes(self) -> bytes:
        """
        Returns a byte representation of the MAC address
        :return: a `bytes` object which is the representation of the mac address.
        """
        address_as_numbers = [int(hex_num, 16) for hex_num in self.string_mac.split(ADDRESSES.MAC.SEPARATOR)]
        return bytes(address_as_numbers)

    def as_number(self) -> int:
        """
        Returns the MAC address as one number (00:11:22:33:44:55:66 -> 0x112233445566)
        :return: an integer which is the MAC address
        """
        return int(''.join(hex_part for hex_part in self.string_mac.split(ADDRESSES.MAC.SEPARATOR)), base=16)

    def __eq__(self, other: object) -> bool:
        """Determines whether two MAC addresses are equal or not"""
        if isinstance(other, str):
            other = MACAddress(other)
        elif not isinstance(other, MACAddress):
            raise NotImplementedError(f"MACAddress can only be checked for equality with an `str` or another `MACAddress` object, "
                                      f"not {other} which is a `{type(other)}`")

        return bool(self.string_mac.lower() == other.string_mac.lower())

    def __hash__(self) -> int:
        """Determines the hash of the `MACAddress` object"""
        return hash(repr(self))

    def __repr__(self) -> str:
        """The ip_layer representation of the MAC address"""
        return self.string_mac.upper()
