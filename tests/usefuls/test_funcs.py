import datetime

import pytest

from NetSym.exceptions import NetworkSimulationError
from NetSym.usefuls.dotdict import DotDict
from NetSym.usefuls.funcs import get_the_one, is_matching, is_hex, with_args, distance, split_by_size, called_in_order, insort, sum_tuples, \
    scale_tuple, normal_color_to_weird_gl_color, lighten_color, darken_color, bindigits, datetime_from_string, all_indexes, my_range, \
    split_with_escaping, temporary_attribute_values, reverse_dict, change_dict_key_names, get_the_one_with_raise, get_the_one_with_default


@pytest.mark.parametrize(
    "iterable, condition, should_return",
    [
        ([],            bool,                   None),
        ([1, 0],        bool,                   1),
        (["", 0, 2, 3], bool,                   2),
        ([20, 3, 4],    (lambda x: x % 2 == 0), 20),
    ]
)
def test_get_the_one(iterable, condition, should_return):
    assert get_the_one(iterable, condition) == should_return


@pytest.mark.parametrize(
    "iterable, condition, raises, should_raise, should_return",
    [
        ([],            bool,                   Exception,              Exception,              None),
        ([1, 0],        bool,                   KeyError,               None,                   1),
        (["", 0, 2, 3], bool,                   ValueError,             None,                   2),
        ([21, 3, 41],   (lambda x: x % 2 == 0), NetworkSimulationError, NetworkSimulationError, None),
        ([2, 3, 4],     (lambda x: x % 2 == 0), NetworkSimulationError, None,                   2),
    ]
)
def test_get_the_one_with_raise(iterable, condition, raises, should_raise, should_return):
    if should_raise:
        with pytest.raises(should_raise):
            get_the_one_with_raise(iterable, condition, raises)
        return

    assert get_the_one_with_raise(iterable, condition, raises) == should_return


@pytest.mark.parametrize(
    "iterable, condition, default, should_return",
    [
        ([],            bool,                   "hello", "hello"),
        ([],            bool,                   None,    None),
        ([1, 0],        bool,                   5,       1),
        (["", 0, 2, 3], bool,                   4003,    2),
        ([2, 3, 4],     (lambda x: x % 2 == 0), 1002,    2),
        ([21, 3, 41],   (lambda x: x % 2 == 0), 1002,    1002),
    ]
)
def test_get_the_one_with_default(iterable, condition, default, should_return):
    assert get_the_one_with_default(iterable, condition, default) == should_return


def test_is_matching():
    assert is_matching(r".*", "hello") is True
    assert is_matching(r"hi", "hello") is False


@pytest.mark.parametrize(
    "string, result",
    [
        ("",         True),
        ("1",        True),
        ("not hex",  False),
        ("0xhex",    False),
        ("0xAB",     True),
        ("0xab",     True),
        ("12FcAb3D", True),
    ]
)
def test_is_hex(string, result):
    assert is_hex(string) is result


@pytest.mark.parametrize(
    "args, kwargs",
    [
        ((1, 2, 3), {}),
        ((),        {"a": 2, "b": 4, "c": 6}),
        ((1, 2, 3), {"a": 2, "b": 4, "c": 6}),
    ]
)
def test_with_args(args, kwargs):
    def function(*inner_args, **inner_kwargs):
        return len(inner_args), len(inner_kwargs)
    function_with_args = with_args(function, *args, **kwargs)

    assert function_with_args()            == (len(args),     len(kwargs))
    assert function_with_args(3, 4, 5)     == (len(args) + 3, len(kwargs))
    assert function_with_args(d=3, e=4)    == (len(args),     len(kwargs) + 2)
    assert function_with_args(6, d=3, e=4) == (len(args) + 1, len(kwargs) + 2)


@pytest.mark.parametrize(
    "p1, p2, result",
    [
        ((0, 0),    (0, 0),   0.0),
        ((0, 0),    (0, 0.1), 0.1),
        ((0, 3),    (4, 0),   5.0),
        ((100, 12), (160, 1), 61.0),
    ]
)
def test_distance(p1, p2, result):
    assert distance(p1, p2) == result


