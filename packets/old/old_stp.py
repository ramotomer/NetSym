import copy

from packets.protocol import Protocol

from exceptions import STPError


class LogicalLinkControl(Protocol):
    """
    This is the third layer that the STP goes over.
    (It does not go over ethernet, only above this logical-link-control layer which takes the IP layer's place as
    the third layer of the packet.)
    """
    def __init__(self, stp_layer):
        """Initiates the layer with no attributes at all, except for the ip_layer of the packet, which is `STP` protocol"""
        super(LogicalLinkControl, self).__init__(3, stp_layer)

    def copy(self):
        """
        Copy the layer
        :return:
        """
        return self.__class__(
            self.data.copy(),
        )

    def multiline_repr(self):
        """The multiline representation of the `LogicalLinkLayer` protocol"""
        return f"\n logical link control:\n{self.data.multiline_repr()}"


class STP(Protocol):
    """
    An STP packet. (actually in real life called BPDU packet).
    It contains information about the sending switch and allows the receiving switch to update accordingly.
    """
    def __init__(self, my_bid, root_bid, distance_to_root, root_declaration_time):
        """
        Initiates the STP packet with all of the fields it requires.
        :param my_bid: The `BID` of the sending switch.
        :param root_bid: the `BID` of the current root switch of the sending switch.
        :param distance_to_root: the shortest distance of the sending switch to the root switch.
        """
        super(STP, self).__init__(4, '')
        self.my_bid = my_bid
        self.root_bid = root_bid
        self.distance_to_root = distance_to_root

        self.root_declaration_time = root_declaration_time

    def copy(self):
        """
        Copy the STP packet
        :return:
        """
        return self.__class__(
            copy.copy(self.my_bid),
            copy.copy(self.root_bid),
            self.distance_to_root,
            self.root_declaration_time,
        )

    def __repr__(self):
        """The string representation of the STP packet"""
        return f"STP(my_bid={self.my_bid}, root_bid={self.root_bid}, distance_to_root={self.distance_to_root})"

    def multiline_repr(self):
        """The multiline representation of the STP packet"""
        return f"\nBPDU (STP):\nsender's BID:\n{self.my_bid!r}\nroot BID:\n{self.root_bid!r}\n " \
            f"distance to root: {self.distance_to_root}"


class BID:
    """
    A Bridge Identifier.
    This is a unique ID for each switch in a STP session.
    I consists of a priority and the switches MAC address (one of them).
    """
    def __init__(self, priority, mac, computer_name):
        """
        Initiates a BID object.
        :param priority: The priority of the switch
        :param mac: one of the `MACAddress`-s of the switch.
        """
        self.priority = priority
        self.mac = mac
        self.computer_name = computer_name
        self.done_loading = True

    @property
    def value(self):
        """
        The numerical value of the BID.
        :return: an integer value of the BID..
        """
        return int(str(self.priority) + str(self.mac.as_number()))

    def __gt__(self, other):
        """
        Allows to use the `this_BID > other_BID` notation
        :param other: another `BID` object or a number.
        :return: whether or not this is greater then the other.
        """
        if isinstance(other, int) or isinstance(other, float):
            return self.value > other
        if not isinstance(other, self.__class__):
            raise STPError(f"Cannot compare BID with this type: {type(other).__name__}!!!!")
        return self.value > other.value

    def __repr__(self):
        """The String representation of the BID"""
        return f"{self.priority}{self.mac} ({self.computer_name})"

    def __str__(self):
        """The short string representation of the BID"""
        return f"{self.priority}{self.mac}"

    def __hash__(self):
        """For using this as dictionary keys"""
        return hash(self.value)

    def __eq__(self, other):
        """Returns whether or not two BID objects are equal"""
        return self.value == other.value
