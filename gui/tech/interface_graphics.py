from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Dict, Callable

from address.mac_address import MACAddress
from consts import *
from exceptions import *
from gui.abstracts.image_graphics import ImageGraphics
from gui.main_window import MainWindow
from gui.shape_drawing import draw_rectangle
from gui.user_interface.viewable_graphics_object import ViewableGraphicsObject
from usefuls.funcs import distance, with_args, get_the_one

if TYPE_CHECKING:
    from computing.internals.interface import Interface
    from gui.tech.computer_graphics import ComputerGraphics
    from gui.user_interface.user_interface import UserInterface


class InterfaceGraphics(ViewableGraphicsObject):
    """
    This is the graphics of a network interface of a computer.
    It is the little square next to computers.
    It allows the user much more control over their computers and to inspect the network interfaces of their computers.
    """
    def __init__(self,
                 x: float,
                 y: float,
                 interface: Interface,
                 computer_graphics: ComputerGraphics) -> None:
        """
        initiates the object.
        :param x:
        :param y: the location
        :param interface: the physical `Interface` of the computer.
        :param computer_graphics: the graphics object of the computer that this interface belongs to.
        """
        super(InterfaceGraphics, self).__init__(x, y, centered=True, is_in_background=True, is_pressable=True)
        self.color = interface.display_color
        self.real_x, self.real_y = x, y
        self.width, self.height = INTERFACES.WIDTH, INTERFACES.HEIGHT
        self.computer_graphics = computer_graphics

        self.interface = interface
        interface.graphics = self

    @property
    def computer_location(self) -> Tuple[float, float]:
        return self.computer_graphics.location

    def is_mouse_in(self) -> bool:
        """
        Returns whether or not the mouse is pressing the interface
        :return:
        """
        x, y = MainWindow.main_window.get_mouse_location()
        return self.real_x - (self.width / 2) < x < self.real_x + (self.width / 2) and \
               self.real_y - (self.height / 2) < y < self.real_y + (self.height / 2)

    def move(self) -> None:
        """
        Moves the interface.
        Keeps it within `INTERFACE_DISTANCE_FROM_COMPUTER` pixels away from the computer.
        :return:
        """
        if self.interface.is_connected():
            start_computer, end_comp = self.interface.connection.connection.graphics.computers
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
            "set MTU": with_args(
                user_interface.ask_user_for,
                int,
                "Insert new MTU:",
                self.interface.set_mtu,
            ),
            "sniffing start/stop (f)": with_args(
                get_the_one(user_interface.computers,
                            lambda c: self.interface in c.interfaces,
                            NoSuchInterfaceError).toggle_sniff,
                self.interface.name,
                is_promisc=True),
            "block (^b)": with_args(self.interface.toggle_block, "STP"),
        }

    def start_viewing(self,
                      user_interface: UserInterface,
                      additional_buttons: Optional[Dict[str, Callable[[], None]]] = None) -> Tuple[pyglet.sprite.Sprite, str, int]:
        """
        Starts the side-window-view of the interface.
        :param user_interface: a `UserInterface` object to register the buttons in.
        :param additional_buttons: more buttons
        """
        buttons = self._create_button_dict(user_interface)
        buttons.update(additional_buttons or {})
        self.buttons_id = user_interface.add_buttons(buttons)
        copied_sprite = ImageGraphics.get_image_sprite(os.path.join(DIRECTORIES.IMAGES, IMAGES.VIEW.INTERFACE))
        return copied_sprite, self.interface.generate_view_text(), self.buttons_id

    def mark_as_selected(self) -> None:
        """
        Marks a rectangle around a `GraphicsObject` that is selected.
        Only call this function if the object is selected.
        :return: None
        """
        x, y = self.x - (self.width / 2), self.y - (self.height / 2)
        draw_rectangle(
            x - SELECTED_OBJECT.PADDING,
            y - SELECTED_OBJECT.PADDING,
            self.width + (2 * SELECTED_OBJECT.PADDING),
            self.height + (2 * SELECTED_OBJECT.PADDING),
            outline_color=SELECTED_OBJECT.COLOR,
        )

    def __repr__(self) -> str:
        return f"Interface Graphics ({self.interface.name})"

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

    def delete(self, user_interface: UserInterface) -> None:
        """
        Delete the interface!
        """
        super(InterfaceGraphics, self).delete(user_interface)
        user_interface.remove_interface(self.interface)