@pytest.mark.parametrize(
    "string, size, result",
    [
        ("aabbcc",   2,  ['aa', 'bb', 'cc']),
        ("wordword", 3,  ['wor', 'dwo', 'rd']),
        ("hi",       10, ['hi']),
        ("",         4,  []),
    ]
)
def test_split_by_size(string, size, result):
    assert split_by_size(string, size) == result


def test_called_in_order():
    no_functions = called_in_order()
    test_list1 = [1, 2, 3]
    test_list2 = [1, 2, 3]
    change_list1 = called_in_order(test_list1.pop, test_list1.pop, with_args(test_list1.append, 4))
    clear_list2  = called_in_order(with_args(test_list2.extend, [4, 5, 6]), test_list2.clear)

    no_functions()  # does nothing
    change_list1()
    clear_list2()

    assert test_list1 == [1, 4]
    assert test_list2 == []


@pytest.mark.parametrize(
    "args, result",
    [
        (([],                  3),                  [3]),
        (([1, 2, 4],           3),                  [1, 2, 3, 4]),
        (([4, 5, 6],           3),                  [3, 4, 5, 6]),
        (([0, 1, 2],           3),                  [0, 1, 2, 3]),
        ((["a", "b", "d"],     "c"),                ["a", "b", "c", "d"]),
        ((["a", "aa", "aaaa"], "aaa", len),         ["a", "aa", "aaa", "aaaa"]),
        (([1, 2, 3],           0,     lambda t: 1), [1, 2, 3, 0]),
    ]
)
def test_insort(args, result):
    list_ = args[0]
    insort(*args)
    assert list_ == result


# def test_circular_coordinates(center_location, radius, count, add_gl_coordinate= False):
#     """
#     a generator of coordinates in a circular fashion around a given point.
#     :param add_gl_coordinate:
#     :param center_location: The location of the center
#     :param radius: The radius of the circle
#     :param count: The count of points
#     :return: yields tuples of coordinates of the points
#     """
#     if count == 0:
#         return
#     x, y = center_location
#     d_theta = (2 * pi) / count
#     initial_theta = 0  # pi / 2
#     for i in range(count):
#         coords = x + (radius * cos((i * d_theta) + initial_theta)), y + (radius * sin((i * d_theta) + initial_theta))
#         yield (coords + (0,)) if add_gl_coordinate else coords


# def test_sine_wave_coordinates(
#         start_coordinates: Tuple[float, float],
#         end_coordinates: Tuple[float, float],
#         amplitude: float = 10,
#         frequency: float = 1) -> Generator[Tuple[float, float]]:
#     """
#     A generator that yields tuples that are coordinates for a sine wave.
#     :return:
#     """
#     start_x, start_y, end_x, end_y = start_coordinates + end_coordinates
#     count = int(distance(start_coordinates, end_coordinates) / SHAPES.SINE_WAVE.MINIMAL_POINT_DISTANCE)
#     relative_angle_of_end = atan((end_y - start_y) / (end_x - start_x)) if (end_x != start_x) else (pi / 2)
#     relative_angle_of_end -= pi if start_x > end_x else 0
#
#     x = SHAPES.SINE_WAVE.INITIAL_ANGLE
#     for i in range(count):
#         y = amplitude * sin(x * frequency)
#         yield rotated_coordinates((x + start_x, y + start_y), start_coordinates, relative_angle_of_end)
#         x += SHAPES.SINE_WAVE.MINIMAL_POINT_DISTANCE
#
#
# def test_rotated_coordinates(coordinates: Tuple[float, float], center: Tuple[float, float], angle: float) -> Tuple[float, float]:
#     """
#     Takes in a tuple of coordinates and rotates them `angle` radians around the point `center`
#     Returns the rotated coordinates
#     :param coordinates: The tuple of (x, y) of the input coordinates
#     :param center: The tuple (cx, cy) of the point to rotate the other point around
#     :param angle: The amount to rotate (in radians) (2 * pi is a full rotation)
#     :return: a tuple (rx, ry) of the rotated coordinates
#     """
#     x, y = coordinates
#     cx, cy = center
#     x, y = (x - cx), (y - cy)
#     rotated = (x + y*1j) * cmath.rect(1, angle)
#     return rotated.real + cx, rotated.imag + cy


