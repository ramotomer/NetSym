from __future__ import annotations

from abc import ABC
from dataclasses import astuple
from typing import Iterable


class IterableDataclass(ABC):

    def __iter__(self) -> Iterable:
        return iter(astuple(self))
