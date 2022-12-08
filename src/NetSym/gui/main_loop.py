from __future__ import annotations

import time
from typing import Type, Optional, TYPE_CHECKING, Callable, Any, List, TypeVar, Dict, Union, Iterable, Sequence

from NetSym.consts import T_Time, MainLoopFunctionPriority
from NetSym.exceptions import *
from NetSym.gui.abstracts.graphics_object import GraphicsObject
from NetSym.gui.main_loop_function_to_call import FunctionToCall

if TYPE_CHECKING:
    pass


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

    def __init__(self) -> None:
        """
        Initiates the MainLoop object
        """
        self.__class__.instance = self

        self.call_functions: Dict[MainLoopFunctionPriority, List[FunctionToCall]] = {priority: [] for priority in MainLoopFunctionPriority}
        # ^ lists of `FunctionToCall` that will all be called in every `update` call

        self.graphics_objects: List[GraphicsObject] = []
        # ^ a list of all registered `GraphicsObject`-s that are being drawn and moved.

        self.is_paused = False
        # ^ whether or not the program is paused now.

        self._time = time.time()  # the time that this will return when the `self.time()` method is called.
        self.paused_time = 0.
        #  ^ the total time the program has been paused so far
        self.last_time_update = time.time()  # the last time that the `self.update_time` method was called.

    @property
    def medium_priority_call_functions(self) -> List[FunctionToCall]:
        return self.call_functions[MainLoopFunctionPriority.MEDIUM]

    @classmethod
    def get_time(cls) -> T_Time:
        """
        This is a class method that returns the time of the MainLoop instance - adjusted to pauses and different speeds (just like the `time` method)
        It allows us to talk about the `time` method (without calling it) even before the `instance` being initiated
        """
        if cls.instance is None:
            raise MainLoopInstanceNotYetInitiated(f"Bummer...")

        return cls.instance.time()

    @classmethod
    def get_time_since(cls, other_time: T_Time) -> T_Time:
        """

        """
        return cls.get_time() - other_time

    def is_registered(self, graphics_object: GraphicsObject) -> bool:
        """
        Return whether or not the supplied `GraphicsObject` is alredy registered in the main loop.
        """
        return graphics_object in self.graphics_objects

    def register_graphics_object(self, graphics_object: Union[GraphicsObject, Sequence[GraphicsObject]], is_in_background: bool = False) -> None:
        """
        This method receives a `GraphicsObject` instance, loads it, and enters
        it into the update main loop with its `move` and `draw` methods.

        If any of the objects supplied is already registered - skip it
        :param graphics_object: The `GraphicsObject` or a list of them
        :param is_in_background: Whether the object will be drawn in the front
            or the back of the other objects.
        """
        graphics_object_sequence = graphics_object if isinstance(graphics_object, Sequence) else [graphics_object]

        for graphics_object_ in graphics_object_sequence:
            if not self.is_registered(graphics_object_):
                graphics_object_.load()
                if is_in_background:
                    self.graphics_objects.insert(0, graphics_object_)
                    self.reversed_insert_to_loop(graphics_object_.draw)
                else:
                    self.graphics_objects.append(graphics_object_)
                    self.insert_to_loop(graphics_object_.draw)

                self.insert_to_loop(graphics_object_.move)
                for function_to_call in graphics_object_.additional_functions_to_register:
                    self.insert_to_loop(function_to_call)

            for child in graphics_object_.get_children():
                self.register_graphics_object(child)

    def unregister_graphics_object(self, graphics_object: GraphicsObject) -> None:
        """
        This method receives a `GraphicsObject` instance and unregisters it.
        It removes its `draw` and `move` methods from the main loop.
        If the object is already unregistered, do nothing.

        Any GraphicsObject that wants to have attributes that are also GraphicsObjects needs to implement
        the `get_children` method and then the returned list is unregistered as well when the main object does.

        :param graphics_object: The `GraphicsObject`
        """
        try:
            self.graphics_objects.remove(graphics_object)
        except ValueError:
            # object is not registered
            print("A graphics object was unregistered - but never registered!!!")

        self.remove_from_loop(graphics_object.draw)
        self.remove_from_loop(graphics_object.move)

        for child in graphics_object.get_children():
            if isinstance(child, GraphicsObject):
                self.unregister_graphics_object(child)

            elif isinstance(child, Iterable):
                for item in child:
                    self.unregister_graphics_object(item)

    def _unregister_requesting_graphics_object(self) -> None:
        """
        Goes over all registered graphics objects
        Checks which of them have the `is_requesting_to_be_unregistered_from_main_loop` flag set
        Unregisters them
        """
        for graphics_object in self.graphics_objects[:]:
            if graphics_object.is_requesting_to_be_unregistered_from_main_loop:
                self.unregister_graphics_object(graphics_object)

    def _register_children_of_requesting_graphics_object(self) -> None:
        """
        Goes over all registered graphics objects
        Checks which of them have the `is_requesting_to_be_unregistered_from_main_loop` flag set

        Registers them again - to make sure all of their children are registered
        """
        for graphics_object in self.graphics_objects:
            if graphics_object.is_requesting_to_register_children:
                self.register_graphics_object(graphics_object)
                graphics_object.is_requesting_to_register_children = False

    def insert_to_loop_prioritized(self,
                                   function: Union[Callable, FunctionToCall],
                                   priority: MainLoopFunctionPriority,
                                   *args: Any,
                                   function_can_be_paused: bool = False,
                                   function_reverse_insert: bool = False,
                                   supply_function_with_main_loop_object: bool = False,
                                   **kwargs: Any,
                                   ) -> None:
        """
        Some functions MUST be called before others! (for example MainWindow.clear must be called first!)
        The priority of a function will determine when in the simulation tick it runs
        First all HIGH priority functions run, then MEDIUM and then LOW
        """
        if isinstance(function, FunctionToCall):
            function_with_args = function
        else:
            function_with_args = FunctionToCall(function, args, kwargs, function_can_be_paused, supply_function_with_main_loop_object)

        if function_reverse_insert:
            self.call_functions[priority].insert(0, function_with_args)
        else:
            self.call_functions[priority].append(function_with_args)
        # debugp(f"{priority}: Added {function.__name__} to {[function.function.__name__ for function in self.call_functions[priority]]}")

    def insert_to_loop(self, function: Union[Callable, FunctionToCall], *args: Any, **kwargs: Any) -> None:
        """
        A 'nice to have' method - is just less parameters for `insert_to_loop_prioritized`

        This method receives a function and inserts it into the main loop of the program. After this is called,
        every clock tick will call the given function with the given arguments.

        :param function: The function to insert
        :param args: Arguments to call it with
        :param kwargs: Key-word arguments to call it with
        :return: None
        """
        self.insert_to_loop_prioritized(function, MainLoopFunctionPriority.MEDIUM, *args, **kwargs)

    def reversed_insert_to_loop(self, function: Callable, *args: Any, **kwargs: Any) -> None:
        """
        A 'nice to have' method - is just less parameters for `insert_to_loop_prioritized`

        This is just like `insert_to_loop` but the function is inserted to the
        head of the list so it is called first. this is done for example so `CableConnection`
        objects will be drawn in the background.
        :param function: The function
        :param args:
        :param kwargs:
        :return: None
        """
        self.insert_to_loop_prioritized(function, MainLoopFunctionPriority.MEDIUM, *args, function_reverse_insert=True, **kwargs)

    def insert_to_loop_pausable(self, function: Callable, *args: Any, **kwargs: Any) -> None:
        """
        A 'nice to have' method - is just less parameters for `insert_to_loop_prioritized`

        It is exactly like it but the function is paused when the program is paused (when space bar is pressed)
        """
        self.insert_to_loop_prioritized(function, MainLoopFunctionPriority.MEDIUM, *args, function_can_be_paused=True, **kwargs)

    def remove_from_loop(self, function: Callable, priority: Optional[MainLoopFunctionPriority] = None) -> None:
        """
        Does the opposite of `insert_to_loop`. removes a given function off the loop.
        If the function is called a few times in the loop, all of the calls are removed.
        :param priority:
        :param function: The function to remove from the loop.
        :return: None
        """
        priorities = [priority] if priority is not None else list(MainLoopFunctionPriority)

        for priority_ in priorities:
            to_remove = [function_and_args for function_and_args in self.medium_priority_call_functions if function_and_args.function == function]
            for function_and_args in to_remove:
                try:
                    self.call_functions[priority_].remove(function_and_args)
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

            for child_graphics_object in graphics_object.get_children():
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

    def graphics_objects_of_types(self, type_: Type[T]) -> List[T]:
        """
        Returns a list of graphics objects of the given types
        """
        return [go for go in self.graphics_objects if isinstance(go, type_)]

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

    def time_since(self, other_time: float) -> T_Time:
        """Returns the amount of time that passed since another time (adjusted to pauses of course)"""
        return self.time() - other_time

    def main_loop(self) -> None:
        """
        The main loop:

        This is the method that is called repeatedly, every clock tick.
        It updates the program and runs all other functions in the main loop.
        The `self.medium_priority_call_functions` list is the list of function that it calls with their arguments.
        :return: None
        """
        function = None
        self.update_time()
        self._unregister_requesting_graphics_object()
        self._register_children_of_requesting_graphics_object()

        try:
            for priority in MainLoopFunctionPriority:
                for function in self.call_functions[priority]:
                    if self.is_paused and function.can_be_paused:
                        continue

                    args = ((self,) + function.args) if function.supply_main_loop_object else function.args
                    function.function(*args, **function.kwargs)
        except AttributeError as e:
            # for some reason pyglet makes AttributeErrors silent - we reraise them or else it is very hard to debug
            print(f"AttributeError!!!! during mainloop '{e.args[0]}' - in function: {function}" if function else '')
            raise