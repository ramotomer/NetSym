from abc import ABCMeta

from gui.abstracts.graphics_object import GraphicsObject


class UserInterfaceGraphicsObject(GraphicsObject, metaclass=ABCMeta):
    """
    A GraphicsObject which is used only for the user interface (popup windows, buttons, etc...)
    """
    def __init__(self, x=None, y=None, do_render=True, centered=False, is_in_background=False, is_pressable=False):
        super(UserInterfaceGraphicsObject, self).__init__(x, y, do_render, centered, is_in_background, is_pressable)

    def text_save(self):
        """
        These do not need to be implement this method.
        It is used to save the simulation status into a file.
        They are loaded anyway, so there is no need to save them.
        :return: None
        """
        return None

    @classmethod
    def from_text_load(cls, text):
        pass
