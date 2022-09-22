from abc import ABCMeta
from itertools import product
from typing import Tuple, Set

from consts import *
from exceptions import NoSuchGraphicsObjectError, PopupWindowWithThisError
from gui.abstracts.graphics_object import GraphicsObject
from gui.main_loop import MainLoop
from gui.main_window import MainWindow
from gui.shape_drawing import draw_rectangle
from gui.user_interface.resizing_dot import ResizingDot
from usefuls.funcs import get_the_one, scale_tuple, sum_tuples
from usefuls.paths import add_path_basename_if_needed


class ImageGraphics(GraphicsObject, metaclass=ABCMeta):
    """
    This class is a superclass of any `GraphicsObject` subclass which uses an image in its `draw` method.
    Put simply, it is a graphics object with a picture.
    """
    PARENT_DIRECTORY = DIRECTORIES.IMAGES

    def __init__(self,
                 image_name: str,
                 x: float,
                 y: float,
                 centered: bool = False,
                 is_in_background: bool = False,
                 scale_factor: float = IMAGES.SCALE_FACTORS.SPRITES,
                 is_pressable: bool = False) -> None:
        super(ImageGraphics, self).__init__(x, y, False, centered, is_in_background, is_pressable=is_pressable)
        self.image_name = add_path_basename_if_needed(self.PARENT_DIRECTORY, image_name or IMAGES.IMAGE_NOT_FOUND)

        self.scale_factor = scale_factor
        self.sprite = None

        self.resizing_dots = []

        MainLoop.instance.register_graphics_object(self, is_in_background)

    @property
    def location(self) -> Tuple[float, float]:
        return self.x, self.y

    @location.setter
    def location(self, value: Tuple[float, float]) -> None:
        self.x, self.y = value

        for dot in self.resizing_dots:
            dot.update_object_location()

    @property
    def width(self) -> float:
        return self.sprite.width

    @property
    def height(self) -> float:
        return self.sprite.height

    @property
    def size(self) -> Tuple[float, float]:
        return self.width, self.height

    @property
    def corners(self) -> Set[Tuple[float, float]]:
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
    def get_image_sprite(image_name, x=0, y=0, scale_factor=IMAGES.SCALE_FACTORS.VIEWING_OBJECTS):
        """
        Receives an image_name and x and y coordinates and returns a `pyglet.sprite.Sprite`
        object that can be displayed on the screen.

        :param image_name: come on bro....
        :param x:
        :param y:
        :param scale_factor:
        :return: `pyglet.sprite.Sprite` object
        """
        returned = pyglet.sprite.Sprite(pyglet.image.load(image_name), x=x, y=y)
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

    def set_transparency(self, amount):
        """
        Set how transparent the sprite is.
            Use the `IMAGES.TRANSPARENCY` class for measures
        :param amount: 35 is very transparent, 255 is not at all
        """
        self.sprite.opacity = amount

    @property
    def is_transparent(self):
        return self.sprite.opacity == IMAGES.TRANSPARENCY.MEDIUM

    @property
    def should_be_transparent(self):
        """
        This property should be overridden - at any given time, the object will become transparent If and Only If this returns `True`
        """
        return False

    def make_transparent(self):
        self.set_transparency(IMAGES.TRANSPARENCY.MEDIUM)

    def make_opaque(self):
        self.set_transparency(IMAGES.TRANSPARENCY.LOW)

    def toggle_opacity(self):
        if self.is_transparent:
            self.make_opaque()
        else:
            self.make_transparent()

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

    def mark_as_selected_non_resizable(self):
        """
        Marks the object as selected, but does not show the resizing dots :)
        :return:
        """
        x, y = self.x, self.y
        if self.centered:
            x, y = self.get_centered_coordinates()

        corner = x - SELECTED_OBJECT.PADDING, y - SELECTED_OBJECT.PADDING
        proportions = self.sprite.width + (2 * SELECTED_OBJECT.PADDING), self.sprite.height + (
                    2 * SELECTED_OBJECT.PADDING)

        draw_rectangle(
            *corner,
            *proportions,
            outline_color=SELECTED_OBJECT.COLOR,
        )

    def mark_as_selected(self):
        """
        Marks a rectangle around a `GraphicsObject` that is selected.
        Only call this function if the object is selected.
        :return: None
        """
        self.mark_as_selected_non_resizable()

        directions = set(product(range(-1, 2), repeat=2)) - {(0, 0)}
        for direction in directions:
            self.show_resizing_dot(direction, constrain_proportions=(0 not in direction))

    def get_corner_by_direction(self, direction):
        """
        Returns the location of a corner based on a direction, which is a tuple indicating the
        sign (positivity or negativity) of the corner
        :param direction: (1, 1) for example, or (0, -1)
        :return:
        """
        x, y = self.x, self.y
        if self.centered:
            x, y = self.get_centered_coordinates()

        bottom_left_x, bottom_left_y = x - SELECTED_OBJECT.PADDING, y - SELECTED_OBJECT.PADDING
        width = self.sprite.width + (2 * SELECTED_OBJECT.PADDING)
        height = self.sprite.height + (2 * SELECTED_OBJECT.PADDING)

        dx, dy = direction
        return (bottom_left_x + width / 2) + ((width / 2) * dx), (bottom_left_y + height / 2) + ((height / 2) * dy)

    def show_resizing_dot(self, direction, constrain_proportions=False):
        """
        Displays and enables the little dot that allows resizing of objects.
        """
        if get_the_one(self.resizing_dots, lambda d: d.direction == direction) is None:
            dot = ResizingDot(*self.get_corner_by_direction(direction), self, direction, constrain_proportions)
            self.resizing_dots.append(dot)
            MainLoop.instance.graphics_objects.append(dot)
            MainLoop.instance.insert_to_loop(dot.self_destruct_if_not_showing)

        dot = get_the_one(self.resizing_dots, lambda d: d.direction == direction, NoSuchGraphicsObjectError)
        dot.draw()
        dot.move()

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
        try:
            self.sprite = self.get_image_sprite(self.image_name, self.x, self.y)
        except FileNotFoundError:
            print(f"Error on finding path '{self.image_name}' :(")
            image_not_found_image_path = os.path.join(DIRECTORIES.IMAGES, IMAGES.IMAGE_NOT_FOUND)
            if self.image_name == image_not_found_image_path:
                raise
            self.image_name = image_not_found_image_path
            self.load()  # try again if the image cannot be loaded

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
        if self.should_be_transparent:
            self.make_transparent()
        else:
            self.make_opaque()

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

    def resize(self, width_diff, height_diff, constrain_proportions=False):
        """
        Receives a diff in the width and height and resizes the object accordingly
        """
        new_width = self.width + width_diff
        new_height = self.height + height_diff

        new_width = max(SHAPES.CIRCLE.RESIZE_DOT.MINIMAL_RESIZE_SIZE, new_width)
        new_height = max(SHAPES.CIRCLE.RESIZE_DOT.MINIMAL_RESIZE_SIZE, new_height)

        current_proportions = self.sprite.scale_y / self.sprite.scale_x

        scale_x = (new_width / self.sprite.image.width)
        scale_y = (new_height / self.sprite.image.height)
        if constrain_proportions:
            scale_y = current_proportions * scale_x

        self.sprite.update(scale_x=scale_x, scale_y=scale_y)

        for dot in self.resizing_dots:
            dot.update_object_size()

    def add_hue(self, hue):
        """
        Adds a certain hue to the picture. the hue should be in the form (r, g, b)
        :param hue:
        :return:
        """
        img = self.sprite.image.get_image_data()
        data = bytearray(img.get_data("BGRA", img.width * 4))

        hue_r, hue_g, hue_b = hue
        new_color_ratio = 0.5
        for i in range(0, len(data), 4):
            b, g, r, a = data[i:i + 4]
            data[i:i + 4] = [
                int(min(255, max(0, (hue_b * (1 - new_color_ratio)) + (b * new_color_ratio)))),
                int(min(255, max(0, (hue_g * (1 - new_color_ratio)) + (g * new_color_ratio)))),
                int(min(255, max(0, (hue_r * (1 - new_color_ratio)) + (r * new_color_ratio)))),
                int(a),
            ]

        img.set_data("BGRA", img.width * 4, bytes(data))
        self.sprite.image = img

    def color_by_name(self, color_name):
        """
        Colors the sprite by a color name ("red", "blue", "light green"
        :param color_name:
        :return:
        """
        color_names = {item.lower().replace('_', ' '): value
                       for item, value in COLORS.__dict__.items()
                       if not item.startswith("__") and "diff" not in item.lower()}
        try:
            color = color_names[color_name.split()[-1]]
        except KeyError:
            raise PopupWindowWithThisError(f"invalid color name: '{color_name}'")

        for _ in range(color_name.split().count("very") + int(len(color_name.split()) > 1)):
            try:
                color = sum_tuples({"light": (50, 50, 50), "dark": (-50, -50, -50)}[color_name.split()[-2]], color)
            except KeyError:
                raise PopupWindowWithThisError(f"invalid color name: '{color_name}'")

        self.add_hue(scale_tuple(1, color, True))

    def flush_colors(self):
        """
        Flushes the colors and hues from the sprite.
        :return:
        """
        self.sprite.image = pyglet.image.load(self.image_name)

    def change_image(self, new_image_name: str):
        """
        Change the image path and reload it
        Only reloads the file if the path has changed (efficient!)
        :param new_image_name: The path to the new image to load
        """
        new_image_name = add_path_basename_if_needed(self.PARENT_DIRECTORY, new_image_name)

        if self.image_name != new_image_name:
            self.image_name = new_image_name
            self.load()

    def __str__(self):
        """The string representation of the GraphicsObject"""
        return f"GraphicsObject({self.image_name}, {self.x, self.y})"

    def __repr__(self):
        """The string representation of the GraphicsObject"""
        return f"GraphicsObject({self.image_name}, {self.x, self.y}, " \
            f"do_render={self.do_render}, " \
            f"centered={self.centered}, " \
            f"scale_factor={self.scale_factor})"
