import functools
import json
import operator
import random
from collections import namedtuple, defaultdict
from functools import reduce
from operator import concat, attrgetter

from pyglet.window import key

from address.ip_address import IPAddress
from computing.computer import Computer
from computing.internals.frequency import Frequency
from computing.internals.interface import Interface
from computing.internals.processes.usermode_processes.daytime_process import DAYTIMEClientProcess
from computing.internals.processes.usermode_processes.stp_process import STPProcess
from computing.internals.wireless_interface import WirelessInterface
from computing.router import Router
from computing.switch import Switch, Hub, Antenna
from consts import *
from exceptions import *
from gui.abstracts.user_interface_graphics_object import UserInterfaceGraphicsObject
from gui.main_loop import MainLoop
from gui.main_window import MainWindow
from gui.shape_drawing import draw_circle, draw_line, draw_tiny_corner_windows_icon
from gui.shape_drawing import draw_pause_rectangles, draw_rectangle
from gui.tech.computer_graphics import ComputerGraphics
from gui.tech.connection_graphics import ConnectionGraphics
from gui.tech.interface_graphics import InterfaceGraphics
from gui.tech.packet_graphics import PacketGraphics
from gui.user_interface.button import Button
from gui.user_interface.popup_windows.device_creation_window import DeviceCreationWindow
from gui.user_interface.popup_windows.popup_console import PopupConsole
from gui.user_interface.popup_windows.popup_error import PopupError
from gui.user_interface.popup_windows.popup_help import PopupHelp
from gui.user_interface.popup_windows.popup_text_box import PopupTextBox
from gui.user_interface.popup_windows.popup_window import PopupWindow
from gui.user_interface.popup_windows.yes_no_popup_window import YesNoPopupWindow
from gui.user_interface.selecting_square import SelectingSquare
from gui.user_interface.text_graphics import Text
from usefuls.funcs import get_the_one, distance, with_args, called_in_order, circular_coordinates, sum_tuples, \
    scale_tuple

ObjectView = namedtuple("ObjectView", [
    "sprite",
    "text",
    "viewed_object",
])
"""
A ip_layer structure to represent the current viewing of a GraphicsObject on the side window in VIEW_MODE
- sprite is the little image that is shown
- text is a `Text` object of the information about the object
- viewed_object is a reference to the GraphicsObject that's viewed. 
"""

ConnectionData = namedtuple("ConnectionData", [
    "connection",
    "computer1",
    "computer2",
])
"""
A way to save the connection on the screen together with the computers they are connected to.
"""


