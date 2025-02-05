from __future__ import annotations

from functools import reduce
from operator import ior as binary_or
from typing import TYPE_CHECKING, Tuple, Any, Set

import pyWinhook
import pyglet

from NetSym.consts import KEYBOARD, WINDOWS, IMAGES, DIRECTORIES, BUTTONS, T_Time, T_PressedKey
from NetSym.usefuls.funcs import normal_color_to_weird_gl_color
from NetSym.usefuls.paths import add_path_basename_if_needed

if TYPE_CHECKING:
    pass


class MainWindow(pyglet.window.Window):
    """
    This is a class that contains the state and methods of our main window of the program.
    It inherits from the pyglet `Window` class.

    There is also only one `MainWindow` object, so there is one class variable, `main_window` which is the instance of
    the `MainWindow`. That way, it is accessible from everywhere in the project.

    This class is in charge of giving us access to pyglet's keyboard, mouse and window options.
    """

    main_window = None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initiates the MainWindow object. opens the window.
        It receives a `UserInterface` object that is in charge of the user input and output of the program.
        """
        super().__init__(*args, **kwargs)

        self.set_location(*WINDOWS.MAIN.INITIAL_LOCATION)
        # ^ window initial location on the screen

        self.mouse_x, self.mouse_y = WINDOWS.MAIN.WIDTH / 2, WINDOWS.MAIN.HEIGHT / 2
        self.mouse_pressed = False
        self.pressed_keys: Set[T_PressedKey] = set()
        self.should_exit = False

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
        """
        Return the currently pressed keys that affect other keys (they are called modifiers - shift, ctrl, alt, etc...)
        :return: a bitmap of the modifiers according to the bits in `KEYBOARD.MODIFIERS`
        """
        no_modifier = KEYBOARD.MODIFIERS.NONE
        return reduce(binary_or, [KEYBOARD.MODIFIERS.KEY_TO_MODIFIER.get(key, no_modifier) for key in self.pressed_keys], no_modifier)

    def block_keyboard_escape_keys(self, event: pyWinhook.HookManager.KeyboardEvent) -> bool:
        """
        This function is a new handler we write. It is set to handle the event of pressing down a key.
        We tell it - if the pressed key is one we want to ignore - ignore it.
        """
        for pywinhook_key, (pyglet_key, _) in self._ignored_keys.items():
            # pywinhook is the library we use for trapping the winkey and pyglet we use for everything else
            if event.Key.lower() == pywinhook_key:
                self.pressed_keys.add(pyglet_key)
                self.on_key_press(pyglet_key, self._active_keyboard_modifiers, is_manually_called=True)
                return WINDOWS.MAIN.KEY_HOOKS.BLOCK_KEY

        return WINDOWS.MAIN.KEY_HOOKS.PASS_KEY_TO_OTHER_HANDLERS

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
        return bool(self._keyboard_hook_manager.keyboard_hook)

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

    def normalize_keyboard_modifiers(self, modifiers: int) -> int:
        """
        Takes in some keyboard modifiers given from pyglet (maybe from a handled event)
        Returns the modifiers we actually CARE about (with winkey and without capslock)
        """
        return (modifiers | self._active_keyboard_modifiers) & (~KEYBOARD.MODIFIERS.NUMLOCK)

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        self.mouse_x, self.mouse_y = x, y

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.mouse_x, self.mouse_y = x, y

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int) -> None:
        self.mouse_pressed = True

    def on_mouse_release(self, x: float, y: float, button: int, modifiers: int) -> None:
        self.mouse_pressed = False

    def on_key_press(self, symbol: int, modifiers: int, is_manually_called: bool = False) -> None:
        """
        This method is called when any key is pressed on the keyboard.
        It uses the `pyWinhook` module in order to disable the 'winkey' - so it can be used in the program
        :param symbol: The key itself.
        :param modifiers:  additional keys that are pressed (ctrl, shift, caps lock, etc..)
        :param is_manually_called:
        """
        if any(symbol == other_symbol for other_symbol, _ in self._ignored_keys.values()) and not is_manually_called:
            # Due to the way pyWinhook works - this actually means the key is released - so we turn off the modifier
            try:
                self.pressed_keys.remove(symbol)
            except KeyError:
                print("weird... key was released but never pressed?")
            return

        self.pressed_keys.add(symbol)

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        """
        This method is called when any key is released on the keyboard.
        :param symbol: The key itself.
        :param modifiers:  additional keys that are pressed (ctrl, shift, caps lock, etc..)
        :return:  None
        """
        try:
            self.pressed_keys.remove(symbol)
        except KeyError:
            print("weird... key was released but never pressed?")

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

    def on_close(self) -> None:
        """
        This is called when the window is closed
        We want the popup message - so we do not want to close immediately
        """
        self.should_exit = True

    def update(self, time_interval: T_Time) -> None:
        """
        This function updates the program every time the clock ticks, about 60
        times a second.

        Currently it exists because `pyglet` is a stupid module.

        The actual main function of the code is `on_draw`

        :param time_interval: The time since the last update
        """
        pass
