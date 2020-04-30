import functools
import operator
import random
import time
from collections import namedtuple
from math import sqrt

from pyglet.window import key

from address.ip_address import IPAddress
from computing.computer import Computer
from computing.interface import Interface
from computing.router import Router
from computing.switch import Switch, Hub
from consts import *
from exceptions import *
from gui.button import Button
from gui.main_loop import MainLoop
from gui.main_window import MainWindow
from gui.shape_drawing import draw_circle
from gui.shape_drawing import draw_pause_rectangles, draw_rect
from gui.text_box import TextBox
from gui.text_graphics import Text
from processes.stp_process import STPProcess
from usefuls import get_the_one, distance
from usefuls import with_args

ObjectView = namedtuple("ObjectView", "sprite text viewed_object")
"""
A data structure to represent the current viewing of a GraphicsObject on the side window in VIEW_MODE
- sprite is the little image that is shown
- text is a `Text` object of the information about the object
- viewed_object is a reference to the GraphicsObject thats viewed. 
"""

ConnectionData = namedtuple("ConnectionData", "connection computer1 computer2")
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
    the `SNIFFING_MODE` is when we choose a computer to start sniffing.  (Blue side window)
    the `PINGING_MODE` is when we choose two computer to send a ping between.  (purple side window)
    the `DELETING_MODE` is when we delete a graphics object. (Brown side window)

    Only set the mode through the `set_mode` method!!!
    """
    WIDTH = SIDE_WINDOW_WIDTH  # pixels

    def __init__(self):
        """
        Initiates the UserInterface class!
        `key_to_action` is a dictionary from keys and their modifiers to actions to be performed when that key is pressed.
        `button_arguments` is a list of argumetns for `Button` objects that will be created after the `MainWindow` is initiated.

        `is_asking_for_string` tells whether or not a popup window is currently up and asking the user for input
        `popup_window` is that window.
        """
        self.key_to_action = {
            (key.N, NO_MODIFIER): with_args(self.create, Computer, True),
            (key.N, CTRL_MODIFIER): self.create_computer_with_ip,
            (key.C, NO_MODIFIER): with_args(self.toggle_mode, CONNECTING_MODE),
            (key.C, CTRL_MODIFIER): self.connect_all_available,
            (key.C, SHIFT_MODIFIER): self.connect_all_to_all,
            (key.P, CTRL_MODIFIER): self.send_random_ping,
            (key.P, NO_MODIFIER): with_args(self.toggle_mode, PINGING_MODE),
            (key.P, SHIFT_MODIFIER): self.send_ping_to_self,
            (key.S, NO_MODIFIER): with_args(self.create, Switch, True),
            (key.S, CTRL_MODIFIER): self.start_all_stp,
            (key.H, NO_MODIFIER): with_args(self.create, Hub, True),
            (key.R, NO_MODIFIER): self.create_router,
            (key.D, SHIFT_MODIFIER): self.delete_all_packets,
            (key.D, CTRL_MODIFIER): self.delete_all,
            (key.D, NO_MODIFIER): with_args(self.toggle_mode, DELETING_MODE),
            (key.F, NO_MODIFIER): with_args(self.toggle_mode, SNIFFING_MODE),
            (key.M, NO_MODIFIER): self.debugging_printer,
            (key.A, NO_MODIFIER): self.ask_for_dhcp,
            (key.SPACE, NO_MODIFIER): self.toggle_pause,
            (key.I, NO_MODIFIER): self.ask_user_for_ip,
            (key.O, NO_MODIFIER): self.power_selected_computer,
        }

        self.action_at_press_by_mode = {
            SIMULATION_MODE: self.view_mode_at_press,
            CONNECTING_MODE: with_args(self.two_pressed_computers, self.connect_computers),
            VIEW_MODE: self.view_mode_at_press,
            SNIFFING_MODE: self.sniffing_mode_at_press,
            PINGING_MODE: with_args(self.two_pressed_computers, self.send_direct_ping),
            DELETING_MODE: self.deleting_mode_at_press,
        }
        # ^ maps what to do when the screen is pressed in each `mode`.

        self.computers = []
        self.connection_data = []
        # ^ a list of `ConnectionData`-s (save information about all existing connections between comuters.

        self.mode = SIMULATION_MODE
        self.other_selected_object = None
        # ^ used if two items are selected one after the other for some purpose (connecting mode, pinging mode etc)

        self.dragged_object = None
        # ^ the object that is currently being dragged (by the courser)
        self.dragging_point = 0, 0
        # ^ the coordinates the mouse is at relative to the object it drags (to avoid weird sudden jumps like it used to do)

        self.selected_object = None
        # ^ the object that is currently dragged

        self.object_view = None
        # ^ the `ObjectView` object that is currently is_showing in the side window.

        self.is_asking_for_string = False
        # ^ whether or not a popup window is currently open on the screen
        self.popup_window = None
        # ^ the popup window object. None if `self.is_asking_for_string` is False.

        self.button_arguments = [
            ((*DEFAULT_BUTTON_LOCATION(-1), lambda: None, "MAIN MENU:", MAIN_MENU_BUTTONS), {}),
            ((*DEFAULT_BUTTON_LOCATION(0), with_args(self.create, Computer), "create a computer (n / ^n)", MAIN_MENU_BUTTONS), {}),
            ((*DEFAULT_BUTTON_LOCATION(1), with_args(self.create, Switch), "create a switch (s)", MAIN_MENU_BUTTONS), {}),
            ((*DEFAULT_BUTTON_LOCATION(2), with_args(self.create, Hub), "create a hub (h)", MAIN_MENU_BUTTONS), {}),
            ((*DEFAULT_BUTTON_LOCATION(3), with_args(self.create, Router), "create a router (r)", MAIN_MENU_BUTTONS), {}),
            ((*DEFAULT_BUTTON_LOCATION(4), with_args(self.toggle_mode, CONNECTING_MODE), "connect (c / ^c / Shift+c)", MAIN_MENU_BUTTONS), {}),
            ((*DEFAULT_BUTTON_LOCATION(5), with_args(self.toggle_mode, PINGING_MODE), "ping (p / ^p / Shift+p)", MAIN_MENU_BUTTONS), {}),
            ((*DEFAULT_BUTTON_LOCATION(6), with_args(self.toggle_mode, SNIFFING_MODE), "toggle sniffing (f)", MAIN_MENU_BUTTONS), {}),
            ((*DEFAULT_BUTTON_LOCATION(7), self.ask_for_dhcp, "ask for DHCP (a)", MAIN_MENU_BUTTONS), {}),
            ((*DEFAULT_BUTTON_LOCATION(8), self.start_all_stp, "start STP (^s)", MAIN_MENU_BUTTONS), {}),
            ((*DEFAULT_BUTTON_LOCATION(9), self.delete_all_packets, "delete all packets (Shift+d)", MAIN_MENU_BUTTONS), {}),
            ((*DEFAULT_BUTTON_LOCATION(10), self.delete_all, "delete all (^d)", MAIN_MENU_BUTTONS), {}),
            ((*DEFAULT_BUTTON_LOCATION(11), with_args(self.toggle_mode, DELETING_MODE), "delete (d)", MAIN_MENU_BUTTONS), {}),
        ]
        self.buttons = []

        self.added_buttons = {} # buttons that are added to the side window while viewing some object. {button_id: list of `Button` objects}

    def show(self):
        """
        This is like the `draw` method of GraphicObject`s.
        :return: None
        """
        draw_rect(WINDOW_WIDTH - self.WIDTH,
                                             0,
                                             self.WIDTH,
                                             WINDOW_HEIGHT, MODES_TO_COLORS[self.mode])
        # ^ the window rectangle itself
        if MainLoop.instance.is_paused:
            draw_pause_rectangles()

        if self.is_asking_for_string:
            if self.popup_window.is_done:
                self.end_string_request()  # deletes the popup window if it is done with asking the string from the user.

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

        sprite, text, button_count = graphics_object.start_viewing(self)
        if sprite is not None:
            sprite.update(*VIEWING_IMAGE_COORDINATES)
            MainLoop.instance.insert_to_loop(sprite.draw)

            if graphics_object.is_packet:
                text = self.packet_from_graphics_object(graphics_object).multiline_repr()

            elif graphics_object.is_computer:
                graphics_object.child_graphics_objects.console.show()

        x, y = VIEWING_TEXT_COORDINATES
        self.object_view = ObjectView(sprite, Text(text, x, y - button_count * DEFAULT_BUTTON_HEIGHT, max_width=SIDE_WINDOW_WIDTH), graphics_object)

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

    def initiate_buttons(self):
        """
        Initiates the buttons in the window.
        This does not happen in init because when init is called here
        `MainWindow.main_window` is still uninitiated so it cannot register the graphics objects of the buttons.
        :return: None
        """
        self.buttons = [Button(*args, **kwargs) for args, kwargs in self.button_arguments]

    def set_mode(self, mode):
        """
        This is the correct way to set the `self.mode` trait of the side window.
        it handles all of the things one needs to do when switching between different modes.
        (especially VIEW_MODE)
        :return: None
        """
        if self.mode == CONNECTING_MODE and mode != CONNECTING_MODE:
            self.other_selected_object = None

        if mode == VIEW_MODE:
            self.end_object_view()
            self.mode = mode
            self.hide_button_group(MAIN_MENU_BUTTONS)
            self.start_object_view(self.selected_object)
            self.show_button_group(VIEW_MODE_BUTTONS)

        else:
            self.mode = mode
            self.hide_button_group(VIEW_MODE_BUTTONS)
            self.end_object_view()
            self.show_button_group(MAIN_MENU_BUTTONS)

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

    def toggle_pause(self):
        """
        Toggling from pause back and fourth.
        :return: None
        """
        MainLoop.instance.is_paused = not MainLoop.instance.is_paused

    def on_mouse_press(self):
        """
        Happens when the mouse is pressed.
        Decides what to do according to the mode we are now in.
        The choosing of a selected and dragged objects should be performed BEFORE this is called!
        :return: None
        """
        for button in self.buttons:
            if button.is_mouse_in() and not button.is_hidden:
                button.action()

        for buttons in list(self.added_buttons.values()):
            for button in buttons:
                if button.is_mouse_in():
                    button.action()

        action_at_press = self.action_at_press_by_mode[self.mode]
        action_at_press()

    def view_mode_at_press(self):
        """
        Happens when we are in viewing mode (or simulation mode) and we press our mouse.
        decides whether to start viewing a new graphics object or finish a previous one.
        """
        if self.selected_object is not None:
            self.set_mode(VIEW_MODE)
        elif self.selected_object is None:
            self.set_mode(SIMULATION_MODE)

    def sniffing_mode_at_press(self):
        """
        Happens when we press the screen in SNIFFING_MODE.
        Decides if to step out of the mode or to start sniffing on a computer.
        :return:
        """
        if self.selected_object is not None and self.selected_object.is_computer:
            self.selected_object.computer.toggle_sniff(is_promisc=True)
        self.set_mode(SIMULATION_MODE)

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

    def create(self, object_type, on_mouse=False):
        """
        Creates an object from a given type.
        :param object_type: an object type that will be created (Computer, Switch, Hub, etc...)
        :param on_mouse: whether or not the object should be created where the mouse is. If this if `False` than the object
        is created in the middle of the screen.
        :return: None
        """
        x, y = WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2
        if on_mouse:
            x, y = MainWindow.main_window.get_mouse_location()

        object = object_type()
        object.show(x, y)
        self.computers.append(object)

    def create_router(self):
        """
        Create a router where the mouse is.
        :return: None
        """
        x, y = MainWindow.main_window.get_mouse_location()

        interfaces = (Interface.with_ip('192.168.1.1'),
                      Interface.with_ip('10.10.10.1'),
                      Interface.with_ip('172.10.3.1'))
        object = Router("Router and DHCP Server", interfaces)
        object.show(x, y)
        self.computers.append(object)

    def two_pressed_computers(self, action):
        """
        This operates the situation when two computers are required to be selected one after the other (like in CONNECTING_MODE,
        PINGING_MODE, etc...)
        :param action: a function that will be activated on the two computers once they are both selected.
            should receive two computers ane return nothing.
        :return: None
        """
        if self.selected_object is not None and self.selected_object.is_computer:
            if self.other_selected_object is None:
                self.other_selected_object = self.selected_object
            else:  # there is another computer to connect with that was already pressed.
                action(self.other_selected_object.computer, self.selected_object.computer)

                self.other_selected_object = None
                self.set_mode(SIMULATION_MODE)

        elif not self.is_mouse_in_side_window() and self.selected_object is None:  # if we press on nothing and not on the side window
            self.other_selected_object = None
            self.set_mode(SIMULATION_MODE)

    def connect_computers(self, computer1, computer2):
        """
        Connect two computers to each other, show the connection and everything....
        :param computer1:
        :param computer2: the two `Computer` object.
        :return: None
        """
        connection = computer1.connect(computer2)
        connection.show(computer1.graphics, computer2.graphics)
        self.connection_data.append(ConnectionData(connection, computer1, computer2))

    def send_direct_ping(self, computer1, computer2):
        """
        Send a ping from `computer1` to `computer2`.
        If one of them does not have an IP address, do nothing.
        :param computer1:
        :param computer2: The `Computer` objects to send a ping between.
        :return: None
        """
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
        if graphics_object.is_computer:
            self.computers.remove(graphics_object.computer)
            self._delete_connections_to(graphics_object.computer)
            self.selected_object = None
            self.dragged_object = None

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
                (computer1 if computer is computer2 else computer2).disconnect(connection)  # disconnect the other computer

                MainLoop.instance.unregister_graphics_object(connection.graphics)
                connection.stop_packets()
                self.connection_data.remove(connection_data)

    def hide_button_group(self, group=None):
        """
        make all of the buttons in a certain button group hidden, if no group is given, hide all
        :param group: a group name (`MAIN_MENU_BUTTONS` for example)
        :return: None
        """
        for button in self.buttons:
            if (group is None) or (button.button_group == group):
                button.hide()

    def show_button_group(self, group):
        """
        make the buttons of a certain button group is_showing, all other groups hidden.
        :param group: a group name (`MAIN_MENU_BUTTONS` for example)
        :return: None
        """
        for button in self.buttons:
            if button.button_group == group:
                button.show()
            else:
                button.hide()

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
        raise NoSuchPacketError("That packet cannot be found!")

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

    def config_ip(self, computer, user_input):
        """
        Config the IP of a computer to be one according to a given user input.
        The user input should be of the syntax '<INTERFACE NAME>, <IP ADDRESS>' or just '<IP ADDRESS>'.
        :param computer: a `Computer` object.
        :param user_input: a string of the mentioned formet.
        :return: None
        """
        if user_input != '':
            if ', ' not in user_input:
                new_ip = user_input
                interface_name = computer.interfaces[0].name
            else:
                interface_name, new_ip = user_input.split(', ')

            try:
                computer.set_ip(interface_name, new_ip)
            except InvalidAddressError:
                print("You have entered an invalid address!!!")
            except NoSuchInterfaceError:
                print("The name you have entered fits no interface!")

    def ask_user_for_ip(self):
        """
        Asks the user for interface name and ip input and sets the computer's IP to be that.
        Does that using popup window in the `TextBox` class.
        :return: None
        """
        if self.selected_object is not None and self.selected_object.is_computer:
            self.is_asking_for_string = True
            computer = self.selected_object.computer
            self.popup_window = TextBox("Enter your desired IP in the form <INTERFACE NAME>, <IP>", with_args(self.config_ip, computer))

    def end_string_request(self):
        """
        If the `UserInterface` Object currently is asking for user input (via the popup window), end that request, unregister the
        asking `TextBox` popup window and set all variables accordingly.
        :return: None
        """
        if not self.is_asking_for_string:
            raise NotAskingForStringError("cannot end string request since currently not asking for string from the user!!")

        self.is_asking_for_string = False
        MainLoop.instance.unregister_graphics_object(self.popup_window)
        self.popup_window = None

    def connect_all_available(self):
        """
        Connects all of the unconnected computers to the latest generated switch or hub
        :return: None
        """
        switches = list(filter(lambda c: isinstance(c, Switch), self.computers))
        for computer in self.computers:
            if isinstance(computer, Switch):
                continue
            nearest_switch = min(switches, key=lambda s: distance(s.graphics.location, computer.graphics.location))
            if not computer.interfaces[0].is_connected():
                self.connect_computers(computer, nearest_switch)

    def ping_switch_with_ip(self):
        """
        Send a ping from a random computer to a switch with an ip. (I used it for testing), if no one uses it it can be deleted.
        :return: None
        """
        switch = get_the_one(self.computers, lambda c: isinstance(c, Switch) and c.has_ip(), NetworkSimulationError)
        pinger = random.choice([computer for computer in self.computers if computer is not switch])
        pinger.start_ping_process(switch.get_ip())

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
        print(f"time: {int(time.time())}, program time: {int(MainLoop.instance.time())}")
        print(f"graphicsObject-s (no buttons or texts): {[go for go in MainLoop.instance.graphics_objects if not isinstance(go, Button) and not isinstance(go, Text)]}")
        print(f"selected object: {self.selected_object}, dragged: {self.dragged_object}")
        print(f"mouse: {MainWindow.main_window.get_mouse_location()}")
        print(f"""computers, {len(self.computers)}, connections, {len(self.connection_data)}, packets: {len(list(filter(lambda go: go.is_packet, MainLoop.instance.graphics_objects)))}""")
        print(f"running processes: ", end='')
        for computer in self.computers:
            processes = [f"{wp.process} of {computer}" for wp in computer.waiting_processes]
            print(processes if processes else '', end=' ')
        print()
        if self.selected_object is not None and self.selected_object.is_computer:
            computer = self.selected_object.computer
            computer.print("------------DEBUG------------------")
            if not isinstance(computer, Switch):
                print(repr(computer.routing_table))
            elif computer.stp_enabled:  # computer is a Switch
                print(computer.get_running_process(STPProcess).get_info())

    def create_computer_with_ip(self):
        """
        Creates a computer with an IP fitting to the computers around it.
        It will look at the nearest computer's subnet, find the max address in that subnet and take the one above it.
        If there no other computers, takes the default IP (DEFAULT_COMPUTER_IP)
        :return: None
        """
        x, y = MainWindow.main_window.get_mouse_location()

        try:
            given_ip = self._get_largest_ip_in_nearest_subnet(x, y)
        except (NoSuchComputerError, NoIPAddressError):      # if there are no computers with IP on the screen.
            given_ip = IPAddress(DEFAULT_COMPUTER_IP)

        new_computer = Computer.with_ip(given_ip)
        self.computers.append(new_computer)
        new_computer.show(x, y)

    def _get_largest_ip_in_nearest_subnet(self, x, y):
        """
        Receives a pair of coordinates, finds the nearest computer's subnet, finds the largest IP address in that subnet
        and returns a copy of it.
        :param x:
        :param y: the coordinates.
        :return: an `IPAddress` object.
        """
        nearest_computers = sorted(self.computers, key=lambda c: sqrt(((x - c.graphics.x) ** 2) + ((y - c.graphics.y) ** 2)))
        nearest_computers_with_ip = list(filter(lambda c: c.has_ip(), nearest_computers))

        try:
            nearest_ip_address = nearest_computers_with_ip[0].get_ip()
        except IndexError:
            raise NoSuchComputerError("There is no such computers!")

        all_ips_in_that_subnet = [IPAddress.copy(computer.get_ip()) for computer in self.computers if computer.has_ip() and computer.get_ip().is_same_subnet(nearest_ip_address)]

        try:
            greatest_ip_in_subnet = max(all_ips_in_that_subnet, key=lambda ip: int(IPAddress.as_bits(ip.string_ip), base=2))
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
            if (computer1 is computer_1 and computer2 is computer_2) or (computer2 is computer_1 and computer1 is computer_2):
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
                if computer is not other_computer and not self.are_connected(computer, other_computer) and random.randint(0, 5) == 1:
                    self.connect_computers(computer, other_computer)

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

    def power_selected_computer(self):
        """Powers off or on the selected object if it is a computer"""
        if self.selected_object is not None:
            if self.selected_object.is_computer:
                self.selected_object.computer.power()

    def set_connection_pl(self, connection, pl_string):
        """
        Receives a number which is a PL percentage and sets it to a connection.
        :param pl_string: a number between 0 and 1 which is the pl percentage the connection will have (in a string form)
        :param connection: a `Connection` object to set the PL to.
        :return: None
        """
        try:
            pl = float(pl_string)
        except ValueError:
            print("invalid PL!!!")
            return

        if not 0 <= pl <= 1:
            print("invalid PL!")
            return
        connection.packet_loss = pl
        connection.graphics.update_color_by_pl(pl)

    def ask_user_for_pl(self, connection_graphics):
        """
        Asks the user for an input to update the PL amount of a `ConnectionGraphics` object.
        :return: None
        """
        self.is_asking_for_string = True
        connection = connection_graphics.connection
        self.popup_window = TextBox("Enter PL amount (a number between 0 and 1):",
                                    with_args(self.set_connection_pl, connection))

    def set_connection_speed(self, connection, speed):
        """
        Sets the speed of a given connection
        :param connection: a `Connection` object
        :param speed: a string that represents a `float` number to set the speed of the connection to.
        :return: None
        """
        try:
            new_speed = float(speed)
        except ValueError:
            print("invalid speed!!")
            return

        connection.speed = new_speed

    def ask_user_for_connection_speed(self, connection_graphics):
        """
        Asks the user to set the Speed of a connection using a `ConnectionGraphics` object that is selected.
        :param connection_graphics: a `ConnectionGraphics` object that is selected and viewed now.
        :return: None
        """
        self.is_asking_for_string = True
        connection = connection_graphics.connection
        self.popup_window = TextBox("Enter new connection speed (pixels/second)",
                                    with_args(self.set_connection_speed, connection))

    def add_buttons(self, dictionary):
        """
        Adds buttons to the side window according to requests of the viewed object.
        :param dictionary: a `dict` of the form {button text: button action}
        :return: None
        """
        buttons_id = 0 if not self.added_buttons else max(self.added_buttons.keys()) + 1
        self.added_buttons[buttons_id] = [
            Button(*DEFAULT_BUTTON_LOCATION(i+1), action, string) for i, (string, action) in enumerate(dictionary.items())
        ]
        return buttons_id

    def remove_buttons(self, buttons_id):
        """
        Unregisters side-view added buttons by their ID. (Buttons that are added using the `self.add_buttons` method.)
        :param buttons_id: an interger returned by the `self.add_buttons` method
        :return: None
        """
        for button in self.added_buttons[buttons_id]:
            MainLoop.instance.unregister_graphics_object(button)
        del self.added_buttons[buttons_id]
