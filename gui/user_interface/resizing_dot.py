import time

from exceptions import ObjectIsNotResizableError
from gui.abstracts.graphics_object import GraphicsObject
from gui.main_window import MainWindow, SHAPES, SELECTION_SQUARE, COLORS
from gui.shape_drawing import draw_circle
from usefuls.funcs import distance


class ResizingDot(GraphicsObject):
    """
    The Dot in the side of the selected resizable objects. 
    Enables you to resize the objects. 
    """
    def __init__(self, x, y, resized_object):
        """
        Initiates the dot with the graphics object to allow it to resize it. 
        :param x: 
        :param y: 
        """
        super(ResizingDot, self).__init__(x, y, centered=True, do_render=False)
        self.radius = SHAPES.CIRCLE.RESIZE_DOT.RADIUS
        self.__resized_object = resized_object
        self.__object_distance = distance((x, y), self.__resized_object.location)

        self.__last_drawn = time.time()

        if not hasattr(self.__resized_object, "resize"):
            raise ObjectIsNotResizableError(f"{self.__resized_object} has not 'resize' method")

        self.location = x, y

    @property
    def ratio(self):
        return distance(self.location, self.__resized_object.location) / self.__object_distance

    @property
    def is_mouse_in(self):
        return distance(MainWindow.main_window.get_mouse_location(), self.location) <= self.radius

    @property
    def color(self):
        if not self.is_mouse_in:
            return SELECTION_SQUARE.COLOR
        return COLORS.RED

    def draw(self):
        draw_circle(self.x, self.y, self.radius, self.color)
        self.__last_drawn = time.time()

    def move(self):
        self.location = MainWindow.main_window.get_mouse_location()
        self.__resized_object.resize(self.ratio)
        self.__object_distance = distance(self.location, self.__resized_object.location)

    def dict_save(self):
        pass
