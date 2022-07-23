from consts import *
from exceptions import UnknownPortError
from gui.abstracts.graphics_object import GraphicsObject
from gui.abstracts.image_graphics import ImageGraphics
from gui.main_loop import MainLoop


class ProcessGraphicsList(GraphicsObject):
    """
    A graphics object which is just a list of `ProcessGraphics`
    """

    def __init__(self, server_graphics):
        """
        initiates the list empty.
        """
        super(ProcessGraphicsList, self).__init__(*server_graphics.location, do_render=False)
        self.server_graphics = server_graphics
        self.child_graphics_objects = []
        self.process_count = 0

    def add(self, port):
        """Add a new process to the list"""
        self.child_graphics_objects.append(ProcessGraphics(port, self.server_graphics, self.process_count))
        # TODO: add a separate list for UDP ports (maybe the drawings of tcp have red glow and udp has blue glow IDK...)
        self.process_count += 1

    def remove(self, port):
        """
        Removes a process from the list and unregisters it.
        :param port:
        :return:
        """
        found = False
        for process_graphics in self.child_graphics_objects[:]:
            if process_graphics.port == port:
                MainLoop.instance.unregister_graphics_object(process_graphics)
                found = True
            elif found:
                process_graphics.process_index -= 1
        if not found:
            raise UnknownPortError(f"The port is not the process list!!! {port}")

    def clear(self):
        """
        Clears the list
        :return:
        """
        for process_graphics in self.child_graphics_objects[:]:
            self.remove(process_graphics.port)
        self.process_count = 0

    def __contains__(self, item):
        """
        Enables the notation '<port num> in <process graphics list>'
        :param item: a port number
        :return:
        """
        for process_graphics in self.child_graphics_objects:
            if process_graphics.port == item:
                return True
        return False

    def __iter__(self):
        """enables running over the list"""
        return iter([pg.port for pg in self.child_graphics_objects])

    def draw(self):
        """Is not drawn..."""
        pass

    def __repr__(self):
        return f"Process Graphics List {[pg.port for pg in self.child_graphics_objects]}"

    def dict_save(self):
        return None


class ProcessGraphics(ImageGraphics):
    """
    The graphics of a TCP process that is running on a server
    """

    def __init__(self, port, server_graphics, process_index):
        """
        Initiates the process graphics from a port number
        :param :
        :param :
        :param :
        """
        super(ProcessGraphics, self).__init__(os.path.join(DIRECTORIES.IMAGES, PORTS.TO_IMAGES[port]) if port in PORTS.TO_IMAGES else None,
                                              *server_graphics.location, True, scale_factor=IMAGES.SCALE_FACTORS.PROCESSES)
        self.server_graphics = server_graphics
        self.process_index = process_index
        self.port = port

    def is_mouse_in(self):
        """Cannot be pressed"""
        return False

    def move(self):
        """
        Moves the process according to the location of the server it runs on.
        :return: None
        """
        pad_x, pad_y = IMAGES.PROCESSES.PADDING
        self.x = self.server_graphics.x + pad_x
        self.y = self.server_graphics.y + pad_y + (self.process_index * IMAGES.PROCESSES.GAP)
        super(ProcessGraphics, self).move()

    def __repr__(self):
        return f"Process Graphics {self.port}"

    def dict_save(self):
        return None
