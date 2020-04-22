from gui.graphics_object import GraphicsObject
from consts import *
import pyglet
from gui.main_loop import MainLoop
from gui.main_window import MainWindow
from gui.shape_drawing import draw_rect_no_fill


class ImageGraphics(GraphicsObject):
    """
    This class is a superclass of any `GraphicsObject` subclass which uses an image in its `draw` method.
    Put simply, it is a graphics object with a picture.
    """
    def __init__(self, image_name, x, y, centered=False, is_in_background=False, scale_factor=SPRITE_SCALE_FACTOR):
        super(ImageGraphics, self).__init__(x, y, False, centered, is_in_background)
        self.image_name = image_name
        self.scale_factor = scale_factor
        self.sprite = None

        MainLoop.instance.register_graphics_object(self, is_in_background)

    @staticmethod
    def get_image_sprite(image_name, x, y):
        """
        Receives an image_name and x and y coordinates and returns a `pyglet.sprite.Sprite`
        object that can be displyed on the screen.

        :param image_name: come on bro....
        :param x:
        :param y:
        :return: `pyglet.sprite.Sprite` object
        """
        return pyglet.sprite.Sprite(pyglet.image.load(image_name), x=x, y=y)

    @staticmethod
    def copy_sprite(sprite, scale):
        """
        Receive a sprite object and return a copy of it.
        :param sprite: a `pyglet.sprite.Sprite` object.
        :param scale: the scaling factor that we want the new sprite to have.
        :return: a new copied `pyglet.sprite.Sprite`
        """
        returned = pyglet.sprite.Sprite(sprite.image, x=sprite.x, y=sprite.y)
        returned.update(scale=scale)
        return returned

    def is_mouse_in(self):
        """
        Returns whether or not the mouse is inside the sprite of this object in the screen.
        :return: Whether the mouse is inside the sprite or not.
        """
        mouse_x, mouse_y = MainWindow.main_window.get_mouse_location()
        if not self.centered:
            return (self.x < mouse_x < self.x + self.sprite.width) and \
                        (self.y < mouse_y < self.y + self.sprite.height)
        return (self.x - (self.sprite.width / 2.0) < mouse_x < self.x + (self.sprite.width / 2.0)) and\
                (self.y - (self.sprite.height / 2.0) < mouse_y < self.y + (self.sprite.height / 2.0))

    def get_center(self):
        """
        Return the location of the center of the sprite as a tuple.
        """
        return self.x + (self.sprite.width / 2.0), \
               self.y + (self.sprite.height / 2.0)

    def get_centered_coordinates(self):
        """
        Return a tuple of coordinates so that:
        If you draw the sprite in those coordinates, (self.x, self.y) will be the center of the sprite.
        """
        return self.x - int(self.sprite.width / 2), \
               self.y - int(self.sprite.height / 2)

    def mark_as_selected(self):
        """
        Marks a rectangle around a `GraphicsObject` that is selected.
        Only call this function if the object is selected.
        :return: None
        """
        x, y = self.x, self.y
        if self.centered:
            x, y = self.get_centered_coordinates()
        draw_rect_no_fill(x - SELECTED_OBJECT_PADDING, y - SELECTED_OBJECT_PADDING, self.sprite.width + (2 * SELECTED_OBJECT_PADDING), self.sprite.height + (2 * SELECTED_OBJECT_PADDING))

    def load(self):
        """
        This function is called once before the object is inserted to the main loop.
        It loads the picture of the object.
        :return: None
        """
        self.sprite = self.get_image_sprite(self.image_name, self.x, self.y)
        self.sprite.update(scale_x=self.scale_factor, scale_y=self.scale_factor)

        if self.centered:
            x, y = self.get_centered_coordinates()
            self.sprite.update(x, y)

    def draw(self):
        """
        This is called once every tick of the clock (`update` function).
        This function is in charge of the graphical drawing of the object, draws the image to the screen.
        :return: None
        """
        self.sprite.draw()

    def move(self):
        """
        This is called once every tick of the clock (`update` function).
        This function is in charge of the motion of the object in a theoretical sense.
        (If the object does not move, no need to override this).
        It updates the sprite's location to be the same as the `GraphicsObjects`'s location.
        :return: None
        """
        x, y = self.x, self.y
        if self.centered:
            x, y = self.get_centered_coordinates()

        self.sprite.update(x=x, y=y)

    def __str__(self):
        """The string representation of the GraphicsObject"""
        return f"GraphicsObject({self.image_name}, {self.x, self.y})"

    def __repr__(self):
        """The string representation of the GraphicsObject"""
        return f"GraphicsObject({self.image_name}, {self.x, self.y}, " \
            f"do_render={self.do_render}, " \
            f"centered={self.centered}, " \
            f"scale_factor={self.scale_factor})"
