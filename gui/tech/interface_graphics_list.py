from consts import INTERFACES
from exceptions import NoSuchInterfaceError
from gui.abstracts.graphics_object import GraphicsObject
from gui.tech.interface_graphics import InterfaceGraphics
from gui.tech.wireless_interface_graphics import WirelessInterfaceGraphics
from usefuls.funcs import circular_coordinates


class InterfaceGraphicsList(GraphicsObject):
    """
    A graphics object that groups together all of the `InterfaceGraphics` objects.
    Allows unregistering them, adding them and manipulating them together with an easy APIs
    """
    def __init__(self, computer_graphics):
        """
        Initiates the interfaces with a computer that owns them.
        :param computer_graphics: `ComputerGraphics` object.
        """
        super(InterfaceGraphicsList, self).__init__(*computer_graphics.location, do_render=False)
        interfaces = computer_graphics.computer.interfaces

        self.child_graphics_objects = []
        self.computer_graphics = computer_graphics

        coords = circular_coordinates(computer_graphics.location, computer_graphics.interface_distance(), len(interfaces))
        for i, coordinate in enumerate(coords):
            self.add(interfaces[i], *coordinate)

    def draw(self):
        pass

    def contains_interface(self, interface):
        """
        whether or not an interface is shown in this list.
        :param interface: `Interface`
        :return:
        """
        return any(interface_graphics.interface is interface for interface_graphics in self.child_graphics_objects)

    def add(self, interface, ix=None, iy=None):
        """
        Adds an interface graphics object to the interface graphics list.
        :return:
        """
        interface_type_to_graphics_class = {
            INTERFACES.TYPE.ETHERNET: InterfaceGraphics,
            INTERFACES.TYPE.WIFI: WirelessInterfaceGraphics,
        }

        x, y = ix, iy
        if ix is None and iy is None:
            x, y = self.computer_graphics.x + self.computer_graphics.interface_distance(), self.computer_graphics.y

        graphics_class = interface_type_to_graphics_class[interface.type]

        interface_graphics = graphics_class(x, y, interface, self.computer_graphics)
        self.child_graphics_objects.append(interface_graphics)
        interface.graphics = interface_graphics

    def remove(self, interface):
        """
        Remove an interface from the list.
        :param interface:
        :return:
        """
        if not self.contains_interface(interface):
            raise NoSuchInterfaceError(f"The interface graphics list does not contains this interface {interface}")

        interface_graphics = None
        for interface_graphics in self.child_graphics_objects:
            if interface_graphics.interface is interface:
                break
        self.child_graphics_objects.remove(interface_graphics)

    def __repr__(self):
        return f"Interface Graphics list ({len(self.child_graphics_objects)})"

    def dict_save(self):
        return None
