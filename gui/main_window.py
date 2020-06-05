import pyglet

from consts import *
from gui.main_loop import MainLoop


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

        self.set_location(*INITIAL_WINDOW_LOCATION)
        # ^ window initial location on the screen

        self.mouse_x, self.mouse_y = WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2
        self.mouse_pressed = False

        self.user_interface = user_interface

    def get_mouse_location(self):
        """Return the mouse's location as a tuple"""
        return self.mouse_x, self.mouse_y

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
        if self.user_interface.is_mouse_in_side_window() and self.user_interface.mode == VIEW_MODE:
            self.user_interface.scroll_view(scroll_y)

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
        try: # this try and except is done becauese for some reason it is done automatically in pyglet and it is very annoying!!!!!!

            self.mouse_pressed = True
            self._set_mouse_pressed_objects()

            if self.user_interface.selected_object is None and self.user_interface.is_asking_for_string:  # if pressed outside a text-box.
                self.user_interface.end_string_request()

            self.user_interface.on_mouse_press()  # this should will be last!

        except (TypeError, AttributeError) as err:
            print(f"error in `on_mouse_press` {err}")
            raise err

    def _set_mouse_pressed_objects(self):
        """
        Sets the `selected_object` and `dragged_object` according to the mouse's press.
        :return: None
        """
        if not self.user_interface.is_mouse_in_side_window():
            object_the_mouse_is_on = MainLoop.instance.get_object_the_mouse_is_on()

            self.user_interface.dragged_object = object_the_mouse_is_on
            self.user_interface.selected_object = object_the_mouse_is_on

            if object_the_mouse_is_on is not None:
                mouse_x, mouse_y = self.get_mouse_location()
                object_x, object_y = object_the_mouse_is_on.location
                self.user_interface.dragging_point = object_x - mouse_x, object_y - mouse_y

    def on_mouse_release(self, x, y, button, modifiers):
        """
        Called the mouse was pressed and now released.
        :param x:
        :param y: The mouses release location.
        :param button: The mouse button.
        :param modifiers:
        :return:
        """
        self.mouse_pressed = False
        self.user_interface.dragged_object = None

    def on_key_press(self, symbol, modifiers):
        """
        This method is called when any key is pressed on the keyboard.
        :param symbol: The key itself.
        :param modifiers:  additional keys that are pressed (ctrl, shift, caps lock, etc..)
        :return:  None
        """
        self.user_interface.on_key_pressed(symbol, modifiers)

    def on_draw(self):
        """
        This method is called every tick of the clock and it is what really calls the main loop.
        The try and except here are because pyglet likes catching certain exceptions and it makes debugging practically
        impossible.
        """
        try:

            MainLoop.instance.main_loop()

        except (TypeError, AttributeError) as err:
            print(f"exception in on_draw: {err}")
            raise err

    def update(self, time_interval):
        """
        This function updates the program every time the clock ticks, about 60
        times a second.
        Currently it exists because `pyglet` is a stupid module.
        :param time_interval: The time since the last update
        :return: None
        """
        pass
