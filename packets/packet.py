from scapy.packet import Raw

from exceptions import *
from gui.tech.packet_graphics import PacketGraphics
from packets.all import Ether, protocols
from usefuls.funcs import get_the_one


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
        :return: A protocol instance (ARP, Ethernet, etc...) which
        is the deepest layer in the packet.
        """
        return self.data.getlayer([layer for layer in self.data.layers() if not issubclass(layer, (Raw, str))][-1])

    def copy(self):
        """
        Copies the packet.
        This is done in flooding of switches.
        :return: a copied `Packet` object.
        """
        copied = self.__class__(
            Ether(self.data.build())
        )
        copied.transform_to_good_attribute_names()
        return copied

    def is_valid(self):
        """
        Returns whether or not the packet is valid.
        """
        # TODO: implement packet.is_valid - use checksums
        return True and (self is self)

    def get_layer_by_name(self, name):
        """
        :param name: The name of the layer one wishes to receive.
        :return: The layer object if it exists, if not, raises KeyError.
        """
        for layer_class in self.data.layers():
            if any(layer_superclass.__name__ == name for layer_superclass in layer_class.__mro__):
                return self.data.getlayer(layer_class)
        raise NoSuchLayerError(f"The packet does not contain the layer '{name}'! \n{self.multiline_repr()}")

    def transform_to_good_attribute_names(self) -> None:
        """
        Change the data of the packet to be of the new classes that override the scapy classes
        Those new classes have nice good indicative attribute names :)
        """
        final_data = None
        for layer_class in self.data.layers():
            new_layer = get_the_one(protocols,
                                    lambda p: issubclass(p, layer_class),
                                    raises=NoSuchLayerError)(**self.data.getlayer(layer_class).fields)
            final_data = (final_data / new_layer) if final_data is not None else new_layer
        self.data = final_data

    def __contains__(self, item):
        """
        Returns whether or not a certain layer is in the packet somewhere.
        :param item: A type-name of the layer you want.
        :return:
        """
        try:
            self.get_layer_by_name(item)
        except NoSuchLayerError:
            return False
        return True

    def __getitem__(self, item):
        """
        This is where the packet acts like a dictionary with the layer type as the key
        and the actual layer object as the value.
        """
        return self.get_layer_by_name(item)

    def __str__(self):
        """The shorter string representation of the packet"""
        return str(self.deepest_layer())

    def __repr__(self):
        """The string representation of the packet"""
        return f"Packet({self.data!r})"

    def multiline_repr(self):
        """Multiline representation of the packet"""
        return f"\nPacket: \n{self.data.show2(dump=True)}"
