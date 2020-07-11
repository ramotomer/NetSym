import pyglet

from consts import *
from gui.abstracts.user_interface_graphics_object import UserInterfaceGraphicsObject


class Text(UserInterfaceGraphicsObject):
    """
    This represents permanent text on the screen.

    The text that is drawn on the screen is kept because if it is created each
    time the screen is updated (like it was before) the program crashes and says it is out of memory.
    Apparently pyglet is having a lot of trouble drawing text.
    """
    def __init__(self, text, x, y,
                 parent_graphics=None,
                 padding=(0, TEXT.DEFAULT_Y_PADDING),
                 is_button=False,
                 start_hidden=False,
                 max_width=WINDOWS.MAIN.WIDTH,
                 font_size=TEXT.FONT.DEFAULT_SIZE,
                 align=TEXT.ALIGN.CENTER,
                 color=TEXT.COLOR,
                 font=TEXT.FONT.DEFAULT):
        """
        Initiates a new `Text` object.
        A `Text` object can have a parent `GraphicsObject` which it will set its coordinates according to it. (if it
            moves, the text moves with it)
        At all times, the coordinates of the `Text` object will be the ones of the `parent_graphics` object plus the
        padding.

        The coordinates `x` and `y` of the `Text` object are in the middle of
        the first line that is drawn on the screen.
        :param text: the actual string that is presented.
        :param x:
        :param y: coordinates
        :param parent_graphics: a `GraphicsObject` to follow
        :param padding: a tuple of x and y padding around the parent object.
        :param is_button:  whether or not this text is on a button (for `hide` and `show` of buttons)
        :param start_hidden:  whether or not to start off hidden.
        :param max_width:  The maximum length that this text is allowed to reach in one line.
        :param font_size: THE FONT SIZE!!!!!!!!!!!!!!!
        :param color: the text color- defaults to white.
        """
        super(Text, self).__init__(x, y, centered=True)
        self._text = text
        self.is_button = is_button  # whether or not it is on a text on a button
        self.is_hidden = start_hidden
        self.max_width = max_width
        self.font_size = font_size
        self.align = align
        self.color = color
        self.font = font

        self.label = None
        self.set_parent_graphics(parent_graphics, padding)
        self.set_text(text)

    @property
    def text(self):
        return self._text

    def set_text(self, text):
        """
        The correct way to update the text of a `Text` object.
        updates the text and corrects the lines and everything necessary.
        :param text: a string which is the new text.
        :return: None
        """
        self._text = text
        self.label = pyglet.text.Label(self._text,
                                       font_name=self.font,
                                       font_size=self.font_size,
                                       x=self.x + self.padding[0], y=(self.y + self.padding[1]),
                                       color=self.color + (255,),
                                       anchor_x='center', anchor_y='top',
                                       align=self.align)

        self.label.width = self.max_width
        self.label.multiline = True
        self.x, self.y = self.label.x, self.label.y
        self.move()

    def append_text(self, text):
        """
        appends a string to the end of the text of the `Text` object.
        :param text:
        :return:
        """
        self.set_text(self.text + text)

    def draw(self):
        """
        Draws the text to the screen
        :return: None
        """
        if not self.is_hidden:
            self.label.draw()

    def show(self):
        """
        Shows the text if it is hidden
        :return: None
        """
        self.is_hidden = False

    def hide(self):
        """
        Hides the text if it is is_showing.
        :return: None
        """
        self.is_hidden = True

    def move(self):
        """
        Moves the text according to the parent object's location.
        :return: None
        """
        if self.parent_graphics is None:
            self.label.x, self.label.y = self.x, self.y
            return
        super(Text, self).move()
        self.label.x, self.label.y = self.x, self.y

    def __str__(self):
        return f"Text Graphics: '{self.text}'"

    def __repr__(self):
        return f"Text(text={self.text!r})"
