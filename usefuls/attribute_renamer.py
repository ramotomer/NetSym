from address.ip_address import IPAddress
from address.mac_address import MACAddress
from exceptions import AttributeError_


def define_attribute_aliases(class_, attribute_name_mapping):
    class AttributeRenamer(class_):
        original_name = getattr(class_, 'original_name', class_.__name__)

        def __init__(self, *args, **kwargs):
            super(AttributeRenamer, self).__init__(
                *args,
                **{attribute_name_mapping.get(key, key): value for key, value in kwargs.items()}
            )

        def __getattr__(self, item):
            try:
                return super(AttributeRenamer, self).__getattr__(attribute_name_mapping.get(item, item))
            except AttributeError as e:
                raise AttributeError_(f"{self!r} has no attribute '{e.args[0]}'")

    return AttributeRenamer


def with_parsed_attributes(class_, attribute_name_to_parser):
    class AttributeParser(class_):
        original_name = getattr(class_, 'original_name', class_.__name__)

        def __getattr__(self, item):
            try:
                if item.startswith("parsed_") and item[len("parsed_"):] in attribute_name_to_parser:
                    return attribute_name_to_parser[item[len("parsed_"):]](super(AttributeParser, self).__getattr__(item[len("parsed_"):]))
                return super(AttributeParser, self).__getattr__(item)
            except AttributeError as e:
                raise AttributeError_(*e.args)

    return AttributeParser


def with_attribute_type_casting(class_, attribute_name_to_type):
    class AttributeTypeCaster(class_):
        original_name = getattr(class_, 'original_name', class_.__name__)

        def __getattr__(self, item):
            try:
                return attribute_name_to_type.get(item, lambda x: x)(super(AttributeTypeCaster, self).__getattr__(item))
            except AttributeError as e:
                raise AttributeError_(f"{self!r} has no attribute '{e.args[0]}'")

    return AttributeTypeCaster


def with_attribute_type_casting_by_suffix(class_, attribute_suffix_to_type):
    class AttributeTypeCasterBySuffix(class_):
        original_name = getattr(class_, 'original_name', class_.__name__)

        def __getattr__(self, item: str):
            try:
                original_value = super(AttributeTypeCasterBySuffix, self).__getattr__(item)
            except AttributeError as e:
                raise AttributeError_(f"{self!r} has no attribute '{e.args[0]}'")

            for suffix, new_type in attribute_suffix_to_type.items():
                if isinstance(original_value, str) and item.endswith(suffix):
                    return new_type(original_value)
            return original_value

    return AttributeTypeCasterBySuffix


def with_automatic_address_type_casting(class_):
    return with_attribute_type_casting_by_suffix(
        class_,
        {
            "_mac": MACAddress,
            "_ip": IPAddress,
        }
    )
