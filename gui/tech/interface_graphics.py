from address.mac_address import MACAddress
from consts import *
from exceptions import *
from gui.abstracts.graphics_object import GraphicsObject
from gui.abstracts.image_graphics import ImageGraphics
from gui.main_window import MainWindow
from gui.shape_drawing import draw_rect, draw_rect_no_fill
from usefuls import distance, circular_coordinates, with_args, get_the_one


class InterfaceGraphics(GraphicsObject):
    """
    This is the graphics of a network interface of a computer.
    It is the little square next to computers.
    It allows the user much more control over their computers and to inspect the interfaces of their computers.
    """
    def __init__(self, x, y, interface, computer_graphics):
        """
        initiates the object.
        :param x:
        :param y: the location
        :param interface: the physical `Interface` of the computer.
        :param computer_graphics: the graphics object of the computer that this interface belongs to.
        """
        super(InterfaceGraphics, self).__init__(x, y, centered=True, is_in_background=True, is_pressable=True)
        self.color = interface.display_color
        self.real_x, self.real_y = x, y
        self.width, self.height = INTERFACE_WIDTH, INTERFACE_HEIGHT
        self.computer_graphics = computer_graphics

        self.interface = interface
        interface.graphics = self

        self.buttons_id = None

    @property
    def location(self):
        return self.real_x, self.real_y

    @property
    def computer_location(self):
        return self.computer_graphics.location

    def is_mouse_in(self):
        """
        Returns whether or not the mouse is pressing the interface
        :return:
        """
        x, y = MainWindow.main_window.get_mouse_location()
        return self.real_x - (self.width / 2) < x < self.real_x + (self.width / 2) and \
               self.real_y - (self.height / 2) < y < self.real_y + (self.height / 2)

    def move(self):
        """
        Moves the interface.
        Keeps it within `INTERFACE_DISTANCE_FROM_COMPUTER` pixels away from the computer.
        :return:
        """
        if self.interface.is_connected():
            start_computer, end_comp = self.interface.connection.connection.graphics.computers
            other_computer = start_computer if self.computer_graphics is end_comp else end_comp
            self.x, self.y = other_computer.location
        computer_x, computer_y = self.computer_location
        dist = distance((computer_x, computer_y), (self.x, self.y)) / self.computer_graphics.interface_distance()
        dist = dist if dist else 1  # cannot be 0

        self.real_x, self.real_y = ((self.x - computer_x) / dist) + computer_x, ((self.y - computer_y) / dist) + computer_y
        self.x, self.y = self.real_x, self.real_y

    def draw(self):
        """
        Draw the interface.
        :return:
        """
        draw_rect(
            self.real_x - (self.width/2), self.real_y - (self.height / 2),
            self.width, self.height,
            self.color,
        )

    def start_viewing(self, user_interface):
        """
        Starts the side-window-view of the interface.
        :param user_interface: a `UserInterface` object to register the buttons in.
        :return: `Sprite`, `str`, `int`
        """
        buttons = {
            "config IP (i)": user_interface.ask_user_for_ip,
            "change MAC (^m)": with_args(
                user_interface.ask_user_for,
                MACAddress,
                "Insert a new mac address:",
                self.interface.set_mac,
            ),
            "change name (shift+n)": with_args(
                user_interface.ask_user_for,
                str,
                "Insert new name:",
                self.interface.set_name,
            ),
            "sniffing start/stop (f)": with_args(
                get_the_one(user_interface.computers,
                            lambda c: self.interface in c.interfaces,
                            NoSuchInterfaceError).toggle_sniff,
                self.interface.name,
                is_promisc=True),
            "block (^b)": with_args(self.interface.toggle_block, "STP"),
        }
        self.buttons_id = user_interface.add_buttons(buttons)
        copied_sprite = ImageGraphics.get_image_sprite(os.path.join(IMAGES_DIR, INTERFACE_VIEW_IMAGE))
        return copied_sprite, self.interface.generate_view_text(), self.buttons_id

    def end_viewing(self, user_interface):
        """
        Unregisters the buttons from the `UserInterface` object.
        :param user_interface:
        :return:
        """
        user_interface.remove_buttons(self.buttons_id)

    def mark_as_selected(self):
        """
        Marks a rectangle around a `GraphicsObject` that is selected.
        Only call this function if the object is selected.
        :return: None
        """
        x, y = self.x - (self.width / 2), self.y - (self.height / 2)
        draw_rect_no_fill(x - SELECTED_OBJECT_PADDING,
                          y - SELECTED_OBJECT_PADDING,
                          self.width + (2 * SELECTED_OBJECT_PADDING),
                          self.height + (2 * SELECTED_OBJECT_PADDING))

    def __repr__(self):
        return f"Interface Graphics ({self.interface.name})"

    def dict_save(self):
        """
        Save the interface as a dict that can be later reconstructed to a new interface
        :return:
        """
        return {
            "class": "Interface",
            "location": (self.real_x, self.real_y),
            "name": self.interface.name,
            "mac": str(self.interface.mac),
            "ip": str(self.interface.ip) if self.interface.ip is not None else None,
            "color": self.color,
            "is_blocked": self.interface.is_blocked,
        }


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
        x, y = ix, iy
        if ix is None and iy is None:
            x, y = self.computer_graphics.x + self.computer_graphics.interface_distance(), self.computer_graphics.y

        interface_graphics = InterfaceGraphics(x, y, interface, self.computer_graphics)
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
