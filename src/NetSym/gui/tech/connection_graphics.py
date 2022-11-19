from __future__ import annotations

import os
from math import acos, sin
from typing import TYPE_CHECKING, NamedTuple, Optional, Dict, Callable, Tuple, List

import pyglet

from NetSym.consts import CONNECTIONS, PACKET, SELECTED_OBJECT, MESSAGES, DIRECTORIES, IMAGES
from NetSym.exceptions import *
from NetSym.gui.abstracts.different_color_when_hovered import DifferentColorWhenHovered
from NetSym.gui.abstracts.image_graphics import ImageGraphics
from NetSym.gui.abstracts.selectable import Selectable
from NetSym.gui.main_loop_function_to_call import FunctionToCall
from NetSym.gui.shape_drawing import draw_line
from NetSym.gui.shape_drawing import draw_rectangle
from NetSym.gui.user_interface.viewable_graphics_object import ViewableGraphicsObject
from NetSym.usefuls.funcs import distance
from NetSym.usefuls.funcs import with_args, get_the_one

if TYPE_CHECKING:
    from NetSym.computing.connection import Connection
    from NetSym.gui.tech.computer_graphics import ComputerGraphics
    from NetSym.gui.tech.interface_graphics import InterfaceGraphics
    from NetSym.gui.user_interface.user_interface import UserInterface
    from NetSym.gui.main_loop import MainLoop


class Computers(NamedTuple):
    """
    A data structure to save the two ComputerGraphics of the two sides of the connection.
    """
    start: Optional[ComputerGraphics]
    end:   Optional[ComputerGraphics]


class Interfaces(NamedTuple):
    """
    A data structure to save the two InterfaceGraphics of the two sides of the connection.
    """
    start: Optional[InterfaceGraphics]
    end:   Optional[InterfaceGraphics]


