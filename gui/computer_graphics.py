from collections import namedtuple
from os import linesep

from consts import *
from gui.console import Console
from gui.image_graphics import ImageGraphics
from gui.text_graphics import Text

ChildGraphicsObjects = namedtuple("ChildGraphicsObjects", "text console")


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
        self.computer = computer
        self.child_graphics_objects = ChildGraphicsObjects(
            Text(self.generate_text(), self.x, self.y, self),
            Console(CONSOLE_X, CONSOLE_Y),
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

    def start_viewing(self, user_interface):
        """
        Starts viewing the computer graphics object in the side-window view.
        :param user_interface: the `UserInterface` object we can use the methods of it.
        :return: a tuple <display sprite>, <display text>, <new button count>
        """
        buttons = {
            "config IP": user_interface.ask_user_for_ip,
            "power on/off": user_interface.power_selected_computer,
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
