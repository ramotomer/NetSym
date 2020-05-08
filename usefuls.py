import math


def get_the_one(iterable, condition, raises=None):
    """
    Receives an iterable and a condition and returns the first item in the
    iterable that the condition is true for.
    If the function does not find one, it returns None, or if raises!=None then
    it will raise a `raises`.
    :param iterable: An iterable object.
    :param condition: A boolean function that takes one argument.
    :param raises: The exception this function will raise if it does not find.
    :return: The item with that condition or None
    """
    for item in iterable:
        if condition(item):
            return item
    if raises is not None:
        raise raises('Failed to "get_the_one" since it does not exist in your iterrable')
    return None


def is_hex(string):
    """
    returns if a data is a hexadecimal digit or not
    """
    string = string[2:] if string.startswith('0x') else string
    hex_digits = set('0123456789abcdefABCDEF')
    return set(string) <= hex_digits


def with_args(function, *args, **kwargs):
    """
    Receives a function and its arguments.
    returns a function which when called without arguments performs `function(*args, **kwargs)`.
    :param function: a function
    :param args: the arguments that the function will be called with
    :param kwargs: the key word arguments that the function will be called with.
    :return: a function that takes no arguments.
    """
    def returned(*more_args, **more_kwargs):
        return function(*args, *more_args, **kwargs, **more_kwargs)
    return returned


def distance(p1, p2):
    """
    Returns the distance between two points.
    :param p1:
    :param p2: 2 tuples of numbers.
    :return: a number
    """
    x1, y1 = p1
    x2, y2 = p2
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def split_by_size(string, size):
    """
    Takes the string and splits it up to `size` sized pieces (or less - for the last one).
    :param string: str
    :param size: int
    :return: list of strings each of size `size` at most
    """
    return [string[i:i + size] for i in range(0, len(string), size)]


def called_in_order(*functions):
    """
    Receives functions and returns a function performs them one after the other in the order they were received in.
    calls them without arguments.
    :param functions: callable objects.
    :return: a function
    """
    def in_order():
        for function in functions:
            function()
    return in_order


def get_first(iterable):
    """
    Returns one of the iterable's items. Usually the first one.
    :param iterable: an iterable
    :return:
    """
    for item in iterable:
        return item
