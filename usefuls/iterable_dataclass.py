from abc import ABCMeta
from dataclasses import astuple


class IterableDataclass(metaclass=ABCMeta):

    def __iter__(self):
        return iter(astuple(self))
