import pyglet

from consts import *
from gui.abstracts.graphics_object import GraphicsObject
from gui.main_loop import MainLoop
from gui.main_window import MainWindow
from gui.shape_drawing import draw_rectangle
from gui.user_interface.resizing_dot import ResizingDot


class ImageGraphics(GraphicsObject):
    """
    This class is a superclass of any `GraphicsObject` subclass which uses an image in its `draw` method.
    Put simply, it is a graphics object with a picture.
    """
    def __init__(self, image_name, x, y, centered=False, is_in_background=False, scale_factor=IMAGES.SCALE_FACTORS.SPRITES,
                 is_opaque=False, is_pressable=False):
        super(ImageGraphics, self).__init__(x, y, False, centered, is_in_background, is_pressable=is_pressable)
        self.image_name = image_name
        self.scale_factor = scale_factor
        self.is_opaque = is_opaque
        self.sprite = None

        self.is_image = True

        self.resizing_dot = None

        MainLoop.instance.register_graphics_object(self, is_in_background)

    @property
    def width(self):
        return self.sprite.width

    @property
    def height(self):
        return self.sprite.height

    @property
    def size(self):
        return self.width, self.height

    @property
    def corners(self):
        if not self.centered:
            return {
                (self.x, self.y),
                (self.x + self.width, self.y),
                (self.x, self.y + self.height),
                (self.x + self.width, self.y + self.height),
            }
        return {
            (self.x - (self.width / 2), self.y - (self.height / 2)),
            (self.x - (self.width / 2), self.y + (self.height / 2)),
            (self.x + (self.width / 2), self.y - (self.height / 2)),
            (self.x + (self.width / 2), self.y + (self.height / 2)),
        }

    @staticmethod
    def get_image_sprite(image_name, x=0, y=0, is_opaque=False, scale_factor=IMAGES.SCALE_FACTORS.VIEWING_OBJECTS):
        """
        Receives an image_name and x and y coordinates and returns a `pyglet.sprite.Sprite`
        object that can be displayed on the screen.

        :param image_name: come on bro....
        :param x:
        :param y:
        :param is_opaque:
        :param scale_factor:
        :return: `pyglet.sprite.Sprite` object
        """
        returned = pyglet.sprite.Sprite(pyglet.image.load(image_name), x=x, y=y)
        returned.opacity = IMAGES.TRANSPARENCY.HIGH if is_opaque else IMAGES.TRANSPARENCY.LOW
        returned.update(scale_x=scale_factor, scale_y=scale_factor)
        return returned

    @staticmethod
    def copy_sprite(sprite, new_width=VIEW.IMAGE_SIZE, new_height=None):
        """
        Receive a sprite object and return a copy of it.
        :param sprite: a `pyglet.sprite.Sprite` object.
        :param new_width: the desired width of the sprite
        :param new_height: if left empty, equals to `new_width`
        :return: a new copied `pyglet.sprite.Sprite`
        """
        returned = pyglet.sprite.Sprite(sprite.image, x=sprite.x, y=sprite.y)
        new_height = new_height if new_height is not None else new_width

        returned.update(scale_x=(new_width / sprite.image.width), scale_y=(new_height / sprite.image.height))
        returned.opacity = sprite.opacity
        return returned

    def toggle_opacity(self):
        """toggles whether or not the image is opaque"""
        self.sprite.opacity = IMAGES.TRANSPARENCY.MEDIUM if self.sprite.opacity == IMAGES.TRANSPARENCY.LOW else IMAGES.TRANSPARENCY.LOW

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

        corner = x - SELECTED_OBJECT.PADDING, y - SELECTED_OBJECT.PADDING
        draw_rectangle(
            *corner,
            self.sprite.width + (2 * SELECTED_OBJECT.PADDING),
            self.sprite.height + (2 * SELECTED_OBJECT.PADDING),
            outline_color=SELECTED_OBJECT.COLOR,
        )

        self.show_resizing_dot(corner)

    def show_resizing_dot(self, corner):
        """
        Displays and enables the little dot that allows resizing of objects.
        :param corner:
        :return:
        """
        if self.resizing_dot is None:
            self.resizing_dot = ResizingDot(*corner, self)
            MainLoop.instance.graphics_objects.append(self.resizing_dot)

        self.resizing_dot.draw()
        self.resizing_dot.move()

    def start_viewing(self, user_interface):
        """
        Returns a tuple a `pyglet.sprite.Sprite` object and a `Text` object that should be shown on the side window
        when this object is pressed. also returns the added button id in the returned tuple.
        :return:
        """
        return self.copy_sprite(self.sprite), self.generate_view_text(), None

    def generate_view_text(self):
        """
        Generates the text that will be displayed on the screen when the object is viewed in the side-window
        :return: string
        """
        return ''

    def load(self):
        """
        This function is called once before the object is inserted to the main loop.
        It loads the picture of the object.
        :return: None
        """
        self.sprite = self.get_image_sprite(self.image_name, self.x, self.y, self.is_opaque)
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

    def resize(self, width_diff, height_diff):
        """

        """
        new_width = self.width + width_diff
        new_height = self.height + height_diff

        new_width = max(SHAPES.CIRCLE.RESIZE_DOT.MINIMAL_RESIZE_SIZE, new_width)
        new_height = max(SHAPES.CIRCLE.RESIZE_DOT.MINIMAL_RESIZE_SIZE, new_height)

        self.sprite.update(scale_x=(new_width / self.sprite.image.width),
                           scale_y=(new_height / self.sprite.image.height))

    def __str__(self):
        """The string representation of the GraphicsObject"""
        return f"GraphicsObject({self.image_name}, {self.x, self.y})"

    def __repr__(self):
        """The string representation of the GraphicsObject"""
        return f"GraphicsObject({self.image_name}, {self.x, self.y}, " \
            f"do_render={self.do_render}, " \
            f"centered={self.centered}, " \
            f"scale_factor={self.scale_factor})"
