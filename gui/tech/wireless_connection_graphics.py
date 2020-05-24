# from usefuls import sine_wave_coordinates
from consts import *
from gui.shape_drawing import draw_sine_wave
from gui.tech.connection_graphics import ConnectionGraphics


class WirelessConnectionGraphics(ConnectionGraphics):
    """
    # TODO: Doc here!
    """
    def __init__(self, *args):
        """

        """
        super(WirelessConnectionGraphics, self).__init__(*args)
        self.regular_color = WIRELESS_CONNECTION_COLOR if not self.connection.packet_loss else PL_CONNECTION_COLOR
        self.color = self.regular_color

    def draw(self):
        """"""
        draw_sine_wave(self.computers.start.location, self.computers.end.location, color=self.color)

    def __repr__(self):
        return "A Wireless connection graphics object"
