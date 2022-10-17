from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Tuple, Any, Dict


@dataclass
class FunctionToCall:
    """
    Represents a function that should be called every tick of the simulation.

    function:                The object to call when calling the function
    args:                    A Tuple to unpack into the function when calling it
    kwargs                   A dict to unpack into the function when calling it
    can_be_paused:           Whether or not the function should be called when the program is paused
    supply_main_loop_object: Whether or not the first parameter that will be given to the function is the MainLoop object itself
    """
    function:                Callable
    args:                    Tuple[Any]     = field(default_factory=tuple)
    kwargs:                  Dict[str, Any] = field(default_factory=dict)
    can_be_paused:           bool           = False
    supply_main_loop_object: bool           = False
