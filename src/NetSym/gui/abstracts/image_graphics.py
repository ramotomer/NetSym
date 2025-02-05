from __future__ import annotations

import os
from typing import Set, Optional, TYPE_CHECKING, Tuple

import pyglet

from NetSym.consts import IMAGES, T_Color, SELECTED_OBJECT, DIRECTORIES, VIEW, SHAPES, COLORS
from NetSym.exceptions import *
from NetSym.gui.abstracts.resizable import Resizable
from NetSym.gui.shape_drawing import draw_rectangle
from NetSym.gui.user_interface.viewable_graphics_object import ViewableGraphicsObject
from NetSym.usefuls.funcs import scale_tuple, sum_tuples
from NetSym.usefuls.paths import add_path_basename_if_needed, are_paths_equal

if TYPE_CHECKING:
    pass


class ImageGraphics(ViewableGraphicsObject, Resizable):
    """
    This class is a superclass of any `GraphicsObject` subclass which uses an image in its `draw` method.
    Put simply, it is a graphics object with a picture.
    """
    x: float
    y: float

    PARENT_DIRECTORY = DIRECTORIES.IMAGES

    def __init__(self,
                 image_name: Optional[str],
                 x: float,
                 y: float,
                 centered: bool = False,
                 is_in_background: bool = False,
                 scale_factor: float = IMAGES.SCALE_FACTORS.SPRITES,
                 is_pressable: bool = False) -> None:
        super(ImageGraphics, self).__init__(x, y, do_render=False, centered=centered, is_in_background=is_in_background, is_pressable=is_pressable)
        self.image_name = add_path_basename_if_needed(self.PARENT_DIRECTORY, image_name if image_name is not None else IMAGES.IMAGE_NOT_FOUND)

        self.scale_factor = scale_factor
        self._sprite: Optional[pyglet.sprite.Sprite] = None

        # MainLoop.instance.register_graphics_object(self, is_in_background)
        self.load()

    @property
    def location(self) -> Tuple[float, float]:
        return self.x, self.y

    @location.setter
    def location(self, value: Tuple[float, float]) -> None:
        self.x, self.y = value

    @property
    def width(self) -> float:
        return float(self.sprite.width)

    @property
    def height(self) -> float:
        return float(self.sprite.height)

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

    @property
    def sprite(self):
        if self._sprite is None:
            raise ImageNotLoadedError(f"{self!r} - not yet loaded!")

        return self._sprite

    @sprite.setter
    def sprite(self, value: pyglet.sprite.Sprite) -> None:
        self._sprite = value

    @staticmethod
    def get_image_sprite(
            image_name: str,
            x: float = 0.0,
            y: float = 0.0,
            scale_factor: float = IMAGES.SCALE_FACTORS.VIEWING_OBJECTS) -> pyglet.sprite.Sprite:
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
    def copy_sprite(sprite: pyglet.sprite.Sprite, new_width: float = VIEW.IMAGE_SIZE, new_height: Optional[float] = None) -> pyglet.sprite.Sprite:
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

    def set_transparency(self, amount: float) -> None:
        """
        Set how transparent the sprite is.
            Use the `IMAGES.TRANSPARENCY` class for measures
        :param amount: 35 is very transparent, 255 is not at all
        """
        self.sprite.opacity = amount

    @property
    def is_transparent(self) -> bool:
        return bool(self.sprite.opacity == IMAGES.TRANSPARENCY.MEDIUM)

    @property
    def should_be_transparent(self) -> bool:
        """
        This property should be overridden - at any given time, the object will become transparent If and Only If this returns `True`
        """
        return False

    def make_transparent(self) -> None:
        self.set_transparency(IMAGES.TRANSPARENCY.MEDIUM)

    def make_opaque(self) -> None:
        self.set_transparency(IMAGES.TRANSPARENCY.LOW)

    def toggle_opacity(self) -> None:
        if self.is_transparent:
            self.make_opaque()
        else:
            self.make_transparent()

    def is_in(self, x: float, y: float) -> bool:
        """
        Returns whether or not the mouse is inside the sprite of this object in the screen.
        :return: Whether the mouse is inside the sprite or not.
        """
        if not self.centered:
            return bool((self.x < x < self.x + self.sprite.width) and (self.y < y < self.y + self.sprite.height))
        return bool((self.x - (self.sprite.width / 2.0) < x < self.x + (self.sprite.width / 2.0)) and
                    (self.y - (self.sprite.height / 2.0) < y < self.y + (self.sprite.height / 2.0)))

    def get_center(self) -> Tuple[float, float]:
        """
        Return the location of the center of the sprite as a tuple.
        """
        return self.x + (self.sprite.width / 2.0), \
               self.y + (self.sprite.height / 2.0)

    def get_centered_coordinates(self) -> Tuple[float, float]:
        """
        Return a tuple of coordinates so that:
        If you draw the sprite in those coordinates, (self.x, self.y) will be the center of the sprite.
        """
        return self.x - int(self.sprite.width / 2), \
               self.y - int(self.sprite.height / 2)

    def mark_as_selected(self) -> None:
        """
        Marks a rectangle around a `GraphicsObject` that is selected.
        Only call this function if the object is selected.
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

    def get_corner_by_direction(self, direction: Tuple[int, int]) -> Tuple[float, float]:
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

    def generate_view_text(self) -> str:
        """
        Generates the text that will be displayed on the screen when the object is viewed in the side-window
        :return: string
        """
        return ''

    def load(self) -> None:
        """
        This function is called once before the object is inserted to the main loop.
        It loads the picture of the object.
        :return: None
        """
        try:
            self.sprite = self.get_image_sprite(self.image_name, self.x, self.y)

        except FileNotFoundError:  # If the image cannot be loaded - load the image for 'image not found'
            print(f"Error: path '{self.image_name}' not found :(")
            image_not_found_image_path = os.path.join(DIRECTORIES.IMAGES, IMAGES.IMAGE_NOT_FOUND)
            if are_paths_equal(self.image_name, image_not_found_image_path):
                raise  # If the image for 'image not found' is not found :)

            self.image_name = image_not_found_image_path
            self.load()
            return

        self.sprite.update(scale_x=self.scale_factor, scale_y=self.scale_factor)
        if self.centered:
            x, y = self.get_centered_coordinates()
            self.sprite.update(x, y)

    def draw(self) -> None:
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

    def move(self) -> None:
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

    def resize(self, width_diff: float, height_diff: float, constrain_proportions: bool = False) -> None:
        """
        Receives a diff in the width and height and resizes the object accordingly
        """
        self._set_size(
            self.width + width_diff,
            self.height + height_diff,
            constrain_proportions
        )

    def rescale(self, scale_x: float, scale_y: float, constrain_proportions: bool = False) -> None:
        """

        """
        self._set_size(
            self.width * scale_x,
            self.height * scale_y,
            constrain_proportions,
        )

    def _set_size(self, new_width: float, new_height: float, constrain_proportions: bool = False) -> None:
        """

        """
        new_width = max(SHAPES.CIRCLE.RESIZE_DOT.MINIMAL_RESIZE_SIZE, new_width)
        new_height = max(SHAPES.CIRCLE.RESIZE_DOT.MINIMAL_RESIZE_SIZE, new_height)

        current_proportions = self.sprite.scale_y / self.sprite.scale_x

        scale_x = (new_width / self.sprite.image.width)
        scale_y = (new_height / self.sprite.image.height)
        if constrain_proportions:
            scale_y = current_proportions * scale_x

        self.sprite.update(scale_x=scale_x, scale_y=scale_y)

    def add_hue(self, hue: T_Color) -> None:
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

    def color_by_name(self, color_name: str) -> None:
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

        self.add_hue(scale_tuple(1, color, round_to_integers=True))

    def flush_colors(self) -> None:
        """
        Flushes the colors and hues from the sprite.
        :return:
        """
        self.sprite.image = pyglet.image.load(self.image_name)

    def change_image(self, new_image_name: str) -> None:
        """
        Change the image path and reload it
        Only reloads the file if the path has changed (efficient!)
        :param new_image_name: The path to the new image to load
        """
        new_image_name = add_path_basename_if_needed(self.PARENT_DIRECTORY, new_image_name)

        if self.image_name != new_image_name:
            self.image_name = new_image_name
            self.load()

    def __str__(self) -> str:
        """The string representation of the GraphicsObject"""
        return f"GraphicsObject({self.image_name}, {self.x, self.y})"

    def __repr__(self) -> str:
        """The string representation of the GraphicsObject"""
        return f"GraphicsObject({self.image_name}, {self.x, self.y}, " \
            f"do_render={self.do_render}, " \
            f"centered={self.centered}, " \
            f"scale_factor={self.scale_factor})"
