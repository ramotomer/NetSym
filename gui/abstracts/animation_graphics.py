import time

import pyglet

from consts import *
from gui.abstracts.image_graphics import ImageGraphics
from gui.main_loop import MainLoop


class AnimationGraphics(ImageGraphics):
    """
    A GraphicsObject of an animation. An image that is made out of little images and the animation if looped through them.
    """
    def __init__(self, image_name, x, y, is_looping=False, x_count=ANIMATIONS.X_COUNT, y_count=ANIMATIONS.Y_COUNT,
                 image_width=IMAGES.SIZE, image_height=IMAGES.SIZE, frame_rate=ANIMATIONS.FRAME_RATE, scale=1.0):
        """
        Initiates the animation graphics
        :param image_name: the name of the image (no need for os.path.join(DIRECTORIES.IMAGES... )
        :param x: the x coordinate of the animation
        :param y: the y coordinate of the animation
        :param is_looping: whether or not the animation loops
        :param x_count: the amount of images in the animation in the x direction
        :param y_count: the amount of images in the animation in the y direction
        :param image_width: a width of a single image in the animation
        :param image_height: a height of a single image in the animation
        """
        self.item_width = image_width
        self.item_height = image_height
        self.is_looping = is_looping
        self.x_count = x_count
        self.y_count = y_count
        self.run_time = None
        self.start_time = time.time()
        self.frame_rate = frame_rate
        self.scale = scale
        super(AnimationGraphics, self).__init__(image_name, x, y, centered=True)

    @property
    def is_done(self):
        """
        Whether or not the simulation has ended
        :return: bool
        """
        return not self.is_looping and (time.time() - self.start_time) > self.run_time

    def get_animation_sprite(self, image_name, x, y, x_count=ANIMATIONS.X_COUNT, y_count=ANIMATIONS.Y_COUNT):
        """
        Returns a pyglet.sprite.Sprite object of the animation
        """
        image = pyglet.image.load(os.path.join(DIRECTORIES.IMAGES, image_name))
        sequence = pyglet.image.ImageGrid(image, x_count, y_count,
                                          item_width=self.item_width, item_height=self.item_height)
        textures = pyglet.image.TextureGrid(sequence)
        animation = pyglet.image.Animation.from_image_sequence(textures[:], self.frame_rate, loop=self.is_looping)
        sprite = pyglet.sprite.Sprite(animation, x, y)
        sprite.scale = self.scale
        return animation.get_duration(), sprite

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

        if self.is_done:
            MainLoop.instance.unregister_graphics_object(self)


# class LogoAnimation(AnimationGraphics):
#     """
#     The animation of the Logo in the start of the simulation.
#     """
#     def __init__(self, x, y):
#         """
#         Initiates the animation of the logo
#         """
#         super(LogoAnimation, self).__init__(LOGO_ANIMATION_IMAGE, x, y, True, 8, 5, 640, 320, 0.2, 0.7)
