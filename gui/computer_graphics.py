from collections import namedtuple
from os import linesep

from address.ip_address import IPAddress
from consts import *
from gui.console import Console
from gui.image_graphics import ImageGraphics
from gui.process_graphics import ProcessGraphicsList
from gui.text_graphics import Text
from processes.daytime_process import DAYTIMEClientProcess
from processes.ftp_process import FTPClientProcess
from usefuls import with_args

ChildGraphicsObjects = namedtuple("ChildGraphicsObjects", "text console process_list")


class ComputerGraphics(ImageGraphics):
    """
    This is the class which is the graphics of the computer.
    It inherits from `ImageGraphics` because there is an image of the computer that should just be drawn.
    This class adds to it the text that exists under a computer.
    """
    def __init__(self, x, y, computer, image=COMPUTER_IMAGE):
        """
        The graphics objects of computers.
        :param x:
        :param y: the coordinates of the computer.
        :param computer: The computer object itself.
        :param image: the name of the image of the computer. (can be changed for different types of computers)
        """
        super(ComputerGraphics, self).__init__(IMAGES.format(image), x, y, centered=True, is_in_background=True)
        self.is_computer = True
        self.is_pressable = True
        self.computer = computer
        self.child_graphics_objects = ChildGraphicsObjects(
            Text(self.generate_text(), self.x, self.y, self),
            Console(CONSOLE_X, CONSOLE_Y),
            ProcessGraphicsList(self),
        )

    def generate_text(self):
        """
        Generates the text under the computer.
        :return: a string with the information that should be displayed there.
        """
        return '\n'.join([self.computer.name] + [str(interface.ip) for interface in self.computer.interfaces if interface.has_ip()])

    def update_text(self):
        """Sometimes the data of the computer is changed and we want to text to change as well"""
        self.child_graphics_objects.text.set_text(self.generate_text())

    def update_image(self):
        """
        Updates the image according to the current computer state
        :return:
        """
        self.image_name = IMAGES.format(SERVER_IMAGE if self.computer.open_ports else COMPUTER_IMAGE)
        self.load()
        self.child_graphics_objects.process_list.clear()
        for port in self.computer.open_ports:
            self.child_graphics_objects.process_list.add(port)

    def start_viewing(self, user_interface):
        """
        Starts viewing the computer graphics object in the side-window view.
        :param user_interface: the `UserInterface` object we can use the methods of it.
        :return: a tuple <display sprite>, <display text>, <new button count>
        """
        buttons = {
            "power on/off (o)": user_interface.power_selected_computer,
            "config IP (i)": with_args(user_interface.ask_user_for, str, INSERT_IP_MSG, with_args(user_interface.config_ip, self.computer)),
            "set default gateway (g)": with_args(user_interface.ask_user_for, IPAddress, INSERT_GATEWAY_MSG, self.computer.set_default_gateway),
            "add interface (^i)": with_args(user_interface.ask_user_for, str, INSERT_INTERFACE_INFO_MSG, self.computer.add_interface),
            "sniffing start/stop (f)": with_args(self.computer.toggle_sniff, is_promisc=True),
            "open/close port (^o)": with_args(user_interface.ask_user_for, int, INSERT_PORT_NUMBER, self.computer.open_port),
            "ask daytime (ctrl+a)": with_args(user_interface.ask_user_for, IPAddress, INSERT_IP_FOR_PROCESS, with_args(self.computer.start_process, DAYTIMEClientProcess)),
            "download file (alt+a)": with_args(user_interface.ask_user_for, IPAddress, INSERT_IP_FOR_PROCESS, with_args(self.computer.start_process, FTPClientProcess)),
        }
        self.buttons_id = user_interface.add_buttons(buttons)
        return self.copy_sprite(self.sprite, VIEWING_OBJECT_SCALE_FACTOR), self.generate_view_text(), len(buttons)

    def end_viewing(self, user_interface):
        """Ends the viewing of the object in the side window"""
        user_interface.remove_buttons(self.buttons_id)

    def generate_view_text(self):
        """
        Generates the text that will be shown in the side window when this computer is pressed.
        :return: a long string.
        """
        return f" \nName:\n{self.computer.name}\n OS: {self.computer.os}\n gateway: {self.computer.routing_table.default_gateway.ip_address}\n\n " \
            f"Interfaces:\n{str(self.computer.loopback)}\n{linesep.join(str(interface) for interface in self.computer.interfaces)}\n "

    def __str__(self):
        return "ComputerGraphics"

    def __repr__(self):
        return f"ComputerGraphics of computer '{self.computer}'"
