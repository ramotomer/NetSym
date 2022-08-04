def define_attribute_aliases(class_, attribute_name_mapping):
    class AttributeRenamer(class_):
        def __init__(self, *args, **kwargs):
            super(AttributeRenamer, self).__init__(
                *args,
                **{attribute_name_mapping.get(key, key): value for key, value in kwargs.items()}
            )

        def __getattr__(self, item):
            return super(AttributeRenamer, self).__getattr__(attribute_name_mapping.get(item, item))

    return AttributeRenamer


def with_parsed_attributes(class_, attribute_name_to_parser):
    class AttributeParser(class_):
        def __getattr__(self, item):
            if item.startswith("parsed_") and item[len("parsed_"):] in attribute_name_to_parser:
                return attribute_name_to_parser[item[len("parsed_"):]](super(AttributeParser, self).__getattr__(item[len("parsed_"):]))
            return super(AttributeParser, self).__getattr__(item)

    return AttributeParser
