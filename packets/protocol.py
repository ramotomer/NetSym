from abc import ABCMeta, abstractmethod


class Protocol(metaclass=ABCMeta):
    """
    This is a layer class.
    It is the superclass of all classes that are layers inside of a packet.
    (Ethernet, IP, TCP, ICMP, ARP and so on)

    It has a `type` property which is the type of the layer WITHIN IT (not itself)
    """
    def __init__(self, data):
        """"""  # TODO: doc here
        self.data = data

    @property
    def type(self):
        """The type of the layer within it"""
        return type(self.data)

    @abstractmethod
    def multiline_repr(self):
        """The multiline representation of the layer."""
