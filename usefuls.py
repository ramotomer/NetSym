import cmath
from functools import reduce
from math import sqrt, sin, cos, pi, atan
from operator import mul

from consts import *


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
        raise raises('Failed to "get_the_one" since it does not exist in your iterable')
    return None


def is_hex(string):
    """
    returns if a ip_layer is a hexadecimal digit or not
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
    return sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


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


def insort(list_, item, key=lambda t: t):
    """
    Insert an item into a sorted list by a given key while keeping it sorted.
    :param list_: the list (assumed to be sorted)
    :param item: an item to insert into the list while keeping it sorted.
    :param key: a function to check the values of the list by.
    :return: None
    """
    low_index = 0
    high_index = len(list_)

    while low_index < high_index:
        middle_index = (low_index + high_index) // 2
        if key(item) < key(list_[middle_index]):
            high_index = middle_index
        else:
            low_index = middle_index + 1
    list_.insert(low_index, item)


def circular_coordinates(center_location: tuple, radius, count):
    """
    a generator of coordinates in a circular fashion around a given point.
    :param center_location: The location of the center
    :param radius: The radius of the circle
    :param count: The count of points
    :return: yields tuples of coordinates of the points
    """
    if count == 0:
        return
    x, y = center_location
    d_theta = (2 * pi) / count
    initial_theta = 0  # pi / 2
    for i in range(count):
        yield x + (radius * cos((i * d_theta) + initial_theta)), y + (radius * sin((i * d_theta) + initial_theta))


def sine_wave_coordinates(start_coordinates, end_coordinates, amplitude=10, frequency=1):
    """
    A generator that yields tuples that are coordinates for a sine wave.
    :return:
    """
    start_x, start_y, end_x, end_y = start_coordinates + end_coordinates
    count = int(distance(start_coordinates, end_coordinates) / SHAPES.SINE_WAVE.MINIMAL_POINT_DISTANCE)
    relative_angle_of_end = atan((end_y - start_y) / (end_x - start_x)) if (end_x != start_x) else (pi / 2)
    relative_angle_of_end -= pi if start_x > end_x else 0

    x = SHAPES.SINE_WAVE.INITIAL_ANGLE
    for i in range(count):
        y = amplitude * sin(x * frequency)
        yield rotated_coordinates((x + start_x, y + start_y), start_coordinates, relative_angle_of_end)
        x += SHAPES.SINE_WAVE.MINIMAL_POINT_DISTANCE


def rotated_coordinates(coordinates, center, angle):
    """
    Takes in a tuple of coordinates and rotates them `angle` radians around the point `center`
    Returns the rotated coordinates
    :param coordinates: The tuple of (x, y) of the input coordinates
    :param center: The tuple (cx, cy) of the point to rotate the other point around
    :param angle: The amount to rotate (in radians) (2 * pi is a full rotation)
    :return: a tuple (rx, ry) of the rotated coordinates
    """
    x, y = coordinates
    cx, cy = center
    x, y = (x - cx), (y - cy)
    rotated = (x + y*1j) * cmath.rect(1, angle)
    return rotated.real + cx, rotated.imag + cy


def sum_tuples(*tuples):
    """
    sums each item of the tuples. returns the new tuple.
    :param tuples: many arguments of tuples.
    :return:
    """
    return tuple(map(sum, zip(*tuples)))


def scale_tuple(scalar, tup):
    """
    Multiplies every item of the tuple with a number.
    :param scalar: number
    :param tup: tuple
    :return:
    """
    return tuple(map(lambda t: reduce(mul, t), zip(([scalar] * len(tup)), tup)))