@pytest.mark.parametrize(
    "tuples, result",
    [
        ([(1, 1)],                       (1, 1)),
        ([(1, 1),       (2, 2)],         (3, 3)),
        ([(1, 1),       (2, 2), (3, 3)], (6, 6)),
        ([(1, 1, 1, 1), (2, 2)],         (3, 3)),
        ([(),           (2, 2)],         ()),
        ([],                             ()),
    ]
)
def test_sum_tuples(tuples, result):
    assert sum_tuples(*tuples) == result


@pytest.mark.parametrize(
    "scalar, tuple_, round_to_integers, result",
    [
        (1,   (),     False, ()),
        (1,   (2, 3), False, (2, 3)),
        (2,   (2, 3), False, (4, 6)),
        (0.5, (3, 5), False, (1.5, 2.5)),
        (0.5, (3, 5), True,  (1, 2)),
    ]
)
def test_scale_tuple(scalar, tuple_, round_to_integers, result):
    assert scale_tuple(scalar, tuple_, round_to_integers,) == result


@pytest.mark.parametrize(
    "color, add_alpha, result",
    [
        ((0, 0, 0),       False,  (0, 0, 0)),
        ((0, 0, 0),       True,   (0, 0, 0, 1)),
        ((255, 255, 255), False,  (1, 1, 1)),
        ((127.5, 255, 0), True,   (0.5, 1, 0, 1.0)),
        ((100, 200, 300), True,   (0.39215686274509803, 0.7843137254901961, 1.1764705882352942, 1.0)),
    ]
)
def test_normal_color_to_weird_gl_color(color, add_alpha, result):
    assert normal_color_to_weird_gl_color(color, add_alpha) == result


@pytest.mark.parametrize(
    "color, diff, result",
    [
        ((0, 0, 0),       10,  (10, 10, 10)),
        ((200, 200, 200), 100, (255, 255, 255)),
    ]
)
def test_lighten_color(color, diff, result):
    assert lighten_color(color, diff) == result


@pytest.mark.parametrize(
    "color, diff, result",
    [
        ((200, 100, 255), 100, (100, 0, 155)),
        ((0, 0, 0),       10,  (0, 0, 0)),
    ]
)
def test_darken_color(color, diff, result):
    assert darken_color(color, diff) == result


@pytest.mark.parametrize(
    "number, bit_count, result",
    [
        (0,      8,  '00000000'),
        (0xff,   8,  '11111111'),
        (0xff,   3,  '111'),
        (0x0a,   9,  '000001010'),
        (-3,     8,  '11111101'),
        (-255,   16, '1111111100000001'),
    ]
)
def test_bindigits(number, bit_count, result):
    assert bindigits(number, bit_count) == result


@pytest.mark.parametrize(
    "datetime_",
    [
        datetime.datetime(2022, 11, 18, 3, 17, 10, 100),
        datetime.datetime(1970, 1,  1,  0, 0,  0,  0),
    ]
)
def test_datetime_from_string(datetime_):
    assert datetime_from_string(repr(datetime_)) == datetime_


@pytest.mark.parametrize(
    "string, substring, result",
    [
        ("test test test", " ",    [4, 9]),
        ("test test test", "test", [0, 5, 10]),
        ("aaaaa",          "aaa",  [0, 1, 2]),
        ("",               "",     [0]),
        ("hello",          "test", []),
        ("hello",          "",     [0, 1, 2, 3, 4, 5]),
    ]
)
def test_all_indexes(string, substring, result):
    assert list(all_indexes(string, substring)) == result


