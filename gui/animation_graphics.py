import time

import pyglet

from consts import *
from gui.image_graphics import ImageGraphics
from gui.main_loop import MainLoop


class AnimationGraphics(ImageGraphics):
    """
    A GraphicsObject of an animation
    """
    def __init__(self, image_name, x, y, x_count=ANIMATION_X_COUNT, y_count=ANIMATION_Y_COUNT):
        super(AnimationGraphics, self).__init__(image_name, x, y, centered=True)
        self.x_count = x_count
        self.y_count = y_count
        self.start_time = time.time()

    @staticmethod
    def get_animation_sprite(image_name, x, y, is_opaque=False, x_count=ANIMATION_X_COUNT, y_count=ANIMATION_Y_COUNT):
        """Returns a pyglet.sprite.Sprite object of the animation"""
        image = pyglet.image.load(IMAGES.format(image_name))
        sequence = pyglet.image.ImageGrid(image, x_count, y_count, item_width=IMAGES_SIZE, item_height=IMAGES_SIZE)
        textures = pyglet.image.TextureGrid(sequence)
        animation = pyglet.image.Animation.from_image_sequence(textures[:], ANIMATION_FRAME_RATE, loop=False)
        return animation.get_duration(), pyglet.sprite.Sprite(animation, x, y)

    def load(self):
        """
        Loading an animation is a little different
        :return: None
        """
        self.run_time, self.sprite = self.get_animation_sprite(self.image_name, self.x, self.y)
        self.sprite.update(scale_x=self.scale_factor, scale_y=self.scale_factor)

        if self.centered:
            x, y = self.get_centered_coordinates()
            self.sprite.update(x, y)

    def move(self):
        """
        Moves the object, In the case of an animation, also unregisters it when it is done :)
        :return: None
        """
        super(AnimationGraphics, self).move()

        if (time.time() - self.start_time) > self.run_time:
            MainLoop.instance.unregister_graphics_object(self)
