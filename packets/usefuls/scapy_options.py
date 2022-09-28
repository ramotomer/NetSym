from typing import Any


class ScapyOptions:
    def __init__(self, options):
        self.options = options

    def __getitem__(self, item):
        for key, value in [option for option in self.options if isinstance(option, tuple)]:
            if key.replace('-', '_') == item:
                return value
        raise KeyError(f"This scapy options list: {self} has no option '{item}'!")

    def __getattr__(self, item):
        if item == 'options':
            return super(ScapyOptions, self).__getattribute__(item)

        try:
            return self[item]
        except KeyError as e:
            raise AttributeError(*e.args)

    def __setattr__(self, key, value):
        if key == 'options':
            super(ScapyOptions, self).__setattr__(key, value)
            return

        for existing_key, existing_value in [option for option in self.options if isinstance(option, tuple)]:
            if existing_key == key:
                self.options = [option for option in self.options if not (isinstance(option, tuple) and option[0] == key)] + [(key, value)]
                return
        self.options.append((key, value))

    def __repr__(self):
        return str(self.options)

    def get(self, item: str, default: Any = None) -> Any:
        try:
            return getattr(self, item)
        except AttributeError:
            return default
