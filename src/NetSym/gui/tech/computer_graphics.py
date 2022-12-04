from __future__ import annotations

from dataclasses import dataclass
from os import linesep
from typing import TYPE_CHECKING, Optional, Dict, Callable, Iterable, Tuple, List

import pyglet

from NetSym.address.ip_address import IPAddress
from NetSym.computing.internals.processes.usermode_processes.daytime_process.daytime_client_process import DAYTIMEClientProcess
from NetSym.computing.internals.processes.usermode_processes.ddos_process import DDOSProcess
from NetSym.computing.internals.processes.usermode_processes.dhcp_process.dhcp_server_process import DHCPServerProcess
from NetSym.computing.internals.processes.usermode_processes.dns_process.dns_server_process import DNSServerProcess
from NetSym.computing.internals.processes.usermode_processes.ftp_process.ftp_client_process import ClientFTPProcess
from NetSym.consts import IMAGES, MESSAGES, INTERFACES, TEXT, PORTS
from NetSym.gui.abstracts.image_graphics import ImageGraphics
from NetSym.gui.tech.loopback_connection_graphics import LoopbackConnectionGraphics
from NetSym.gui.tech.output_console import OutputConsole
from NetSym.gui.tech.process_graphics import ProcessGraphicsList
from NetSym.gui.user_interface.popup_windows.popup_console import PopupConsole
from NetSym.gui.user_interface.popup_windows.popup_error import PopupError
from NetSym.gui.user_interface.text_graphics import Text
from NetSym.usefuls.funcs import with_args

if TYPE_CHECKING:
    from NetSym.gui.tech.network_interfaces.network_interface_graphics import NetworkInterfaceGraphics
    from NetSym.computing.computer import Computer
    from NetSym.gui.user_interface.user_interface import UserInterface


