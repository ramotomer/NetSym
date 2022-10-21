from __future__ import annotations

import functools
import json
import operator
import os
import pprint
import random
import time
from functools import reduce
from math import sqrt
from operator import concat, attrgetter
from typing import TYPE_CHECKING, Optional, NamedTuple, List, Type, Callable, Dict, TypeVar, Tuple, Union, Any, Iterable

import pyglet
from pyglet.window import key

from NetSym.address.ip_address import IPAddress
from NetSym.computing.computer import Computer
from NetSym.computing.internals.frequency import Frequency
from NetSym.computing.internals.interface import Interface
from NetSym.computing.internals.processes.usermode_processes.ftp_process.ftp_client_process import ClientFTPProcess
from NetSym.computing.internals.processes.usermode_processes.stp_process import STPProcess
from NetSym.computing.internals.wireless_interface import WirelessInterface
from NetSym.computing.router import Router
from NetSym.computing.switch import Switch, Hub, Antenna
from NetSym.consts import VIEW, TEXT, BUTTONS, IMAGES, DIRECTORIES, T_Color, SELECTED_OBJECT, KEYBOARD, MODES, WINDOWS, COLORS, CONNECTIONS, \
    INTERFACES, ADDRESSES, MESSAGES, MAIN_LOOP
from NetSym.exceptions import *
from NetSym.gui.abstracts.different_color_when_hovered import DifferentColorWhenHovered
from NetSym.gui.abstracts.resizable import is_resizable
from NetSym.gui.abstracts.selectable import Selectable
from NetSym.gui.abstracts.uniquely_dragged import UniquelyDragged
from NetSym.gui.abstracts.user_interface_graphics_object import UserInterfaceGraphicsObject
from NetSym.gui.main_window import MainWindow
from NetSym.gui.shape_drawing import draw_circle, draw_line, draw_tiny_corner_windows_icon
from NetSym.gui.shape_drawing import draw_pause_rectangles, draw_rectangle
from NetSym.gui.tech.computer_graphics import ComputerGraphics
from NetSym.gui.tech.interface_graphics import InterfaceGraphics
from NetSym.gui.tech.packet_graphics import PacketGraphics
from NetSym.gui.user_interface.button import Button
from NetSym.gui.user_interface.popup_windows.device_creation_window import DeviceCreationWindow
from NetSym.gui.user_interface.popup_windows.popup_console import PopupConsole
from NetSym.gui.user_interface.popup_windows.popup_error import PopupError
from NetSym.gui.user_interface.popup_windows.popup_help import PopupHelp
from NetSym.gui.user_interface.popup_windows.popup_text_box import PopupTextBox
from NetSym.gui.user_interface.popup_windows.popup_window import PopupWindow
from NetSym.gui.user_interface.popup_windows.yes_no_popup_window import YesNoPopupWindow
from NetSym.gui.user_interface.resizing_dots_handler import ResizingDotsHandler
from NetSym.gui.user_interface.selecting_square import SelectingSquare
from NetSym.gui.user_interface.text_graphics import Text
from NetSym.gui.user_interface.viewable_graphics_object import ViewableGraphicsObject
from NetSym.usefuls.funcs import get_the_one, distance, with_args, called_in_order, circular_coordinates, sum_tuples, \
    scale_tuple

if TYPE_CHECKING:
    from NetSym.gui.abstracts.graphics_object import GraphicsObject
    from NetSym.packets.packet import Packet
    from NetSym.computing.connection import Connection
    from NetSym.gui.main_loop import MainLoop


T = TypeVar("T")


class ObjectView(NamedTuple):
    """
    A data structure to represent the current viewing of a GraphicsObject on the side window in VIEW_MODE
    - sprite is the little image that is shown
    - text is a `Text` object of the information about the object
    - viewed_object is a reference to the GraphicsObject that's viewed.
    """
    sprite:        pyglet.sprite.Sprite
    text:          Text
    viewed_object: ViewableGraphicsObject


