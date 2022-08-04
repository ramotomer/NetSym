def define_attribute_aliases(class_, attribute_name_mapping):
    class AttributeRenamer(class_):
        def __init__(self, *args, **kwargs):
            super(AttributeRenamer, self).__init__(
                *args,
                **{attribute_name_mapping.get(key, key): value for key, value in kwargs.items()}
            )

        def __getattr__(self, item):
            try:
                return super(AttributeRenamer, self).__getattr__(attribute_name_mapping[item])
            except KeyError:
                return super(AttributeRenamer, self).__getattr__(item)

    return AttributeRenamer