@dataclass
class ChildGraphicsObjects:
    text: Text
    console: OutputConsole
    process_list: ProcessGraphicsList
    interface_list: List[NetworkInterfaceGraphics]
    loopback: Optional[LoopbackConnectionGraphics] = None

    def __iter__(self) -> Iterable:
        return iter((
            self.text,
            self.console,
            self.process_list,
            self.interface_list,
            self.loopback,
        ))


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
                 image: Optional[str] = None,
                 scale_factor: float = IMAGES.SCALE_FACTORS.SPRITES,
                 console_location: Tuple[float, float] = (0, 0),
                 ) -> None:
        """
        The graphics objects of computers.
        :param x:
        :param y: the coordinates of the computer.
        :param computer: The computer object itself.
        :param image: the name of the image of the computer. (can be changed for different types of computers)
        """
        self.original_image = image if image is not None else IMAGES.COMPUTERS.CLASS_NAME_TO_IMAGE[computer.__class__.__name__]

        super(ComputerGraphics, self).__init__(
            self.original_image,
            x, y,
            centered=        True,
            is_in_background=True,
            is_pressable=    True,
            scale_factor=    scale_factor,
        )
        self.computer: Computer = computer
        self.class_name = self.computer.__class__.__name__

        interface_list = [interface.init_graphics(self) for interface in self.computer.interfaces]

        self.child_graphics_objects = ChildGraphicsObjects(
            Text(self.generate_text(), self.x, self.y, self),
            OutputConsole(*console_location),
            ProcessGraphicsList(self),
            interface_list,
        )

        # debugp(f"Creating computer: {computer.name + ',':<15}scale: {self.scale_factor}")
        # self._set_size(*self.computer.initial_size)
        # self.rescale(self.scale_factor, self.scale_factor, constrain_proportions=True)
        # TODO: make files keep track of the size of computers!!!

        self.update_text_location()

    @property
    def logic_object(self):
        return self.computer

    @property
    def should_be_transparent(self) -> bool:
        return not self.computer.is_powered_on

    def get_image_path(self) -> str:
        """
        Return the path to the image that should be displayed when the computer is drawn
        """
        return IMAGES.COMPUTERS.SERVER if self._is_server() else self.original_image

    def draw(self) -> None:
        self.update_image()
        self.update_text()
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
        self.change_image(self.get_image_path())
        self.child_graphics_objects.process_list.set_list([port for port in self.computer.get_open_ports() if port in PORTS.SERVER_PORTS])

    def _get_per_process_buttons(self, user_interface: UserInterface) -> Dict[str, Callable[[], None]]:
        """
        Some buttons are only relevant if a certain process is running on the computer
        This method returns the additional buttons that should be added based on what processes
            are currently running
        """
        process_button_mapping = {
            DNSServerProcess: {
                "add DNS record (alt+d)": with_args(
                    user_interface.ask_user_for,
                    str,
                    "Enter the DNS mapping - full hostname and IP address, separated by a space:",
                    self.computer.add_dns_entry
                ),
                "add/remove DNS zone (z)": with_args(
                    user_interface.ask_user_for,
                    str,
                    "Enter the name of your DNS zone:",
                    self.computer.add_remove_dns_zone,
                ),
            },
            DHCPServerProcess: {
                "set DNS server (alt+d)": with_args(
                    user_interface.ask_user_for,
                    IPAddress,
                    MESSAGES.INSERT.DNS_SERVER_FOR_DHCP_SERVER,
                    self.computer.set_dns_server_for_dhcp_server,
                ),
                "set domain (shift+alt+d)": with_args(
                    user_interface.ask_user_for,
                    str,
                    MESSAGES.INSERT.DOMAIN_FOR_DHCP_SERVER,
                    self.computer.set_domain_for_dhcp_server,
                ),
            },
        }
        all_buttons = {}
        for process_type, button_dict in process_button_mapping.items():
            if self.computer.process_scheduler.is_process_running_by_type(process_type):
                all_buttons.update(button_dict)
        return all_buttons

    def start_viewing(self,
                      user_interface: UserInterface,
                      additional_buttons: Optional[Dict[str, Callable[[], None]]] = None) -> Tuple[pyglet.sprite.Sprite, str, int]:
        """
        Starts viewing the computer graphics object in the side-window view.

        parameter user_interface: the `UserInterface` object we can use the methods of it.
        Returns a tuple <display sprite>, <display text>, <new button count>
        """
        self.child_graphics_objects.console.location = user_interface.get_computer_output_console_location()
        self.child_graphics_objects.console.show()

        buttons: Dict[str,  Callable[[], None]] = {
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
                with_args(user_interface.add_delete_interface, self, interface_type=INTERFACES.TYPE.WIFI),
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
                str,
                MESSAGES.INSERT.IP_FOR_PROCESS,
                with_args(self.computer.process_scheduler.start_usermode_process, DAYTIMEClientProcess)
            ),
            "download file (alt+a)": with_args(
                user_interface.ask_user_for,
                str,
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
        buttons.update(additional_buttons or {})
        buttons.update(self._get_per_process_buttons(user_interface))
        self.buttons_id = user_interface.add_buttons(buttons)
        return self.copy_sprite(self.sprite), self.generate_view_text(), self.buttons_id

    def end_viewing(self, user_interface: UserInterface) -> None:
        """Ends the viewing of the object in the side window"""
        super(ComputerGraphics, self).end_viewing(user_interface)
        self.child_graphics_objects.console.hide()

    def _open_shell(self, user_interface: UserInterface) -> None:
        """
        Opens a shell window on the computer
        :return:
        """
        if not self.computer.is_powered_on:
            user_interface.register_window(PopupError(f"{self.computer.name} is turned off! \nCannot open console"))
            return
        user_interface.register_window(PopupConsole(self.computer))

    def generate_view_text(self) -> str:
        """
        Generates the text that will be shown in the side window when this computer is pressed.
        :return: a long string.
        """
        gateway = self.computer.routing_table.default_gateway
        addresses = linesep.join(str(interface.ip) for interface in self.computer.interfaces if interface.has_ip())

        return f"""
[## Computer ##]
'{self.computer.name}'

{f'Operation System: {self.computer.os}' if self.computer.os is not None else ""}
{f'Gateway: {gateway.ip_address}' if gateway is not None else ""}
{f'DNS server: {self.computer.dns_server}' if self.computer.dns_server is not None else ""}
{f'IP Addresses: {linesep + addresses}' if addresses else ""}
"""

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

    def dict_save(self) -> Dict:
        """
        Save the computer object with all of its attributes to tex
        :return: str
        """
        dict_ = {
            "class": self.class_name,
            "location": self.location,
            "name": self.computer.name,
            "scale_factor": self.scale_factor,
            "os": self.computer.os,
            "interfaces": [interface.graphics.dict_save() for interface in self.computer.interfaces],
            "open_tcp_ports": self.computer.get_open_ports("TCP"),
            "open_udp_ports": self.computer.get_open_ports("UDP"),
            "routing_table": self.computer.routing_table.dict_save(),
            "filesystem": self.computer.filesystem.dict_save(),
        }

        if self.class_name == "Router":
            dict_["is_dhcp_server"] = self.computer.process_scheduler.is_usermode_process_running(DHCPServerProcess)

        return dict_

    def delete(self, user_interface: UserInterface) -> None:
        """
        Delete the computer graphics object
        """
        super(ComputerGraphics, self).delete(user_interface)
        user_interface.remove_computer(self.computer)
        user_interface.delete_connections_to(self.computer)

    def __str__(self) -> str:
        return f"ComputerGraphics"

    def __repr__(self) -> str:
        return f"<< ComputerGraphics of computer '{self.computer}' >>"
