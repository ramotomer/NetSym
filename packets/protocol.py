from abc import ABCMeta, abstractmethod


class Protocol(metaclass=ABCMeta):
    """
    This is a layer class.
    It is the superclass of all classes that are layers inside of a packet.
    (Ethernet, IP, TCP, ICMP, ARP and so on)

    It has a `type` property which is the type of the layer WITHIN IT (not itself)

    The `layer_index` is the number of the layer the protocol belongs to (Ethernet - 2, IP - 3 etc...)
    """
    def __init__(self, layer_index, data):
        """
        Initiates the protocol instance.
        The only requirement is a `ip_layer` attribute.
        :param data: The ip_layer of the protocol (usually, another `Protocol` instance)
        """
        self.layer_index = layer_index
        self.data = data

    @property
    def type(self):
        """The type of the layer within it"""
        return type(self.data)

    @abstractmethod
    def copy(self):
        """
        Copy this specific protocol layer. (Not its ip_layer)
        :return: a new `Protocol` instance
        """
        pass

    @abstractmethod
    def multiline_repr(self):
        """
        The multiline representation of the layer, used for the VIEW_MODE in the `UserInterface` class.
        :return: a string.
        """
        pass
