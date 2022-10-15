from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Callable

from NetSym.address.mac_address import MACAddress
from NetSym.consts import INTERFACES
from NetSym.exceptions import NoSuchInterfaceError
from NetSym.gui.main_window import MainWindow
from NetSym.gui.shape_drawing import draw_circle
from NetSym.gui.tech.interface_graphics import InterfaceGraphics
from NetSym.usefuls.funcs import with_args, get_the_one, distance

if TYPE_CHECKING:
    from NetSym.computing.internals.interface import Interface
    from NetSym.gui.tech.computer_graphics import ComputerGraphics


class WirelessInterfaceGraphics(InterfaceGraphics):
    """
    The graphics object of a wireless interface.
    """
    def __init__(self,
                 x: float, y: float,
                 interface: Interface,
                 computer_graphics: ComputerGraphics) -> None:
        super(WirelessInterfaceGraphics, self).__init__(x, y, interface, computer_graphics)
        self.width = INTERFACES.WIDTH / 2

    @property
    def radius(self) -> float:
        return self.width

    def draw(self) -> None:
        """
        Draw the interface.
        :return:
        """
        if self.interface.is_connected():
            self.color = self.interface.frequency_object.color

        draw_circle(
            self.real_x, self.real_y,
            self.radius,
            outline_color=self.color,
            fill_color=self.color,
        )

    def move(self) -> None:
        """
        Moves the interface.
        Keeps it within `INTERFACE_DISTANCE_FROM_COMPUTER` pixels away from the computer.
        :return:
        """
        computer_x, computer_y = self.computer_location

        if self.interface.is_connected():
            self.x, self.y = computer_x, computer_y + self.computer_graphics.interface_distance()
            self.real_x, self.real_y = self.x, self.y

        else:
            dist = distance((computer_x, computer_y), (self.x, self.y)) / self.computer_graphics.interface_distance()
            dist = dist if dist else 1  # cannot be 0
            self.real_x, self.real_y = ((self.x - computer_x) / dist) + computer_x, ((self.y - computer_y) / dist) + computer_y
            self.x, self.y = self.real_x, self.real_y
            # ^ keeps the interface in a fixed distance away from the computer despite being dragged.

    def is_mouse_in(self) -> bool:
        """
        Returns whether or not the mouse is pressing the interface
        :return:
        """
        return distance(MainWindow.main_window.get_mouse_location(), (self.real_x, self.real_y)) < self.radius

    def _create_button_dict(self, user_interface) -> Dict[str, Callable[[], None]]:
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

    def dict_save(self) -> Dict:
        """
        Save the interface as a dict that can be later reconstructed to a new interface
        :return:
        """
        return {
            "class": "WirelessInterface",
            "location": (self.real_x, self.real_y),
            "name": self.interface.name,
            "mac": str(self.interface.mac),
            "ip": repr(self.interface.ip) if self.interface.ip is not None else None,
            "color": self.color,
            "is_blocked": self.interface.is_blocked,
            "type_": self.interface.type,
            "frequency": self.interface.frequency,
        }
