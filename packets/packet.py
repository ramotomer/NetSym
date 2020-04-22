from exceptions import *
from gui.packet_graphics import PacketGraphics
from packets.protocol import Protocol


class Packet:
    """
    The container for all sendable packets.
    The class contains the Ethernet layer which is turn contains the IP layer
    and so on. The Packet class allows us to recursively check if a layer is in
    the packet and to draw the packet on the screen as one complete object.
    """
    def __init__(self, data=None):
        """"""  # TODO: doc here
        self.data = data
        self.graphics = None

    def show(self, connection_graphics, direction):
        """
        This signals the packet that it starts to be sent and that where it
        is sent from and to (Graphically).
        :param connection_graphics: a ConnectionGraphic object.
        :return: None
        """
        self.graphics = PacketGraphics(self.deepest_layer(), connection_graphics, direction)

    def deepest_layer(self):
        """
        Returns a pointer to the deepest layer in the packet.
        :return: A `Protocol` subclass object (ARP, Ethernet, etc...) which
        is the deepest layer in the packet. Not including strings and so on.
        Must be a `Protocol` subclass instance.
        """
        layer = self
        while isinstance(layer.data, Protocol):
            layer = layer.data
        return layer

    def __contains__(self, item):
        """
        Returns whether or not a certain layer is in the packet somewhere.
        :param item: A type-name of the layer you want.
        :return:
        """
        layer = self.data
        while isinstance(layer, Protocol):
            if layer.__class__.__name__ == item:
                return True
            layer = layer.data
        return False

    def __getitem__(self, item):
        """
        This is where the packet acts like a dictionary with the layer type as the key
        and the actual layer object as the value.
        :param item: The layer type one wishes to receive.
        :return: The layer object if it exists, if not, raises KeyError.
        """
        layer = self.data
        while layer is not None:
            if layer.__class__.__name__ == item:
                return layer
            layer = layer.data
        raise NoSuchLayerError('The packet does not contain that layer!')

    def __str__(self):
        """The shorter string representation of the packet"""
        return str(self.deepest_layer())

    def __repr__(self):
        """The string representation of the packet"""
        return f"Packet({self.data!r})"

    def multiline_repr(self):
        """Multiline representation of the packet"""
        return f"Packet: \n{self.data.multiline_repr()}"
