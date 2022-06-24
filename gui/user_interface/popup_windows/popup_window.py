from pyglet.window import key

from consts import *
from gui.abstracts.user_interface_graphics_object import UserInterfaceGraphicsObject
from gui.main_loop import MainLoop
from gui.main_window import MainWindow
from gui.shape_drawing import draw_rectangle
from gui.user_interface.button import Button
from gui.user_interface.text_graphics import Text
from usefuls.funcs import with_args


class PopupWindow(UserInterfaceGraphicsObject):
    """
    A window that pops up sometime.
    It can contain buttons, text and maybe images?
    """
    def __init__(self, x, y, text, user_interface, buttons,
                 width=WINDOWS.POPUP.TEXTBOX.WIDTH, height=WINDOWS.POPUP.TEXTBOX.HEIGHT,
                 color=WINDOWS.POPUP.TEXTBOX.OUTLINE_COLOR, title="window!",
                 outline_width=SHAPES.RECT.DEFAULT_OUTLINE_WIDTH):
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
        self.outline_width = outline_width

        title_text = Text(title, self.x, self.y, self, ((self.width / 2) + 2, self.height + 22),
                          color=COLORS.BLACK, align='left', max_width=self.width)
        information_text = Text(text, self.x, self.y, self, ((self.width / 2), self.height - 25), max_width=self.width)

        for button in buttons:
            button.set_parent_graphics(self, (button.x - self.x, button.y - self.y))

        self.exit_button = Button(
            *WINDOWS.POPUP.SUBMIT_BUTTON.COORDINATES,
            action=self.delete,
            text="X",
            width=WINDOWS.POPUP.TEXTBOX.UPPER_PART_HEIGHT,
            height=WINDOWS.POPUP.TEXTBOX.UPPER_PART_HEIGHT,
            color=self.outline_color,
            text_color=COLORS.BLACK,
            key=(key.ESCAPE, KEYBOARD.MODIFIERS.NONE),
            is_outlined=False,
        )
        self.exit_button.set_parent_graphics(self, (self.width - WINDOWS.POPUP.TEXTBOX.UPPER_PART_HEIGHT, self.height))

        self.remove_buttons = None
        self.child_graphics_objects = [
            title_text,
            information_text,
            self.exit_button,
            *buttons,
        ]
        user_interface.register_window(self, self.exit_button, *buttons)
        self.unregister_from_user_interface = with_args(user_interface.unregister_window, self)

    def is_mouse_in(self):
        """
        Returns whether or not the mouse is pressing the upper part of the window (where it can be moved)
        :return: `bool`
        """
        x, y = MainWindow.main_window.get_mouse_location()
        return self.x < x < self.x + self.width and \
            self.y < y < self.y + self.height + WINDOWS.POPUP.TEXTBOX.UPPER_PART_HEIGHT

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
        outline_color = self.outline_color if self.__is_active else WINDOWS.POPUP.DEACTIVATED_COLOR
        draw_rectangle(self.x, self.y,
                       self.width,
                       self.height,
                       WINDOWS.POPUP.TEXTBOX.COLOR,
                       outline_color,
                       self.outline_width)

        draw_rectangle(
            self.x - (self.outline_width / 2), self.y + self.height,
            self.width + self.outline_width, WINDOWS.POPUP.TEXTBOX.UPPER_PART_HEIGHT,
            color=outline_color,
        )

    def activate(self):
        """
        Marks the window as activated
        :return:
        """
        self.exit_button.color = self.outline_color
        self.__is_active = True

    def deactivate(self):
        """
        Marks the window as deactivated
        :return:
        """
        self.exit_button.color = WINDOWS.POPUP.DEACTIVATED_COLOR
        self.__is_active = False

    def __str__(self):
        return f"PopupWindow(title='{self.child_graphics_objects[0].text}')"
