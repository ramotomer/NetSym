from consts import *
from exceptions import WrongUsageError
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
        self.creation_time = MainLoop.instance.time()

        self.title_text = Text(title, self.x, self.y, self, self.get_title_text_padding(),
                               color=COLORS.BLACK, align='left', max_width=self.width)
        information_text = Text(text, self.x, self.y, self, ((self.width / 2), self.height - 25), max_width=self.width)
        # TODO: if PopupConsole does not have `information_text` - it should not be in the parent class `PopupWindow`!!!!

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
            is_outlined=False,
            custom_active_color=COLORS.LIGHT_RED
        )
        self.exit_button.set_parent_graphics(self, self.get_exit_button_padding())

        self.remove_buttons = None
        self.child_graphics_objects = [
            self.title_text,
            information_text,
            self.exit_button,
            *buttons,
        ]
        user_interface.register_window(self, self.exit_button, *buttons)
        self.unregister_from_user_interface = with_args(user_interface.unregister_window, self)

        self._x_before_pinning, self._y_before_pinning = None, None
        self._size_before_pinning = self.width, self.height
        self._pinned_directions = set()

    @property
    def location(self):
        return self.x, self.y

    @location.setter
    def location(self, value):
        # this is the way the `UserInterface` moves the `selected_object`
        self.x, self.y = value
        self._x_before_pinning, self._y_before_pinning = value
        self._pinned_directions = set()
        self._size_before_pinning = self.width, self.height

    @property
    def is_pinned(self):
        return bool(self._pinned_directions)

    def get_exit_button_padding(self):
        return self.width - WINDOWS.POPUP.TEXTBOX.UPPER_PART_HEIGHT, self.height

    def get_title_text_padding(self):
        return (self.width / 2) + 2, self.height + 22

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

    def resize(self, width, height):
        self.width, self.height = width, height
        self.exit_button.padding = self.get_exit_button_padding()
        self.title_text.resize(self.get_title_text_padding(), width)

    def pin_to(self, direction):
        """
        Pin the window to one side like the effect windows has when you press Winkey+arrow
        :param direction:
        :return:
        """
        if not self.is_pinned:
            self._x_before_pinning, self._y_before_pinning = self.x, self.y

        right, left, up, down = WINDOWS.POPUP.DIRECTIONS.RIGHT, WINDOWS.POPUP.DIRECTIONS.LEFT, \
                                WINDOWS.POPUP.DIRECTIONS.UP, WINDOWS.POPUP.DIRECTIONS.DOWN
        pinned_directions = self._pinned_directions

        if direction == up:
            if not self.is_pinned or up in pinned_directions:
                self.maximize()
            elif {left, right} & pinned_directions:
                sideways_direction, = {left, right} & pinned_directions
                if down in pinned_directions:
                    self.make_split_screen(sideways_direction)
                else:
                    self.make_quarter_screen({up, sideways_direction})

        elif direction == down:
            if {left, right} & pinned_directions:
                sideways_direction, = {left, right} & pinned_directions
                if up in pinned_directions:
                    self.make_split_screen(sideways_direction)
                else:
                    self.make_quarter_screen({down, sideways_direction})
            elif up in pinned_directions:
                self.make_like_before_pinned()

        elif direction in [left, right]:
            if not self.is_pinned or pinned_directions == {up}:
                self.make_split_screen(direction)
            elif ({left, right} & pinned_directions) and (direction not in pinned_directions):
                if {up, down} & pinned_directions:
                    sideways_direction, = {left, right} & pinned_directions
                    rightways_direction, = {up, down} & pinned_directions
                    self.make_quarter_screen({WINDOWS.POPUP.DIRECTIONS.OPPOSITE[sideways_direction], rightways_direction})
                else:
                    self.make_like_before_pinned()

    def maximize(self):
        """
        Make the window the size of the whole screen
        """
        self.x, self.y = 0, 0
        self.resize((MainWindow.main_window.width - WINDOWS.SIDE.WIDTH), MainWindow.main_window.height - WINDOWS.POPUP.TEXTBOX.UPPER_PART_HEIGHT)
        self._pinned_directions = {WINDOWS.POPUP.DIRECTIONS.UP}

    def make_split_screen(self, direction):
        """
        Set the size and location of the window to be exactly half of the screen
        :param direction: What half of the screen should that be 'right' or 'left'
        """
        if direction not in [WINDOWS.POPUP.DIRECTIONS.RIGHT, WINDOWS.POPUP.DIRECTIONS.LEFT]:
            raise WrongUsageError(f"direction must be either right or left not '{direction}'!")

        self.resize((MainWindow.main_window.width - WINDOWS.SIDE.WIDTH) / 2,
                    MainWindow.main_window.height - WINDOWS.POPUP.TEXTBOX.UPPER_PART_HEIGHT)

        if direction == WINDOWS.POPUP.DIRECTIONS.RIGHT:
            self.x, self.y = (MainWindow.main_window.width - WINDOWS.SIDE.WIDTH) / 2, 0
        elif direction == WINDOWS.POPUP.DIRECTIONS.LEFT:
            self.x, self.y = 0, 0

        self._pinned_directions = {direction}

    def make_quarter_screen(self, directions):
        """
        Set the size and location of the window to be exactly a quarter of the screen
        :param directions: What quarter of the screen should that be. A `set` of two directions. Like: {'right', 'up'}
        """
        if len(directions) != 2:
            raise WrongUsageError(f"must supply at exactly two directions in order to make quarter screen! supplied directions: {directions}")

        self.resize((MainWindow.main_window.width - WINDOWS.SIDE.WIDTH) / 2,
                    (MainWindow.main_window.height / 2) - WINDOWS.POPUP.TEXTBOX.UPPER_PART_HEIGHT)

        if WINDOWS.POPUP.DIRECTIONS.RIGHT in directions:
            self.x = (MainWindow.main_window.width - WINDOWS.SIDE.WIDTH) / 2
        elif WINDOWS.POPUP.DIRECTIONS.LEFT in directions:
            self.x = 0

        if WINDOWS.POPUP.DIRECTIONS.UP in directions:
            self.y = MainWindow.main_window.height / 2
        elif WINDOWS.POPUP.DIRECTIONS.DOWN in directions:
            self.y = 0

        self._pinned_directions = directions

    def make_like_before_pinned(self):
        """
        Set the size and location of the window to be just like before the window was pinned
        """
        self.x, self.y = self._x_before_pinning, self._y_before_pinning
        self.resize(*self._size_before_pinning)
        self._pinned_directions = set()

    def __str__(self):
        return f"PopupWindow(title='{self.child_graphics_objects[0].text}')"
