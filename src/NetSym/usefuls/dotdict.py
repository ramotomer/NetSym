from typing import Any


class DotDict(dict):
    def set(self, key: Any, value: Any) -> None:
        """
        Set a key value mapping
        """
        self[key] = value

    def __getattribute__(self, item: str) -> Any:
        """
        Get the keys of the dictionary as attributes
        """
        try:
            return super(DotDict, self).__getattribute__(item)
        except AttributeError:
            return self[item]

    def __setattr__(self, key: Any, value: Any) -> None:
        """
        Set an attribute of the dictionary - translates it to a key-value mapping
        """
        if hasattr(self, key):
            super(DotDict, self).__setattr__(key, value)
            return

        self[key] = value
