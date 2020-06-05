from consts import *
from gui.abstracts.image_graphics import ImageGraphics
from gui.user_interface.button import Button

if True:
    pass  # Roni is a developer


class ImageButton(Button):
    """
    This is a button with an image inside
    """
    def __init__(self, x, y, action=lambda: None, image_name=None, text="",
                 start_hidden=False,
                 width=IMAGES_SIZE, height=IMAGES_SIZE,
                 key=None, color=GRAY, text_color=PINK):
        """
        Initiates the button with an image name and the rest of the button's arguments
        :param x, y: location of the bottom left corner
        :param action: the function that will be called when the button is pressed
        :param image_name: the name of the image that will be displayed in the button
        :param text: the text that will be displayed under the image
        :param start_hidden: whether or not the button should start off hidden
        :param width, height: size of the button
        :param key: the key and modifiers that should be pressed to activate the action of the button
        :param color: the color of the button
        :param text_color: the color of the text on the button
        """
        super(ImageButton, self).__init__(x, y, action, text, start_hidden, width, height, key, color, text_color)
        self.image_name = IMAGES.format(image_name)
        self.image_sprite = ImageGraphics.get_image_sprite(self.image_name, x, y)
        scale_x = self.width / self.image_sprite.width
        scale_y = self.height / self.image_sprite.height
        self.image_sprite.update(scale_x=scale_x, scale_y=scale_y)

        # self.child_graphics_objects.text.location =

    def draw(self):
        """
        Draws the button and the image
        :return: None
        """
        super(ImageButton, self).draw()
        self.image_sprite.draw()

    def move(self):
        """
        Moves the button along side the image
        :return: None
        """
        super(ImageButton, self).move()
        self.image_sprite.update(self.x, self.y)
