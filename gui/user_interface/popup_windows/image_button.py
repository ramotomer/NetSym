from consts import *
from gui.abstracts.image_graphics import ImageGraphics
from gui.user_interface.button import Button


class ImageButton(Button):
    """
    This is a button with an image inside
    """
    def __init__(self, x, y, action=lambda: None, image_name=None, text="",
                 start_hidden=False,
                 width=IMAGES.SIZE, height=IMAGES.SIZE,
                 key=None, color=BUTTONS.COLOR, text_color=BUTTONS.TEXT_COLOR, is_outlined=False):
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
        super(ImageButton, self).__init__(x, y, action, text, start_hidden, width, height,
                                          key, color, text_color, is_outlined)

        self.pad_x, self.pad_y = 10, 10
        self.image_name = os.path.join(DIRECTORIES.IMAGES, image_name)
        self.image_sprite = ImageGraphics.get_image_sprite(self.image_name, x + self.pad_x / 2, y + self.pad_y / 2)

        scale_x, scale_y = self.image_sprite.scale_x, self.image_sprite.scale_y
        scale_x = ((self.width - 2 * self.pad_x) / self.image_sprite.width) * scale_x
        scale_y = ((self.height - 2 * self.pad_y) / self.image_sprite.height) * scale_y
        self.image_sprite.update(scale_x=scale_x, scale_y=scale_y)

        pad_x, pad_y = self.child_graphics_objects.text.padding
        self.child_graphics_objects.text.padding = pad_x, self.height

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
        self.image_sprite.update(self.x + self.pad_x / 2, self.y + self.pad_y / 2)
