from computing.computer import Computer
from consts import *
from gui.tech.computer_graphics import ComputerGraphics


class NAT(Computer):
    """

    """
    def __init__(self):
        """

        """
        super(NAT, self).__init__()

    def show(self, x, y):
        """

        :param x:
        :param y:
        :return:
        """
        self.graphics = ComputerGraphics(x, y, self, NAT_IMAGE)
