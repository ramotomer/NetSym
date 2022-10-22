from typing import Any


class DotDict(dict):
    def __getattribute__(self, item: str) -> Any:
        """
        Get the keys of the dictionary as attributes
        """
        try:
            return super(DotDict, self).__getattribute__(item)
        except AttributeError:
            return self[item]