class UserInterface:
    """
    This class constructs the interface the user sees and uses.

    It contains all construction of buttons and of keyboard keys and their actions.
    All of the computers that are created and all packets and connections are all saved and handled in this class,
    since the methods that add and delete them are here.

    The selected and dragged objects (The ones that are surrounded with a white square and are moved by the mouse) are
    also save in this class.

    The `self.mode` variable determines in what mode the user interface is currently in.
    if the mode is `MODES.NORMAL`, the regular menu is presented.
    if the mode is `MODES.CONNECTING` than the two next computers the user will press will become connected.
    the `VIEW_MODE` is when a computer's details are currently is_showing in the side window nicely.
    the `PINGING_MODE` is when we choose two computer to send a ping between.  (purple side window)
    the `DELETING_MODE` is when we delete a graphics object. (Brown side window)

    Only set the mode through the `set_mode` method!!!
    """
    WIDTH = WINDOWS.SIDE.WIDTH  # pixels

    def __init__(self):
        """
        Initiates the UserInterface class!
        `key_to_action` is a dictionary from keys and their modifiers to actions to perform when that key is pressed.
        `button_arguments` is a list of arguments for `Button` objects that will be created after
        the `MainWindow` is initiated.

        """
        self.key_to_action = {
            (key.N, KEYBOARD.MODIFIERS.CTRL): self.create_computer_with_ip,
            (key.N, KEYBOARD.MODIFIERS.CTRL | KEYBOARD.MODIFIERS.SHIFT): with_args(self.create_computer_with_ip, True),
            (key.C, KEYBOARD.MODIFIERS.CTRL): self.smart_connect,
            (key.C, KEYBOARD.MODIFIERS.SHIFT): self.connect_all_to_all,
            (key.P, KEYBOARD.MODIFIERS.CTRL): self.send_random_ping,
            (key.P, KEYBOARD.MODIFIERS.SHIFT): self.send_ping_to_self,
            (key.R, KEYBOARD.MODIFIERS.CTRL): with_args(self.create_device, Router),
            (key.M, KEYBOARD.MODIFIERS.NONE): self.print_debugging_info,
            (key.W, KEYBOARD.MODIFIERS.NONE): self.add_tcp_test,
            (key.Q, KEYBOARD.MODIFIERS.CTRL): self.exit,
            (key.A, KEYBOARD.MODIFIERS.CTRL): self.select_all,
            (key.SPACE, KEYBOARD.MODIFIERS.NONE): self.toggle_pause,
            (key.TAB, KEYBOARD.MODIFIERS.NONE): self.tab_through_selected,
            (key.TAB, KEYBOARD.MODIFIERS.SHIFT): with_args(self.tab_through_selected, True),
            (key.ESCAPE, KEYBOARD.MODIFIERS.NONE): self.clear_selected_objects_and_active_window,
            (key.DELETE, KEYBOARD.MODIFIERS.NONE): self.delete_selected_and_marked,
            (key.J, KEYBOARD.MODIFIERS.NONE): self.color_by_subnets,
            (key.LALT, KEYBOARD.MODIFIERS.CTRL | KEYBOARD.MODIFIERS.ALT): with_args(self.set_is_ignoring_keyboard_escape_keys, False),
            (key.G, KEYBOARD.MODIFIERS.CTRL): with_args(self.set_is_ignoring_keyboard_escape_keys, True),
            (key.TAB, KEYBOARD.MODIFIERS.ALT): self.tab_through_windows,
            (key.TAB, KEYBOARD.MODIFIERS.ALT | KEYBOARD.MODIFIERS.SHIFT): with_args(self.tab_through_windows, True),
            (key.RIGHT, KEYBOARD.MODIFIERS.WINKEY): with_args(self.pin_active_window_to, WINDOWS.POPUP.DIRECTIONS.RIGHT),
            (key.LEFT, KEYBOARD.MODIFIERS.WINKEY): with_args(self.pin_active_window_to, WINDOWS.POPUP.DIRECTIONS.LEFT),
            (key.UP, KEYBOARD.MODIFIERS.WINKEY): with_args(self.pin_active_window_to, WINDOWS.POPUP.DIRECTIONS.UP),
            (key.DOWN, KEYBOARD.MODIFIERS.WINKEY): with_args(self.pin_active_window_to, WINDOWS.POPUP.DIRECTIONS.DOWN),
        }

        for direction in {key.UP, key.RIGHT, key.LEFT, key.DOWN}:
            self.key_to_action[(direction, KEYBOARD.MODIFIERS.NONE)] = with_args(
                self.move_selected_mark,
                direction,
            )
            self.key_to_action[(direction, KEYBOARD.MODIFIERS.CTRL)] = with_args(
                self.move_selected_object,
                direction,
            )
            self.key_to_action[(direction, KEYBOARD.MODIFIERS.CTRL | KEYBOARD.MODIFIERS.SHIFT)] = with_args(
                self.move_selected_object,
                direction,
                SELECTED_OBJECT.SMALL_STEP_SIZE,
            )
            self.key_to_action[(direction, KEYBOARD.MODIFIERS.CTRL | KEYBOARD.MODIFIERS.ALT)] = with_args(
                self.move_selected_object,
                direction,
                SELECTED_OBJECT.BIG_STEP_SIZE,
            )

        for device, (_, key_string) in DeviceCreationWindow.DEVICE_TO_IMAGE.items():
            self.key_to_action[self.key_from_string(key_string)] = with_args(self.create_device, device)

        self.action_at_press_by_mode = {
            MODES.NORMAL: self.normal_mode_at_press,
            MODES.VIEW: self.normal_mode_at_press,
            MODES.CONNECTING: self.start_device_visual_connecting,
            MODES.PINGING: self.start_device_visual_connecting,
        }
        # ^ maps what to do when the screen is pressed in each `mode`.

        self.saving_file_class_name_to_class = {
            class_.__name__: class_ for class_ in (Computer, Switch, Router, Hub, Antenna)
        }

        self.computers = []
        self.connection_data = []
        # ^ a list of `ConnectionData`-s (save information about all existing connections between computers.
        self.frequencies = []  # a list of all Frequency objects that exist in the simulation!

        self.mode = MODES.NORMAL
        self.source_of_line_drag = None
        # ^ used if two items are selected one after the other for some purpose (connecting mode, pinging mode etc)

        self.dragged_object = None
        # ^ the object that is currently being dragged (by the courser)

        self.object_view = None
        # ^ the `ObjectView` object that is currently is_showing in the side window.

        self.popup_windows = []
        self.__active_window = None

        self.button_arguments = [
            ((with_args(DeviceCreationWindow, self), "create device (e)"), {"key": (key.E, KEYBOARD.MODIFIERS.NONE)}),
            ((with_args(self.toggle_mode, MODES.CONNECTING), "connect (c / ^c / Shift+c)"), {"key": (key.C, KEYBOARD.MODIFIERS.NONE)}),
            ((with_args(self.toggle_mode, MODES.PINGING), "ping (p / ^p / Shift+p)"), {"key": (key.P, KEYBOARD.MODIFIERS.NONE)}),
            ((self.ask_for_dhcp, "ask for DHCP (shift+a)"), {"key": (key.A, KEYBOARD.MODIFIERS.SHIFT)}),
            ((self.start_all_stp, "start STP (ctrl+shift+s)"), {"key": (key.S, KEYBOARD.MODIFIERS.CTRL | KEYBOARD.MODIFIERS.SHIFT)}),
            ((self.delete_all_packets, "delete all packets (Shift+d)"), {"key": (key.D, KEYBOARD.MODIFIERS.SHIFT)}),
            ((self.delete_all, "delete all (^d)"), {"key": (key.D, KEYBOARD.MODIFIERS.CTRL)}),
            ((with_args(self.ask_user_for, str, "save file as:", self._save_to_file_with_override_safety), "save to file(^s)"),
             {"key": (key.S, KEYBOARD.MODIFIERS.CTRL)}),
            # TODO: saving to files does not work :(
            ((self._ask_user_for_load_file, "load from file (^o)"), {"key": (key.O, KEYBOARD.MODIFIERS.CTRL)}),
            ((self.open_help, "help (shift+/)"), {"key": (key.SLASH, KEYBOARD.MODIFIERS.SHIFT)}),
        ]
        self.buttons = {}
        # ^ a dictionary in the form, {button_id: [list of `Button` objects]}
        self.showing_buttons_id = BUTTONS.MAIN_MENU.ID
        self.scrolled_view = None
        self.debug_counter = 0

        self.selecting_square = None

        self.marked_objects = []
        self.dragging_points = defaultdict(lambda: (None, None))

        self.__selected_object = None
        # ^ the object that is currently dragged
        self.selected_object = None

    @property
    def all_marked_objects(self):
        """
        The `marked_objects` list with the selected_object together in one list
        :return:
        """
        if self.selected_object in self.marked_objects:
            return self.marked_objects
        return self.marked_objects + ([self.selected_object] if self.selected_object is not None else [])

    @property
    def active_window(self):
        return self.__active_window

    @active_window.setter
    def active_window(self, window):
        if self.active_window is not None:
            self.active_window.deactivate()

        if window is not None:
            window.activate()
        self.__active_window = window

        if MainLoop.instance is not None and window is not None:
            MainLoop.instance.move_to_front(window)

    @property
    def selected_object(self):
        return self.__selected_object

    @selected_object.setter
    def selected_object(self, graphics_object):
        if isinstance(graphics_object, PopupWindow):
            self.active_window = graphics_object
        else:
            self.__selected_object = graphics_object
            self.active_window = None

    @staticmethod
    def set_is_ignoring_keyboard_escape_keys(value):
        """
        :param value: Whether or not to swallow special keyboard shortcuts passed (winkey, alt+tab...)

            This must be a separate method because inside this class's __init__ method the `MainWindow.main_window` object is still `None`
        """
        MainWindow.main_window.set_is_ignoring_keyboard_escape_keys(value)

    def show(self):
        """
        This is like the `draw` method of GraphicObject`s.
        :return: None
        """
        self._draw_side_window()
        if MainLoop.instance.is_paused:
            draw_pause_rectangles()
        if MainWindow.main_window.is_ignoring_keyboard_escape_keys:
            draw_tiny_corner_windows_icon()
        self.drag_objects()
        self._stop_viewing_dead_packets()
        self._showcase_running_stp()

        if self.mode == MODES.CONNECTING:
            self._draw_connection_to_mouse(CONNECTIONS.COLOR)
        elif self.mode == MODES.PINGING:
            self._draw_connection_to_mouse(COLORS.PURPLE)

    def _draw_connection_to_mouse(self, color):
        """
        This draws the connection while connecting two computers in connecting mode.
        (when they are not connected yet...)
        :return:
        """
        if self.source_of_line_drag is None:
            return

        draw_line(self.source_of_line_drag.location, MainWindow.main_window.get_mouse_location(), color=color)
        self.source_of_line_drag.mark_as_selected_non_resizable()

        destination = MainLoop.instance.get_object_the_mouse_is_on()
        if destination is not None:
            destination.mark_as_selected_non_resizable()

    def _stop_viewing_dead_packets(self):
        """
        Checks if a packet that is currently viewed has left the screen (reached the destination or dropped) and if so
        stops viewing it.
        :return:
        """
        if self.selected_object is not None and \
                self.selected_object.is_packet and \
                self.packet_from_graphics_object(self.selected_object) is None:
            self.set_mode(MODES.NORMAL)

    def _draw_side_window(self):
        """
        Draws the side window
        :return:
        """
        draw_rectangle(MainWindow.main_window.width - self.WIDTH, 0, self.WIDTH, MainWindow.main_window.height,
                       color=MODES.TO_COLORS[self.mode])

    def drag_objects(self):
        """
        Drags the object that should be dragged around the screen.
        Essentially sets the objects coordinates to be the ones of the mouse.
        :return: None
        """
        if self.selecting_square is not None:
            return
        dragging_objects = self.marked_objects + ([self.dragged_object] if self.dragged_object is not None else [])
        for object_ in dragging_objects:
            if not isinstance(object_, Button):
                drag_x, drag_y = self.dragging_points[object_]
                if drag_x is None:
                    continue
                mouse_x, mouse_y = MainWindow.main_window.get_mouse_location()
                object_.location = mouse_x + drag_x, mouse_y + drag_y

    @property
    def viewing_image_location(self):
        x = (MainWindow.main_window.width - (WINDOWS.SIDE.WIDTH / 2)) - (IMAGES.SIZE * IMAGES.SCALE_FACTORS.VIEWING_OBJECTS / 2)
        y = MainWindow.main_window.height - ((IMAGES.SIZE * IMAGES.SCALE_FACTORS.VIEWING_OBJECTS) + 15)
        return x, y

    @property
    def viewing_text_location(self):
        return (MainWindow.main_window.width - (WINDOWS.SIDE.WIDTH / 2)), \
               self.viewing_image_location[1] + VIEW.TEXT_PADDING

    def start_object_view(self, graphics_object):
        """
        Starts viewing an object on the side window.
        Creates an `ObjectView` namedtuple which packs together the ip_layer required to view an object.
        :param graphics_object: A graphics object to view.
        :return: None
        """
        self.scrolled_view = 0

        sprite, text, buttons_id = graphics_object.start_viewing(self)
        if sprite is not None:
            sprite.update(*self.viewing_image_location,
                          scale_x=VIEW.IMAGE_SIZE / sprite.image.width,
                          scale_y=VIEW.IMAGE_SIZE / sprite.image.height)
            MainLoop.instance.insert_to_loop(sprite.draw)

            if graphics_object.is_packet:
                text = self.packet_from_graphics_object(graphics_object).multiline_repr()

        x, y = self.viewing_text_location
        self.object_view = ObjectView(
            sprite,
            Text(
                text, x, y,
                max_width=(WINDOWS.SIDE.WIDTH - WINDOWS.SIDE.VIEWING_OBJECT.TEXT.PADDING[0]),
                align=TEXT.ALIGN.LEFT,
                padding=WINDOWS.SIDE.VIEWING_OBJECT.TEXT.PADDING
            ),
            graphics_object,
        )
        self.adjust_viewed_text_to_buttons(buttons_id + 1)

    def adjust_viewed_text_to_buttons(self, buttons_id):
        """
        This is called when the buttons of the viewed object are changed.
        The location of the viewed text is changed according to it.
        :return:
        """
        if self.object_view is None:
            raise WrongUsageError("Only call this in VIEW MODE")

        try:
            self.object_view.text.y = self.viewing_text_location[1] - \
                                      ((len(self.buttons[buttons_id]) + 0.5) *
                                       (BUTTONS.DEFAULT_HEIGHT + BUTTONS.Y_GAP)) - self.scrolled_view
        except KeyError:
            pass

    def end_object_view(self):
        """
        Removes the text object from the loop and ends the viewing of an object in the side window.
        if no object was viewed, does nothing.
        """
        if self.object_view is not None:
            self.object_view.viewed_object.end_viewing(self)
            MainLoop.instance.unregister_graphics_object(self.object_view.text)
            if self.object_view.sprite is not None:  # if the viewed graphics object is an image graphics object.
                MainLoop.instance.remove_from_loop(self.object_view.sprite.draw)

            if isinstance(self.object_view.viewed_object, ComputerGraphics):
                self.object_view.viewed_object.child_graphics_objects.console.hide()

            self.object_view = None
            self.scrolled_view = None

    def scroll_view(self, scroll_count):
        """
        Scrolls through the view of an object if it is too long to view all at once.
        This is called when the mouse wheel is scrolled.
        :return: None
        """
        if self.object_view is None:
            raise SomethingWentTerriblyWrongError(
                "Not supposed to get here!!! In MODES.VIEW the `self.object_view` is never None"
            )

        sprite, text_graphics, viewed_object = self.object_view
        if scroll_count < 0 or self.scrolled_view <= -scroll_count * VIEW.PIXELS_PER_SCROLL:
            self.scrolled_view += scroll_count * VIEW.PIXELS_PER_SCROLL

            sprite.y = self.viewing_image_location[1] - self.scrolled_view
            self.adjust_viewed_text_to_buttons(self.showing_buttons_id)

            for buttons_id in self.buttons:
                for button in self.buttons[buttons_id]:
                    if not button.is_hidden:
                        button.y = button.initial_location[1] - self.scrolled_view

    def initiate_buttons(self):
        """
        Initiates the buttons in the window.
        This does not happen in init because when init is called here
        `MainWindow.main_window` is still uninitiated so it cannot register the graphics objects of the buttons.
        :return: None
        """
        self.buttons[BUTTONS.MAIN_MENU.ID] = [
            Button(
                *MainWindow.main_window.button_location_by_index(i - 1),
                *args,
                **kwargs,
            ) for i, (args, kwargs) in enumerate(self.button_arguments)
        ]

        for i, button in enumerate(self.buttons[BUTTONS.MAIN_MENU.ID]):
            x, y = MainWindow.main_window.button_location_by_index(i - 1)
            padding = x - WINDOWS.MAIN.WIDTH, y - WINDOWS.MAIN.HEIGHT
            button.set_parent_graphics(MainWindow.main_window, padding)

    def tab_through_windows(self, reverse=False):
        """

        :param reverse:
        :return:
        """
        available_windows = sorted(list(filter(lambda o: isinstance(o, PopupWindow), MainLoop.instance.graphics_objects)),
                                   key=lambda w: w.creation_time)
        if not available_windows:
            return
        if reverse:
            available_windows = list(reversed(available_windows))

        try:
            index = available_windows.index(self.active_window)
            self.active_window = available_windows[index - 1]
        except ValueError:
            self.active_window = available_windows[-1]

    def tab_through_selected(self, reverse=False):
        """
        This is called when the TAB key is pressed.
        It goes through the graphics objects one by one and selects them.
        Allows working without the mouse when there are not a lot of objects on the screen
        :return:
        """
        available_graphics_objects = [object_ for object_ in MainLoop.instance.graphics_objects
                                      if object_.is_pressable and object_.can_be_viewed]
        if not available_graphics_objects:
            return
        if reverse:
            available_graphics_objects = list(reversed(available_graphics_objects))

        try:
            index = available_graphics_objects.index(self.selected_object)
            self.selected_object = available_graphics_objects[index - 1]
        except ValueError:
            self.selected_object = available_graphics_objects[-1]

        self.set_mode(MODES.VIEW)

    def set_mode(self, new_mode):
        """
        This is the correct way to set the `self.new_mode` trait of the side window.
        it handles all of the things one needs to do when switching between different modes.
        (especially VIEW_MODE)
        :return: None
        """
        if self.mode == MODES.CONNECTING and new_mode != MODES.CONNECTING:
            self.source_of_line_drag = None

        if new_mode == MODES.VIEW:
            self.end_object_view()
            self.mode = new_mode
            self.hide_buttons(BUTTONS.MAIN_MENU.ID)
            if not self.selected_object.can_be_viewed:
                raise WrongUsageError(
                    "The new_mode should not be switched to view new_mode when the selected object cannot be viewed"
                )
            self.start_object_view(self.selected_object)

        else:  # new_mode == MODES.NORMAL
            self.source_of_line_drag = None
            self.mode = new_mode
            self.end_object_view()
            if self.selected_object is not None:
                self.selected_object = None
            self.show_buttons(BUTTONS.MAIN_MENU.ID)
            self.marked_objects.clear()

    def clear_selected_objects_and_active_window(self):
        if self.selected_object is not None:
            self.selected_object = None
        self.marked_objects.clear()
        self.active_window = None

    def toggle_mode(self, mode):
        """
        Toggles to and from a mode!
        If the mode is already the `mode` given, switch to `MODES.NORMAL`.
        :param mode: a mode to toggle to and from (MODES.NORMAL, MODES.CONNECTING, etc...)
        :return: None
        """
        if self.mode == mode:
            self.set_mode(MODES.NORMAL)
        else:
            self.set_mode(mode)

    @staticmethod
    def toggle_pause():
        """
        Toggling from pause back and fourth.
        This is done because when the keys are paired in the __init__ method `MainLoop.instance` is not yet initiated
        :return: None
        """
        MainLoop.instance.toggle_pause()

    def on_mouse_press(self):
        """
        Happens when the mouse is pressed.
        Decides what to do according to the mode we are now in.
        The choosing of a selected and dragged objects should be performed BEFORE this is called!
        :return: None
        """
        for button in reversed(reduce(concat, list(self.buttons.values()))):
            if not button.is_hidden and button.is_mouse_in():
                button.action()
                break
        else:
            self.action_at_press_by_mode[self.mode]()

        if self.active_window is None:
            self._create_selecting_square()

    def pin_active_window_to(self, direction):
        """

        :param direction:
        :return:
        """
        if self.active_window is not None:
            self.active_window.pin_to(direction)

    def _create_selecting_square(self):
        """
        Creates the selection square when the mouse is pressed and dragged around
        :return:
        """
        if self.mode == MODES.NORMAL:
            self.selecting_square = SelectingSquare(
                *MainWindow.main_window.get_mouse_location(),
                MainLoop.instance.graphics_objects_of_types(ComputerGraphics, PacketGraphics),
                self,
            )

    def on_mouse_release(self):
        """
        this is called when the mouse is released
        :return:
        """
        self.dragging_points.clear()
        if self.selecting_square is not None:
            MainLoop.instance.unregister_graphics_object(self.selecting_square)
            self.selecting_square = None

        elif self.mode == MODES.CONNECTING:
            self.end_device_visual_connecting(self.connect_devices)

        elif self.mode == MODES.PINGING:
            self.end_device_visual_connecting(self.send_direct_ping)

    def on_key_pressed(self, symbol, modifiers):
        """
        Called when a key is pressed
        :param symbol:
        :param modifiers:
        :return:
        """
        modifiers = modifiers & (~KEYBOARD.MODIFIERS.NUMLOCK)

        # if (not modifiers & KEYBOARD.MODIFIERS.WINKEY) and (symbol != key.ESCAPE):
        if isinstance(self.active_window, PopupTextBox):
            if self.active_window.key_writer.pressed(symbol, modifiers):
                return

        if isinstance(self.active_window, PopupConsole):
            if self.active_window.shell.key_writer.pressed(symbol, modifiers):
                return

        modified_key = (symbol, modifiers)
        for button_id in sorted(list(self.buttons)):
            for button in self.buttons[button_id]:
                if button.key == modified_key:
                    button.action()
                    return
        self.key_to_action.get(modified_key, lambda: None)()

    def normal_mode_at_press(self):
        """
        Happens when we are in viewing mode (or simulation mode) and we press our mouse.
        decides whether to start viewing a new graphics object or finish a previous one.
        """
        self.set_mouse_pressed_objects()

        if self.is_mouse_in_side_window():
            return

        if self.selected_object is not None and self.selected_object.can_be_viewed:
            self.set_mode(MODES.VIEW)
        elif self.selected_object is None:
            self.set_mode(MODES.NORMAL)

        # we only get here if an an object that cannot be viewed is pressed - do nothing

    def is_mouse_in_side_window(self):
        """Return whether or not the mouse is currently in the side window."""
        mouse_x, _ = MainWindow.main_window.get_mouse_location()
        return mouse_x > (MainWindow.main_window.width - self.WIDTH)

    def create_device(self, object_type):
        """
        Creates an object from a given type.
        :param object_type: an object type that will be created (Computer, Switch, Hub, etc...)
        :return: None
        """
        x, y = MainWindow.main_window.get_mouse_location()
        if self.is_mouse_in_side_window():
            x, y = WINDOWS.MAIN.WIDTH / 2, WINDOWS.MAIN.HEIGHT / 2

        object_ = object_type()
        object_.show(x, y)
        self.computers.append(object_)

    def two_pressed_objects(self, action, more_pressable_types=None):
        """
        This operates the situation when two things are required to be selected one after the other (like in
        MODES.CONNECTING, MODES.PINGING, etc...)
        Usually allows pressing just ComputerGraphics objects. This can be extended to more types using the
        `more_pressable_types` list.
        :param action: a function that will be activated on the two computers once they are both selected.
            should receive two computers ane return nothing.
        :param more_pressable_types: a list of other types that can be pressed using this method.
        :return: None
        """
        pressable_types = [ComputerGraphics] + ([] if more_pressable_types is None else more_pressable_types)
        if self.selected_object is not None and type(self.selected_object) in pressable_types:
            if self.source_of_line_drag is None:
                self.source_of_line_drag = self.selected_object
            else:  # there is another computer to connect with that was already pressed.
                action(self.source_of_line_drag, self.selected_object)

                self.source_of_line_drag = None
                self.set_mode(MODES.NORMAL)

        elif not self.is_mouse_in_side_window() and self.selected_object is None:  # pressing the background
            self.source_of_line_drag = None
            self.set_mode(MODES.NORMAL)

    def start_device_visual_connecting(self):
        """
        This is called when we start to drag the connection from computer to the next in connecting mode
        :return:
        """
        self.source_of_line_drag = MainLoop.instance.get_object_the_mouse_is_on()
        if self.source_of_line_drag is None or self.is_mouse_in_side_window():
            self.set_mode(MODES.NORMAL)

    def end_device_visual_connecting(self, action):
        """
        This is called when the the line was dragged between the two devices and now the action can be performed.
        :param action: a function that is called with the two devices.
        :return:
        """
        connected = MainLoop.instance.get_object_the_mouse_is_on()
        if self.is_mouse_in_side_window() or connected is None:
            self.set_mode(MODES.NORMAL)
            return
        action(self.source_of_line_drag, connected)
        self.set_mode(MODES.NORMAL)

    def connect_devices(self, device1, device2):
        """
        Connect two devices to each other, show the connection and everything....
        The devices can be computers or interfaces. Works either way
        :param device1:
        :param device2: the two `Computer` object or `Interface` objects. Could also be their graphics objects.
        :return: None
        """
        devices = device1, device2
        computers = [device1, device2]  # `Computer`-s
        interfaces = [device1, device2]  # `Interface`-s

        for i, device in enumerate(devices):
            if isinstance(device, InterfaceGraphics):
                device = device.interface
            elif isinstance(device, ComputerGraphics):
                device = device.computer

            if isinstance(device, Interface):
                computers[i] = get_the_one(self.computers, lambda c: device in c.interfaces, NoSuchInterfaceError)
                interfaces[i] = device
            elif isinstance(device, Computer):
                computers[i] = device
                interfaces[i] = device.available_interface()
            else:
                # raise WrongUsageError(f"Only give this function computers or interfaces!!! ({device1, device2})")
                return

        if len(set(computers)) == 1:
            return

        if any(isinstance(interface, WirelessInterface) for interface in interfaces):
            PopupError(
                "Wireless interfaces do not connect peer-to-peer! They just need to be on the same frequency and then they can communicate :)",
                self
            )
            return

        try:
            connection = interfaces[0].connect(interfaces[1])
        except DeviceAlreadyConnectedError:
            PopupError("That interface is already connected :(", self)
            return
        self.connection_data.append(ConnectionData(connection, *computers))
        connection.show(computers[0].graphics, computers[1].graphics)
        return connection

    @staticmethod
    def send_direct_ping(computer_graphics1, computer_graphics2):
        """
        Send a ping from `computer1` to `computer2`.
        If one of them does not have an IP address, do nothing.
        :param computer_graphics1:
        :param computer_graphics2: The `ComputerGraphics` objects to send a ping between computers.
        :return: None
        """
        computer1, computer2 = computer_graphics1.computer, computer_graphics2.computer
        if computer1.has_ip() and computer2.has_ip():
            computer1.start_ping_process(computer2.get_ip())

    def send_random_ping(self):
        """
        Sends a ping from a random computer to another random computer (both with IP addresses).
        If does not have enough to choose from, do nothing.
        """
        try:
            sending_computer = random.choice([computer for computer in self.computers if computer.has_ip()])
            receiving_computer = random.choice([computer for computer in self.computers
                                                if computer.has_ip() and computer is not sending_computer])
            sending_computer.start_ping_process(receiving_computer.get_ip())
        except IndexError:
            pass

    def delete_all(self):
        """
        Deletes all of the objects and graphics objects that exist.
        Totally clears the screen.
        :return: None
        """
        for object_ in list(filter(lambda go: not go.is_button, MainLoop.instance.graphics_objects)):
            MainLoop.instance.unregister_graphics_object(object_)

        self.selected_object = None
        self.dragged_object = None

        for connection, _, _ in self.connection_data:
            MainLoop.instance.remove_from_loop(connection.move_packets)

        for computer in self.computers:
            MainLoop.instance.remove_from_loop(computer.logic)

        self.computers.clear()
        self.connection_data.clear()
        self.frequencies.clear()
        self.set_mode(MODES.NORMAL)

    def delete_all_packets(self):
        """
        Deletes all of the packets from all of the connections.
        Useful if one has created a "chernobyl packet" (an endless packet loop)
        :return: None
        """
        for connection, _, _ in self.connection_data:
            connection.stop_packets()

    def delete(self, graphics_object):
        """
        Receives a graphics object, deletes it from the main loop and disconnects it (if it is a computer).
        :param graphics_object: a `GraphicsObject` to delete.
        :return: None
        """
        MainLoop.instance.unregister_graphics_object(graphics_object)
        self.selected_object = None
        self.dragged_object = None

        if isinstance(graphics_object, ComputerGraphics):
            self.computers.remove(graphics_object.computer)
            self._delete_connections_to(graphics_object.computer)

        elif isinstance(graphics_object, ConnectionGraphics):
            for connection, computer1, computer2 in self.connection_data:
                if connection is graphics_object.connection:
                    computer1.disconnect(connection)
                    computer2.disconnect(connection)
                    break

        elif isinstance(graphics_object, InterfaceGraphics):
            interface = graphics_object.interface
            computer = get_the_one(self.computers, (lambda c: interface in c.interfaces), NoSuchInterfaceError)
            if interface.is_connected:
                connection = interface.connection.connection
                self.delete(connection.graphics)
            computer.add_remove_interface(interface.name)

    def _delete_connections_to(self, computer):
        """
        Delete all of the connections to a computer!
        Also delete all of the packets inside of them.
        :param computer: a `Computer` object.
        :return: None
        """
        for connection_data in self.connection_data[:]:
            connection, computer1, computer2 = connection_data
            if computer is computer1 or computer is computer2:
                computer.disconnect(connection)
                (computer1 if computer is computer2 else computer2).disconnect(connection)  # disconnect other computer

                MainLoop.instance.unregister_graphics_object(connection.graphics)
                connection.stop_packets()
                self.connection_data.remove(connection_data)

        for interface in computer.interfaces:
            if isinstance(interface, WirelessInterface):
                interface.disconnect()

    def add_delete_interface(self, computer_graphics, interface_name, type_=INTERFACES.TYPE.ETHERNET):
        """
        Add an interface with a given name to a computer.
        If the interface already exists, remove it.
        :param computer_graphics: a `ComputerGraphics` object.
        :param interface_name: a string name of the interface.
        :param type_: the type of the interface (ethernet / wireless / ...)
        :return: None
        """
        computer = computer_graphics.computer
        interface = get_the_one(computer.interfaces, lambda i: i.name == interface_name)
        try:
            computer.add_interface(interface_name, type_=type_)
        except DeviceNameAlreadyExists:
            if interface.is_connected():
                self.delete(interface.connection.connection.graphics)
            computer.remove_interface(interface_name)

    def hide_buttons(self, buttons_id=None):
        """
        make all of the buttons with a certain button_id hidden, if no group is given, hide all
        :param buttons_id: the buttons id of the buttons you want to hide.
        :return: None
        """
        if buttons_id is None:
            for other_buttons_id in self.buttons:
                self.hide_buttons(other_buttons_id)

        for button in self.buttons[buttons_id]:
            button.hide()

    def show_buttons(self, buttons_id):
        """
        make the buttons of a certain buttons_id is_showing, all other groups hidden.
        :param buttons_id: the ID of the buttons one wishes to show.
        :return: None
        """
        for button in self.buttons[buttons_id]:
            button.show()
        self.showing_buttons_id = buttons_id

    def packet_from_graphics_object(self, graphics_object):
        """
        Receive a graphics object of a packet and return the packet object itself.
        :param graphics_object: a `PacketGraphics` object.
        :return:
        """
        all_connections = [connection_data[0] for connection_data in self.connection_data] + \
                          [computer.loopback.connection.connection for computer in self.computers] + self.frequencies
        all_sent_packets = functools.reduce(operator.concat, map(operator.attrgetter("sent_packets"), all_connections))

        for sent_packet in all_sent_packets:
            packet = sent_packet[0]
            if packet.graphics is graphics_object:
                return packet
        return None

    def drop_packet(self, packet_graphics):
        """
        Receives a `PacketGraphics` object and drops its `Packet` from the connection that it is running through
        :param packet_graphics: a `PacketGraphics` object of the `Packet` we want to drop.
        :return: None
        """
        all_connections = [connection_data[0] for connection_data in self.connection_data] + \
                          [computer.loopback.connection.connection for computer in self.computers]

        for connection in all_connections:
            for sent_packet in connection.sent_packets[:]:
                if sent_packet.packet.graphics is packet_graphics:
                    self.selected_object = None
                    self.set_mode(MODES.NORMAL)
                    connection.sent_packets.remove(sent_packet)
                    packet_graphics.drop()
                    return
        raise NoSuchPacketError("That packet cannot be found!")

    def ask_user_for_ip(self):
        """
        Asks user for an IP address for an interface.
        Does that using popup window in the `PopupTextBox` class.
        :return: None
        """
        computer, interface = None, None
        if self.selected_object is not None:
            if isinstance(self.selected_object, InterfaceGraphics):
                interface = self.selected_object.interface
                computer = get_the_one(self.computers, lambda c: interface in c.interfaces, NoSuchInterfaceError)

            elif isinstance(self.selected_object, ComputerGraphics):
                computer = self.selected_object.computer
                if computer.interfaces:
                    interface = computer.interfaces[0]

            self.ask_user_for(IPAddress,
                              MESSAGES.INSERT.IP,
                              with_args(computer.set_ip, interface),
                              "Invalid IP Address!!!")

    def smart_connect(self):
        """
        Connects all of the unconnected computers to their nearest  switch or hub
        If there is no such one, to the nearest router, else to connects all of the computers to all others
        :return: None
        """
        switches = list(filter(lambda c: isinstance(c, Switch), self.computers))
        routers = list(filter(lambda c: isinstance(c, Router), self.computers))
        if switches:
            for computer in self.computers:
                if isinstance(computer, Switch):
                    continue
                nearest_switch = min(switches, key=lambda s: distance(s.graphics.location, computer.graphics.location))
                if not computer.interfaces or not computer.interfaces[0].is_connected():
                    self.connect_devices(computer, nearest_switch)
        elif routers:
            for computer in self.computers:
                if isinstance(computer, Router):
                    continue
                nearest_router = min(routers, key=lambda s: distance(s.graphics.location, computer.graphics.location))
                if not computer.interfaces or not computer.interfaces[0].is_connected():
                    self.connect_devices(computer, nearest_router)
        else:
            self.connect_all_to_all()

    def ping_switch_with_ip(self):
        """
        Send a ping from a random computer to a switch with an ip. (I used it for testing), if no one uses it it
        can be deleted.
        :return: None
        """
        switch = get_the_one(self.computers, lambda c: isinstance(c, Switch) and c.has_ip(), NetworkSimulationError)
        pinging_computer = random.choice([computer for computer in self.computers if computer is not switch])
        pinging_computer.start_ping_process(switch.get_ip())

    def ask_for_dhcp(self):
        """
        Make all computers without an IP address ask for an IP address using DHCP.
        :return: None
        """
        for computer in self.computers:
            if not isinstance(computer, Switch) and not isinstance(computer, Router) and not computer.has_ip():
                computer.ask_dhcp()

    def print_debugging_info(self):
        """
        Prints out lots of useful information for debugging.
        :return: None
        """

        # print(f"time: {int(time.time())}, program time: {int(MainLoop.instance.time())}")
        def gos():
            return [go for go in MainLoop.instance.graphics_objects if not isinstance(go, UserInterfaceGraphicsObject)]

        print(MainWindow.main_window.get_mouse_location())
        self.debug_counter = self.debug_counter + 1 if hasattr(self, "debug_counter") else 0
        goes = list(filter(lambda go: not isinstance(go, UserInterfaceGraphicsObject), MainLoop.instance.graphics_objects))
        print(f"graphicsObject-s (no buttons or texts): {goes}")
        print(f"computers, {len(self.computers)}, connections, {len(self.connection_data)},"
              f"packets: {len(list(filter(lambda go: go.is_packet, MainLoop.instance.graphics_objects)))}")
        print(f"running processes: ", end='')
        for computer in self.computers:
            processes = [f"{waiting_process.process} of {computer}" for waiting_process in computer.waiting_processes]
            if processes:
                print(processes, end=' ')
        print()
        if self.selected_object is not None and isinstance(self.selected_object, ComputerGraphics):
            computer = self.selected_object.computer
            computer.print(f"{'DEBUG':^20}{self.debug_counter}")
            if not isinstance(computer, Switch):
                print(repr(computer.routing_table))
            elif computer.stp_enabled and computer.process_scheduler.is_usermode_process_running_by_type(STPProcess):  # computer is a Switch
                print(computer.process_scheduler.get_usermode_process_by_type(STPProcess).get_info())

        # self.set_all_connection_speeds(200)

    def create_computer_with_ip(self, wireless=False):
        """
        Creates a computer with an IP fitting to the computers around it.
        It will look at the nearest computer's subnet, find the max address in that subnet and take the one above it.
        If there no other computers, takes the default IP (DEFAULT_COMPUTER_IP)
        :return: the Computer object.
        """
        x, y = MainWindow.main_window.get_mouse_location()

        try:
            given_ip = self._get_largest_ip_in_nearest_subnet(x, y)
        except (NoSuchComputerError, NoIPAddressError):  # if there are no computers with IP on the screen.
            given_ip = IPAddress(ADDRESSES.IP.DEFAULT)

        new_computer = Computer.with_ip(given_ip) if not wireless else Computer.wireless_with_ip(given_ip)
        self.computers.append(new_computer)
        new_computer.show(x, y)
        return new_computer

    def _get_largest_ip_in_nearest_subnet(self, x, y):
        """
        Receives a pair of coordinates, finds the nearest computer's subnet, finds the largest IP address in that subnet
        and returns a copy of it.
        :param x:
        :param y: the coordinates.
        :return: an `IPAddress` object.
        """
        nearest_computers = sorted(self.computers, key=lambda c: distance((x, y), c.graphics.location))
        nearest_computers_with_ip = list(filter(lambda c: c.has_ip(), nearest_computers))

        try:
            nearest_ip_address = nearest_computers_with_ip[0].get_ip()
        except IndexError:
            raise NoSuchComputerError("There is no such computer!")

        all_ips_in_that_subnet = [
            IPAddress.copy(computer.get_ip())
            for computer in self.computers if computer.has_ip() and computer.get_ip().is_same_subnet(nearest_ip_address)
        ]

        try:
            greatest_ip_in_subnet = max(all_ips_in_that_subnet, key=lambda ip: int(IPAddress.as_bits(ip.string_ip),
                                                                                   base=2))
        except ValueError:
            raise NoIPAddressError("There are no IP addresses that fit the description!")

        return IPAddress.increased(greatest_ip_in_subnet)

    def start_all_stp(self):
        """
        Starts the STP process on all of the switches that enable it. (Only if not already started)
        :return: None
        """
        for switch in filter(lambda computer: isinstance(computer, Switch), self.computers):
            if switch.stp_enabled:
                switch.start_stp()

    def are_connected(self, computer1, computer2):
        """Receives two computers and returns if they are connected"""
        for _, computer_1, computer_2 in self.connection_data:
            if (computer1 is computer_1 and computer2 is computer_2) or \
                    (computer2 is computer_1 and computer1 is computer_2):
                return True
        return False

    def connect_all_to_all(self):
        """
        Connects all of the computers to all other computers!!!
        very fun!
        :return: None
        """
        for computer in self.computers:
            for other_computer in self.computers:
                if computer is not other_computer and not self.are_connected(computer, other_computer):
                    self.connect_devices(computer, other_computer)

    def send_ping_to_self(self):
        """
        The selected computer sends a ping to himself on the loopback.
        :return: None
        """
        if self.selected_object is None or not isinstance(self.selected_object, ComputerGraphics):
            return
        self.send_direct_ping(self.selected_object, self.selected_object)

    def _showcase_running_stp(self):
        """
        Displays the roots of all STP processes that are running. (circles the roots with a yellow circle)
        :return: None
        """
        stp_runners = [computer for computer in self.computers if computer.process_scheduler.is_usermode_process_running_by_type(STPProcess)]
        roots = [computer.process_scheduler.get_usermode_process_by_type(STPProcess).root_bid for computer in stp_runners]
        for computer in stp_runners:
            if computer.process_scheduler.get_usermode_process_by_type(STPProcess).my_bid in roots:
                draw_circle(*computer.graphics.location, 60, COLORS.YELLOW)

    def ask_user_for(self, type_, window_text, action, error_msg="invalid input!!!"):
        """
        Pops up the little window that asks the user to insert something.
        Receives the text of the window, the type that the string should have, and an action to perform with the already
        casted string. (The parameter that the action will receives will be of type `type_`)
        :param type_: the type the inserted value should have (`float` / `int` / `IPAddress`)
        :param window_text: the string that will be displayed on the popup window
        :param action: a function that receives the casted input value and does something with it.
        :param error_msg: The msg to be displayed if the input is invalid
        :return: None
        """

        def try_casting_with_action(string):
            try:
                user_input_object = type_(string)
            except (ValueError, InvalidAddressError):
                PopupError(error_msg, self)
                return

            try:
                action(user_input_object)
            except PopupWindowWithThisError as err:
                PopupError(str(err), self)
                return

        PopupTextBox(window_text, self, try_casting_with_action)

    @staticmethod
    def key_from_string(string):
        """
        Receives a button-string and returns the key that should be pressed to activate that button
        for example:
         'connect all (^c)' -> `key_from_string` -> `(key.C, KEYBOARD.MODIFIERS.CTRL)`
        :param string:
        :return:
        """
        if '(' not in string:
            return None

        _, modified_key = string.lower().split('(')
        modified_key, _ = modified_key.split(')')
        if modified_key.startswith('^'):
            return ord(modified_key[-1]), KEYBOARD.MODIFIERS.CTRL

        modifiers = KEYBOARD.MODIFIERS.NONE
        if 'ctrl' in modified_key.split('+'):
            modifiers |= KEYBOARD.MODIFIERS.CTRL
        if 'shift' in modified_key.split('+'):
            modifiers |= KEYBOARD.MODIFIERS.SHIFT
        if 'alt' in modified_key.split('+'):
            modifiers |= KEYBOARD.MODIFIERS.ALT
        return ord(modified_key[-1]), modifiers

    def add_buttons(self, dictionary):
        """
        Adds buttons to the side window according to requests of the viewed object.
        One plus the buttons_id is the button of the options
        :param dictionary: a `dict` of the form {button text: button action}
        :return: None
        """
        buttons_id = 0 if not self.buttons else max(self.buttons.keys()) + 1
        self.buttons[buttons_id] = [
            Button(
                *MainWindow.main_window.button_location_by_index(len(dictionary) + 1),
                called_in_order(
                    with_args(self.hide_buttons, buttons_id),
                    with_args(self.show_buttons, buttons_id + 1),
                    with_args(self.adjust_viewed_text_to_buttons, buttons_id + 1),
                ),
                "back (backspace)",
                key=(key.BACKSPACE, KEYBOARD.MODIFIERS.NONE),
                start_hidden=True,
            ),

            *[
                Button(
                    *MainWindow.main_window.button_location_by_index(i + 1),
                    action,
                    string,
                    key=self.key_from_string(string),
                    start_hidden=True,
                )
                for i, (string, action) in enumerate(dictionary.items())
            ],
        ]

        self.buttons[buttons_id + 1] = [
            Button(
                *MainWindow.main_window.button_location_by_index(1),
                called_in_order(
                    with_args(self.hide_buttons, buttons_id + 1),
                    with_args(self.show_buttons, buttons_id),
                    with_args(self.adjust_viewed_text_to_buttons, buttons_id),
                ),
                "options (enter)",
                key=(key.ENTER, KEYBOARD.MODIFIERS.NONE),
            ),
        ]
        self.showing_buttons_id = buttons_id + 1
        return buttons_id

    def remove_buttons(self, buttons_id):
        """
        Unregisters side-view added buttons by their ID. (Buttons that are added using the `self.add_buttons` method.)
        :param buttons_id: an integer returned by the `self.add_buttons` method
        :return: None
        """
        for button in self.buttons[buttons_id] + self.buttons[buttons_id + 1]:
            MainLoop.instance.unregister_graphics_object(button)
        del self.buttons[buttons_id]
        del self.buttons[buttons_id + 1]

    def add_tcp_test(self):
        """
        Adds the computers that i create every time i do a test for TCP processes. saves time.
        :return:
        """
        new_computers = [self.create_computer_with_ip() for _ in range(6)]
        self.create_device(Switch)
        self.smart_connect()
        for i, location in enumerate(
                circular_coordinates(MainWindow.main_window.get_mouse_location(), 150, len(new_computers))):
            new_computers[i].graphics.location = location

        self.tab_through_selected()
        self.selected_object.computer.open_port(21, "TCP")
        self.selected_object.computer.open_port(13, "TCP")
        self.tab_through_selected()
        self.tab_through_selected()
        self.selected_object.computer.process_scheduler.start_usermode_process(DAYTIMEClientProcess, IPAddress("192.168.1.2"))

    def register_window(self, window, *buttons):
        """
        Receives a window and adds it to the window list and make it known to the user interface
        object.
        :param window: a PopupWindow object
        :param buttons: the buttons that the
        window contains
        :return:
        """
        if self.popup_windows:
            window.x, window.y = map(sum, zip(self.popup_windows[-1].location, WINDOWS.POPUP.STACKING_PADDING))

        self.popup_windows.append(window)
        self.selected_object = window
        self.buttons[BUTTONS.ON_POPUP_WINDOWS.ID] = self.buttons.get(BUTTONS.ON_POPUP_WINDOWS.ID, []) + list(buttons)

        def remove_buttons():
            for button_ in buttons:
                self.buttons[BUTTONS.ON_POPUP_WINDOWS.ID].remove(button_)
                MainLoop.instance.unregister_graphics_object(button_)

        window.remove_buttons = remove_buttons

    def unregister_window(self, window):
        """
        receives a window that is registered in the UI object and removes it, it will be ready to be deleted afterwards
        :param window: a `PopupWindow` object
        :return: None
        """
        try:
            self.popup_windows.remove(window)
        except ValueError:
            raise WrongUsageError("The window is not registered in the UserInterface!!!")

        if self.active_window is window:
            self.active_window = None
        if self.selected_object is window:
            self.selected_object = None

        if self.popup_windows:
            self.active_window = self.popup_windows[0]

    def open_device_creation_window(self):
        """
        Creates the device creation window
        :return:
        """
        DeviceCreationWindow(self)

    def _connect_interfaces_by_name(self, start_computer_name,
                                    end_computer_name,
                                    start_interface_name,
                                    end_interface_name,
                                    connection_packet_loss=0,
                                    connection_speed=CONNECTIONS.DEFAULT_SPEED):
        """
        Connects two computers' interfaces by names of the computers and the interfaces
        """
        computers = [
            get_the_one(
                self.computers,
                lambda c: c.name == name,
                NoSuchComputerError,
            ) for name in (start_computer_name, end_computer_name)
        ]
        interfaces = [
            get_the_one(
                computer.interfaces,
                lambda i: i.name == name,
                NoSuchInterfaceError,
            ) for computer, name in zip(computers, (start_interface_name, end_interface_name))
        ]
        connection = self.connect_devices(*interfaces)
        connection.set_pl(connection_packet_loss)
        connection.set_speed(connection_speed)

    def _save_to_file_with_override_safety(self, filename):
        """
        Saves all of the state of the simulation at the moment into a file, that we can
        later load into an empty simulation, and get all of the computers, interface, and connections.
        :return: None
        """
        if os.path.isfile(os.path.join(DIRECTORIES.SAVES, f"{filename}.json")):
            YesNoPopupWindow("file exists! override?", self, yes_action=with_args(self.save_to_file, filename))
        else:
            self.save_to_file(filename)

    def save_to_file(self, filename):
        """
        Save the state of the simulation to a file named filename
        :param filename:
        :return:
        """
        dict_to_file = {
            "computers": [
                computer.graphics.dict_save() for computer in self.computers
            ],
            "connections": [
                connection_data.connection.graphics.dict_save() for connection_data in self.connection_data
            ],
        }

        os.makedirs(DIRECTORIES.SAVES, exist_ok=True)
        json.dump(dict_to_file, open(os.path.join(DIRECTORIES.SAVES, f"{filename}.json"), "w"), indent=4)

    def load_from_file(self, filename):
        """
        Loads the state of the simulation from a file
        :return:
        """
        try:
            dict_from_file = json.load(open(os.path.join(DIRECTORIES.SAVES, f"{filename}.json"), "r"))
        except FileNotFoundError:
            raise PopupWindowWithThisError("There is not such file!!!")

        self._create_map_from_file_dict(dict_from_file)

    def _create_map_from_file_dict(self, dict_from_file):
        """
        Creates the simulation state from a file
        :param dict_from_file:
        :return:
        """
        self.delete_all()

        for computer_dict in dict_from_file["computers"]:
            class_ = self.saving_file_class_name_to_class[computer_dict["class"]]
            computer = class_.from_dict_load(computer_dict)
            computer.show(*computer_dict["location"])
            self.computers.append(computer)
            for port in computer_dict["open_tcp_ports"]:
                computer.open_tcp_port(port)
            for port in computer_dict["open_udp_ports"]:
                computer.open_udp_port(port)

        for connection_dict in dict_from_file["connections"]:
            self._connect_interfaces_by_name(
                connection_dict["start"]["computer"],
                connection_dict["end"]["computer"],
                connection_dict["start"]["interface"],
                connection_dict["end"]["interface"],
                connection_dict["packet_loss"],
                connection_dict["speed"],
            )

    @staticmethod
    def _list_saved_files():
        """
        Returns a string of all of the files that are saved already
        :return:
        """
        file_list = os.listdir(DIRECTORIES.SAVES)
        return ", ".join(map(lambda f: f.split('.')[0], file_list))

    def _ask_user_for_load_file(self):
        """
        asks the user for a filename to open, while offering him the names that exist
        :return:
        """
        saved_files = self._list_saved_files()
        self.ask_user_for(
            str,
            f"insert file name to open:" + (f"[options: {saved_files}]" if saved_files else ""),
            self.load_from_file
        )

    def delete_selected_and_marked(self):
        """
        Deletes the selected and marked objects
        This is called when one presses the delete button
        :return:
        """
        if self.selected_object is not None:
            self.delete(self.selected_object)
            self.selected_object = None
            self.set_mode(MODES.NORMAL)

        for object_ in self.marked_objects:
            self.delete(object_)
        self.marked_objects.clear()

    def move_selected_mark(self, direction):
        """
        Moves the square that marks the selected computer to a given direction.
        (pressing an arrow key calls this)
        :param direction: one of {key.UP, key.DOWN, key.RIGHT, key.LEFT}
        :return:
        """
        if self.selected_object is None:
            self.tab_through_selected()
            return

        try:
            computer_distance_in_direction = {
                key.RIGHT: (lambda c: c.graphics.x - self.selected_object.x),
                key.LEFT: (lambda c: self.selected_object.x - c.graphics.x),
                key.UP: (lambda c: c.graphics.y - self.selected_object.y),
                key.DOWN: (lambda c: self.selected_object.y - c.graphics.y),
            }[direction]
        except KeyError:
            raise WrongUsageError("direction must be one of {key.UP, key.DOWN, key.RIGHT, key.LEFT}")

        optional_computers = list(filter(lambda c: computer_distance_in_direction(c) > 0, self.computers))
        if not optional_computers:
            return

        def weighted_distance(computer):
            x, y = computer.graphics.location
            sx, sy = self.selected_object.location

            if direction in {key.UP, key.DOWN}:
                return sqrt((x - sx) ** 50 + (y - sy) ** 2)
            return sqrt((x - sx) ** 2 + (y - sy) ** 50)

        new_selected = min(optional_computers, key=weighted_distance)
        self.selected_object = new_selected.graphics
        self.set_mode(MODES.VIEW)

    def move_selected_object(self, direction, step_size=SELECTED_OBJECT.STEP_SIZE):
        """
        Moves the computer that is selected a little bit in the direction given.
        :param direction:
        :param step_size: how many pixels the object will move in each step
        :return:
        """
        try:
            step = scale_tuple(step_size, {
                key.UP: (0, 1),
                key.DOWN: (0, -1),
                key.RIGHT: (1, 0),
                key.LEFT: (-1, 0),
            }[direction])
        except KeyError:
            raise WrongUsageError("direction must be one of {key.UP, key.DOWN, key.RIGHT, key.LEFT}")

        moved_objects = self.marked_objects + ([] if self.selected_object is None else [self.selected_object])
        for object_ in moved_objects:
            object_.location = sum_tuples(object_.location, step)

    def exit(self):
        """
        Closes the simulation
        :return:
        """
        YesNoPopupWindow("Are you sure you want to exit?", self, yes_action=pyglet.app.exit)

    def select_all(self):
        """
        Mark all of the computers on the screen.
        :return:
        """
        self.marked_objects.clear()
        self.selected_object = None
        self.marked_objects += list(map(attrgetter("graphics"), self.computers))

    def open_help(self):
        """
        Opens the help window.
        :return:
        """
        PopupHelp(self)

    def set_mouse_pressed_objects(self):
        """
        Sets the `selected_object` and `dragged_object` according to the mouse's press.
        :return: None
        """
        if self.is_mouse_in_side_window():
            return

        object_the_mouse_is_on = MainLoop.instance.get_object_the_mouse_is_on()

        self.dragged_object = object_the_mouse_is_on
        if (not isinstance(object_the_mouse_is_on, UserInterfaceGraphicsObject)) or isinstance(object_the_mouse_is_on, PopupWindow):
            self.selected_object = object_the_mouse_is_on

        if object_the_mouse_is_on is None:
            self.marked_objects.clear()
            return

        # vv this block is in charge of dragging the marked objects vv
        mouse_x, mouse_y = MainWindow.main_window.get_mouse_location()
        for object_ in self.marked_objects + [object_the_mouse_is_on]:
            object_x, object_y = object_.location
            self.dragging_points[object_] = object_x - mouse_x, object_y - mouse_y

    def set_all_connection_speeds(self, new_speed):
        """
        Sets the speed of all of the connections
        :param new_speed:
        :return:
        """
        for connection, _, _ in self.connection_data:
            connection.set_speed(new_speed)

    def color_by_subnets(self):
        """
        randomly colors the computers on the screen based on their subnet
        :return:
        """
        subnets = {}
        for computer in self.computers:
            if not computer.has_ip():
                continue

            for ip in computer.ips:
                subnet = get_the_one(subnets, lambda net: net.is_same_subnet(ip))
                if subnet is None:
                    subnets[ip.subnet()] = [computer]
                else:
                    subnets[subnet].append(computer)

        for subnet in subnets:
            color = (random.randint(0, 255),
                     random.randint(0, 255),
                     random.randint(0, 255))
            for computer in subnets[subnet]:
                computer.graphics.flush_colors()
                computer.graphics.add_hue(color)

    def get_frequency(self, frequency):
        """
        Receives a float indicating a frequency and returning a Frequency object to connect the wireless devices
        that are listening to that frequency.
        :param frequency: `float`
        :return:
        """
        for freq in self.frequencies:
            if freq.frequency == frequency:
                return freq

        new_freq = Frequency(frequency)
        self.frequencies.append(new_freq)
        return new_freq
