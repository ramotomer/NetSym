import time

from exceptions import ObjectIsNotResizableError
from gui.abstracts.user_interface_graphics_object import UserInterfaceGraphicsObject
from gui.main_loop import MainLoop
from gui.main_window import MainWindow, SHAPES, SELECTION_SQUARE, COLORS
from gui.shape_drawing import draw_circle
from usefuls.funcs import distance


class ResizingDot(UserInterfaceGraphicsObject):
    """
    The Dot in the side of the selected resizable objects. 
    Enables you to resize the objects. 
    """
    def __init__(self, x, y, resized_object, direction, constrain_proportions=False):
        """
        Initiates the dot with the graphics object to allow it to resize it. 
        :param x: 
        :param y:w
        :param direction: a tuple simulating where in the object the dot is located (1, 1) for example if it is in
        """
        super(ResizingDot, self).__init__(x, y, centered=True, do_render=False)
        self.radius = SHAPES.CIRCLE.RESIZE_DOT.RADIUS
        self._resized_object = resized_object

        self._x_diff, self._y_diff = self._resized_object.x - x, self._resized_object.y - y

        self.__last_drawn = time.time()

        if not hasattr(self._resized_object, "resize"):
            raise ObjectIsNotResizableError(f"{self._resized_object} has not 'resize' method")

        self.location = x, y
        self.direction = direction
        self.constrain_proportions = constrain_proportions

    def is_mouse_in(self):
        return distance(MainWindow.main_window.get_mouse_location(), self.location) <= self.radius

    def mark_as_selected(self):
        pass

    @property
    def color(self):
        if not self.is_mouse_in():
            return SELECTION_SQUARE.COLOR
        return SHAPES.CIRCLE.RESIZE_DOT.COLOR_WHEN_SELECTED

    def draw(self):
        draw_circle(self.x, self.y, self.radius, COLORS.BLACK, self.color)
        self.__last_drawn = time.time()

    def move(self):
        if self.is_mouse_in() and MainWindow.main_window.mouse_pressed:
            self.location = MainWindow.main_window.get_mouse_location()
            x, y = self.location

            current_x_diff, current_y_diff = self._resized_object.x - x, self._resized_object.y - y

            direction_x, direction_y = self.direction
            self._resized_object.resize((self._x_diff - current_x_diff) * 2 * direction_x,
                                        (self._y_diff - current_y_diff) * 2 * direction_y,
                                        constrain_proportions=self.constrain_proportions)

            self._x_diff, self._y_diff = self._resized_object.x - x, self._resized_object.y - y

    def self_destruct_if_not_showing(self):
        """
        This method should be called every tick to check that the dot was drawn in the last 0.5 seconds.
        If it was not, it erases itself.
        :return:
        """
        if time.time() - self.__last_drawn > 0.5:
            self._resized_object.resizing_dots.remove(self)
            MainLoop.instance.unregister_graphics_object(self)
            MainLoop.instance.remove_from_loop(self.self_destruct_if_not_showing)

    def update_object_location(self):
        x, y = self._resized_object.location
        self.x = x - self._x_diff
        self.y = y - self._y_diff

    def update_object_size(self):
        self.location = self._resized_object.get_corner_by_direction(self.direction)
        x, y = self.location
        self._x_diff, self._y_diff = self._resized_object.x - x, self._resized_object.y - y

    def dict_save(self):
        pass

    def __repr__(self):
        return f"resizing dot for object: {repr(self._resized_object)}"
