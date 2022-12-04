from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Set, Tuple, Sequence, cast

from NetSym.consts import WINDOWS, T_Color, COLORS, SHAPES, debugp
from NetSym.exceptions import *
from NetSym.exceptions import WrongUsageError
from NetSym.gui.abstracts.user_interface_graphics_object import UserInterfaceGraphicsObject
from NetSym.gui.main_loop import MainLoop
from NetSym.gui.shape_drawing import draw_rectangle
from NetSym.gui.user_interface.button import Button
from NetSym.gui.user_interface.text_graphics import Text

if TYPE_CHECKING:
    from NetSym.gui.user_interface.user_interface import UserInterface


class PopupWindow(UserInterfaceGraphicsObject):
    """
    A window that pops up sometime.
    It can contain buttons, text and maybe images?
    """

    def __init__(self,
                 x: float,
                 y: float,
                 buttons: Optional[Sequence[Button]] = None,
                 width: float = WINDOWS.POPUP.TEXTBOX.WIDTH,
                 height: float = WINDOWS.POPUP.TEXTBOX.HEIGHT,
                 color: T_Color = WINDOWS.POPUP.TEXTBOX.OUTLINE_COLOR,
                 title: str = "window!",
                 outline_width: float = SHAPES.RECT.DEFAULT_OUTLINE_WIDTH) -> None:
        """
        Initiates the `PopupWindow` object.
        :param x, y: the location of the bottom left corner of the window
        :param buttons: a list of buttons that will be displayed on this window. The `X` button is not included.
        """
        super(PopupWindow, self).__init__(x, y)
        button_list = list(buttons) if buttons is not None else []

        self.width, self.height = width, height
        self.__is_active = False
        self.outline_color = color
        self.outline_width = outline_width
        self.creation_time = MainLoop.get_time()

        self.title_text = Text(
            title,
            self.x, self.y,
            self,
            self.get_title_text_padding(),
            color=COLORS.BLACK,
            align='left',
            max_width=self.width
        )

        for button in button_list:
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

        self.child_graphics_objects = [
            self.title_text,
            self.exit_button,
            *button_list,
        ]

        self.buttons = [self.exit_button] + button_list

        self._x_before_pinning: Optional[float] = None
        self._y_before_pinning: Optional[float] = None
        self._size_before_pinning = self.width, self.height
        self._pinned_directions: Set[str] = set()

        self.unregister_this_window_from_user_interface = False

    @property
    def location(self) -> Tuple[float, float]:
        return self.x, self.y

    @location.setter
    def location(self, value: Tuple[float, float]) -> None:
        # this is the way the `UserInterface` moves the `selected_object`
        self.x, self.y = value
        self._x_before_pinning, self._y_before_pinning = value
        self._pinned_directions = set()
        self._size_before_pinning = self.width, self.height

    @property
    def is_pinned(self) -> bool:
        return bool(self._pinned_directions)

    def get_exit_button_padding(self) -> Tuple[float, float]:
        return self.width - WINDOWS.POPUP.TEXTBOX.UPPER_PART_HEIGHT, self.height

    def get_title_text_padding(self) -> Tuple[float, float]:
        return (self.width / 2) + 2, self.height + 22

    def is_in(self, x: float, y: float) -> bool:
        """
        Returns whether or not the mouse is pressing the upper part of the window (where it can be moved)
        :return: `bool`
        """
        return self.x < x < self.x + self.width and \
               self.y < y < self.y + self.height + WINDOWS.POPUP.TEXTBOX.UPPER_PART_HEIGHT

    def delete(self, user_interface: Optional[UserInterface] = None) -> None:
        """
        Deletes the window and removes it from the UserInterface.popup_windows list
        :return: None
        """
        super(PopupWindow, self).delete(user_interface)
        self.unregister_this_window_from_user_interface = True

    def draw(self) -> None:
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

    def drag(self, mouse_x: float, mouse_y: float, drag_x: float, drag_y: float) -> None:
        """
        Dragging the window around
        """
        debugp(f"calling :)")

    def activate(self) -> None:
        """
        Marks the window as activated
        :return:
        """
        self.exit_button.color = self.outline_color
        self.__is_active = True

    def deactivate(self) -> None:
        """
        Marks the window as deactivated
        :return:
        """
        self.exit_button.color = WINDOWS.POPUP.DEACTIVATED_COLOR
        self.__is_active = False

    def resize(self, width: float, height: float) -> None:
        self.width, self.height = width, height
        self.exit_button.padding = self.get_exit_button_padding()
        self.title_text.resize(self.get_title_text_padding(), width)

    def pin_to(self, direction: str, screen_width: float, screen_height: float) -> None:
        """
        Pin the window to one side like the effect windows has when you press Winkey+arrow
        :param screen_height:
        :param screen_width:
        :param direction: one of `WINDOWS.POPUP.DIRECTIONS`
        """
        if not self.is_pinned:
            self._x_before_pinning, self._y_before_pinning = self.x, self.y

        right, left, up, down = WINDOWS.POPUP.DIRECTIONS.RIGHT, WINDOWS.POPUP.DIRECTIONS.LEFT, \
                                WINDOWS.POPUP.DIRECTIONS.UP, WINDOWS.POPUP.DIRECTIONS.DOWN
        pinned_directions = self._pinned_directions

        if direction == up:
            if not self.is_pinned or up in pinned_directions:
                self.maximize(screen_width, screen_height)
            elif {left, right} & pinned_directions:
                sideways_direction, = {left, right} & pinned_directions
                if down in pinned_directions:
                    self.make_split_screen(sideways_direction, screen_width, screen_height)
                else:
                    self.make_quarter_screen({up, sideways_direction}, screen_width, screen_height)

        elif direction == down:
            if {left, right} & pinned_directions:
                sideways_direction, = {left, right} & pinned_directions
                if up in pinned_directions:
                    self.make_split_screen(sideways_direction, screen_width, screen_height)
                else:
                    self.make_quarter_screen({down, sideways_direction}, screen_width, screen_height)
            elif up in pinned_directions:
                self.make_like_before_pinned()

        elif direction in [left, right]:
            if not self.is_pinned or pinned_directions == {up}:
                self.make_split_screen(direction, screen_width, screen_height)
            elif ({left, right} & pinned_directions) and (direction not in pinned_directions):
                if {up, down} & pinned_directions:
                    sideways_direction, = {left, right} & pinned_directions
                    rightways_direction, = {up, down} & pinned_directions
                    self.make_quarter_screen({WINDOWS.POPUP.DIRECTIONS.OPPOSITE[sideways_direction], rightways_direction},
                                             screen_width, screen_height)
                else:
                    self.make_like_before_pinned()

    def maximize(self, screen_width: float, screen_height: float) -> None:
        """
        Make the window the size of the whole screen
        """
        self.x, self.y = 0, 0
        self.resize((screen_width - WINDOWS.SIDE.WIDTH), screen_height - WINDOWS.POPUP.TEXTBOX.UPPER_PART_HEIGHT)
        self._pinned_directions = {WINDOWS.POPUP.DIRECTIONS.UP}

    def make_split_screen(self, direction: str, screen_width: float, screen_height: float) -> None:
        """
        Set the size and location of the window to be exactly half of the screen
        :param screen_width:
        :param screen_height:
        :param direction: What half of the screen should that be 'right' or 'left'
        """
        if direction not in [WINDOWS.POPUP.DIRECTIONS.RIGHT, WINDOWS.POPUP.DIRECTIONS.LEFT]:
            raise WrongUsageError(f"direction must be either right or left not '{direction}'!")

        self.resize((screen_width - WINDOWS.SIDE.WIDTH) / 2,
                     screen_height - WINDOWS.POPUP.TEXTBOX.UPPER_PART_HEIGHT)

        if direction == WINDOWS.POPUP.DIRECTIONS.RIGHT:
            self.x, self.y = (screen_width - WINDOWS.SIDE.WIDTH) / 2, 0
        elif direction == WINDOWS.POPUP.DIRECTIONS.LEFT:
            self.x, self.y = 0, 0

        self._pinned_directions = {direction}

    def make_quarter_screen(self, directions: Set[str], screen_width: float, screen_height: float) -> None:
        """
        Set the size and location of the window to be exactly a quarter of the screen
        :param screen_width:
        :param screen_height:
        :param directions: What quarter of the screen should that be. A `set` of two directions. Like: {'right', 'up'}
        """
        if len(directions) != 2:
            raise WrongUsageError(f"must supply at exactly two directions in order to make quarter screen! supplied directions: {directions}")

        self.resize((screen_width - WINDOWS.SIDE.WIDTH) / 2,
                    (screen_height / 2) - WINDOWS.POPUP.TEXTBOX.UPPER_PART_HEIGHT)

        if WINDOWS.POPUP.DIRECTIONS.RIGHT in directions:
            self.x = (screen_width - WINDOWS.SIDE.WIDTH) / 2
        elif WINDOWS.POPUP.DIRECTIONS.LEFT in directions:
            self.x = 0

        if WINDOWS.POPUP.DIRECTIONS.UP in directions:
            self.y = screen_height / 2
        elif WINDOWS.POPUP.DIRECTIONS.DOWN in directions:
            self.y = 0

        self._pinned_directions = directions

    def make_like_before_pinned(self) -> None:
        """
        Set the size and location of the window to be just like before the window was pinned
        """
        if (self._x_before_pinning is None) or (self._y_before_pinning is None):
            raise SomethingWentTerriblyWrongError("!! Do not call this function if there is no 'before pinned'....")

        self.x, self.y = self._x_before_pinning, self._y_before_pinning
        self.resize(*self._size_before_pinning)
        self._pinned_directions = set()

    def __repr__(self) -> str:
        return f"""<< PopupWindow(title='{cast(Text, self.child_graphics_objects[0]).text}') >>"""