class ConnectionData(NamedTuple):
    """
    A way to save the connection on the screen together with the computers they are connected to.
    """
    connection: Connection
    computer1:  Computer
    computer2:  Computer


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

    def __init__(self, main_loop: MainLoop, main_window: MainWindow) -> None:
        """
        Initiates the UserInterface class!
        `key_to_action` is a dictionary from keys and their modifiers to actions to perform when that key is pressed.
        `button_arguments` is a list of arguments for `Button` objects that will be created after
        the `MainWindow` is initiated.

        """
        self.main_loop = main_loop
        self.main_window = main_window

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
            (key.SPACE, KEYBOARD.MODIFIERS.NONE): self.main_loop.toggle_pause,
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
            MODES.NORMAL:           self.normal_mode_at_press,
            MODES.VIEW:             self.normal_mode_at_press,
        }
        # ^ maps what to do when the screen is pressed in each `mode`.  (No need to put here modes that are one of MODES.COMPUTER_CONNECTING_MODES)

        self.saving_file_class_name_to_class = {
            class_.__name__: class_ for class_ in (Computer, Switch, Router, Hub, Antenna)
        }
        self.__saving_file: Optional[str] = None

        self.computers:       List[Computer] = []
        self.connection_data: List[ConnectionData] = []
        self.frequencies:     List[Frequency] = []

        self.mode = MODES.NORMAL
        self.source_of_line_drag: Optional[GraphicsObject] = None
        # ^ used if two items are selected one after the other for some purpose (connecting mode, pinging mode etc)

        self.dragged_object: Optional[GraphicsObject] = None
        # ^ the object that is currently being dragged (by the courser)

        self.object_view: Optional[ObjectView] = None
        # ^ the `ObjectView` object that is currently is_showing in the side window.

        self.popup_windows: List[PopupWindow] = []
        self.__active_window: Optional[PopupWindow] = None

        self.button_arguments = [
            ((self.open_device_creation_window, "create device (e)"), {"key": (key.E, KEYBOARD.MODIFIERS.NONE)}),
            ((with_args(self.toggle_mode, MODES.CONNECTING), "connect (c / ^c / Shift+c)"), {"key": (key.C, KEYBOARD.MODIFIERS.NONE)}),
            ((with_args(self.toggle_mode, MODES.PINGING), "ping (p / ^p / Shift+p)"), {"key": (key.P, KEYBOARD.MODIFIERS.NONE)}),
            ((with_args(self.toggle_mode, MODES.FILE_DOWNLOADING),
              "Start file download (Ctrl+Shift+a)"),
             {"key": (key.A, KEYBOARD.MODIFIERS.CTRL | KEYBOARD.MODIFIERS.SHIFT)}),
            ((self.ask_for_dhcp, "ask for DHCP (shift+a)"), {"key": (key.A, KEYBOARD.MODIFIERS.SHIFT)}),
            ((self.start_all_stp, "start STP (ctrl+shift+s)"), {"key": (key.S, KEYBOARD.MODIFIERS.CTRL | KEYBOARD.MODIFIERS.SHIFT)}),
            ((self.delete_all_packets, "delete all packets (Shift+d)"), {"key": (key.D, KEYBOARD.MODIFIERS.SHIFT)}),
            ((self.delete_all, "delete all (^d)"), {"key": (key.D, KEYBOARD.MODIFIERS.CTRL)}),
            ((self._save_or_ask_user_for_filename_and_then_save, "save to file(^s)"), {"key": (key.S, KEYBOARD.MODIFIERS.CTRL)}),
            ((self._ask_user_for_load_file, "load from file (^o)"), {"key": (key.O, KEYBOARD.MODIFIERS.CTRL)}),
            ((self.open_help, "help (shift+/)"), {"key": (key.SLASH, KEYBOARD.MODIFIERS.SHIFT)}),
        ]
        self.buttons: Dict[int, List[Button]] = {}
        # ^ a dictionary in the form, {button_id: [list of `Button` objects]}
        self.showing_buttons_id: int = BUTTONS.MAIN_MENU.ID
        self.scrolled_view: Optional[float] = None
        self.debug_counter = 0

        self.selecting_square: Optional[SelectingSquare] = None

        self.marked_objects: List[Selectable] = []
        self.dragging_points: Dict[GraphicsObject, Tuple[float, float]] = {}

        self.__selected_object: Optional[Selectable] = None
        # ^ the object that is currently surrounded by the blue square
        self.selected_object = None  # this sets the `selected_object` attribute
        self.resizing_dots_handler = ResizingDotsHandler()

        self.main_loop.insert_to_loop(self.select_selected_and_marked_objects)
        self.main_loop.insert_to_loop(self.show)

        self.register_main_window_event_handlers()

        self.main_loop.insert_to_loop_prioritized(self.main_window.clear, MAIN_LOOP.FunctionPriority.HIGH)
        self.initiate_buttons()

    @property
    def all_marked_objects(self) -> List[Selectable]:
        """
        The `marked_objects` list with the selected_object together in one list
        :return:
        """
        if self.selected_object in self.marked_objects:
            return self.marked_objects
        return self.marked_objects + ([self.selected_object] if self.selected_object is not None else [])

    @property
    def active_window(self) -> PopupWindow:
        return self.__active_window

    @property
    def saving_file(self) -> Optional[str]:
        return self.__saving_file

    @saving_file.setter
    def saving_file(self, value: Optional[str]) -> None:
        self.__saving_file = value

        new_window_name = WINDOWS.MAIN.NAME
        if self.__saving_file is not None:
            new_window_name += ": " + self.__saving_file
        self.main_window.set_caption(new_window_name)

    @active_window.setter
    def active_window(self, window: PopupWindow) -> None:
        if self.active_window is not None:
            self.active_window.deactivate()

        if window is not None:
            window.activate()
        self.__active_window = window

        if window is not None:
            self.main_loop.move_to_front(window)

    @property
    def selected_object(self) -> Selectable:
        return self.__selected_object

    @selected_object.setter
    def selected_object(self, graphics_object: Selectable) -> None:
        if isinstance(graphics_object, PopupWindow):
            self.active_window = graphics_object
        else:
            self.__selected_object = graphics_object
            self.active_window = None

    def set_is_ignoring_keyboard_escape_keys(self, value) -> None:
        """
        :param value: Whether or not to swallow special keyboard shortcuts passed (winkey, alt+tab...)

            This must be a separate method because inside this class's __init__ method the `MainWindow.main_window` object is still `None`
        """
        self.main_window.set_is_ignoring_keyboard_escape_keys(value)

    def register_main_window_event_handlers(self) -> None:
        """
        Register all functions of the `UserInterface` that should be called every time an event occurs
        """
        self.main_window.set_handler('on_draw',          self.main_loop.main_loop)  # < The single most important line of the code
        self.main_window.set_handler('on_resize',        self.on_resize)
        self.main_window.set_handler('on_key_press',     self.on_key_press)
        self.main_window.set_handler('on_mouse_press',   self.on_mouse_press)
        self.main_window.set_handler('on_mouse_scroll',  self.on_mouse_scroll)
        self.main_window.set_handler('on_mouse_release', self.on_mouse_release)

    def show(self) -> None:
        """
        This is like the `draw` method of GraphicObject`s.
        :return: None
        """
        self._draw_side_window()
        if self.main_loop.is_paused:
            draw_pause_rectangles()
        if self.main_window.is_ignoring_keyboard_escape_keys:
            draw_tiny_corner_windows_icon()
        self.drag_objects()
        self._stop_viewing_dead_packets()
        self._showcase_running_stp()
        self._unregister_requesting_popup_windows()
        self._handle_resizing_dots()
        self._color_hovered_objects_differently()

        if self.mode in MODES.COMPUTER_CONNECTING_MODES:
            self._draw_connection_to_mouse(MODES.TO_COLORS[self.mode])

    def _draw_connection_to_mouse(self, color: T_Color) -> None:
        """
        This draws the connection while connecting two computers in connecting mode.
        (when they are not connected yet...)
        :return:
        """
        if self.source_of_line_drag is None:
            return

        draw_line(
            self.source_of_line_drag.location, self.main_window.get_mouse_location(),
            color=color,
            width=MODES.COMPUTER_CONNECTING_MODES_LINE_TO_MOUSE_WIDTH,
        )
        if isinstance(self.source_of_line_drag, Selectable):
            self.source_of_line_drag.mark_as_selected()

        destination = self.get_object_the_mouse_is_on()
        if destination is not None and isinstance(destination, Selectable):
            destination.mark_as_selected()

    def _color_hovered_objects_differently(self) -> None:
        """
        Some objects need to be colored a different color once the mouse is hovering over them!
        This function is in charge to find that out and changing the color if necessary
        """
        for graphics_object in self.main_loop.graphics_objects:
            if isinstance(graphics_object, DifferentColorWhenHovered):
                if graphics_object.is_in(*self.main_window.get_mouse_location()):
                    graphics_object.set_hovered_color()
                else:
                    graphics_object.set_normal_color()

    def _stop_viewing_dead_packets(self) -> None:
        """
        Checks if a packet that is currently viewed has left the screen (reached the destination or dropped) and if so
        stops viewing it.
        :return:
        """
        if isinstance(self.selected_object, PacketGraphics) and \
                self.packet_from_graphics_object(self.selected_object) is None:
            self.set_mode(MODES.NORMAL)

    def _draw_side_window(self) -> None:
        """
        Draws the side window
        :return:
        """
        draw_rectangle(self.main_window.width - self.WIDTH, 0, self.WIDTH, self.main_window.height,
                       color=MODES.TO_COLORS[self.mode])

    def drag_objects(self) -> None:
        """
        Drags the object that should be dragged around the screen.
        Essentially sets the objects coordinates to be the ones of the mouse.
        :return: None
        """
        if not self.main_window.mouse_pressed:
            return

        if self.selecting_square is not None:
            return

        mouse_x, mouse_y = self.main_window.get_mouse_location()

        dragging_objects = ([self.dragged_object] if self.dragged_object is not None else []) + self.marked_objects
        for object_ in dragging_objects:
            if isinstance(object_, Button):
                continue

            try:
                drag_x, drag_y = self.dragging_points[object_]
            except KeyError:
                continue

            if isinstance(object_, UniquelyDragged):
                object_.drag(mouse_x, mouse_y, drag_x, drag_y)
            else:
                object_.location = mouse_x + drag_x, mouse_y + drag_y

            if not isinstance(object_, Selectable):
                return  # This can only happen on the first object - the self.dragged_object

    @property
    def viewing_image_location(self) -> Tuple[float, float]:
        x = (self.main_window.width - (WINDOWS.SIDE.WIDTH / 2)) - (IMAGES.SIZE * IMAGES.SCALE_FACTORS.VIEWING_OBJECTS / 2)
        y = self.main_window.height - ((IMAGES.SIZE * IMAGES.SCALE_FACTORS.VIEWING_OBJECTS) + 15)
        return x, y

    @property
    def viewing_text_location(self) -> Tuple[float, float]:
        return (self.main_window.width - (WINDOWS.SIDE.WIDTH / 2)), \
               self.viewing_image_location[1] + VIEW.TEXT_PADDING

    def start_object_view(self, graphics_object: ViewableGraphicsObject) -> None:
        """
        Starts viewing an object on the side window.
        Creates an `ObjectView` which packs together the ip_layer required to view an object.
        :param graphics_object: A graphics object to view.
        :return: None
        """
        self.scrolled_view = 0
        sprite, text, buttons_id = graphics_object.start_viewing(self)
        if sprite is not None:
            sprite.update(*self.viewing_image_location,
                          scale_x=VIEW.IMAGE_SIZE / sprite.image.width,
                          scale_y=VIEW.IMAGE_SIZE / sprite.image.height)
            self.main_loop.insert_to_loop(sprite.draw)

            if isinstance(graphics_object, PacketGraphics):
                text = self.packet_from_graphics_object(graphics_object).multiline_repr()

        x, y = self.viewing_text_location
        text = Text(
            text, x, y,
            max_width=(WINDOWS.SIDE.WIDTH - WINDOWS.SIDE.VIEWING_OBJECT.TEXT.PADDING[0]),
            align=TEXT.ALIGN.LEFT,
            padding=WINDOWS.SIDE.VIEWING_OBJECT.TEXT.PADDING
        )
        self.main_loop.register_graphics_object(text)
        self.object_view = ObjectView(sprite, text, graphics_object)

        self.adjust_viewed_text_to_buttons(buttons_id + 1)

    def adjust_viewed_text_to_buttons(self, buttons_id: int) -> None:
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

    def end_object_view(self) -> None:
        """
        Removes the text object from the loop and ends the viewing of an object in the side window.
        if no object was viewed, does nothing.
        """
        if self.object_view is not None:
            self.object_view.viewed_object.end_viewing(self)
            self.main_loop.unregister_graphics_object(self.object_view.text)
            if self.object_view.sprite is not None:  # if the viewed graphics object is an image graphics object.
                self.main_loop.remove_from_loop(self.object_view.sprite.draw)

            if isinstance(self.object_view.viewed_object, ComputerGraphics):
                self.object_view.viewed_object.child_graphics_objects.console.hide()

            self.object_view: Optional[ObjectView] = None
            self.scrolled_view = None

    def scroll_view(self, scroll_count: int) -> None:
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

    def initiate_buttons(self) -> None:
        """
        Create all buttons of the main menu in their currect locations
        """
        self.buttons[BUTTONS.MAIN_MENU.ID] = [
            Button(
                *self.main_window.button_location_by_index(i - 1),
                *args,
                **kwargs,
            ) for i, (args, kwargs) in enumerate(self.button_arguments)
        ]

        for i, button in enumerate(self.buttons[BUTTONS.MAIN_MENU.ID]):
            x, y = self.main_window.button_location_by_index(i - 1)
            padding = x - WINDOWS.MAIN.WIDTH, y - WINDOWS.MAIN.HEIGHT
            button.set_parent_graphics(self.main_window, padding)
            self.main_loop.register_graphics_object(button)

    def tab_through_windows(self, reverse: bool = False) -> None:
        """

        :param reverse:
        :return:
        """
        available_windows = sorted(list(filter(lambda o: isinstance(o, PopupWindow), self.main_loop.graphics_objects)),
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

    def tab_through_selected(self, reverse: bool = False) -> None:
        """
        This is called when the TAB key is pressed.
        It goes through the graphics objects one by one and selects them.
        Allows working without the mouse when there are not a lot of objects on the screen
        :return:
        """
        available_graphics_objects = [object_ for object_ in self.main_loop.graphics_objects
                                      if object_.is_pressable and isinstance(object_, ViewableGraphicsObject)]
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

    def set_mode(self, new_mode: int) -> None:
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
            if isinstance(self.selected_object, ViewableGraphicsObject):
                self.start_object_view(self.selected_object)
            else:
                raise WrongUsageError(
                    "The new_mode should not be switched to view new_mode when the selected object cannot be viewed"
                )

        else:
            self.source_of_line_drag = None
            self.mode = new_mode
            self.end_object_view()
            if self.selected_object is not None:
                self.selected_object = None
            self.show_buttons(BUTTONS.MAIN_MENU.ID)
            self.marked_objects.clear()

    def clear_selected_objects_and_active_window(self) -> None:
        if self.selected_object is not None:
            self.selected_object = None
        self.marked_objects.clear()
        self.active_window = None

    def toggle_mode(self, mode) -> None:
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

    def _get_pressed_button(self) -> Optional[Button]:
        """
        Get the button the mouse is on.
        If the mouse is not hovering over any buttons - return None
        """
        for button in reversed(reduce(concat, list(self.buttons.values()))):
            if not button.is_hidden and button.is_in(*self.main_window.get_mouse_location()):
                return button
        return None

    def _get_on_mouse_pressed_action_by_mode(self) -> Callable[[], None]:
        """
        Decide what happens when the mouse is pressed - only with the things that regard the current MODE of the simulation
        If the mode has no action related to it - raise UnknownModeError
        """
        action = self.action_at_press_by_mode.get(self.mode)
        if action is None:
            if self.mode not in MODES.COMPUTER_CONNECTING_MODES:
                raise UnknownModeError("No handler was set for this mode! What to do when the mouse is pressed?")

            action = self.start_device_visual_connecting
        return action

    def on_mouse_press(self, x: float, y: float, mouse_button: int, modifiers: int) -> None:
        """
        Happens when the mouse is pressed.
        Decides what to do according to the mode we are now in.
        The choosing of a selected and dragged objects should be performed BEFORE this is called!
        """
        button = self._get_pressed_button()
        if button is not None:
            button.action()
            return

        action_by_mode = self._get_on_mouse_pressed_action_by_mode()
        action_by_mode()

        if self.active_window is None:
            self._create_selecting_square()

    def on_mouse_scroll(self, x: float, y: float, scroll_x: Union[int, float], scroll_y: Union[int, float]) -> None:
        """
        Defines what happens when the mouse is scrolled
        """
        if self.is_mouse_in_side_window() and self.mode == MODES.VIEW:
            self.scroll_view(scroll_y)
        else:
            for obj in self.all_marked_objects:
                if obj is not None and hasattr(obj, "resize"):
                    obj.resize(10 * scroll_y, 10 * scroll_y, constrain_proportions=True)

    def on_resize(self, *args: Any, **kwargs: Any) -> None:
        """

        """
        self.set_mode(MODES.NORMAL)

    def pin_active_window_to(self, direction) -> None:
        """

        :param direction:
        :return:
        """
        if self.active_window is not None:
            self.active_window.pin_to(direction)

    def _create_selecting_square(self) -> None:
        """
        Creates the selection square when the mouse is pressed and dragged around
        :return:
        """
        if self.mode == MODES.NORMAL:
            mouse_x, mouse_y = self.main_window.get_mouse_location()
            self.selecting_square = SelectingSquare(
                mouse_x, mouse_y,
                mouse_x, mouse_y,
            )
            self.main_loop.register_graphics_object(self.selecting_square)

    def on_mouse_release(self, x: float, y: float, button: int, modifiers: int) -> None:
        """
        this is called when the mouse is released
        :return:
        """
        self.dragging_points.clear()
        if self.selecting_square is not None:
            self.main_loop.unregister_graphics_object(self.selecting_square)
            self.selecting_square = None
            return

        if self.mode in MODES.COMPUTER_CONNECTING_MODES:
            self.end_device_visual_connecting({
                MODES.CONNECTING:       self.connect_devices,
                MODES.PINGING:          self.send_direct_ping,
                MODES.FILE_DOWNLOADING: self.start_file_download,
            }[self.mode])

        self.dragged_object = None

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        """
        Called when a key is pressed
        """
        modifiers = self.main_window.normalize_keyboard_modifiers(modifiers)

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

    def normal_mode_at_press(self) -> None:
        """
        Happens when we are in viewing mode (or simulation mode) and we press our mouse.
        decides whether to start viewing a new graphics object or finish a previous one.
        """
        self.set_mouse_pressed_objects()

        if self.is_mouse_in_side_window():
            return

        if self.selected_object is not None and isinstance(self.selected_object, ViewableGraphicsObject):
            self.set_mode(MODES.VIEW)
            return

        if self.selected_object is None:
            self.set_mode(MODES.NORMAL)

        # we only get here if an an object that cannot be viewed is pressed - do nothing

    def is_mouse_in_side_window(self) -> bool:
        """Return whether or not the mouse is currently in the side window."""
        mouse_x, _ = self.main_window.get_mouse_location()
        return mouse_x > (self.main_window.width - self.WIDTH)

    def create_device(self, object_type: Type[Computer]) -> None:
        """
        Creates an object from a given type.
        :param object_type: an object type that will be created (Computer, Switch, Hub, etc...)
        """
        x, y = self.main_window.get_mouse_location()
        if self.is_mouse_in_side_window():
            x, y = WINDOWS.MAIN.WIDTH / 2, WINDOWS.MAIN.HEIGHT / 2

        object_ = object_type()
        self.main_loop.register_graphics_object(object_.init_graphics(x, y))
        self.computers.append(object_)

    def two_pressed_objects(self,
                            action: Callable[[GraphicsObject, GraphicsObject], None],
                            more_pressable_types: Optional[List[Type[GraphicsObject]]] = None) -> None:
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

    def start_device_visual_connecting(self) -> None:
        """
        This is called when we start to drag the connection from computer to the next in connecting mode
        :return:
        """
        self.source_of_line_drag = self.get_object_the_mouse_is_on()
        if self.source_of_line_drag is None or self.is_mouse_in_side_window():
            self.set_mode(MODES.NORMAL)

    def get_object_the_mouse_is_on(self, exclude_types: Optional[Iterable[Type]] = None) -> GraphicsObject:
        """
        Returns the `GraphicsObject` that should be selected if the mouse is pressed
        (so the object that the mouse is on right now) or `None` if the mouse is not resting upon any object.
        :return: a `GraphicsObject` or None.
        """
        exclude_types = exclude_types if exclude_types is not None else [Button]
        mouse_x, mouse_y = self.main_window.get_mouse_location()
        return get_the_one(
            reversed(self.main_loop.graphics_objects),
            lambda go: go.is_in(mouse_x, mouse_y) and not isinstance(go, tuple(exclude_types))
        )

    def end_device_visual_connecting(self, action: Callable[[GraphicsObject, GraphicsObject], None]) -> None:
        """
        This is called when the the line was dragged between the two devices and now the action can be performed.
        :param action: a function that is called with the two devices.
        :return:
        """
        if self.is_mouse_in_side_window():
            return

        connected = self.get_object_the_mouse_is_on()
        if connected is None:
            self.set_mode(MODES.NORMAL)
            return

        action(self.source_of_line_drag, connected)
        self.set_mode(MODES.NORMAL)

    def connect_devices(self,
                        device1: Union[Computer, ComputerGraphics, Interface, InterfaceGraphics],
                        device2: Union[Computer, ComputerGraphics, Interface, InterfaceGraphics]) -> Optional[Connection]:
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
            self.register_window(PopupError(
                "Wireless interfaces do not connect peer-to-peer! They just need to be on the same frequency and then they can communicate :)",
            ))
            return

        try:
            connection = interfaces[0].connect(interfaces[1])
        except DeviceAlreadyConnectedError:
            self.register_window(PopupError("That interface is already connected :("))
            return
        self.connection_data.append(ConnectionData(connection, *computers))
        self.main_loop.register_graphics_object(connection.init_graphics(computers[0].graphics, computers[1].graphics))
        return connection

    @staticmethod
    def send_direct_ping(computer_graphics1: ComputerGraphics, computer_graphics2: ComputerGraphics) -> None:
        """
        Send a ping from `computer1` to `computer2`.
        If one of them does not have an IP address, do nothing.
        :param computer_graphics1:
        :param computer_graphics2: The `ComputerGraphics` objects to send a ping between computers.
        :return: None
        """
        computer1, computer2 = computer_graphics1.computer, computer_graphics2.computer
        if computer1.has_ip() and computer2.has_ip():
            computer1.start_ping_process(computer2.get_ip().string_ip)

    @staticmethod
    def start_file_download(computer_graphics1: ComputerGraphics, computer_graphics2: ComputerGraphics) -> None:
        """
        Make `computer1` start downloading a file from `computer2`.
        If one of them does not have an IP address, do nothing.
        :param computer_graphics1:
        :param computer_graphics2: The `ComputerGraphics` objects to send a ping between computers.
        """
        computer1, computer2 = computer_graphics1.computer, computer_graphics2.computer
        if computer1.has_ip() and computer2.has_ip():
            computer1.process_scheduler.start_usermode_process(ClientFTPProcess, computer2.get_ip().string_ip)

    def send_random_ping(self) -> None:
        """
        Sends a ping from a random computer to another random computer (both with IP addresses).
        If does not have enough to choose from, do nothing.
        """
        try:
            sending_computer = random.choice([computer for computer in self.computers if computer.has_ip()])
            receiving_computer = random.choice([computer for computer in self.computers
                                                if computer.has_ip() and computer is not sending_computer])
            sending_computer.start_ping_process(receiving_computer.get_ip().string_ip)
        except IndexError:
            pass

    def delete_all(self, reset_saving_file: bool = True) -> None:
        """
        Deletes all of the objects and graphics objects that exist.
        Totally clears the screen.
        """
        for object_ in list(filter(
                lambda go: not isinstance(go, Button) and not (isinstance(go, Text) and go.is_button),
                self.main_loop.graphics_objects)):
            self.main_loop.unregister_graphics_object(object_)

        self.selected_object = None
        self.dragged_object = None
        self.active_window = None

        for connection_data in self.connection_data:
            self.main_loop.remove_from_loop(connection_data.connection.move_packets)

        for computer in self.computers:
            self.main_loop.remove_from_loop(computer.logic)

        self.computers.clear()
        self.connection_data.clear()
        self.frequencies.clear()
        self.popup_windows.clear()
        self.set_mode(MODES.NORMAL)

        if reset_saving_file:
            self.saving_file = None

    def delete_all_packets(self) -> None:
        """
        Deletes all of the packets from all of the connections.
        Useful if one has created a "chernobyl packet" (an endless packet loop)
        :return: None
        """
        for connection, _, _ in self.connection_data:
            connection.stop_packets()

    def remove_computer(self, computer: Computer) -> None:
        """
        Removes a computer from the simulation (but NOT the ComputerGraphics object)
        """
        self.computers.remove(computer)

    def remove_connection(self, connection: Connection) -> None:
        """
        Take in a connection and disconnect it from the computers in both sides
        """
        for connection_data in self.connection_data:
            other_connection, computer1, computer2 = connection_data
            if connection is other_connection:
                computer1.disconnect(connection)
                computer2.disconnect(connection)
                self.connection_data.remove(connection_data)
                break

    def remove_interface(self, interface: Interface) -> None:
        """
        Remove an interface and disconnect everything it is connected to
        """
        computer = get_the_one(self.computers, (lambda c: interface in c.interfaces), NoSuchInterfaceError)
        if interface.is_connected:
            connection = interface.connection.connection
            self.delete(connection.graphics)
        computer.remove_interface(interface.name)

    def delete(self, graphics_object: GraphicsObject) -> None:
        """
        Receives a graphics object, deletes it from the main loop and disconnects it (if it is a computer).
        :param graphics_object: a `GraphicsObject` to delete.
        :return: None
        """
        graphics_object.delete(self)
        self.selected_object = None
        self.dragged_object = None

    def delete_connections_to(self, computer: Computer) -> None:
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

                self.main_loop.unregister_graphics_object(connection.graphics)
                connection.stop_packets()
                self.connection_data.remove(connection_data)

        for interface in computer.interfaces:
            if isinstance(interface, WirelessInterface):
                interface.disconnect()

    def add_delete_interface(self,
                             computer_graphics: ComputerGraphics,
                             interface_name: str,
                             interface_type: str = INTERFACES.TYPE.ETHERNET) -> None:
        """
        Add an interface with a given name to a computer.
        If the interface already exists, remove it.
        """
        computer = computer_graphics.computer
        interface = get_the_one(computer.interfaces, lambda i: i.name == interface_name)
        try:
            interface = computer.add_interface(interface_name, type_=interface_type)
            self.main_loop.register_graphics_object(interface.graphics)

        except DeviceNameAlreadyExists:
            if interface.is_connected():
                self.delete(interface.connection.connection.graphics)
            computer.remove_interface(interface_name)

    def hide_buttons(self, buttons_id: Optional[int] = None) -> None:
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

    def show_buttons(self, buttons_id: int) -> None:
        """
        make the buttons of a certain buttons_id is_showing, all other groups hidden.
        :param buttons_id: the ID of the buttons one wishes to show.
        :return: None
        """
        for button in self.buttons[buttons_id]:
            button.show()
        self.showing_buttons_id = buttons_id

    def packet_from_graphics_object(self, graphics_object: GraphicsObject) -> Optional[Packet]:
        """
        Receive a graphics object of a packet and return the packet object itself.
        :param graphics_object: a `PacketGraphics` object.
        :return:
        """
        all_connections = [connection_data[0] for connection_data in self.connection_data] + \
                          [computer.loopback.connection.connection for computer in self.computers] + self.frequencies
        all_sent_packets = functools.reduce(operator.concat, map(operator.attrgetter("sent_packets"), all_connections))

        for sent_packet in all_sent_packets:
            if sent_packet.packet.graphics is graphics_object:
                return sent_packet.packet
        return None

    def drop_packet(self, packet_graphics: PacketGraphics) -> None:
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
                    packet_graphics.unregister()
                    self.main_loop.register_graphics_object(packet_graphics.get_drop_animation())
                    return
        raise NoSuchPacketError("That packet cannot be found!")

    def decrease_packet_speed(self, packet_graphics: PacketGraphics) -> None:
        """
        Decrease the speed of the supplied packet and play the appropriate animation
        """
        packet_graphics.decrease_speed()
        self.main_loop.register_graphics_object(packet_graphics.get_decrease_speed_animation())

    def ask_user_for_ip(self) -> None:
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

    def smart_connect(self) -> None:
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

    def ask_for_dhcp(self) -> None:
        """
        Make all computers without an IP address ask for an IP address using DHCP.
        :return: None
        """
        for computer in self.computers:
            if not isinstance(computer, Switch) and not isinstance(computer, Router) and not computer.has_ip():
                computer.ask_dhcp()

    def print_debugging_info(self) -> None:
        """
        Prints out lots of useful information for debugging.
        :return: None
        """
        self.learn_all_macs()
        print(f"\n{' debugging info ':-^100}")
        print(f"time: {int(time.time())}, program time: {int(self.main_loop.time())}")

        def gos() -> List[GraphicsObject]:
            return [go for go in self.main_loop.graphics_objects if not isinstance(go, (Button, Text))]

        print(f"Mouse location: {self.main_window.get_mouse_location()}\n")
        self.debug_counter = self.debug_counter + 1 if hasattr(self, "debug_counter") else 0
        pprint.pprint(f"graphicsObject-s (no buttons or texts): ")
        pprint.pprint(gos())
        print(f"\ncomputers, {len(self.computers)}, connections, {len(self.connection_data)}, "
              f"packets: {len(list(filter(lambda go: isinstance(go, PacketGraphics), self.main_loop.graphics_objects)))}")

        print()
        if self.selected_object is not None and isinstance(self.selected_object, ComputerGraphics):
            computer = self.selected_object.computer
            computer.print(f"{'DEBUG':^20}{self.debug_counter}")
            if not isinstance(computer, Switch):
                print(repr(computer.routing_table))
            elif computer.stp_enabled and computer.process_scheduler.is_usermode_process_running_by_type(STPProcess):  # computer is a Switch
                print(computer.process_scheduler.get_usermode_process_by_type(STPProcess).get_info())

        # self.set_all_connection_speeds(200)

    def create_computer_with_ip(self, wireless: bool = False) -> Computer:
        """
        Creates a computer with an IP fitting to the computers around it.
        It will look at the nearest computer's subnet, find the max address in that subnet and take the one above it.
        If there no other computers, takes the default IP (DEFAULT_COMPUTER_IP)
        :return: the Computer object.
        """
        x, y = self.main_window.get_mouse_location()

        try:
            given_ip = self._get_largest_ip_in_nearest_subnet(x, y)
        except (NoSuchComputerError, NoIPAddressError):  # if there are no computers with IP on the screen.
            given_ip = IPAddress(ADDRESSES.IP.DEFAULT)

        new_computer = Computer.with_ip(given_ip) if not wireless else Computer.wireless_with_ip(given_ip)
        self.computers.append(new_computer)
        self.main_loop.register_graphics_object(new_computer.init_graphics(x, y))
        return new_computer

    def _get_largest_ip_in_nearest_subnet(self, x: float, y: float) -> IPAddress:
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

    def start_all_stp(self) -> None:
        """
        Starts the STP process on all of the switches that enable it. (Only if not already started)
        :return: None
        """
        for switch in filter(lambda computer: isinstance(computer, Switch), self.computers):
            switch: Switch
            if switch.stp_enabled:
                switch.start_stp()

    def are_connected(self, computer1: Computer, computer2: Computer) -> bool:
        """Receives two computers and returns if they are connected"""
        for _, computer_1, computer_2 in self.connection_data:
            if (computer1 is computer_1 and computer2 is computer_2) or \
                    (computer2 is computer_1 and computer1 is computer_2):
                return True
        return False

    def connect_all_to_all(self) -> None:
        """
        Connects all of the computers to all other computers!!!
        very fun!
        :return: None
        """
        for computer in self.computers:
            for other_computer in self.computers:
                if computer is not other_computer and not self.are_connected(computer, other_computer):
                    self.connect_devices(computer, other_computer)

    def send_ping_to_self(self) -> None:
        """
        The selected computer sends a ping to himself on the loopback.
        :return: None
        """
        if self.selected_object is None:
            return

        if not isinstance(self.selected_object, ComputerGraphics):
            return

        selected_computer_graphics: ComputerGraphics = self.selected_object
        self.send_direct_ping(selected_computer_graphics, selected_computer_graphics)

    def _showcase_running_stp(self) -> None:
        """
        Displays the roots of all STP processes that are running. (circles the roots with a yellow circle)
        :return: None
        """
        stp_runners = [computer for computer in self.computers if computer.process_scheduler.is_usermode_process_running_by_type(STPProcess)]
        roots = [computer.process_scheduler.get_usermode_process_by_type(STPProcess).root_bid for computer in stp_runners]
        for computer in stp_runners:
            if computer.process_scheduler.get_usermode_process_by_type(STPProcess).my_bid in roots:
                draw_circle(*computer.graphics.location, 60, COLORS.YELLOW)

    def ask_user_for(self,
                     type_: Type[T],
                     window_text: str,
                     action: Callable[[T], None],
                     error_msg: str = "invalid input!!!") -> None:
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

        def try_casting_with_action(string: str) -> None:
            try:
                user_input_object = type_(string)
            except (ValueError, InvalidAddressError):
                self.register_window(PopupError(error_msg))
                return

            try:
                action(user_input_object)
            except PopupWindowWithThisError as err:
                self.register_window(PopupError(str(err)))
                return

        self.register_window(PopupTextBox(window_text, try_casting_with_action))

    @staticmethod
    def key_from_string(string: str) -> Optional[Tuple[int, int]]:
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

    def add_buttons(self, dictionary: Dict[str, Callable[[], None]]) -> int:
        """
        Adds buttons to the side window according to requests of the viewed object.
        One plus the buttons_id is the button of the options
        :param dictionary: a `dict` of the form {button text: button action}
        :return: None
        """
        buttons_id = 0 if not self.buttons else max(self.buttons.keys()) + 1
        self.buttons[buttons_id] = [
            Button(
                self.main_window.button_location_by_index(len(dictionary) + 1)[0],
                self.main_window.button_location_by_index(len(dictionary) + 1)[1],
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
                    *self.main_window.button_location_by_index(i + 1),
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
                self.main_window.button_location_by_index(1)[0],
                self.main_window.button_location_by_index(1)[1],
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
        self.main_loop.register_graphics_object(self.buttons[buttons_id] + self.buttons[buttons_id + 1])
        return buttons_id

    def remove_buttons(self, buttons_id: int) -> None:
        """
        Unregisters side-view added buttons by their ID. (Buttons that are added using the `self.add_buttons` method.)
        :param buttons_id: an integer returned by the `self.add_buttons` method
        :return: None
        """
        for button in self.buttons[buttons_id] + self.buttons[buttons_id + 1]:
            self.main_loop.unregister_graphics_object(button)
        del self.buttons[buttons_id]
        del self.buttons[buttons_id + 1]

    def learn_all_macs(self) -> None:
        """
        Adds every computer every other computer's MAC and IP address mapping to its ARP cache
        """
        for computer in self.computers:
            for other_computer in self.computers:
                if other_computer is computer:
                    continue

                for interface in other_computer.interfaces:
                    if not interface.has_ip():
                        continue

                    computer.arp_cache.add_dynamic(interface.ip, interface.mac)

    def add_tcp_test(self) -> None:
        """
        Adds the computers that i create every time i do a test for TCP processes. saves time.
        :return:
        """
        DEFAULT_DOMAIN = "fun."
        new_computers = [self.create_computer_with_ip() for _ in range(6)]
        self.create_device(Switch)
        self.smart_connect()

        server: Computer = new_computers[0]
        server.open_port(21,   "TCP")
        server.open_port(13,   "TCP")
        server.open_port(53,   "UDP")
        server.open_port(1000, "UDP")
        server.add_remove_dns_zone(DEFAULT_DOMAIN)

        for computer, location in zip(new_computers, circular_coordinates(self.main_window.get_mouse_location(), 150, len(new_computers))):
            computer.graphics.location = location
            computer.domain = DEFAULT_DOMAIN
            computer.dns_server = server.get_ip()
            server.add_dns_entry(f"{computer.name}.{DEFAULT_DOMAIN} {computer.get_ip().string_ip}")

        self.learn_all_macs()

    def register_window(self, window: PopupWindow) -> None:
        """
        Receives a window and adds it to the window list and make it known to the user interface
        object.
        :param window: a PopupWindow object
        """
        self.main_loop.register_graphics_object(window)

        if self.popup_windows:
            window.x, window.y = map(sum, zip(self.popup_windows[-1].location, WINDOWS.POPUP.STACKING_PADDING))

        self.popup_windows.append(window)
        self.selected_object = window

        self.buttons[BUTTONS.ON_POPUP_WINDOWS.ID] = self.buttons.get(BUTTONS.ON_POPUP_WINDOWS.ID, []) + list(window.buttons)

    def unregister_window(self, window: PopupWindow) -> None:
        """
        receives a window that is registered in the UI object and removes it, it will be ready to be deleted afterwards
        :param window: a `PopupWindow` object
        :return: None
        """
        for button_ in window.buttons:
            self.buttons[BUTTONS.ON_POPUP_WINDOWS.ID].remove(button_)
            self.main_loop.unregister_graphics_object(button_)

        try:
            self.popup_windows.remove(window)
        except ValueError:
            raise WrongUsageError("The window is not registered in the UserInterface!!!")  # TODO: change exception type to be more specific

        if self.active_window is window:
            self.active_window = None
        if self.selected_object is window:
            self.selected_object = None

        if self.popup_windows:
            self.active_window = self.popup_windows[0]

    def _unregister_requesting_popup_windows(self) -> None:
        """
        Call the `unregister_window` upon every window that has the `unregister_this_window_from_user_interface` flag set
        """
        for window in self.popup_windows[:]:
            if window.unregister_this_window_from_user_interface:
                self.unregister_window(window)

    def open_device_creation_window(self) -> None:
        """
        Creates the device creation window
        :return:
        """
        self.register_window(DeviceCreationWindow(self))

    def _connect_interfaces_by_name(self,
                                    start_computer_name: str,
                                    end_computer_name: str,
                                    start_interface_name: str,
                                    end_interface_name: str,
                                    connection_packet_loss: float = 0.0,
                                    connection_speed: int = CONNECTIONS.DEFAULT_SPEED) -> None:
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

    def _save_or_ask_user_for_filename_and_then_save(self) -> None:
        """
        If the simulation state was once saved already - remember the file name and do not ask for it again
        """
        if self.saving_file is None:
            self.ask_user_for(str, "save file as:", self._save_to_file_with_override_safety)
            return
        self._save_to_file_with_override_safety(self.saving_file)

    def _save_to_file_with_override_safety(self, filename: str) -> None:
        """
        Saves all of the state of the simulation at the moment into a file, that we can
        later load into an empty simulation, and get all of the computers, interface, and connections.
        :return: None
        """
        if os.path.isfile(os.path.join(DIRECTORIES.SAVES, f"{filename}.json")):
            self.register_window(YesNoPopupWindow("file exists! override?", yes_action=with_args(self.save_to_file, filename)))
        else:
            self.save_to_file(filename)

    def save_to_file(self, filename: str) -> None:
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
        self.saving_file = filename

    def load_from_file(self, filename) -> None:
        """
        Loads the state of the simulation from a file
        :return:
        """
        try:
            dict_from_file = json.load(open(os.path.join(DIRECTORIES.SAVES, f"{filename}.json"), "r"))
        except FileNotFoundError:
            raise PopupWindowWithThisError("There is not such file!!!")

        self.saving_file = filename
        self._create_map_from_file_dict(dict_from_file)

    def _create_map_from_file_dict(self, dict_from_file: Dict) -> None:
        """
        Creates the simulation state from a file
        :param dict_from_file:
        :return:
        """
        self.delete_all(reset_saving_file=False)

        for computer_dict in dict_from_file["computers"]:
            class_ = self.saving_file_class_name_to_class[computer_dict["class"]]
            computer = class_.from_dict_load(computer_dict)
            self.main_loop.register_graphics_object(computer.init_graphics(*computer_dict["location"]))
            self.computers.append(computer)
            for port in computer_dict["open_tcp_ports"]:
                computer.open_port(port, "TCP")
            for port in computer_dict["open_udp_ports"]:
                computer.open_port(port, "UDP")

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
    def _list_saved_files() -> str:
        """
        Returns a string of all of the files that are saved already
        :return:
        """
        if not os.path.isdir(DIRECTORIES.SAVES):
            return ""

        file_list = os.listdir(DIRECTORIES.SAVES)
        return ", ".join(map(lambda f: f.split('.')[0], file_list))

    def _ask_user_for_load_file(self) -> None:
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

    def _update_selecting_square(self) -> None:
        """
        Set the SelectingSquare to the appropriate size according to the mouse location
        """
        if self.selecting_square is None:
            return

        self.selecting_square.location2 = self.main_window.get_mouse_location()

    def _mark_object_inside_selecting_square(self, object_types: Iterable[Type[GraphicsObject]] = ()) -> None:
        """
        Select the objects that are inside the square - add them to the `self.marked_objects` list
        """
        if self.selecting_square is None:
            return

        for graphics_object in [go for go in self.main_loop.graphics_objects if isinstance(go, tuple(object_types))]:
            if graphics_object in self.selecting_square and isinstance(graphics_object, Selectable):
                if graphics_object not in self.marked_objects:
                    self.marked_objects.append(graphics_object)
                    continue

                if graphics_object not in self.selecting_square:
                    self.marked_objects.remove(graphics_object)

    def delete_selected_and_marked(self) -> None:
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

    def select_selected_and_marked_objects(self) -> None:
        """
        Draws a rectangle around the selected object.
        The selected object is the object that was last pressed and is surrounded by a white square.
        :return: None
        """
        self._update_selecting_square()
        self._mark_object_inside_selecting_square(object_types=(ComputerGraphics, PacketGraphics))

        if self.selected_object is not None:
            self.selected_object.mark_as_selected()
            if is_resizable(self.selected_object):
                self.resizing_dots_handler.select(self.selected_object)
        else:
            self.resizing_dots_handler.deselect()

        for marked_object in self.marked_objects:
            marked_object.mark_as_selected()

    def move_selected_mark(self, direction: int) -> None:
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
                key.LEFT:  (lambda c: self.selected_object.x - c.graphics.x),
                key.UP:    (lambda c: c.graphics.y - self.selected_object.y),
                key.DOWN:  (lambda c: self.selected_object.y - c.graphics.y),
            }[direction]
        except KeyError:
            raise WrongUsageError("direction must be one of {key.UP, key.DOWN, key.RIGHT, key.LEFT}")

        optional_computers = list(filter(lambda c: computer_distance_in_direction(c) > 0, self.computers))
        if not optional_computers:
            return

        def weighted_distance(computer: Computer) -> float:
            x, y = computer.graphics.location
            sx, sy = self.selected_object.location

            if direction in {key.UP, key.DOWN}:
                return sqrt((x - sx) ** 50 + (y - sy) ** 2)
            return sqrt((x - sx) ** 2 + (y - sy) ** 50)

        new_selected = min(optional_computers, key=weighted_distance)
        self.selected_object = new_selected.graphics
        self.set_mode(MODES.VIEW)

    def move_selected_object(self, direction: int, step_size: float = SELECTED_OBJECT.STEP_SIZE) -> None:
        """
        Moves the computer that is selected a little bit in the direction given.
        :param direction: one of {key.UP, key.DOWN, key.RIGHT, key.LEFT}
        :param step_size: how many pixels the object will move in each step
        :return:
        """
        try:
            step = scale_tuple(step_size, {
                key.UP:    (0, 1),
                key.DOWN:  (0, -1),
                key.RIGHT: (1, 0),
                key.LEFT:  (-1, 0),
            }[direction])
        except KeyError:
            raise WrongUsageError("direction must be one of {key.UP, key.DOWN, key.RIGHT, key.LEFT}")

        moved_objects = self.marked_objects + ([] if self.selected_object is None else [self.selected_object])
        for object_ in moved_objects:
            object_.location = sum_tuples(object_.location, step)

    def exit(self) -> None:
        """
        Closes the simulation
        :return:
        """
        self.register_window(YesNoPopupWindow("Are you sure you want to exit?", yes_action=pyglet.app.exit))

    def select_all(self) -> None:
        """
        Mark all of the computers on the screen.
        :return:
        """
        self.marked_objects.clear()
        self.selected_object = None
        self.marked_objects += list(map(attrgetter("graphics"), self.computers))

    def open_help(self) -> None:
        """
        Opens the help window.
        :return:
        """
        self.register_window(PopupHelp())

    def set_mouse_pressed_objects(self) -> None:
        """
        Sets the `selected_object` and `dragged_object` according to the mouse's press.
        :return: None
        """
        if self.is_mouse_in_side_window():
            return

        object_the_mouse_is_on = self.get_object_the_mouse_is_on()

        self.dragged_object = object_the_mouse_is_on
        if (not isinstance(object_the_mouse_is_on, UserInterfaceGraphicsObject)) or isinstance(object_the_mouse_is_on, PopupWindow):
            self.selected_object = object_the_mouse_is_on

        if object_the_mouse_is_on is None:
            self.marked_objects.clear()
            return

        # vv this block is in charge of dragging the marked objects vv
        mouse_x, mouse_y = self.main_window.get_mouse_location()
        for object_ in self.marked_objects + [object_the_mouse_is_on]:
            object_x, object_y = object_.location
            self.dragging_points[object_] = object_x - mouse_x, object_y - mouse_y

    def set_all_connection_speeds(self, new_speed) -> None:
        """
        Sets the speed of all of the connections
        :param new_speed:
        :return:
        """
        for connection_data in self.connection_data:
            connection_data.connection.set_speed(new_speed)

    def color_by_subnets(self) -> None:
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

    def get_frequency(self, frequency: float) -> Frequency:
        """
        Receives a float indicating a frequency and returning a Frequency object to connect the wireless devices
        that are listening to that frequency.
        :param frequency: `float`
        :return:
        """
        for freq in self.frequencies:
            if freq.frequency == frequency:
                return freq

        new_frequency = Frequency(frequency, longest_line_in_screen=sqrt((self.main_window.width ** 2) + (self.main_window.height ** 2)))
        self.frequencies.append(new_frequency)
        self.main_loop.insert_to_loop_pausable(new_frequency.move_packets, supply_function_with_main_loop_object=True)
        return new_frequency

    def set_interface_frequency(self, interface: WirelessInterface, frequency: float) -> None:
        """
        Take in a WirelessInterface and set its frequency object
        If the object does not exist - create it :)
        """
        interface.connect(self.get_frequency(frequency))

    def _handle_resizing_dots(self) -> None:
        """
        Perform all of the actions `ResizingDot`s require doing periodically
        Register the new dots that are created as `GraphicsObject`s in the main loop.
        """
        has_new_dots = self.resizing_dots_handler.update_dot_state()

        if has_new_dots:
            self.main_loop.register_graphics_object(self.resizing_dots_handler.dots)
