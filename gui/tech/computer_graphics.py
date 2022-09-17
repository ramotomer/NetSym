from __future__ import annotations

from os import linesep
from typing import TYPE_CHECKING, Tuple

from recordclass import recordclass

from address.ip_address import IPAddress
from computing.internals.processes.usermode_processes.daytime_process import DAYTIMEClientProcess
from computing.internals.processes.usermode_processes.ddos_process import DDOSProcess
from computing.internals.processes.usermode_processes.ftp_process import ClientFTPProcess
from consts import *
from gui.abstracts.image_graphics import ImageGraphics
from gui.main_window import MainWindow
from gui.tech.interface_graphics_list import InterfaceGraphicsList
from gui.tech.output_console import OutputConsole
from gui.tech.process_graphics import ProcessGraphicsList
from gui.user_interface.popup_windows.popup_console import PopupConsole
from gui.user_interface.popup_windows.popup_error import PopupError
from gui.user_interface.text_graphics import Text
from usefuls.funcs import with_args

if TYPE_CHECKING:
    from computing.internals.interface import Interface
    from computing.computer import Computer
    from gui.user_interface.user_interface import UserInterface


ChildGraphicsObjects = recordclass("ChildGraphicsObjects", [
    "text",
    "console",
    "process_list",
    "interface_list",
    "loopback",
])


