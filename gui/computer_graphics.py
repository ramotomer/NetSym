from gui.image_graphics import ImageGraphics
from consts import *
from gui.text_graphics import Text
from os import linesep
from collections import namedtuple
from gui.console import Console


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

    def generate_view_text(self):
        """
        Generates the text that will be shown in the side window when this computer is pressed.
        :return: a long string.
        """
        return f" \nName:\n {self.computer.name}\n OS: {self.computer.os}\n gateway: {self.computer.routing_table.default_gateway.ip_address}\n\n " \
            f"Interfaces:\n {linesep.join(str(interface) for interface in self.computer.interfaces)}\n "

    def __str__(self):
        return "ComputerGraphics"

    def __repr__(self):
        return f"ComputerGraphics of computer {self.computer!r}"
