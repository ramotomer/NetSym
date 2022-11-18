from __future__ import annotations

from typing import List, TYPE_CHECKING, Set, Iterable

from NetSym.consts import PORTS, IMAGES, T_Port
from NetSym.exceptions import UnknownPortError
from NetSym.gui.abstracts.graphics_object import GraphicsObject
from NetSym.gui.abstracts.image_graphics import ImageGraphics

if TYPE_CHECKING:
    from NetSym.gui.tech.computer_graphics import ComputerGraphics


class ProcessGraphicsList(GraphicsObject):
    """
    A graphics object which is just a list of `ProcessGraphics`
    """

    def __init__(self, server_graphics: ComputerGraphics) -> None:
        """
        initiates the list empty.
        """
        super(ProcessGraphicsList, self).__init__(*server_graphics.location, do_render=False)
        self.server_graphics = server_graphics
        self.child_graphics_objects: List[ProcessGraphics] = []
        self.process_count = 0

    @property
    def set_of_all_ports(self) -> Set[T_Port]:
        return {process_graphics.port for process_graphics in self.child_graphics_objects}

    def add(self, port: T_Port) -> None:
        """Add a new process to the list"""
        self.child_graphics_objects.append(ProcessGraphics(port, self.server_graphics, self.process_count))
        self.process_count += 1
        self.register_children()

    def remove(self, port: T_Port) -> None:
        """
        Removes a process from the list and unregisters it.
        :param port:
        :return:
        """
        found = False
        for process_graphics in self.child_graphics_objects[:]:
            if process_graphics.port == port:
                process_graphics.unregister()
                self.child_graphics_objects.remove(process_graphics)
                found = True
            elif found:
                process_graphics.process_index -= 1
                # ^ move down the processes that are above the removed one
        if not found:
            raise UnknownPortError(f"The port is not the process list!!! {port}")

    def set_list(self, list_: List[int]) -> None:
        """
        Sets the list of ports to the supplied list
        """
        if set(list_) == self.set_of_all_ports:
            return  # EFFICIENCY!!!

        self.clear()
        for port in list_:
            self.add(port)

    def clear(self) -> None:
        """
        Clears the list
        :return:
        """
        for process_graphics in self.child_graphics_objects[:]:
            self.remove(process_graphics.port)
        self.process_count = 0

    def __contains__(self, item: T_Port) -> bool:
        """
        Enables the notation '<port num> in <process graphics list>'
        :param item: a port number
        :return:
        """
        for process_graphics in self.child_graphics_objects:
            if process_graphics.port == item:
                return True
        return False

    def __iter__(self) -> Iterable[T_Port]:
        """enables running over the list"""
        return iter([pg.port for pg in self.child_graphics_objects])

    def draw(self) -> None:
        """Is not drawn..."""
        pass

    def __repr__(self) -> str:
        return f"<< ProcessGraphicsList {[pg.port for pg in self.child_graphics_objects]} >>"

    def dict_save(self) -> None:
        pass


class ProcessGraphics(ImageGraphics):
    """
    The graphics of a TCP process that is running on a server
    """

    def __init__(self,
                 port: T_Port,
                 server_graphics: ComputerGraphics,
                 process_index: int) -> None:
        """
        Initiates the process graphics from a port number
        """
        super(ProcessGraphics, self).__init__(PORTS.TO_IMAGES.get(port, None), *server_graphics.location, True,
                                              scale_factor=IMAGES.SCALE_FACTORS.PROCESSES)
        self.server_graphics = server_graphics
        self.process_index = process_index
        self.port = port

    def is_in(self, x: float, y: float) -> bool:
        """Cannot be pressed"""
        return False

    def move(self) -> None:
        """
        Moves the process according to the location of the server it runs on.
        :return: None
        """
        pad_x, pad_y = IMAGES.PROCESSES.PADDING
        self.x = self.server_graphics.x + pad_x
        self.y = self.server_graphics.y + pad_y + (self.process_index * IMAGES.PROCESSES.GAP)
        super(ProcessGraphics, self).move()

    def __str__(self) -> str:
        return "ProcessGraphics"

    def __repr__(self) -> str:
        return f"<< ProcessGraphics of port {self.port} on computer {self.server_graphics.computer.name!r} >>"

    def dict_save(self) -> None:
        pass
