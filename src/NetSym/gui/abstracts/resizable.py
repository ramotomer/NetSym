from typing import Protocol


def is_resizable(object_):
    return hasattr(object_, "resize")


class Resizable(Protocol):
    """

    """
    def resize(self, width_diff: float, height_diff: float, constrain_proportions: bool = False) -> None:
        ...
