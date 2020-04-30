from collections import namedtuple

from consts import *
from gui.graphics_object import GraphicsObject
from gui.main_window import MainWindow
from gui.shape_drawing import draw_rect
from gui.text_graphics import Text

ChildGraphicsObjects = namedtuple("ChildGraphicsObjects", "text")


class Button(GraphicsObject):
    """
    A class of a button which you can press and assign text and an action to.
    """
    def __init__(self, x, y, action=lambda: None, text=DEFAULT_BUTTON_TEXT,
                 button_group=None, start_hidden=False, width=DEFAULT_BUTTON_WIDTH, height=DEFAULT_BUTTON_HEIGHT):
        """
        Initiates the button.
        :param x:
        :param y: coordinates of the left
        :param action: a function that will be called when the button is pressed.
        :param text: a string that will be written on the button.
        :param button_group: a group that the button will belong to, it will allow us to perform actions on all buttons
            in the same group.
        :param start_hidden: whether or not this button should be created hidden, and only later shown.
        :param width: the button's width.
        :param height: the button's height.
        """
        super(Button, self).__init__(x, y)
        self.is_button = True
        self.is_hidden = start_hidden

        self.button_group = button_group

        self.width, self.height = width, height
        self.action = action
        self.child_graphics_objects = ChildGraphicsObjects(
            Text(text, x, y, self, (self.width / 2, self.height / 2 + BUTTON_TEXT_PADDING),
                 is_button=True,
                 start_hidden=start_hidden,
                 max_width=SIDE_WINDOW_WIDTH,
                 color=PINK),
        )

    def is_mouse_in(self):
        """Returns whether or not the mouse is located inside of the button."""
        mouse_x, mouse_y = MainWindow.main_window.get_mouse_location()
        return (self.x < mouse_x < self.x + self.width) and \
               (self.y < mouse_y < self.y + self.height)

    def toggle_showing(self):
        """
        Hides the button when it is not in use (when it is not supposed to be pressed)
        If the button is hidden now, shows it.
        """
        self.is_hidden = not self.is_hidden
        self.child_graphics_objects.text.is_hidden = not self.child_graphics_objects.text.is_hidden

    def hide(self):
        """
        Hides the button so it cannot be pressed or seen
        """
        self.is_hidden = True
        self.child_graphics_objects.text.hide()

    def show(self):
        """
        Shows the button again if it was hidden, allows it to be pressed regularly.
        """
        self.is_hidden = False
        self.child_graphics_objects.text.show()

    def draw(self):
        """
        Draws the button (If it is not hidden).
        :return: None
        """
        if not self.is_hidden:
            draw_rect(self.x, self.y, self.width, self.height, (DARK_GRAY if self.is_mouse_in() else GRAY))

    def __str__(self):
        return f"Button '{self.child_graphics_objects.text.text}'"

    def __repr__(self):
        return f"Button('{self.child_graphics_objects.text}')"
