from pyglet.window import key

from consts import *
from gui.abstracts.user_interface_graphics_object import UserInterfaceGraphicsObject
from gui.main_loop import MainLoop
from gui.main_window import MainWindow
from gui.shape_drawing import draw_rectangle
from gui.user_interface.button import Button
from gui.user_interface.text_graphics import Text
from usefuls import with_args


class PopupWindow(UserInterfaceGraphicsObject):
    """
    A window that pops up sometime.
    It can contain buttons, text and maybe images?
    """
    def __init__(self, x, y, text, user_interface, buttons,
                 width=WINDOWS.POPUP.TEXTBOX.WIDTH, height=WINDOWS.POPUP.TEXTBOX.HEIGHT, color=TEXTBOX_OUTLINE_COLOR, title="window!"):
        """
        Initiates the `PopupWindow` object.
        :param x, y: the location of the bottom left corner of the window
        :param text: the text for `self._text` attribute.
        :param user_interface: the UserInterface object that holds all of the windows
        :param buttons: a list of buttons that will be displayed on this window. The `X` button is not included.
        """
        super(PopupWindow, self).__init__(x, y)
        self.width, self.height = width, height
        self.__is_active = False
        self.outline_color = color

        title_text = Text(title, self.x, self.y, self, ((self.width / 2) + 2, self.height + 22),
                          color=COLORS.BLACK, align='left', max_width=self.width)
        information_text = Text(text, self.x, self.y, self, ((self.width / 2), 6 * (self.height / 7)), max_width=self.width)

        for button in buttons:
            button.set_parent_graphics(self, (button.x - self.x, button.y - self.y))

        exit_button = Button(
            *WINDOWS.POPUP.SUBMIT_BUTTON.COORDINATES,
            action=self.delete,
            text="X",
            width=TEXTBOX_UPPER_PART_HEIGHT,
            height=TEXTBOX_UPPER_PART_HEIGHT,
            color=self.outline_color,
            text_color=COLORS.BLACK,
            key=(key.ESCAPE, NO_MODIFIER),
        )
        exit_button.set_parent_graphics(self, (self.width - TEXTBOX_UPPER_PART_HEIGHT, self.height))

        self.remove_buttons = None
        user_interface.register_window(self, exit_button, *buttons)
        self.unregister_from_user_interface = with_args(user_interface.unregister_window, self)

        self.child_graphics_objects = [
            title_text,
            information_text,
            exit_button,
            *buttons,
        ]

    def is_mouse_in(self):
        """
        Returns whether or not the mouse is pressing the upper part of the window (where it can be moved)
        :return: `bool`
        """
        x, y = MainWindow.main_window.get_mouse_location()
        return self.x < x < self.x + self.width and \
            self.y < y < self.y + WINDOWS.POPUP.TEXTBOX.HEIGHT + TEXTBOX_UPPER_PART_HEIGHT

    def mark_as_selected(self):
        """
        required for the API
        :return: None
        """
        pass

    def delete(self):
        """
        Deletes the window and removes it from the UserInterface.popup_windows list
        :return: None
        """
        MainLoop.instance.unregister_graphics_object(self)
        self.remove_buttons()
        self.unregister_from_user_interface()

    def draw(self):
        """
        Draws the popup window (text box) on the screen.
        Basically a rectangle.
        :return: None
        """
        draw_rectangle(self.x, self.y,
                       self.width,
                       self.height,
                       TEXTBOX_COLOR,
                       self.outline_color,
                       SHAPES.RECT.DEFAULT_OUTLINE_WIDTH - (0 if self.__is_active else 2))
        # TODO: make self.outline_width a thing instead of the const

        draw_rectangle(
            self.x - (SHAPES.RECT.DEFAULT_OUTLINE_WIDTH / 2), self.y + self.height,
            self.width + SHAPES.RECT.DEFAULT_OUTLINE_WIDTH, TEXTBOX_UPPER_PART_HEIGHT,
            color=self.outline_color,
        )

    def activate(self):
        """
        Marks the window as activated
        :return:
        """
        self.__is_active = True

    def deactivate(self):
        """
        Marks the window as deactivated
        :return:
        """
        self.__is_active = False

    def __str__(self):
        return "A popup window"
