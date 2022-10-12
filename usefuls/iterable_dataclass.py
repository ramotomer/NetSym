from abc import ABCMeta
from dataclasses import astuple
from typing import Iterable


class IterableDataclass(metaclass=ABCMeta):

    def __iter__(self) -> Iterable:
        return iter(astuple(self))
