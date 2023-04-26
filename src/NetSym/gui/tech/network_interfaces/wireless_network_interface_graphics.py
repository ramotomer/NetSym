from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Callable, Optional

from NetSym.address.mac_address import MACAddress
from NetSym.consts import INTERFACES, COLORS
from NetSym.exceptions import NoSuchInterfaceError
from NetSym.gui.shape_drawing import draw_circle
from NetSym.gui.tech.network_interfaces.network_interface_graphics import NetworkInterfaceGraphics
from NetSym.usefuls.funcs import with_args, distance, get_the_one_with_raise

if TYPE_CHECKING:
    from NetSym.computing.internals.network_interfaces.wireless_network_interface import WirelessNetworkInterface
    from NetSym.gui.tech.computer_graphics import ComputerGraphics


class WirelessNetworkInterfaceGraphics(NetworkInterfaceGraphics):
    """
    The graphics object of a wireless interface.
    """
    interface: WirelessNetworkInterface

    def __init__(self,
                 x: Optional[float], y: Optional[float],
                 interface: WirelessNetworkInterface,
                 computer_graphics: ComputerGraphics) -> None:
        super(WirelessNetworkInterfaceGraphics, self).__init__(x, y, interface, computer_graphics)
        self.width = INTERFACES.WIDTH / 2

    @property
    def radius(self) -> float:
        return self.width

    def draw(self) -> None:
        """
        Draw the interface.
        :return:
        """
        self.color = self.interface.connection.color if self.interface.is_connected() else COLORS.BLACK

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

    def is_in(self, x: float, y: float) -> bool:
        """
        Returns whether or not the mouse is pressing the interface
        :return:
        """
        return distance((x, y), (self.real_x, self.real_y)) < self.radius

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
                get_the_one_with_raise(user_interface.computers,
                                       lambda c: self.interface in c.interfaces,
                                       NoSuchInterfaceError).toggle_sniff,
                self.interface.name,
                is_promisc=True),
            "block (^b)": with_args(self.interface.toggle_block, "STP"),
            "set frequency (alt+f)": with_args(
                user_interface.ask_user_for,
                float,
                "Insert frequency:",
                with_args(user_interface.set_interface_frequency, self.interface),
            )
        }

    def dict_save(self) -> Dict:
        """
        Save the interface as a dict that can be later reconstructed to a new interface
        :return:
        """
        return {
            "class": "WirelessNetworkInterface",
            "location": (self.real_x, self.real_y),
            "name": self.interface.name,
            "mac": str(self.interface.mac),
            "ip": repr(self.interface.ip) if self.interface.ip is not None else None,
            "color": self.color,
            "is_blocked": self.interface.is_blocked,
            "type_": self.interface.type,
            "frequency": self.interface.frequency,
        }
