from typing import Any, List, Tuple


class ScapyOptions:
    def __init__(self, options: List[Tuple[str, Any]]) -> None:
        self.options = options

    def __getitem__(self, item: str) -> Any:
        for key, value in [option for option in self.options if isinstance(option, tuple)]:
            if key.replace('-', '_') == item:
                return value
        raise KeyError(f"This scapy options list: {self} has no option '{item}'!")

    def __getattr__(self, item: str) -> Any:
        if item in ['options', 'get']:
            return super(ScapyOptions, self).__getattribute__(item)

        try:
            return self[item]
        except KeyError as e:
            raise AttributeError(*e.args)

    def __setattr__(self, key: str, value: Any) -> None:
        if key == 'options':
            super(ScapyOptions, self).__setattr__(key, value)
            return

        for existing_key, existing_value in [option for option in self.options if isinstance(option, tuple)]:
            if existing_key == key:
                self.options = [option for option in self.options if not (isinstance(option, tuple) and option[0] == key)] + [(key, value)]
                return
        self.options.append((key, value))

    def __repr__(self) -> str:
        return str(self.options)

    def get(self, item: str, default: Any = None) -> Any:
        try:
            return getattr(self, item)
        except AttributeError:
            return default