class ComputerGraphics(ImageGraphics):
    """
    This is the class which is the graphics of the computer.
    It inherits from `ImageGraphics` because there is an image of the computer that should just be drawn.
    This class adds to it the text that exists under a computer.
    """
    def __init__(self,
                 x: float,
                 y: float,
                 computer: Computer,
                 image: str = IMAGES.COMPUTERS.COMPUTER,
                 scale_factor: float = IMAGES.SCALE_FACTORS.SPRITES) -> None:
        """
        The graphics objects of computers.
        :param x:
        :param y: the coordinates of the computer.
        :param computer: The computer object itself.
        :param image: the name of the image of the computer. (can be changed for different types of computers)
        """
        super(ComputerGraphics, self).__init__(
            image,
            x, y,
            centered=True,
            is_in_background=True,
            is_pressable=True,
            scale_factor=scale_factor,
        )
        self.computer = computer
        self.class_name = self.computer.__class__.__name__
        self.original_image = image

        self.child_graphics_objects = ChildGraphicsObjects(
            Text(self.generate_text(), self.x, self.y, self),
            OutputConsole(*self.console_location),
            ProcessGraphicsList(self),
            InterfaceGraphicsList(self),
            None,                        # This is the loopback graphics. It will be set once the LoopbackGraphicsObject is initiated
        )

        self.buttons_id = None

        self.sprite.update(scale_x=self.computer.initial_size[0], scale_y=self.computer.initial_size[1])
        self.update_text_location()

    @property
    def console_location(self) -> Tuple[float, float]:
        return MainWindow.main_window.width - (WINDOWS.SIDE.WIDTH / 2) - (CONSOLE.WIDTH / 2), CONSOLE.Y

    @property
    def should_be_transparent(self) -> bool:
        return not self.computer.is_powered_on

    def draw(self) -> None:
        self.update_image()
        super(ComputerGraphics, self).draw()

    def generate_text(self) -> str:
        """
        Generates the text under the computer.
        :return: a string with the information that should be displayed there.
        """
        return '\n'.join([self.computer.name] + [str(interface.ip) for interface in self.computer.interfaces if interface.has_ip()])

    def update_text(self) -> None:
        """Sometimes the ip_layer of the computer is changed and we want to text to change as well"""
        self.child_graphics_objects.text.set_text(self.generate_text())

    def _is_server(self) -> bool:
        """
        :return: Whether or not the computer should be displayed as a server - by the ports that are open on it
        """
        return bool(set(self.computer.get_open_ports()) & set(PORTS.SERVER_PORTS))

    def update_image(self) -> None:
        """
        Refreshes the image according to the current computer state
        """
        self.change_image(IMAGES.COMPUTERS.SERVER if self._is_server() else self.original_image)
        self.child_graphics_objects.process_list.set_list([port for port in self.computer.get_open_ports() if port in PORTS.SERVER_PORTS])

    def start_viewing(self, user_interface: UserInterface) -> Tuple[pyglet.sprite.Sprite, str, int]:
        """
        Starts viewing the computer graphics object in the side-window view.
        :param user_interface: the `UserInterface` object we can use the methods of it.
        :return: a tuple <display sprite>, <display text>, <new button count>
        """
        self.child_graphics_objects.console.location = self.console_location
        self.child_graphics_objects.console.show()

        buttons = {
            "set ip (i)": user_interface.ask_user_for_ip,
            "change name (shift+n)": with_args(
                user_interface.ask_user_for,
                str,
                MESSAGES.INSERT.COMPUTER_NAME,
                self.computer.set_name,
            ),
            "power on/off (o)": self.computer.power,
            "add/delete interface (^i)": with_args(
                user_interface.ask_user_for,
                str,
                MESSAGES.INSERT.INTERFACE_INFO,
                with_args(user_interface.add_delete_interface, self),
            ),
            "add/delete wireless interface (alt+w)": with_args(
                user_interface.ask_user_for,
                str,
                MESSAGES.INSERT.INTERFACE_INFO,
                with_args(user_interface.add_delete_interface, self, type_=INTERFACES.TYPE.WIFI),
            ),
            "open/close TCP port (shift+o)": with_args(
                user_interface.ask_user_for,
                int,
                MESSAGES.INSERT.PORT_NUMBER,
                self.computer.open_port,
            ),
            "open/close UDP port (shift+u)": with_args(
                user_interface.ask_user_for,
                int,
                MESSAGES.INSERT.PORT_NUMBER,
                with_args(self.computer.open_port, protocol="UDP"),
            ),
            "set default gateway (g)": with_args(
                user_interface.ask_user_for,
                IPAddress,
                MESSAGES.INSERT.GATEWAY,
                self.computer.set_default_gateway
            ),
            "ask daytime (ctrl+alt+a)": with_args(
                user_interface.ask_user_for,
                IPAddress,
                MESSAGES.INSERT.IP_FOR_PROCESS,
                with_args(self.computer.process_scheduler.start_usermode_process, DAYTIMEClientProcess)
            ),
            "download file (alt+a)": with_args(
                user_interface.ask_user_for,
                IPAddress,
                MESSAGES.INSERT.IP_FOR_PROCESS,
                with_args(self.computer.process_scheduler.start_usermode_process, ClientFTPProcess)
            ),
            "start DDOS process (ctrl+w)": with_args(
                self.computer.process_scheduler.start_usermode_process,
                DDOSProcess,
                100,
                0.05
            ),
            "open console (shift+i)": with_args(
                self._open_shell,
                user_interface,
            ),
            "color (ctrl+alt+c)": with_args(
                user_interface.ask_user_for,
                str,
                MESSAGES.INSERT.COLOR,
                self.color_by_name,
            ),
        }
        self.buttons_id = user_interface.add_buttons(buttons)
        return self.copy_sprite(self.sprite), self.generate_view_text(), self.buttons_id

    def end_viewing(self, user_interface: UserInterface) -> None:
        """Ends the viewing of the object in the side window"""
        user_interface.remove_buttons(self.buttons_id)
        self.child_graphics_objects.console.hide()

    def _open_shell(self, user_interface: UserInterface) -> None:
        """
        Opens a shell window on the computer
        :return:
        """
        if not self.computer.is_powered_on:
            PopupError(f"{self.computer.name} is turned off! \nCannot open console", user_interface)
            return
        PopupConsole(user_interface, self.computer)

    def generate_view_text(self) -> str:
        """
        Generates the text that will be shown in the side window when this computer is pressed.
        :return: a long string.
        """
        gateway = self.computer.routing_table.default_gateway.ip_address
        addresses = linesep.join(str(interface.ip) for interface in self.computer.interfaces if interface.has_ip())

        return f"""
Computer:

Name: {self.computer.name}
{f'os: {self.computer.os}' if self.computer.os is not None else ""}
{f'gateway: {gateway}' if gateway is not None else ""}
{f'addresses: {linesep + addresses}' if addresses else ""}
"""

    def add_interface(self, interface: Interface) -> None:
        """
        Adds an interface to the viewed interfaces.
        """
        self.child_graphics_objects.interface_list.add(interface)

    def interface_distance(self) -> float:
        """
        Calculates the distance that the interface should be away from the computer.
        :return:
        """
        return min(self.width, self.height) * INTERFACES.COMPUTER_DISTANCE_RATIO

    def update_text_location(self) -> None:
        """
        updates the location of the text (the padding) according to the size of the computer
        :return:
        """
        self.child_graphics_objects.text.padding = 0, (-self.height / 2) + TEXT.DEFAULT_Y_PADDING

    def resize(self, width_diff: float, height_diff: float, constrain_proportions: bool = False) -> None:
        super(ComputerGraphics, self).resize(width_diff, height_diff, constrain_proportions)
        self.update_text_location()

    def __str__(self) -> str:
        return f"ComputerGraphics ({self.computer.name})"

    def __repr__(self) -> str:
        return f"ComputerGraphics of computer '{self.computer}'"

    def dict_save(self):
        """
        Save the computer object with all of its attributes to tex
        :return: str
        """
        dict_ = {
            "class": self.class_name,
            "location": self.location,
            "name": self.computer.name,
            "size": [self.sprite.scale_x, self.sprite.scale_y],
            "os": self.computer.os,
            "interfaces": [interface.graphics.dict_save() for interface in self.computer.interfaces],
            "open_tcp_ports": self.computer.open_tcp_ports,
            "open_udp_ports": self.computer.open_udp_ports,
            "routing_table": self.computer.routing_table.dict_save(),
            "filesystem": self.computer.filesystem.dict_save(),
        }

        if self.class_name == "Router":
            dict_["is_dhcp_server"] = self.computer.is_dhcp_server

        return dict_

    def delete(self, user_interface: UserInterface) -> None:
        """
        Delete the computer graphics object
        """
        super(ComputerGraphics, self).delete(user_interface)
        user_interface.remove_computer(self.computer)
        user_interface.delete_connections_to(self.computer)
