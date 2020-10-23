from pyautogui import size as screen_size

from address.mac_address import MACAddress
from exceptions import NoSuchInterfaceError
from gui.shape_drawing import draw_circle
from gui.tech.interface_graphics import InterfaceGraphics
from usefuls.funcs import with_args, get_the_one, distance


class WirelessInterfaceGraphics(InterfaceGraphics):
    """
    The graphics object of a wireless interface.
    """
    def __init__(self, x, y, interface, computer_graphics):
        super(WirelessInterfaceGraphics, self).__init__(x, y, interface, computer_graphics)

    def draw(self):
        """
        Draw the interface.
        :return:
        """
        if self.interface.is_connected():
            self.color = self.interface.frequency_object.color

        draw_circle(
            self.real_x, self.real_y,
            self.width,
            outline_color=self.color,
            fill_color=self.color,
        )

    def move(self):
        """
        Moves the interface.
        Keeps it within `INTERFACE_DISTANCE_FROM_COMPUTER` pixels away from the computer.
        :return:
        """
        computer_x, computer_y = self.computer_location

        if self.interface.is_connected():
            self.x, self.y = computer_x, screen_size()[1]

        dist = distance((computer_x, computer_y), (self.x, self.y)) / self.computer_graphics.interface_distance()
        dist = dist if dist else 1  # cannot be 0
        self.real_x, self.real_y = ((self.x - computer_x) / dist) + computer_x, ((self.y - computer_y) / dist) + computer_y
        self.x, self.y = self.real_x, self.real_y
        # ^ keeps the interface in a fixed distance away from the computer despite being dragged.

    def _create_button_dict(self, user_interface):
        return {
            "config IP (i)": user_interface.ask_user_for_ip,
            "change MAC (^m)": with_args(
                user_interface.ask_user_for,
                MACAddress,
                "Insert a new mac address:",
                self.interface.set_mac,
            ),
            "change name (shift+n)": with_args(
                user_interface.ask_user_for,
                str,
                "Insert new name:",
                self.interface.set_name,
            ),
            "sniffing start/stop (f)": with_args(
                get_the_one(user_interface.computers,
                            lambda c: self.interface in c.interfaces,
                            NoSuchInterfaceError).toggle_sniff,
                self.interface.name,
                is_promisc=True),
            "block (^b)": with_args(self.interface.toggle_block, "STP"),
            "set frequency (alt+f)": with_args(
                user_interface.ask_user_for,
                float,
                "Insert frequency:",
                self.interface.connect
            )
        }
