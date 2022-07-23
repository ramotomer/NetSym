from gui.tech.wireless_packet_graphics import WirelessPacketGraphics
from packets.packet import Packet


class WirelessPacket(Packet):
    """
    just like a regular packet but it is sent over a Frequency rather than a regular connection.
    """
    def __init__(self, data):
        super(WirelessPacket, self).__init__(data)

    def show(self, frequency_object, sending_interface):
        """
        Starts the display of the object. (Creating the graphics object)
        :param frequency_object:
        :param sending_interface:
        :return:
        """
        self.graphics = WirelessPacketGraphics(*sending_interface.graphics.location, self.deepest_layer(), frequency_object)
