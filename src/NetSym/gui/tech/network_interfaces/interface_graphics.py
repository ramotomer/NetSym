from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Dict, Callable

from NetSym.address.mac_address import MACAddress
from NetSym.consts import INTERFACES
from NetSym.exceptions import *
from NetSym.gui.shape_drawing import draw_rectangle
from NetSym.gui.tech.network_interfaces.base_interface_graphics import BaseInterfaceGraphics
from NetSym.usefuls.funcs import distance, with_args, get_the_one_with_raise

if TYPE_CHECKING:
    from NetSym.computing.internals.network_interfaces.interface import Interface
    from NetSym.gui.tech.computer_graphics import ComputerGraphics
    from NetSym.gui.user_interface.user_interface import UserInterface


class InterfaceGraphics(BaseInterfaceGraphics):
    """
    This is the graphics of a network interface of a computer.
    It is the little square next to computers.
    It allows the user much more control over their computers and to inspect the network interfaces of their computers.
    """
    interface: Interface

    def __init__(self,
                 x: Optional[float],
                 y: Optional[float],
                 interface: Interface,
                 computer_graphics: ComputerGraphics) -> None:
        """
        initiates the object.
        :param x:
        :param y: the location
        :param interface: the physical `Interface` of the computer.
        :param computer_graphics: the graphics object of the computer that this interface belongs to.
        """
        super(InterfaceGraphics, self).__init__(x, y, interface, computer_graphics)

    @property
    def logic_object(self) -> Interface:
        return self.interface

    def is_in(self, x: float, y: float) -> bool:
        """
        Returns whether or not the mouse is pressing the interface
        :return:
        """
        return self.real_x - (self.width / 2) < x < self.real_x + (self.width / 2) and \
               self.real_y - (self.height / 2) < y < self.real_y + (self.height / 2)

    def move(self) -> None:
        """
        Moves the interface.
        Keeps it within `INTERFACE_DISTANCE_FROM_COMPUTER` pixels away from the computer.
        :return:
        """
        if self.interface.is_connected():
            start_computer, end_comp = self.interface.connection.get_graphics().computers
            other_computer = start_computer if self.computer_graphics is end_comp else end_comp
            self.x, self.y = other_computer.location
        computer_x, computer_y = self.computer_location
        dist = distance((computer_x, computer_y), (self.x, self.y)) / self.computer_graphics.interface_distance()
        dist = dist if dist else 1  # cannot be 0

        self.real_x, self.real_y = ((self.x - computer_x) / dist) + computer_x, ((self.y - computer_y) / dist) + computer_y
        self.x, self.y = self.real_x, self.real_y
        # ^ keeps the interface in a fixed distance away from the computer despite being dragged.

    def draw(self) -> None:
        """
        Draw the interface.
        :return:
        """
        self.color = INTERFACES.BLOCKED_COLOR if self.interface.is_blocked else INTERFACES.COLOR
        draw_rectangle(
            self.real_x - (self.width/2), self.real_y - (self.height / 2),
            self.width, self.height,
            color=self.color,
        )

    def _create_button_dict(self, user_interface: UserInterface) -> Dict[str, Callable[[], None]]:
        """
        Creates the dict of the buttons that are displayed in the side window when this object is viewed.
        :param user_interface:
        :return:
        """
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
            "set MTU (alt+m)": with_args(
                user_interface.ask_user_for,
                int,
                "Insert new MTU:",
                self.interface.set_mtu,
            ),
            "sniffing start/stop (f)": with_args(
                get_the_one_with_raise(user_interface.computers,
                                       lambda c: self.interface in c.interfaces,
                                       NoSuchInterfaceError).toggle_sniff,
                self.interface.name,
                is_promisc=True),
            "block (^b)": with_args(self.interface.toggle_block, "STP"),
        }

    def dict_save(self) -> Dict:
        """
        Save the interface as a dict that can be later reconstructed to a new interface
        :return:
        """
        return {
            "class": "Interface",
            "location": (self.real_x, self.real_y),
            "name": self.interface.name,
            "mac": str(self.interface.mac),
            "ip": repr(self.interface.ip) if self.interface.ip is not None else None,
            "color": self.color,
            "is_blocked": self.interface.is_blocked,
            "type_": self.interface.type,
            "mtu": self.interface.mtu,
        }

    def __str__(self) -> str:
        return "InterfaceGraphics"

    def __repr__(self) -> str:
        return f"<< InterfaceGraphics of interface {self.interface.name!r} in computer {self.computer_graphics.computer.name!r} >>"
