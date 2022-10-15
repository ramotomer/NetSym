from __future__ import annotations

import time
from typing import Type, Iterable, Optional, TYPE_CHECKING, Callable, Any, List, TypeVar

from NetSym.consts import T_Time
from NetSym.exceptions import *
from NetSym.usefuls.funcs import get_the_one

if TYPE_CHECKING:
    from NetSym.gui.abstracts.graphics_object import GraphicsObject
    from NetSym.gui.main_window import MainWindow


T = TypeVar("T")


class MainLoop:
    """
    This class handles everything related to the main loop of the program.
    It holds a list of all of the graphics objects that have registered their methods to the loop.
    (read more about these in 'gui.graphics_object.py') It contains the main loop of the program, and contains methods
    that allow us to insert new function calls into the main loop.

    There is only one instance of this class. That instance is saved in the class attribute `MainLoop.instance`
    """
    instance: Optional[MainLoop] = None

    def __init__(self, main_window: MainWindow) -> None:
        """
        Initiates the MainLoop object with a main window.
        :param main_window: a `MainWindow` object.
        """
        self.__class__.instance = self
        self.main_window = main_window

        self.call_functions = []
        # ^ a list of tuples (function, args, kwargs) that will all be called in every `update` call

        self.graphics_objects = []
        # ^ a list of all registered `GraphicsObject`-s that are being drawn and moved.

        self.is_paused = False
        # ^ whether or not the program is paused now.

        self._time = time.time()  # the time that this will return when the `self.time()` method is called.
        self.paused_time = 0
        #  ^ the total time the program has been paused so far
        self.last_time_update = time.time()  # the last time that the `self.update_time` method was called.

        self.main_window.user_interface.initiate_buttons()
        # ^ creates the buttons of the user interface.

        # self.logo_animation = self.main_window.user_interface.init_logo_animation()

    @classmethod
    def get_instance_time(cls) -> T_Time:
        """
        This is a class method that returns the time of the MainLoop instance - adjusted to pauses and different speeds (just like the `time` method)
        It allows us to talk about the `time` method (without calling it) even before the `instance` being initiated
        """
        if cls.instance is None:
            raise MainLoopInstanceNotYetInitiated(f"Bummer...")

        return cls.instance.time()

    def register_graphics_object(self, graphics_object: GraphicsObject, is_in_background: bool = False) -> None:
        """
        This method receives a `GraphicsObject` instance, loads it, and enters
        it into the update main loop with its `move` and `draw` methods.
        :param graphics_object: The `GraphicsObject`
        :param is_in_background: Whether the object will be drawn in the front
            or the back of the other objects.
        :return: None
        """
        graphics_object.load()

        if is_in_background:
            self.graphics_objects.insert(0, graphics_object)
            self.reversed_insert_to_loop(graphics_object.draw)
        else:
            self.graphics_objects.append(graphics_object)
            self.insert_to_loop(graphics_object.draw)

        self.insert_to_loop(graphics_object.move)

    def unregister_graphics_object(self, graphics_object: GraphicsObject) -> None:
        """
        This method receives a `GraphicsObject` instance and unregisters it.
        It removes its `draw` and `move` methods from the main loop.
        If the object is already unregistered, do nothing.

        Any GraphicsObject that wants to have attributes that are also GraphicsObjects needs to have an iterable
        which is called `child_graphics_objects` and that list is unregistered as well when the main object does.

        :param graphics_object: The `GraphicsObject`
        :return: None
        """
        try:
            self.graphics_objects.remove(graphics_object)
        except ValueError:
            # object is not registered
            pass

        self.remove_from_loop(graphics_object.draw)
        self.remove_from_loop(graphics_object.move)

        if hasattr(graphics_object, "child_graphics_objects"):
            for child in graphics_object.child_graphics_objects:
                self.unregister_graphics_object(child)

    def insert_to_loop(self, function: Callable, *args: Any, **kwargs: Any) -> None:
        """
        This method receives a function and inserts it into the main loop of the program. After this is called,
        every clock tick will call the given function with the given arguments.

        :param function: The function to insert
        :param args: Arguments to call it with
        :param kwargs: Key-word arguments to call it with
        :return: None
        """
        self.call_functions.append((function, args, kwargs, False))  # the False is for "can it be paused"

    def reversed_insert_to_loop(self, function: Callable, *args: Any, **kwargs: Any) -> None:
        """
        This is just like `insert_to_loop` but the function is inserted to the
        head of the list so it is called first. this is done for example so `Connection`
        objects will be drawn in the background.
        :param function: The function
        :param args:
        :param kwargs:
        :return: None
        """
        self.call_functions.insert(0, (function, args, kwargs, False))  # the False is "can it be paused"

    def insert_to_loop_pausable(self, function: Callable, *args: Any, **kwargs: Any) -> None:
        """
        Exactly like `insert_to_loop` but the function is paused when the program is paused (when space bar is pressed)
        """
        self.call_functions.append((function, args, kwargs, True))

    def remove_from_loop(self, function: Callable) -> None:
        """
        Does the opposite of `insert_to_loop`. removes a given function off the loop.
        If the function is called a few times in the loop, all of the calls are removed.
        :param function: The function to remove from the loop.
        :return: None
        """
        to_remove = [function_and_args for function_and_args in self.call_functions if function_and_args[0] == function]
        for function_and_args in to_remove:
            try:
                self.call_functions.remove(function_and_args)
            except ValueError:
                pass

    def move_to_front(self, graphics_object: GraphicsObject) -> None:
        """
        Receives a graphics object that is registered and moves it to the front to be on top of all other registered
        graphics objects
        :param graphics_object: a `GraphicsObject` object that is registered
        :return: None
        """
        try:
            self.graphics_objects.remove(graphics_object)
            self.graphics_objects.append(graphics_object)

            self.remove_from_loop(graphics_object.draw)
            self.insert_to_loop(graphics_object.draw)

            if hasattr(graphics_object, "child_graphics_objects"):
                for child_graphics_object in graphics_object.child_graphics_objects:
                    self.move_to_front(child_graphics_object)
                    # if this is not the order that they were meant to be in, this might cause bugs, fix in the future
                    # if necessary

        except ValueError:
            raise NoSuchGraphicsObjectError(f"The graphics object is not registered!!! object: {graphics_object!r}")

    def toggle_pause(self) -> None:
        """
        Toggles the pause
        :return:
        """
        self.is_paused = not self.is_paused

    def select_selected_and_marked_objects(self) -> None:
        """
        Draws a rectangle around the selected object.
        The selected object is the object that was last pressed and is surrounded by a white square.
        :return: None
        """
        if self.main_window.user_interface.selected_object is not None:
            self.main_window.user_interface.selected_object.mark_as_selected()

        for marked_object in self.main_window.user_interface.marked_objects:
            marked_object.mark_as_selected_non_resizable()

    def get_object_the_mouse_is_on(self, exclude_types: Iterable[Type] = ()) -> GraphicsObject:
        """
        Returns the `GraphicsObject` that should be selected if the mouse is pressed
        (so the object that the mouse is on right now) or `None` if the mouse is not resting upon any object.
        :return: a `GraphicsObject` or None.
        """
        return get_the_one(reversed(self.graphics_objects), lambda go: go.is_mouse_in() and not isinstance(go, tuple(exclude_types)))

    def graphics_objects_of_types(self, *types: Type[T]) -> List[T]:
        """
        Returns a list of graphics objects of the given types
        :param types:
        :return:
        """
        if not types:
            return self.graphics_objects
        return list(filter(lambda go: any(isinstance(go, type_) for type_ in types), self.graphics_objects))

    def update_time(self) -> None:
        """
        Updates the time that the `self.time()` method returns, adjusted to pauses.
        :return: None
        """
        if not self.is_paused:
            self._time = (time.time() - self.paused_time)
        else:  # if the program is paused now
            self.paused_time += (time.time() - self.last_time_update)
            # ^ add to `self.paused_time` the amount of time since the last update.

        self.last_time_update = time.time()

    def time(self) -> T_Time:
        """
        This method is just like the `time.time()` method, with one different, when the program is paused, the time does
        not run. this is very important for some processes (STP, TCP, Switches, etc...)
        :return:
        """
        return self._time

    def time_since(self, other_time) -> T_Time:
        """Returns the amount of time that passed since another time (adjusted to pauses of course)"""
        return self.time() - other_time

    def main_loop(self) -> None:
        """
        The main loop:

        This is the method that is called repeatedly, every clock tick.
        It updates the program and runs all other functions in the main loop.
        The `self.call_functions` list is the list of function that it calls with their arguments.
        :return: None
        """
        function = None
        self.main_window.clear()

        self.update_time()
        self.select_selected_and_marked_objects()
        self.main_window.user_interface.show()

        try:
            for function, args, kwargs, can_be_paused in self.call_functions:
                if self.is_paused and can_be_paused:
                    continue
                function(*args, **kwargs)
        except AttributeError as e:
            # for some reason pyglet makes AttributeErrors silent - we reraise them or else it is very hard to debug
            print(f"AttributeError!!!! during mainloop '{e.args[0]}' - in function: {function}" if function else '')
            raise
