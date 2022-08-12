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