class ConnectionGraphics(ViewableGraphicsObject, DifferentColorWhenHovered, Selectable):
    """
    This is a GraphicsObject subclass which displays a connection.
    It shows the graphics of the connection (a line) between the two endpoints it is connected to.
    """
    def __init__(self,
                 connection: Connection,
                 computer_graphics_start: Optional[ComputerGraphics],
                 computer_graphics_end: Optional[ComputerGraphics],
                 packet_loss: float = 0,
                 width: float = CONNECTIONS.DEFAULT_WIDTH,
                 ) -> None:
        """
        Initiates the Connection Graphics object which is basically a line between
        two dots (the two ends of the connection).
        It is given two `ComputerGraphics` objects which are the graphics of the computers that are connected on each
        side of this connection. They are used for their coordinates.
        :param connection: the `Connection` object which is the connection that is being drawn
        :param computer_graphics_start: The computer graphics at the beginning of the connection.
        :param computer_graphics_end: The computer graphics at the end of the connection.
        :param packet_loss: the PL percent of the connection (defaults to 0)
        """
        super(ConnectionGraphics, self).__init__(0, 0, is_in_background=True, is_pressable=True)
        self.computers = Computers(computer_graphics_start, computer_graphics_end)
        self.regular_color = CONNECTIONS.COLOR if not packet_loss else CONNECTIONS.PL_COLOR
        self.color = self.regular_color
        self.width = width
        self.marked_as_blocked = False

        self.connection = connection  # the `Connection` object.

        self.interfaces = Interfaces(None, None)

        if all(computer is not None for computer in self.computers):
            self.interfaces = Interfaces(
                get_the_one(
                    self.start_computer.computer.interfaces,
                    lambda i: i.connection is not None and i.connection.connection is connection,
                    NoSuchInterfaceError,
                ).graphics,
                get_the_one(
                    self.end_computer.computer.interfaces,
                    lambda i: i.connection is not None and i.connection.connection is connection,
                    NoSuchInterfaceError,
                ).graphics,
            )

    @property
    def length(self) -> float:  # the length of the connection.
        return distance(self.interfaces.start.location, self.interfaces.end.location)

    @property
    def start_computer(self) -> ComputerGraphics:
        if self.computers.start is None:
            raise ConnectionComputerNotDefined(f"The start computer of the connection was never defined! "
                                               f"The connection is probably disconnected on that end!")

        return self.computers.start

    @property
    def end_computer(self) -> ComputerGraphics:
        if self.computers.end is None:
            raise ConnectionComputerNotDefined(f"The end computer of the connection was never defined! "
                                               f"The connection is probably disconnected on that end!")

        return self.computers.end

    def set_hovered_color(self):
        self.color = CONNECTIONS.SELECTED_COLOR

    def set_normal_color(self):
        self.color = self.regular_color

    def move_packets(self, main_loop: MainLoop) -> None:
        """
        This is temporary i promise
        """
        self.connection.move_packets(main_loop)

    @property
    def additional_functions_to_register(self) -> List[FunctionToCall]:
        return [FunctionToCall(self.move_packets, can_be_paused=True, supply_main_loop_object=True)]

    def update_appearance(self) -> None:
        """Updates the color of the connection according to the PL and latency of the connection"""
        self.regular_color = CONNECTIONS.COLOR if not self.connection.packet_loss else CONNECTIONS.PL_COLOR
        self.color = self.color if all(not side.is_blocked for side in self.connection.get_sides()) else CONNECTIONS.BLOCKED_COLOR

        self.width = CONNECTIONS.DEFAULT_WIDTH if not self.connection.latency else CONNECTIONS.LATENCY_WIDTH

    def is_in(self, x: float, y: float) -> bool:
        """Returns whether or not the mouse is close enough to the connection for it to count as pressed"""
        if any(interface is None for interface in self.interfaces):
            pass
        location = x, y
        a = distance(self.interfaces.start.location, location)
        b = distance(self.interfaces.end.location, location)
        c = distance(self.interfaces.start.location, self.interfaces.end.location)
        if b > c or a > c:
            return False

        if 2*a*c == 0:
            return True

        cos_of_beta = (c**2 + a**2 - b**2) / (2 * a * c)
        beta = 0
        try:
            beta = acos(cos_of_beta)  # the law of the cosines
        except ValueError:
            pass
        mouse_distance_to_connection = a * sin(beta)
        return mouse_distance_to_connection <= CONNECTIONS.MOUSE_TOUCH_SENSITIVITY

    def get_coordinates(self, direction: str = PACKET.DIRECTION.RIGHT) -> Tuple[float, float, float, float]:
        """
        Return a tuple of the coordinates at the start and the end of the connection.
        Receives a `direction` that the we look at the connection from (to know which is the end and which is the start)
        If the connection is opposite the coordinates will also be flipped.
        :param direction: `PACKET.DIRECTION.RIGHT` or `PACKET.DIRECTION.LEFT`.
        :return: (self.start_computer.x, self.start_computer.y, self.end_computer.x, self.end_computer.y)
        """
        if direction == PACKET.DIRECTION.RIGHT:
            return self.interfaces.start.x, self.interfaces.start.y, self.interfaces.end.x, self.interfaces.end.y
        elif direction == PACKET.DIRECTION.LEFT:
            return self.interfaces.end.x, self.interfaces.end.y, self.interfaces.start.x, self.interfaces.start.y
        raise WrongUsageError("a packet can only go left or right!")

    def get_computer_coordinates(self, direction: str = PACKET.DIRECTION.RIGHT) -> Tuple[float, float, float, float]:
        """
        Return a tuple of the coordinates at the start and the end of the connection.
        Receives a `direction` that we look at the connection from (to know which is the end and which is the start)
        If the connection is opposite the coordinates will also be flipped.
        :param direction: `PACKET.DIRECTION.RIGHT` or `PACKET.DIRECTION.LEFT`.
        :return: (self.start_computer.x, self.start_computer.y, self.end_computer.x, self.end_computer.y)
        """
        if direction == PACKET.DIRECTION.RIGHT:
            return self.start_computer.x, self.start_computer.y, self.end_computer.x, self.end_computer.y
        elif direction == PACKET.DIRECTION.LEFT:
            return self.end_computer.x, self.end_computer.y, self.start_computer.x, self.start_computer.y
        raise WrongUsageError("a packet can only go left or right!")

    def packet_location(self, direction: str, progress: float) -> Tuple[float, float]:
        """
        Returns the location of the packet in the connection based of its direction and its progress in it
        This method knows the start and end coordinates of the travel of the packet
        in the connection and it also knows the progress percent.
        It calculates (with a vector based calculation) the current coordinates of the packet
        on the screen.

        :param direction: the direction the packet is going in the connection.
        :param progress: the progress of the packet through the connection.
        :return: returns coordinates of the packet according to that
        """
        start_x, start_y, end_x, end_y = self.get_computer_coordinates(direction)
        return ((((end_x - start_x) * progress) + start_x),
                (((end_y - start_y) * progress) + start_y))

    def mark_as_selected(self) -> None:
        """
        Marks a rectangle around a `GraphicsObject` that is selected.
        Only call this function if the object is selected.
        :return: None
        """
        start_x, start_y, end_x, end_y = self.get_coordinates()
        x, y = (start_x + end_x) / 2, (start_y + end_y) / 2
        draw_rectangle(
            x - 2*SELECTED_OBJECT.PADDING,
            y - 2*SELECTED_OBJECT.PADDING,
            (4 * SELECTED_OBJECT.PADDING),
            (4 * SELECTED_OBJECT.PADDING),
            outline_color=SELECTED_OBJECT.COLOR,
        )

    def draw(self) -> None:
        """
        Draws the connection (The line) between its end point and its start point.
        :return: None
        """
        self.update_appearance()
        sx, sy, ex, ey = self.get_coordinates()
        draw_line((sx, sy), (ex, ey), self.color, self.width)

    def start_viewing(self,
                      user_interface: UserInterface,
                      additional_buttons: Optional[Dict[str, Callable[[], None]]] = None) -> Tuple[pyglet.sprite.Sprite, str, int]:
        """
        Starts the viewing of this object in the side window.
        """
        buttons = {
            "Set PL amount (alt+p)": with_args(user_interface.ask_user_for, float, MESSAGES.INSERT.PL,      self.connection.set_pl),
            "Set speed (alt+s)":     with_args(user_interface.ask_user_for, float, MESSAGES.INSERT.SPEED,   self.connection.set_speed),
            "Set latency (alt+l)":   with_args(user_interface.ask_user_for, float, MESSAGES.INSERT.LATENCY, self.connection.set_latency),
        }

        buttons.update(additional_buttons or {})
        self.buttons_id = user_interface.add_buttons(buttons)
        copied_sprite = ImageGraphics.get_image_sprite(os.path.join(DIRECTORIES.IMAGES, IMAGES.VIEW.CONNECTION))

        return copied_sprite, self.generate_view_text(), self.buttons_id

    def generate_view_text(self) -> str:
        """
        Generates the text that is under the buttons in the side-window when the connection is viewed.
        :return: None
        """
        return f"\nConnection:\n\nfrom: {self.start_computer.computer.name}\nto: " \
            f"{self.end_computer.computer.name}\nlength: {str(self.connection.length)[:6]} pixels\nspeed: " \
            f"{self.connection.speed} pixels/second\ndeliver time: {str(self.connection.deliver_time)[:4]} seconds" \
            f"\nPL percent: {self.connection.packet_loss}"

    def dict_save(self) -> Dict:
        """
        Save the connection as a dictionary in order to later save it to a file
        :return:
        """
        return {
            "class": "Connection",
            "packet_loss": self.connection.packet_loss,
            "speed": self.connection.speed,
            "start": {
                "computer": self.start_computer.computer.name,
                "interface": get_the_one(
                                self.start_computer.computer.interfaces,
                                lambda i: i.is_connected() and i.connection.connection is self.connection,
                                ThisCodeShouldNotBeReached,
                            ).name,
            },
            "end": {
                "computer": self.end_computer.computer.name,
                "interface": get_the_one(
                                self.end_computer.computer.interfaces,
                                lambda i: i.is_connected() and i.connection.connection is self.connection,
                                ThisCodeShouldNotBeReached,
                            ).name,
            },
        }

    def delete(self, user_interface: UserInterface) -> None:
        """
        Delete the connection and disconnect it from both sides
        :param user_interface:
        :return:
        """
        super(ConnectionGraphics, self).delete(user_interface)
        user_interface.remove_connection(self.connection)

    def __str__(self) -> str:
        return "ConnectionGraphics"

    def __repr__(self) -> str:
        return f"<< ConnectionGraphics between ({self.start_computer.computer.name!r}, {self.end_computer.computer.name!r}) >>"
