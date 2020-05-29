import functools
import operator
import random
from collections import namedtuple
from functools import reduce
from operator import concat

from pyglet.window import key

from address.ip_address import IPAddress
from computing.computer import Computer
from computing.interface import Interface
from computing.router import Router
from computing.switch import Switch, Hub, Antenna
from consts import *
from exceptions import *
from gui.main_loop import MainLoop
from gui.main_window import MainWindow
from gui.shape_drawing import draw_circle
from gui.shape_drawing import draw_pause_rectangles, draw_rect
from gui.tech.computer_graphics import ComputerGraphics
from gui.tech.interface_graphics import InterfaceGraphics
from gui.user_interface.button import Button
from gui.user_interface.popup_error import PopupError
from gui.user_interface.popup_text_box import PopupTextBox
from gui.user_interface.text_graphics import Text
from processes.stp_process import STPProcess
from processes.tcp_process import TCPProcess
from usefuls import get_the_one, distance, with_args, called_in_order, circular_coordinates

# from gui.animation_graphics import LogoAnimation


ObjectView = namedtuple("ObjectView", [
    "sprite",
    "text",
    "viewed_object",
])
"""
A data structure to represent the current viewing of a GraphicsObject on the side window in VIEW_MODE
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
    if the mode is `SIMULATION_MODE`, the regular menu is presented.
    if the mode is `CONNECTING_MODE` than the two next computers the user will press will become connected.
    the `VIEW_MODE` is when a computer's details are currently is_showing in the side window nicely.
    the `PINGING_MODE` is when we choose two computer to send a ping between.  (purple side window)
    the `DELETING_MODE` is when we delete a graphics object. (Brown side window)

    Only set the mode through the `set_mode` method!!!
    """
    WIDTH = SIDE_WINDOW_WIDTH  # pixels

    def __init__(self):
        """
        Initiates the UserInterface class!
        `key_to_action` is a dictionary from keys and their modifiers to actions to perform when that key is pressed.
        `button_arguments` is a list of arguments for `Button` objects that will be created after
        the `MainWindow` is initiated.

        `is_asking_for_string` tells whether or not a popup window is currently up and asking the user for input
        `popup_window` is that window.
        """
        self.key_to_action = {
            (key.N, CTRL_MODIFIER): self.create_computer_with_ip,
            (key.C, CTRL_MODIFIER): self.smart_connect,
            (key.C, SHIFT_MODIFIER): self.connect_all_to_all,
            (key.P, CTRL_MODIFIER): self.send_random_ping,
            (key.P, SHIFT_MODIFIER): self.send_ping_to_self,
            (key.R, CTRL_MODIFIER): with_args(self.create, Router),
            (key.M, NO_MODIFIER): self.debugging_printer,
            (key.W, NO_MODIFIER): self.add_tcp_test,
            (key.SPACE, NO_MODIFIER): self.toggle_pause,
            (key.TAB, NO_MODIFIER): self.tab_through_selected,
            (key.TAB, SHIFT_MODIFIER): with_args(self.tab_through_selected, True),
            (key.ESCAPE, NO_MODIFIER): with_args(self.set_mode, SIMULATION_MODE),
        }

        self.action_at_press_by_mode = {
            SIMULATION_MODE: self.view_mode_at_press,
            CONNECTING_MODE: with_args(self.two_pressed_objects, self.connect_devices, [InterfaceGraphics]),
            VIEW_MODE: self.view_mode_at_press,
            PINGING_MODE: with_args(self.two_pressed_objects, self.send_direct_ping),
            DELETING_MODE: self.deleting_mode_at_press,
        }
        # ^ maps what to do when the screen is pressed in each `mode`.

        self.computers = []
        self.connection_data = []
        # ^ a list of `ConnectionData`-s (save information about all existing connections between computers.

        self.mode = SIMULATION_MODE
        self.other_selected_object = None
        # ^ used if two items are selected one after the other for some purpose (connecting mode, pinging mode etc)

        self.dragged_object = None
        # ^ the object that is currently being dragged (by the courser)
        self.dragging_point = 0, 0
        # ^ the coordinates the mouse is at relative to the object it drags

        self.selected_object = None
        # ^ the object that is currently dragged

        self.object_view = None
        # ^ the `ObjectView` object that is currently is_showing in the side window.

        self.is_asking_for_string = False
        # ^ whether or not a popup window is currently open on the screen
        self.popup_windows = []
        self.active_window = None

        self.button_arguments = [
            ((*DEFAULT_BUTTON_LOCATION(-1), lambda: None, "MAIN MENU:"), {}),

            ((*DEFAULT_BUTTON_LOCATION(0), with_args(self.create, Computer),
              "create a computer (n / ^n)"), {"key": (key.N, NO_MODIFIER)}),
            ((*DEFAULT_BUTTON_LOCATION(1), with_args(self.create, Switch),
              "create a switch (s)"), {"key": (key.S, NO_MODIFIER)}),
            ((*DEFAULT_BUTTON_LOCATION(2), with_args(self.create, Hub),
              "create a hub (h)"), {"key": (key.H, NO_MODIFIER)}),
            ((*DEFAULT_BUTTON_LOCATION(3), with_args(self.create, Antenna),
              "create an antenna (shift+r)"), {"key": (key.R, SHIFT_MODIFIER)}),
            ((*DEFAULT_BUTTON_LOCATION(4), self.create_router,
              "create a router (r / ^r)"), {"key": (key.R, NO_MODIFIER)}),
            ((*DEFAULT_BUTTON_LOCATION(5), with_args(self.toggle_mode, CONNECTING_MODE),
              "connect (c / ^c / Shift+c)"), {"key": (key.C, NO_MODIFIER)}),
            ((*DEFAULT_BUTTON_LOCATION(6), with_args(self.toggle_mode, PINGING_MODE),
              "ping (p / ^p / Shift+p)"), {"key": (key.P, NO_MODIFIER)}),
            ((*DEFAULT_BUTTON_LOCATION(7), self.ask_for_dhcp,
              "ask for DHCP (a)"), {"key": (key.A, NO_MODIFIER)}),
            ((*DEFAULT_BUTTON_LOCATION(8), self.start_all_stp,
              "start STP (^s)"), {"key": (key.S, CTRL_MODIFIER)}),
            ((*DEFAULT_BUTTON_LOCATION(9), self.delete_all_packets,
              "delete all packets (Shift+d)"), {"key": (key.D, SHIFT_MODIFIER)}),
            ((*DEFAULT_BUTTON_LOCATION(10), self.delete_all,
              "delete all (^d)"), {"key": (key.D, CTRL_MODIFIER)}),
            ((*DEFAULT_BUTTON_LOCATION(11), with_args(self.toggle_mode, DELETING_MODE),
              "delete (d)"), {"key": (key.D, NO_MODIFIER)}),
        ]
        self.buttons = {}
        # ^ a dictionary in the form, {button_id: [list of `Button` objects]}
        self.showing_buttons_id = MAIN_BUTTONS_ID
        self.scrolled_view = None
        self.debug_counter = 0

    def show(self):
        """
        This is like the `draw` method of GraphicObject`s.
        :return: None
        """
        draw_rect(WINDOW_WIDTH - self.WIDTH, 0, self.WIDTH, WINDOW_HEIGHT, MODES_TO_COLORS[self.mode])
        # ^ the window rectangle itself
        if MainLoop.instance.is_paused:
            draw_pause_rectangles()

        if self.selected_object is not None and \
                self.selected_object.is_packet and \
                self.packet_from_graphics_object(self.selected_object) is None:
            self.set_mode(SIMULATION_MODE)

    def drag_object(self):
        """
        Drags the object that should be dragged around the screen.
        Essentially sets the objects coordinates to be the ones of the mouse.
        :return: None
        """
        if self.dragged_object is not None and not self.dragged_object.is_button:
            drag_x, drag_y = self.dragging_point
            mouse_x, mouse_y = MainWindow.main_window.get_mouse_location()
            self.dragged_object.x, self.dragged_object.y = mouse_x + drag_x, mouse_y + drag_y

    def start_object_view(self, graphics_object):
        """
        Starts viewing an object on the side window.
        Creates an `ObjectView` namedtuple which packs together the data required to view an object.
        :param graphics_object: A graphics object to view.
        :return: None
        """
        self.scrolled_view = 0

        sprite, text, buttons_id = graphics_object.start_viewing(self)
        if sprite is not None:
            sprite.update(*VIEWING_IMAGE_COORDINATES)
            MainLoop.instance.insert_to_loop(sprite.draw)

            if graphics_object.is_packet:
                text = self.packet_from_graphics_object(graphics_object).multiline_repr()

        x, y = VIEWING_TEXT_COORDINATES
        self.object_view = ObjectView(sprite, Text(text, x, y, max_width=SIDE_WINDOW_WIDTH), graphics_object)
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
            self.object_view.text.y = VIEWING_TEXT_COORDINATES[1] - ((len(self.buttons[buttons_id]) + 0.5) *
                                                                     DEFAULT_BUTTON_HEIGHT) - self.scrolled_view
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

            if self.object_view.viewed_object.is_computer:
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
                "Not supposed to get here!!! In VIEW_MODE the `self.object_view` is never None"
            )

        sprite, text_graphics, viewed_object = self.object_view
        if scroll_count < 0 or self.scrolled_view <= -scroll_count * PIXELS_PER_SCROLL:
            self.scrolled_view += scroll_count * PIXELS_PER_SCROLL

            sprite.y = VIEWING_IMAGE_COORDINATES[1] - self.scrolled_view
            self.adjust_viewed_text_to_buttons(self.showing_buttons_id)

            for buttons_id in self.buttons:
                for button in self.buttons[buttons_id]:
                    if not button.is_hidden:
                        button.y = button.initial_location[1] - self.scrolled_view

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

        self.set_mode(VIEW_MODE)

    def initiate_buttons(self):
        """
        Initiates the buttons in the window.
        This does not happen in init because when init is called here
        `MainWindow.main_window` is still uninitiated so it cannot register the graphics objects of the buttons.
        :return: None
        """
        self.buttons[MAIN_BUTTONS_ID] = [Button(*args, **kwargs) for args, kwargs in self.button_arguments]

    def set_mode(self, new_mode):
        """
        This is the correct way to set the `self.new_mode` trait of the side window.
        it handles all of the things one needs to do when switching between different modes.
        (especially VIEW_MODE)
        :return: None
        """
        if self.mode == CONNECTING_MODE and new_mode != CONNECTING_MODE:
            self.other_selected_object = None

        if new_mode == VIEW_MODE:
            self.end_object_view()
            self.mode = new_mode
            self.hide_buttons(MAIN_BUTTONS_ID)
            if not self.selected_object.can_be_viewed:
                raise WrongUsageError(
                    "The new_mode should not be switched to view new_mode when the selected object cannot be viewed"
                )
            self.start_object_view(self.selected_object)

        else:
            self.mode = new_mode
            self.end_object_view()
            self.selected_object = None
            self.show_buttons(MAIN_BUTTONS_ID)

    def toggle_mode(self, mode):
        """
        Toggles to and from a mode!
        If the mode is already the `mode` given, switch to `SIMULATION_MODE`.
        :param mode: a mode to toggle to and from (SIMULATION_MODE, CONNECTING_MODE, etc...)
        :return: None
        """
        if self.mode == mode:
            self.set_mode(SIMULATION_MODE)
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
        for button in reduce(concat, list(self.buttons.values())):
            if not button.is_hidden and button.is_mouse_in():
                button.action()

        self.action_at_press_by_mode[self.mode]()

    def on_key_pressed(self, symbol, modifiers):
        """
        Called when a key is pressed
        :param symbol:
        :param modifiers:
        :return:
        """
        if isinstance(self.active_window, PopupTextBox):
            self.active_window.pressed(symbol, modifiers)
        else:
            modified_key = (symbol, int(bin(modifiers)[2:][-4:], base=2))
            for button_id in sorted(list(self.buttons)):
                for button in self.buttons[button_id]:
                    if button.key == modified_key:
                        button.action()
                        return
            self.key_to_action.get(modified_key, lambda: None)()

    def view_mode_at_press(self):
        """
        Happens when we are in viewing mode (or simulation mode) and we press our mouse.
        decides whether to start viewing a new graphics object or finish a previous one.
        """
        if not self.is_mouse_in_side_window():
            if self.selected_object is not None and self.selected_object.can_be_viewed:
                self.set_mode(VIEW_MODE)
            elif self.selected_object is None:
                self.set_mode(SIMULATION_MODE)
            else:  # if an an object that cannot be viewed is pressed
                pass

    def deleting_mode_at_press(self):
        """
        Happens when we press the screen in DELETING_MODE.
        Decides if to step out of the mode or to delete an object.
        :return: None
        """
        if self.selected_object is not None:
            self.delete(self.selected_object)
        self.set_mode(SIMULATION_MODE)

    def is_mouse_in_side_window(self):
        """Return whether or not the mouse is currently in the side window."""
        mouse_x, _ = MainWindow.main_window.get_mouse_location()
        return mouse_x > (WINDOW_WIDTH - self.WIDTH)

    def create(self, object_type):
        """
        Creates an object from a given type.
        :param object_type: an object type that will be created (Computer, Switch, Hub, etc...)
        :return: None
        """
        x, y = MainWindow.main_window.get_mouse_location()
        if self.is_mouse_in_side_window():
            x, y = WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2

        object_ = object_type()
        object_.show(x, y)
        self.computers.append(object_)

    def create_router(self):
        """
        Create a router where the mouse is.
        :return: None
        """
        x, y = MainWindow.main_window.get_mouse_location()
        if self.is_mouse_in_side_window():
            x, y = WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2

        router = Router("Router and DHCP Server", (
                        Interface.with_ip('192.168.1.1'),
                        Interface.with_ip('10.10.10.1'),
                        Interface.with_ip('172.3.10.1'),
                        Interface.with_ip('1.1.1.1'),
                        ))
        router.show(x, y)
        self.computers.append(router)

    def two_pressed_objects(self, action, more_pressable_types=None):
        """
        This operates the situation when two things are required to be selected one after the other (like in
        CONNECTING_MODE, PINGING_MODE, etc...)
        Usually allows pressing just ComputerGraphics objects. This can be extended to more types using the
        `more_pressable_types` list.
        :param action: a function that will be activated on the two computers once they are both selected.
            should receive two computers ane return nothing.
        :param more_pressable_types: a list of other types that can be pressed using this method.
        :return: None
        """
        pressable_types = [ComputerGraphics] + ([] if more_pressable_types is None else more_pressable_types)
        if self.selected_object is not None and type(self.selected_object) in pressable_types:
            if self.other_selected_object is None:
                self.other_selected_object = self.selected_object
            else:  # there is another computer to connect with that was already pressed.
                action(self.other_selected_object, self.selected_object)

                self.other_selected_object = None
                self.set_mode(SIMULATION_MODE)

        elif not self.is_mouse_in_side_window() and self.selected_object is None:  # pressing the background
            self.other_selected_object = None
            self.set_mode(SIMULATION_MODE)

    def connect_devices(self, device1, device2):
        """
        Connect two devices to each other, show the connection and everything....
        The devices can be computers or interfaces. Works either way
        :param device1:
        :param device2: the two `Computer` object or `Interface` objects. Could also be their graphics objects.
        :return: None
        """
        devices = device1, device2
        computers = [device1, device2]  # Computer-s
        interfaces = [device1, device2]  # Interface-s

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
                raise WrongUsageError("Only supply this function with computers or interfaces!!!!")

        is_wireless = all(computer.is_supporting_wireless_connections for computer in computers)
        connection = interfaces[0].connect(interfaces[1], is_wireless=is_wireless)
        self.connection_data.append(ConnectionData(connection, *computers))
        connection.show(computers[0].graphics, computers[1].graphics)

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
            receiving_computer = random.choice([computer for computer in self.computers if computer.has_ip()])
            sending_computer.start_ping_process(receiving_computer.get_ip())
        except IndexError:
            pass

    def delete_all(self):
        """
        Deletes all of the objects and graphics objects that exist.
        Totally clears the screen.
        :return: None
        """
        MainLoop.instance.delete_all_graphics()
        self.selected_object = None
        self.dragged_object = None

        if self.is_asking_for_string:
            self.end_string_request()

        for connection, _, _ in self.connection_data:
            MainLoop.instance.remove_from_loop(connection.move_packets)

        for computer in self.computers:
            MainLoop.instance.remove_from_loop(computer.logic)

        self.computers.clear()
        self.connection_data.clear()

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

        if graphics_object.is_computer:
            self.computers.remove(graphics_object.computer)
            self._delete_connections_to(graphics_object.computer)

        elif graphics_object.is_connection:
            for connection, computer1, computer2 in self.connection_data:
                if connection is graphics_object.connection:
                    computer1.disconnect(connection)
                    computer2.disconnect(connection)
                    break

        elif isinstance(graphics_object, InterfaceGraphics):
            interface = graphics_object.interface
            computer = get_the_one(self.computers, lambda c: interface in c.interfaces, NoSuchInterfaceError)
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

    def add_delete_interface(self, computer_graphics, interface_name):
        """
        Add an interface with a given name to a computer.
        If the interface already exists, remove it.
        :param computer_graphics: a `ComputerGraphics` object.
        :param interface_name: a string name of the interface.
        :return: None
        """
        computer = computer_graphics.computer
        interface = get_the_one(computer.interfaces, lambda i: i.name == interface_name)
        try:
            computer.add_interface(interface_name)
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
        all_connections = [connection_data[0] for connection_data in self.connection_data] +\
                          [computer.loopback.connection.connection for computer in self.computers]
        all_sent_packets = functools.reduce(operator.concat, map(operator.attrgetter("sent_packets"), all_connections))

        for packet, _, _, _ in all_sent_packets:
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
                    self.set_mode(SIMULATION_MODE)
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
                              INSERT_IP_MSG,
                              with_args(computer.set_ip, interface),
                              "Invalid IP Address!!!")

    def end_string_request(self):
        """
        If the `UserInterface` Object currently is asking for user input (via the popup window), end that request,
        unregister the asking `PopupTextBox` popup window and set all variables accordingly.
        :return: None
        """
        self.is_asking_for_string = False
        self.active_window = None

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

    def debugging_printer(self):
        """
        Prints out lots of useful information for debugging.
        :return: None
        """
        # print(f"time: {int(time.time())}, program time: {int(MainLoop.instance.time())}")
        self.debug_counter = self.debug_counter+1 if hasattr(self, "debug_counter") else 0
        goes = [go for go in MainLoop.instance.graphics_objects
                if not isinstance(go, Button) and not isinstance(go, Text)]
        print(f"graphicsObject-s (no buttons or texts): {goes}")
        print(f"selected object: {self.selected_object}, dragged: {self.dragged_object}")
        print(f"mouse: {MainWindow.main_window.get_mouse_location()}")
        print(f"""computers, {len(self.computers)}, connections, {len(self.connection_data)},
        packets: {len(list(filter(lambda go: go.is_packet, MainLoop.instance.graphics_objects)))}""")
        print(f"running processes: ", end='')
        for computer in self.computers:
            processes = [f"{wp.process} of {computer}" for wp in computer.waiting_processes]
            print(processes if processes else '', end=' ')
        print()
        if self.selected_object is not None and self.selected_object.is_computer:
            computer = self.selected_object.computer
            computer.print(f"{'DEBUG':^20}{self.debug_counter}")
            if not isinstance(computer, Switch):
                print(repr(computer.routing_table))
            elif computer.stp_enabled and computer.is_process_running(STPProcess):  # computer is a Switch
                print(computer.get_running_process(STPProcess).get_info())

            if computer.is_process_running(TCPProcess):
                process = computer.get_running_process(TCPProcess)
                print(f"window (of {process}): {process.sending_window}")

    def create_computer_with_ip(self):
        """
        Creates a computer with an IP fitting to the computers around it.
        It will look at the nearest computer's subnet, find the max address in that subnet and take the one above it.
        If there no other computers, takes the default IP (DEFAULT_COMPUTER_IP)
        :return: the Computer object.
        """
        x, y = MainWindow.main_window.get_mouse_location()

        try:
            given_ip = self._get_largest_ip_in_nearest_subnet(x, y)
        except (NoSuchComputerError, NoIPAddressError):      # if there are no computers with IP on the screen.
            given_ip = IPAddress(DEFAULT_COMPUTER_IP)

        new_computer = Computer.with_ip(given_ip)
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
        if self.selected_object is None or not self.selected_object.is_computer:
            return
        computer = self.selected_object.computer
        self.send_direct_ping(computer, computer)

    def showcase_running_stp(self):
        """
        Displays the roots of all STP processes that are running. (circles the roots with a yellow circle)
        :return: None
        """
        stp_runners = [computer for computer in self.computers if computer.is_process_running(STPProcess)]
        roots = [computer.get_running_process(STPProcess).root_bid for computer in stp_runners]
        for computer in stp_runners:
            if computer.get_running_process(STPProcess).my_bid in roots:
                draw_circle(*computer.graphics.location, 60, YELLOW)

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
                arg = type_(string)
            except (ValueError, InvalidAddressError):
                self.end_string_request()
                PopupError(error_msg, self)
                return
            try:
                action(arg)
            except PopupWindowWithThisError as err:
                PopupError(str(err), self)
                return

        self.is_asking_for_string = True
        PopupTextBox(window_text, self, try_casting_with_action)

    @staticmethod
    def key_from_string(string):
        """
        Receives a button-string and returns the key that should be pressed to activate that button
        for example:
         'connect all (^c)' -> `key_from_string` -> `(key.C, CTRL_MODIFIER)`
        :param string:
        :return:
        """
        if '(' not in string:
            return None

        _, modified_key = string.lower().split('(')
        modified_key, _ = modified_key.split(')')
        if modified_key.startswith('^'):
            return ord(modified_key[-1]), CTRL_MODIFIER

        modifiers = NO_MODIFIER
        if 'ctrl' in modified_key.split('+'):
            modifiers |= CTRL_MODIFIER
        if 'shift' in modified_key.split('+'):
            modifiers |= SHIFT_MODIFIER
        if 'alt' in modified_key.split('+'):
            modifiers |= ALT_MODIFIER
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
                *DEFAULT_BUTTON_LOCATION(len(dictionary) + 1),
                called_in_order(
                    with_args(self.hide_buttons, buttons_id),
                    with_args(self.show_buttons, buttons_id + 1),
                    with_args(self.adjust_viewed_text_to_buttons, buttons_id + 1),
                ),
                "back (backspace)",
                key=(key.BACKSPACE, NO_MODIFIER),
                start_hidden=True,
            ),

            *[
                Button(
                    *DEFAULT_BUTTON_LOCATION(i+1),
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
                *DEFAULT_BUTTON_LOCATION(1),
                called_in_order(
                    with_args(self.hide_buttons, buttons_id + 1),
                    with_args(self.show_buttons, buttons_id),
                    with_args(self.adjust_viewed_text_to_buttons, buttons_id),
                ),
                "options (enter)",
                key=(key.ENTER, NO_MODIFIER),
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
        self.create(Switch)
        self.smart_connect()
        for i, (x, y) in enumerate(
                circular_coordinates(MainWindow.main_window.get_mouse_location(), 150, len(new_computers))):
            new_computers[i].graphics.x = x
            new_computers[i].graphics.y = y

        self.tab_through_selected()
        self.selected_object.computer.open_port(21)
        self.tab_through_selected()

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
            x, y = self.popup_windows[-1].location
            window.x, window.y = x + 10, y - 10
        self.popup_windows.append(window)
        self.active_window = window
        self.selected_object = window
        self.buttons[WINDOW_BUTTONS_ID] = self.buttons.get(WINDOW_BUTTONS_ID, []) + list(buttons)

        def remove_buttons():
            for button in buttons:
                self.buttons[WINDOW_BUTTONS_ID].remove(button)
                MainLoop.instance.unregister_graphics_object(button)
        window.remove_buttons = remove_buttons

    def unregister_window(self, window):
        """
        receives a window that is registered in the UI object and removes it, it will be ready to be deleted afterwards
        :param window: a `PopupWindow` object
        :return: None
        """
        if self.active_window is window:
            self.active_window = None
        if self.selected_object is window:
            self.selected_object = None

        try:
            self.popup_windows.remove(window)
        except ValueError:
            raise WrongUsageError("The window is not registered in the UserInterface!!!")

    # @staticmethod
    # def init_logo_animation():
    #     """
    #     Initiates the logo animation in the start of the simulation
    #     :return:
    #     """
    #     return LogoAnimation((WINDOW_WIDTH / 2) - 30, WINDOW_HEIGHT / 2)
