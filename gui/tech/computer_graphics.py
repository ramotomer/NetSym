from collections import namedtuple
from os import linesep

from address.ip_address import IPAddress
from computing.internals.processes.daytime_process import DAYTIMEClientProcess
from computing.internals.processes.ddos_process import DDOSProcess
from computing.internals.processes.ftp_process import FTPClientProcess
from consts import *
from gui.abstracts.image_graphics import ImageGraphics
from gui.main_window import MainWindow
from gui.tech.interface_graphics import InterfaceGraphicsList
from gui.tech.output_console import OutputConsole
from gui.tech.process_graphics import ProcessGraphicsList
from gui.user_interface.popup_windows.popup_console import PopupConsole
from gui.user_interface.text_graphics import Text
from usefuls.funcs import with_args

ChildGraphicsObjects = namedtuple("ChildGraphicsObjects", [
    "text",
    "console",
    "process_list",
    "interface_list",
])


class ComputerGraphics(ImageGraphics):
    """
    This is the class which is the graphics of the computer.
    It inherits from `ImageGraphics` because there is an image of the computer that should just be drawn.
    This class adds to it the text that exists under a computer.
    """
    def __init__(self, x, y, computer, image=IMAGES.COMPUTERS.COMPUTER, scale_factor=IMAGES.SCALE_FACTORS.SPRITES):
        """
        The graphics objects of computers.
        :param x:
        :param y: the coordinates of the computer.
        :param computer: The computer object itself.
        :param image: the name of the image of the computer. (can be changed for different types of computers)
        """
        super(ComputerGraphics, self).__init__(
            os.path.join(DIRECTORIES.IMAGES, image),
            x, y,
            centered=True,
            is_in_background=True,
            is_pressable=True,
            scale_factor=scale_factor,
        )
        self.is_computer = True
        self.computer = computer
        self.class_name = self.computer.__class__.__name__

        self.child_graphics_objects = ChildGraphicsObjects(
            Text(self.generate_text(), self.x, self.y, self),
            OutputConsole(*self.console_location),
            ProcessGraphicsList(self),
            InterfaceGraphicsList(self),
        )

        self.buttons_id = None

    @property
    def console_location(self):
        return MainWindow.main_window.width - (WINDOWS.SIDE.WIDTH / 2) - (CONSOLE.WIDTH / 2), CONSOLE.Y

    def generate_text(self):
        """
        Generates the text under the computer.
        :return: a string with the information that should be displayed there.
        """
        return '\n'.join([self.computer.name] + [str(interface.ip) for interface in self.computer.interfaces if interface.has_ip()])

    def update_text(self):
        """Sometimes the ip_layer of the computer is changed and we want to text to change as well"""
        self.child_graphics_objects.text.set_text(self.generate_text())

    def update_image(self):
        """
        Updates the image according to the current computer state
        :return:
        """
        self.image_name = os.path.join(DIRECTORIES.IMAGES, IMAGES.COMPUTERS.SERVER if self.computer.open_tcp_ports else IMAGES.COMPUTERS.COMPUTER)
        self.load()
        self.child_graphics_objects.process_list.clear()
        for port in self.computer.open_tcp_ports:
            self.child_graphics_objects.process_list.add(port)

    def start_viewing(self, user_interface):
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
                with_args(user_interface.add_delete_interface, self)
            ),
            "open/close port (shift+o)": with_args(
                user_interface.ask_user_for,
                int,
                MESSAGES.INSERT.PORT_NUMBER,
                self.computer.open_tcp_port
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
                with_args(self.computer.start_process, DAYTIMEClientProcess)
            ),
            "download file (alt+a)": with_args(
                user_interface.ask_user_for,
                IPAddress,
                MESSAGES.INSERT.IP_FOR_PROCESS,
                with_args(self.computer.start_process, FTPClientProcess)
            ),
            "start DDOS process (ctrl+w)": with_args(
                self.computer.start_process,
                DDOSProcess,
                1000,
                0.8
            ),
            "open console (shift+i)": with_args(
                self._open_shell,
                user_interface,
            ),
        }
        self.buttons_id = user_interface.add_buttons(buttons)
        return self.copy_sprite(self.sprite), self.generate_view_text(), self.buttons_id

    def end_viewing(self, user_interface):
        """Ends the viewing of the object in the side window"""
        user_interface.remove_buttons(self.buttons_id)
        self.child_graphics_objects.console.hide()

    def _open_shell(self, user_interface):
        """
        Opens a shell window on the computer
        :return:
        """
        if self.computer.is_powered_on:
            PopupConsole(user_interface, self.computer)

    def generate_view_text(self):
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

    def add_interface(self, interface):
        """
        Adds an interface to the viewed interfaces.
        :param interface: `Interface`
        :return:
        """
        self.child_graphics_objects.interface_list.add(interface)

    def interface_distance(self):
        """
        Calculates the distance that the interface should be away from the computer.
        :return:
        """
        return (IMAGES.SIZE * self.sprite.scale_x) - INTERFACES.COMPUTER_DISTANCE

    def __str__(self):
        return "ComputerGraphics"

    def __repr__(self):
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
