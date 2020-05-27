# from usefuls import sine_wave_coordinates
from consts import *
from gui.abstracts.image_graphics import ImageGraphics
from gui.shape_drawing import draw_sine_wave
from gui.tech.connection_graphics import ConnectionGraphics
from usefuls import sine_wave_coordinates


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

        self.amplitude = DEFAULT_SINE_WAVE_AMPLITUDE
        self.frequency = DEFAULT_SINE_WAVE_FREQUENCY

        self.coordinates = None
        self.previous_coordinates = None

    def packet_location(self, direction, progress):
        """
        Returns the location of the packet in the connection based of its direction and its progress in it
        This method knows the start and end coordinates of the travel of the packet
        in the connection and it also knows the progress percent.
        It calculates (with a vector based calculation) the current coordinates of the packet
        on the screen.

        :param direction: the direction the packet is going in the connection.
        :param progress: the progress of the packet through the connection.
        :return: returns coordinates of the packet according to that
        """
        sx, sy, ex, ey = self.get_computer_coordinates()
        if self.previous_coordinates != (sx, sy, ex, ey):
            self.coordinates = list(sine_wave_coordinates(
                (sx, sy),
                (ex, ey),
                amplitude=self.amplitude,
                frequency=self.frequency,
            ))

        sign = 1 if direction is PACKET_GOING_RIGHT else -1

        return self.coordinates[sign * int(len(self.coordinates) * progress)]
        
    def start_viewing(self, user_interface):
        """
        
        :param user_interface: 
        :return: 
        """
        _, text, buttons_id = super(WirelessConnectionGraphics, self).start_viewing(user_interface)
        return ImageGraphics.get_image_sprite(IMAGES.format(WIRELESS_CONNECTION_VIEW_IMAGE)), text, buttons_id

    def generate_view_text(self):
        """

        :return:
        """
        return f"\nWireless {super(WirelessConnectionGraphics, self).generate_view_text()[1:]}"

    def draw(self):
        """
        # TODO: doc here!
        :return: 
        """
        color = self.color if not self.is_mouse_in() else SELECTED_CONNECTION_COLOR
        draw_sine_wave(self.computers.start.location,
                       self.computers.end.location,
                       amplitude=self.amplitude,
                       frequency=self.frequency,
                       color=color)

    def __repr__(self):
        return "A Wireless connection graphics object"
