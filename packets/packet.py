from exceptions import *
from gui.tech.packet_graphics import PacketGraphics
from packets.protocol import Protocol


class Packet:
    """
    The container for all sendable packets.
    The class contains the Ethernet layer which is turn contains the IP layer
    and so on. The Packet class allows us to recursively check if a layer is in
    the packet and to draw the packet on the screen as one complete object.
    """
    def __init__(self, data=None):
        """
        Initiates the packet object, ip_layer is the out-most layer of the packet (usually Ethernet).
        `self.graphics` is a `PacketGraphics` object.
        :param data:
        """
        self.data = data
        self.graphics = None

    def show(self, connection_graphics, direction, is_opaque=False):
        """
        This signals the packet that it starts to be sent and that where it
        is sent from and to (Graphically).
        :param connection_graphics: a ConnectionGraphic object.
        :param direction: The direction that the packet is going in the connection.
        :param is_opaque: whether or not the packet is opaque (in a blocked connection)
        :return: None
        """
        self.graphics = PacketGraphics(self.deepest_layer(), connection_graphics, direction, is_opaque)

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

    def copy(self):
        """
        Copies the packet.
        This is done in flooding of switches.
        :return: a copied `Packet` object.
        """
        return self.__class__(
            self.data.copy(),
        )

    def get_layers(self):
        """
        This is a generator that runs over all of the layers in the packet not including the last one (if it is a string
        in ICMP for example)
        :yield: a `Protocol` object usually but any object that is put in the `ip_layer` field of a protocol.
        """
        layer = self.data
        while isinstance(layer, Protocol):
            yield layer
            layer = layer.data

    def is_valid(self):
        """
        Returns whether or not the packet is valid.
        The check is simply if the layer indexes are increasing. (for example layer 2, layer 3 then layer 4 as expected).
        :return: None
        """
        layer_indexes = [layer.layer_index for layer in self.get_layers()]
        return layer_indexes == sorted(layer_indexes)

    def __contains__(self, item):
        """
        Returns whether or not a certain layer is in the packet somewhere.
        :param item: A type-name of the layer you want.
        :return:
        """
        for layer in self.get_layers():
            if layer.__class__.__name__ == item:
                return True
        return False

    def __getitem__(self, item):
        """
        This is where the packet acts like a dictionary with the layer type as the key
        and the actual layer object as the value.
        :param item: The layer type one wishes to receive.
        :return: The layer object if it exists, if not, raises KeyError.
        """
        for layer in self.get_layers():
            if layer.__class__.__name__ == item:
                return layer
        raise NoSuchLayerError('The packet does not contain that layer!')

    def __str__(self):
        """The shorter string representation of the packet"""
        return str(self.deepest_layer())

    def __repr__(self):
        """The string representation of the packet"""
        return f"Packet({self.data!r})"

    def multiline_repr(self):
        """Multiline representation of the packet"""
        return f"\nPacket: \n{self.data.multiline_repr()}"
