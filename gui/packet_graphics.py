from gui.image_graphics import ImageGraphics
from consts import *


class PacketGraphics(ImageGraphics):
    """
    This class is a `GraphicsObject` subclass which is the graphical representation
    of packets that are sent between computers.

    The packets know the connection's length, speed start and end, and so they can calculate where they should be at
    any given moment.
    """
    def __init__(self, deepest_layer, connection_graphics, direction):
        """
        This method initiates a `PacketGraphics` instance.
        :param deepest_layer: The deepest packet layer in the packet.
        :param connection_graphics: The `ConnectionGraphics` object which is the graphics of the `Connection` this packet
            is sent through. It is used for the start and end coordinates.

        The self.progress variable is how much of the connection the packet has passed already. That information comes
        from the `Connection` class that sent the packet. It updates it in the `Connection.move_packets` method.
        """
        super(PacketGraphics, self).__init__(
                            IMAGES.format(self.image_from_packet(deepest_layer)),
                            connection_graphics.get_coordinates(direction)[0],
                            connection_graphics.get_coordinates(direction)[1],
                            centered=True,
                            scale_factor=PACKET_SCALE_FACTOR)
        self.is_packet = True

        self.connection_graphics = connection_graphics
        self.direction = direction
        self.progress = 0
        self.str = str(deepest_layer)

    def move(self):
        """
        Make the packet move on the screen.
        This is called every clock tick.
        Calculates its coordinates according to the `self.progress` attribute.
        :return: None
        """
        self.x, self.y = self.calculate_coordinates()
        super(PacketGraphics, self).move()

    def calculate_coordinates(self):
        """
        This method knows the start and end coordinates of the travel of the packet
        in the connection and it also knows the progress percent.
        It calculates (with a vector based calculation) the current coordinates of the packet
        on the screen.
        :return: None
        """
        start_x, start_y, end_x, end_y = self.connection_graphics.get_coordinates(self.direction)
        return ((((end_x - start_x) * self.progress) + start_x),
                (((end_y - start_y) * self.progress) + start_y))

    @staticmethod
    def image_from_packet(layer):
        """
        Returns an image name from the `layer` name it receives.
        The `layer` will usually be the most inner layer in a packet.
        :param layer: The `Protocol` instance that you wish to get an image for.
        :return: a string of the corresponding image's location.
        """

        PACKET_TYPE_TO_IMAGE = {
            "Ethernet": ETHERNET_IMAGE,
            "IP": IP_IMAGE,
            "ARP": {
                ARP_REQUEST: ARP_REQUEST_IMAGE,
                ARP_REPLY: ARP_REPLY_IMAGE,
                ARP_GRAT: ARP_GRAT_IMAGE,
            },
            "UDP": UDP_IMAGE,
            "DHCP": {
                DHCP_DISCOVER: DHCP_DISCOVER_IMAGE,
                DHCP_OFFER: DHCP_OFFER_IMAGE,
                DHCP_REQUEST: DHCP_REQUEST_IMAGE,
                DHCP_PACK: DHCP_PACK_IMAGE,
            },
            "ICMP": {
                ICMP_REQUEST: ICMP_REQUEST_IMAGE,
                ICMP_REPLY: ICMP_REPLY_IMAGE,
                ICMP_TIME_EXCEEDED: ICMP_TIME_EXCEEDED_IMAGE,
            },
        }

        if hasattr(layer, "opcode"):
            return PACKET_TYPE_TO_IMAGE[type(layer).__name__][layer.opcode]
        return PACKET_TYPE_TO_IMAGE[type(layer).__name__]

    def __repr__(self):
        return self.str
