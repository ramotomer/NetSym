from consts import *
from exceptions import InvalidAddressError


class IPAddress:
    """
    This class represents an IP address in the program.
    """
    def __init__(self, string_ip):
        """
        Initiates a IPAddress object from a data
        :param string_mac: The data mac ('132.23.245.1/24' for example or '1.1.1.1')
        """
        if isinstance(string_ip, self.__class__):
            self.string_ip, self.subnet_mask = string_ip.string_ip, string_ip.subnet_mask
            return
        elif not isinstance(string_ip, str):
            raise InvalidAddressError("The argument to this constructor must be a string or an IPAddress object!!!")

        ip, subnet_mask = string_ip, DEFAULT_SUBNET_MASK
        if IP_SUBNET_SEPARATOR in string_ip:
            ip, subnet_mask = string_ip.lower().split(IP_SUBNET_SEPARATOR)

        if not self.is_valid(ip) or not self.is_valid_subnet_mask(subnet_mask):
            raise InvalidAddressError(INVALID_IP_ADDRESS + ' ' + str(string_ip))

        self.string_ip = ip
        self.subnet_mask = int(subnet_mask)

    def is_same_subnet(self, other):
        """
        Receives another ip address and returns if they are in the same subnet.
        :param other: The other IPAddress object to check.
        :return: Whether or not the IP addresses are in the same subnet
        """
        mask = int(self.as_bits(self.mask_from_number(self.subnet_mask)), 2)

        my_masked_address = int(self.as_bits(self.string_ip), 2) & mask
        other_masked_address = int(other.as_bits(other.string_ip), 2) & mask

        return my_masked_address == other_masked_address

    def is_broadcast(self):
        """
        Returns if the IP address is a broadcast address or not.
        :return:
        """
        _, _, _, last_byte = self.string_ip.split(IP_ADDRESS_SEPARATOR)
        return int(last_byte) == 255  # I had some thinking if to put in constant, decided not to...

    def increase(self):
        """Increases the IP address by one. If the IP is at max, raise AddressError"""
        as_bytes = IPAddress.as_bytes(self.string_ip)
        as_bytes[3] = int(as_bytes[3]) + 1
        self.string_ip = IP_ADDRESS_SEPARATOR.join([str(byte) for byte in as_bytes])

    def expected_gateway(self):
        """Returns the expected IP address of this subnet (for example if this IP is 192.168.1.5/24 it will return 192.168.1.1)"""
        splitted = self.string_ip.split(IP_ADDRESS_SEPARATOR)
        splitted[3] = '1'
        return self.__class__(IP_ADDRESS_SEPARATOR.join(splitted) + '/' + str(self.subnet_mask))

    @staticmethod
    def as_bytes(address):
        """
        Returns a byte representation of the IP address
        :param address: The string address
        :return: a `bytearray` object which is the representation of the ip address.
        """
        address_as_numbers = [int(part) for part in address.split(IP_ADDRESS_SEPARATOR)]
        return bytearray(address_as_numbers)

    @staticmethod
    def is_valid(address):
        """
        Receives a data that is supposed to be an ip address and returns whether
        or not it is a valid address.
        :param address: The data address
        :return: Whether or not it is valid.
        """
        if not isinstance(address, str):
            return False
        splitted_address = address.split(IP_ADDRESS_SEPARATOR)
        return len(splitted_address) == 4 and \
               all([part.isdigit() and 0 <= int(part) < 256 for part in splitted_address])

    @staticmethod
    def is_valid_subnet_mask(subnet_mask):
        """
        Receives a subnet mask in the numerical form ('24' or '16') and decides if
        it is valid or not.
        :param subnet_mask: A data that should be a numerical form of a mask
        :return: whether it is valid
        """
        return isinstance(subnet_mask, str) and subnet_mask.isdigit() and 0 <= int(subnet_mask) < IP_ADDRESS_BIT_LENGTH

    @staticmethod
    def mask_from_number(number):
        """
        Receive a numeral simple representation of the subnet mask (24) and
        return the long 'mask' form ('255.255.255.0')
        :param number: An integer with the numeral form.
        :return: a string of the subnet mask with the 'mask' form. ('255.255.255.0')
        """
        bits = ''.join(reversed(('1' * number).zfill(IP_ADDRESS_BIT_LENGTH)))
        grouped_as_bytes = [''.join(bits[i:i+8]) for i in range(0, IP_ADDRESS_BIT_LENGTH, 8)]
        return IP_ADDRESS_SEPARATOR.join([str(int(byte, 2)) for byte in grouped_as_bytes])

    @classmethod
    def as_bits(cls, address):
        """
        Returns a binary representation of the IP address.
        :param address: a string address to turn into bits.
        :return: a string starting with 0b and the rest of the bits of the IP address
        """
        return '0b' + ''.join(
            [bin(byte)[2:].zfill(8) for byte in cls.as_bytes(address)])

    @classmethod
    def copy(cls, other):
        """
        Receive an IPAddress and return a copy of that object.
        :param other: IPAddress object
        :return: another differrent but identical IPAddress object.
        """
        return cls(other.string_ip + IP_SUBNET_SEPARATOR + str(other.subnet_mask))

    @classmethod
    def increased(cls, other):
        """
        Receives an IP address and returns a copy of it which is increased by one.
        (192.168.1.1 /24  -->  192.168.1.2 /24)

        :param other: an IPAddres object.
        :return: a different object which the increased IP address.
        """
        returned = cls.copy(other)
        returned.increase()
        return returned

    def __eq__(self, other):
        """Test whether two ip addresses are equal or not"""
        return self.string_ip == other.string_ip

    def __hash__(self):
        """Allows the IPAddress object to be a key in a dictionary or a set"""
        return hash(self.string_ip)

    def __repr__(self):
        """The string representation of the IP address"""
        return f"{self.string_ip} /{self.subnet_mask}"

    def __str__(self):
        """The shorter string representation of the IP address"""
        return self.string_ip