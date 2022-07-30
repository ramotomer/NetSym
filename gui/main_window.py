import pyWinhook
import pyglet

from consts import *
from gui.main_loop import MainLoop
from usefuls.funcs import normal_color_to_weird_gl_color
from usefuls.paths import add_path_basename_if_needed


class MainWindow(pyglet.window.Window):
    """
    This is a class that contains the state and methods of our main window of the program.
    It inherits from the pyglet `Window` class.

    There is also only one `MainWindow` object, so there is one class variable, `main_window` which is the instance of
    the `MainWindow`. That way, it is accessible from everywhere in the project.

    This class is in charge of giving us access to pyglet's keyboard, mouse and window options.
    """

    main_window = None

    def __init__(self, user_interface, *args, **kwargs):
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

        self.user_interface = user_interface

        self.previous_width = self.width
        self.previous_height = self.height

        try:
            self.set_icon(pyglet.image.load(add_path_basename_if_needed(DIRECTORIES.IMAGES, IMAGES.PACKETS.ICMP.REQUEST)))
        except FileNotFoundError:
            print("ERROR: could not find icon image :( No window icon set :(")

        pyglet.gl.glClearColor(*normal_color_to_weird_gl_color(WINDOWS.MAIN.BACKGROUND))

        # v  allows ignoring the Winkey and Alt+tab keys...
        self._keyboard_hook_manager = pyWinhook.HookManager()
        self._keyboard_hook_manager.KeyDown = self.block_keyboard_escape_keys
        self.set_is_ignoring_keyboard_escape_keys(True)

    @staticmethod
    def block_keyboard_escape_keys(event):
        if event.Key.lower() in ['lwin', 'tab']:
            return False  # block these keys
        return True
        # ^ return True to pass the event to other handlers

    def set_is_ignoring_keyboard_escape_keys(self, value):
        """
        :param value: Whether or not to swallow special keyboard shortcuts passed (winkey, alt+tab...)
        """
        if value and not self._keyboard_hook_manager.keyboard_hook:
            self._keyboard_hook_manager.HookKeyboard()
        elif not value and self._keyboard_hook_manager.keyboard_hook:
            self._keyboard_hook_manager.UnhookKeyboard()

    @property
    def location(self):
        return self.width, self.height

    @property
    def center(self):
        return self.width / 2 - WINDOWS.SIDE.WIDTH, self.height / 2

    def get_mouse_location(self):
        """Return the mouse's location as a tuple"""
        return self.mouse_x, self.mouse_y

    def button_location_by_index(self, button_index):
        """
        Decides the location of the buttons by the index of the button in the button list.
        :param button_index: `int`
        :return:
        """
        return (self.width - WINDOWS.SIDE.WIDTH + 20), \
               (self.height - 90 - (button_index * (BUTTONS.DEFAULT_HEIGHT + BUTTONS.Y_GAP)))

    def on_mouse_motion(self, x, y, dx, dy):
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

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
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

    def on_mouse_enter(self, x, y):
        """
        This method is called when the mouse enters the frame.
        Updates the coordinates of the mouse that this class holds.
        :param x:
        :param y:
        :return:
        """
        self.mouse_x, self.mouse_y = x, y

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
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

    def on_mouse_press(self, x, y, button, modifiers):
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

    def on_mouse_release(self, x, y, button, modifiers):
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

    def on_key_press(self, symbol, modifiers):
        """
        This method is called when any key is pressed on the keyboard.
        :param symbol: The key itself.
        :param modifiers:  additional keys that are pressed (ctrl, shift, caps lock, etc..)
        :return:  None
        """
        debugp(F"calling on key pressed :) {symbol} {modifiers}")
        self.user_interface.on_key_pressed(symbol, modifiers)

    def _on_resize(self):
        """
        The original on_resize does not work, so i wrote one of my own...
        :return:
        """
        self.user_interface.set_mode(MODES.NORMAL)
        self.previous_width = self.width
        self.previous_height = self.height

    def on_draw(self):
        """
        This method is called every tick of the clock and it is what really calls the main loop.
        The try and except here are because pyglet likes catching certain exceptions and it makes debugging practically
        impossible.
        """
        MainLoop.instance.main_loop()

        if self.width != self.previous_width or self.height != self.previous_height:
            self._on_resize()  # `on_resize` does not work, I wrote `_on_resize` instead.

    def on_activate(self):
        """
        Called when the `MainWindow` is activated
        """
        self.set_is_ignoring_keyboard_escape_keys(True)

    def on_deactivate(self):
        """
        Called when the `MainWindow` is deactivated
        """
        self.set_is_ignoring_keyboard_escape_keys(False)

    def update(self, time_interval):
        """
        This function updates the program every time the clock ticks, about 60
        times a second.
        Currently it exists because `pyglet` is a stupid module.
        :param time_interval: The time since the last update
        :return: None
        """
        pass
