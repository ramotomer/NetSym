from abc import ABCMeta

from gui.abstracts.graphics_object import GraphicsObject
from usefuls.funcs import sum_tuples


class UserInterfaceGraphicsObject(GraphicsObject, metaclass=ABCMeta):
    """
    A GraphicsObject which is used only for the user interface (popup windows, buttons, etc...)
    """
    def __init__(self, x=None, y=None, do_render=True, centered=False, is_in_background=False, is_pressable=False):
        super(UserInterfaceGraphicsObject, self).__init__(x, y, do_render, centered, is_in_background, is_pressable)
        self.parent_graphics = None
        self.padding = None

    def set_parent_graphics(self, parent_graphics, padding=(0, 0)):
        """
        Sets the parent graphics of the Graphics Object, It follows it around.
        :param parent_graphics:
        :param padding:
        :return:
        """
        self.parent_graphics = parent_graphics
        self.padding = padding

    def move(self):
        """
        For consoles that have to move relatively to a parent graphics object.
        :return:
        """
        if self.parent_graphics is not None:
            self.location = sum_tuples(self.parent_graphics.location, self.padding)

    def dict_save(self):
        """
        These do not need to be implement this method.
        It is used to save the simulation status into a file.
        They are loaded anyway, so there is no need to save them.
        :return: None
        """
        return None
