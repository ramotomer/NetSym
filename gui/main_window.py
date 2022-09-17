from __future__ import annotations

from functools import reduce
from operator import ior as binary_or
from typing import Tuple, TYPE_CHECKING, Any, Union

import pyWinhook

from consts import *
from gui.main_loop import MainLoop
from usefuls.funcs import normal_color_to_weird_gl_color
from usefuls.paths import add_path_basename_if_needed

if TYPE_CHECKING:
    from gui.user_interface.user_interface import UserInterface


class MainWindow(pyglet.window.Window):
    """
    This is a class that contains the state and methods of our main window of the program.
    It inherits from the pyglet `Window` class.

    There is also only one `MainWindow` object, so there is one class variable, `main_window` which is the instance of
    the `MainWindow`. That way, it is accessible from everywhere in the project.

    This class is in charge of giving us access to pyglet's keyboard, mouse and window options.
    """

    main_window = None

    def __init__(self, user_interface: UserInterface, *args: Any, **kwargs: Any) -> None:
        """
        Initiates the MainWindow object. opens the window.
        It receives a `UserInterface` object that is in charge of the user input and output of the program.
        """
        super().__init__(*args, **kwargs)
        MainWindow.main_window = self

        self.set_location(*WINDOWS.MAIN.INITIAL_LOCATION)
        # ^ window initial location on the screen

        self.mouse_x, self.mouse_y = WINDOWS.MAIN.WIDTH / 2, WINDOWS.MAIN.HEIGHT / 2
        self.mouse_pressed = False
        self.pressed_keys = set()

        self.user_interface = user_interface

        self.previous_width = self.width
        self.previous_height = self.height

        try:
            self.set_icon(pyglet.image.load(add_path_basename_if_needed(DIRECTORIES.IMAGES, IMAGES.PACKETS.ICMP.REQUEST)))
        except FileNotFoundError:
            print("ERROR: could not find icon image :( No window icon set :(")

        pyglet.gl.glClearColor(*normal_color_to_weird_gl_color(WINDOWS.MAIN.BACKGROUND))

        # v  allows ignoring the Winkey and Alt+tab keys...
        self._ignored_keys = {
            'lwin': (pyglet.window.key.LWINDOWS, KEYBOARD.MODIFIERS.WINKEY),
            'tab':  (pyglet.window.key.TAB, KEYBOARD.MODIFIERS.NONE),
        }
        self._keyboard_hook_manager = pyWinhook.HookManager()
        self._keyboard_hook_manager.KeyDown = self.block_keyboard_escape_keys
        self.set_is_ignoring_keyboard_escape_keys(True)

    @property
    def _active_keyboard_modifiers(self) -> int:
        no_modifier = KEYBOARD.MODIFIERS.NONE
        return reduce(binary_or, [KEYBOARD.MODIFIERS.KEY_TO_MODIFIER.get(key, no_modifier) for key in self.pressed_keys], no_modifier)

    def block_keyboard_escape_keys(self, event: pyWinhook.HookManager.KeyboardEvent) -> bool:
        for pywinhook_key, (pyglet_key, _) in self._ignored_keys.items():
            # pywinhook is the library we use for trapping the winkey and pyglet we use for everything else
            if event.Key.lower() == pywinhook_key:
                self.pressed_keys.add(pyglet_key)
                self.on_key_press(pyglet_key, self._active_keyboard_modifiers, is_manually_called=True)
                return False
        return True
        # ^ return True to pass the event to other handlers

    def set_is_ignoring_keyboard_escape_keys(self, value: bool) -> None:
        """
        :param value: Whether or not to swallow special keyboard shortcuts passed (winkey, alt+tab...)
        """
        if value and not self.is_ignoring_keyboard_escape_keys:
            self._keyboard_hook_manager.HookKeyboard()
        elif not value and self.is_ignoring_keyboard_escape_keys:
            self._keyboard_hook_manager.UnhookKeyboard()

    @property
    def is_ignoring_keyboard_escape_keys(self) -> bool:
        return self._keyboard_hook_manager.keyboard_hook

    @property
    def location(self) -> Tuple[float, float]:
        return self.width, self.height

    @property
    def center(self) -> Tuple[float, float]:
        return self.width / 2 - WINDOWS.SIDE.WIDTH, self.height / 2

    def get_mouse_location(self) -> Tuple[float, float]:
        """Return the mouse's location as a tuple"""
        return self.mouse_x, self.mouse_y

    def button_location_by_index(self, button_index: int) -> Tuple[float, float]:
        """
        Decides the location of the buttons by the index of the button in the button list.
        """
        return (self.width - WINDOWS.SIDE.WIDTH + 20), \
               (self.height - 90 - (button_index * (BUTTONS.DEFAULT_HEIGHT + BUTTONS.Y_GAP)))

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        """
        This method is called when the mouse moves.
        Updates the location of the mouse that this class holds.
        :param x:
        :param y:  The coordinates of the mouse
        :param dx:
        :param dy:  The difference from the last location of the mouse
        :return:
        """
        self.mouse_x, self.mouse_y = x, y

    def on_mouse_drag(self, x: float, y: float, dx: float, dy: float, buttons: int, modifiers: int) -> None:
        """
        This is called when the mouse is dragged.
        Updates the coordinates of mouse that this class holds.
        :param x:
        :param y:  The coordinates of the mouse.
        :param dx:
        :param dy:
        :param buttons:
        :param modifiers:
        :return:
        """
        self.mouse_x, self.mouse_y = x, y

    def on_mouse_enter(self, x: float, y: float) -> None:
        """
        This method is called when the mouse enters the frame.
        Updates the coordinates of the mouse that this class holds.
        :param x:
        :param y:
        :return:
        """
        self.mouse_x, self.mouse_y = x, y

    def on_mouse_scroll(self, x: float, y: float, scroll_x: Union[int, float], scroll_y: Union[int, float]) -> None:
        """
        This occurs when the mouse wheel is scrolled.
        :param x:
        :param y: mouse coordinates
        :param scroll_x:
        :param scroll_y:  The amount of scrolls in each direction
        :return: None
        """
        if self.user_interface.is_mouse_in_side_window() and self.user_interface.mode == MODES.VIEW:
            self.user_interface.scroll_view(scroll_y)
        else:
            for obj in self.user_interface.all_marked_objects:
                if obj is not None and hasattr(obj, "resize"):
                    obj.resize(10 * scroll_y, 10 * scroll_y, constrain_proportions=True)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int) -> None:
        """
        called when the mouse is pressed.
        Updates the selected and dragged object.
        Also calls the `on_mouse_press` method in `UserInterface`.
        :param x:
        :param y:  The coordinates of the mouse press.
        :param button: The mouse button.
        :param modifiers:
        :return:
        """
        self.mouse_pressed = True
        self.user_interface.on_mouse_press()  # this should will be last!

    def on_mouse_release(self, x: float, y: float, button: int, modifiers: int) -> None:
        """
        Called the mouse was pressed and now released.
        :param x:
        :param y: The mouses release location.
        :param button: The mouse button.
        :param modifiers:
        :return:
        """
        self.user_interface.on_mouse_release()
        self.mouse_pressed = False
        self.user_interface.dragged_object = None

    def on_key_press(self, symbol: int, modifiers: int, is_manually_called: bool = False) -> None:
        """
        This method is called when any key is pressed on the keyboard.
        :param symbol: The key itself.
        :param modifiers:  additional keys that are pressed (ctrl, shift, caps lock, etc..)
        :param is_manually_called:
        """
        if any(symbol == other_symbol for other_symbol, _ in self._ignored_keys.values()) and not is_manually_called:
            # Due to the way pyWinhook works - this actually means the key is released - so turn off the modifier
            self.pressed_keys.remove(symbol)
            return

        self.pressed_keys.add(symbol)
        self.user_interface.on_key_pressed(symbol, modifiers | self._active_keyboard_modifiers)

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        """
        This method is called when any key is released on the keyboard.
        :param symbol: The key itself.
        :param modifiers:  additional keys that are pressed (ctrl, shift, caps lock, etc..)
        :return:  None
        """
        self.pressed_keys.remove(symbol)

    def _on_resize(self) -> None:
        """
        The original on_resize does not work, so i wrote one of my own...
        :return:
        """
        self.user_interface.set_mode(MODES.NORMAL)
        self.previous_width = self.width
        self.previous_height = self.height

    def on_draw(self) -> None:
        """
        This method is called every tick of the clock and it is what really calls the main loop.
        The try and except here are because pyglet likes catching certain exceptions and it makes debugging practically
        impossible.
        """
        MainLoop.instance.main_loop()

        if self.width != self.previous_width or self.height != self.previous_height:
            self._on_resize()  # `on_resize` does not work, I wrote `_on_resize` instead.

    def on_activate(self) -> None:
        """
        Called when the `MainWindow` is activated
        """
        self.set_is_ignoring_keyboard_escape_keys(True)

    def on_deactivate(self) -> None:
        """
        Called when the `MainWindow` is deactivated
        """
        self.set_is_ignoring_keyboard_escape_keys(False)

    def update(self, time_interval: t_time) -> None:
        """
        This function updates the program every time the clock ticks, about 60
        times a second.
        Currently it exists because `pyglet` is a stupid module.
        :param time_interval: The time since the last update
        :return: None
        """
        pass