@pytest.mark.parametrize(
    "args, result",
    [
        ([3],                 [0, 1, 2]),
        ([0],                 []),
        ([1,    4],           [1, 2, 3]),
        ([1,    1],           []),
        ([0.3,  0.6,  0.1],   [0.3, 0.4, 0.5]),
        ([0,    3,    0.5],   [0, 0.5, 1, 1.5, 2, 2.5]),
        ([-0.6, -0.3, 0.1],   [-0.6, -0.5, -0.4]),
        ([0.2,  0,    -0.05], [0.2, 0.15, 0.1, 0.05]),
    ]
)
def test_my_range(args, result):
    assert list(map(lambda n: round(n, 7), my_range(*args))) == result


@pytest.mark.parametrize(
    "string, separator, escaping_char, remove_empty_spaces, result",
    [
        ('',                                 'J', 'H', True,   []),
        ('hi  hi',                           ' ', '"', True,   ['hi', 'hi']),
        ('hi  hi',                           ' ', '"', False,  ['hi', '', 'hi']),
        ('hi "ai bi " ci  ',                 ' ', '"', True,   ['hi', '"ai bi "', 'ci']),
        ('h "a b" c"w h"',                   ' ', '"', True,   ['h', '"a b"', 'c"w h"']),
        ('^hi hi hi^',                       ' ', '^', True,   ['^hi hi hi^']),
        ('^hi&hi&hi^&&k',                    '&', '^', False,  ['^hi&hi&hi^', '', 'k']),
        ('and i said "hello w o r l d" ! !', ' ', '"', True,   ['and', 'i', 'said', '"hello w o r l d"', '!', '!']),
    ]
)
def test_split_with_escaping(string, separator, escaping_char, remove_empty_spaces, result):
    assert split_with_escaping(string, separator, escaping_char, remove_empty_spaces) == result


def test_temporary_attribute_values():
    object_ = DotDict(a=55)

    initial_value = object_.a
    with temporary_attribute_values(object_, {'a': 101010101}):
       temporary_value  = object_.a
    final_value = object_.a

    assert initial_value == final_value == 55
    assert temporary_value == 101010101


@pytest.mark.parametrize(
    "dict_, result",
    [
        ({}, {}),
        ({1: 2}, {2: 1}),
        ({1: 2, 'a': 'b'}, {2: 1, 'b': 'a'}),
    ]
)
def test_reverse_dict__success(dict_, result):
    assert reverse_dict(dict_) == result


@pytest.mark.parametrize(
    "dict_",
    [
        {1: 2, 5: 2, 3: 4, 7: 6},
        {'a': 'A', 'A': 'A'},
    ]
)
def test_reverse_dict__fail(dict_):
    with pytest.raises(KeyError):
        reverse_dict(dict_)


@pytest.mark.parametrize(
    "dict_, key_name_mapping, result",
    [
        ({},                       {},                 {}),
        ({},                       {1: 2, 2: 3, 3: 4}, {}),
        ({1: 2},                   {},                 {1: 2}),
        ({1: 2, 3: 4},             {1: 3},             {3: 4}),
        ({1: 'a', 2: 'b', 3: 'c'}, {1: 'A', 2: 'B'},   {'A': 'a', 'B': 'b', 3: 'c'}),
        ({1: 10, 2: 20, 3: 30},    {1: 2, 2: 3, 3: 4}, {2: 10, 3: 20, 4: 30}),
    ]
)
def test_change_dict_key_names__success(dict_, key_name_mapping, result):
    """
    Receive a dict and a mapping between old and new names
    change the keys of the dict to their new names (if they appear in the mapping)
    """
    assert change_dict_key_names(dict_, key_name_mapping) == result


@pytest.mark.parametrize(
    "dict_, key_name_mapping",
    [
        ({1: 2, 3: 4},               {1: 3}),
        ({'hi': 2, 'bye': 3, '': 0}, {'hi': 'bye', '': '3'}),
        ({1: None, 2: None},         {3: 3}),
        ({1: None, 2: None},         {1: 2, 2: 2}),
    ]
)
def test_change_dict_key_names__fail(dict_, key_name_mapping):
    """
    Receive a dict and a mapping between old and new names
    change the keys of the dict to their new names (if they appear in the mapping)
    """
    with pytest.raises(KeyError):
        change_dict_key_names(dict_, key_name_mapping)
