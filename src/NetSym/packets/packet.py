from __future__ import annotations

from typing import TYPE_CHECKING, Tuple, Optional, List

import scapy

from NetSym.exceptions import *
from NetSym.gui.tech.packet_graphics import PacketGraphics
from NetSym.packets.all import Ether
from NetSym.packets.usefuls.usefuls import is_raw_layer, scapy_layer_class_to_our_class

if TYPE_CHECKING:
    from NetSym.gui.tech.cable_connection_graphics import CableConnectionGraphics


class Packet:
    """
    The container for all sendable packets.
    The class contains the Ethernet layer which is turn contains the IP layer
    and so on. The Packet class allows us to recursively check if a layer is in
    the packet and to draw the packet on the screen as one complete object.
    """
    def __init__(self, data: scapy.packet.Packet) -> None:
        """
        Initiates the packet object, ip_layer is the out-most layer of the packet (usually Ethernet).
        `self.graphics` is a `PacketGraphics` object.
        """
        self.data: scapy.packet.Packet = data
        self.graphics: Optional[PacketGraphics] = None

    def init_graphics(self, connection_graphics: CableConnectionGraphics, direction: str) -> List[PacketGraphics]:
        """
        This signals the packet that it starts to be sent and that where it
        is sent from and to (Graphically).
        :param connection_graphics: the graphics_object of the connection the packet is currently in
        :param direction: The direction that the packet is going in the connection.
        """
        self.graphics = PacketGraphics(self.deepest_layer(), connection_graphics, direction)
        return [self.graphics]

    def get_graphics(self) -> PacketGraphics:
        """
        Get the PacketGraphics object of this packet, If it is not yet initialized - raise
        """
        if self.graphics is None:
            raise GraphicsObjectNotYetInitialized(f"packet: {self.multiline_repr()}")

        return self.graphics

    def deepest_layer(self) -> scapy.packet.Packet:
        """
        Returns the deepest layer in the packet.
        :return: A protocol instance (ARP, Ethernet, etc...) which
        is the deepest layer in the packet.
        """
        return self.data.getlayer([layer for layer in self.data.layers() if not is_raw_layer(layer)][-1])

    def copy(self: Packet) -> Packet:
        """
        Return a separate identical instance of the packet object
        """
        return self.__class__(self.data.copy())

    def is_valid(self) -> bool:
        """
        Returns whether or not the packet is valid.
        """
        # TODO: implement packet.is_valid - use checksums
        return True

    def get_layer_by_name(self, name: str) -> scapy.packet.Packet:
        """
        :param name: The name of the layer one wishes to receive.
        :return: The layer object if it exists, if not, raises KeyError.
        """
        for layer_class in self.data.layers():
            if any(layer_superclass.__name__ == name for layer_superclass in layer_class.__mro__):
                return self.data.getlayer(layer_class)
        # raise NoSuchLayerError(f"The packet does not contain the layer '{name}'! \n{self.multiline_repr()}")  # multiline repr failed... :(
        raise NoSuchLayerError(f"The packet does not contain the layer '{name}'!")

    def get_layer_by_name_no_payload(self, name: str) -> scapy.packet.Packet:
        """
        Return only the header of the specific layer requested - without the payload that is inside it
        """
        layer = self.get_layer_by_name(name)
        return scapy_layer_class_to_our_class(layer.__class__)(layer.build()[:-len(layer.payload)])

    def transform_to_indicative_attribute_names(self) -> None:
        """
        Change the data of the packet to be of the new classes that override the scapy classes
        Those new classes have nice good indicative attribute names :)
        If the packet contains a layer that does not have indicative attribute names available - keep that layer of the packet
        """
        final_data = None
        for layer_class in self.data.layers():
            new_layer = scapy_layer_class_to_our_class(layer_class)(**self.data.getlayer(layer_class).fields)
            final_data = (final_data / new_layer) if final_data is not None else new_layer
        self.data = final_data

    def reparse_layers(self) -> None:
        """
        Run again the parsing of the different layers of the packet
        """
        self.data = Ether(self.data.build())
        self.transform_to_indicative_attribute_names()

    def summary(self, discarded_protocols: Tuple[str] = ("Ether", "IP", "Raw")) -> str:
        """
        Return a short string which is a summary line of the packet
        Uses the scapy `packet.summary` method - but removes some redundant text from it.
        You can choose what protocols to ignore using the `discarded_protocols` parameter
        """
        scapy_summary = scapy.layers.l2.Ether(self.data.build()).summary()
        return ' / '.join([layer for layer in scapy_summary.split(' / ') if layer not in discarded_protocols])

    def __contains__(self, item: str) -> bool:
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

    def __getitem__(self, item: str) -> scapy.packet.Packet:
        """
        This is where the packet acts like a dictionary with the layer type as the key
        and the actual layer object as the value.
        """
        return self.get_layer_by_name(item)

    def __str__(self) -> str:
        """The shorter string representation of the packet"""
        return str(self.deepest_layer())

    def __repr__(self) -> str:
        """The string representation of the packet"""
        return f"Packet({self.data!r})"

    def multiline_repr(self) -> str:
        """Multiline representation of the packet"""
        return f"\nPacket: (length: {len(self.data)}) \n{self.data.show2(dump=True)}"
