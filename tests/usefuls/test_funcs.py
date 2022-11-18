import pytest

from NetSym.usefuls.funcs import get_the_one, is_matching, is_hex, with_args, distance, split_by_size, called_in_order, insort


@pytest.mark.parametrize(
    "iterable, condition, raises, default, should_raise, should_return",
    [
        ([],            bool,                   None,      None,    None,      None),
        ([],            bool,                   None,      "hello", None,      "hello"),
        ([],            bool,                   Exception, None,    Exception, None),
        ([1, 0],        bool,                   None,      None,    None,      1),
        (["", 0, 2, 3], bool,                   None,      None,    None,      2),
        ([2, 3, 4],     (lambda x: x % 2 == 0), None,      None,    None,      2),
    ]
)
def test_get_the_one(iterable, condition, raises, default, should_raise, should_return):
    if should_raise:
        with pytest.raises(should_raise):
            get_the_one(iterable, condition, raises, default)
        return

    assert get_the_one(iterable, condition, raises, default) == should_return


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


# def test_circular_coordinates(center_location: Tuple[float, float], radius: float, count: int, add_gl_coordinate: bool = False):
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
#
#
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
#
#
# def test_sum_tuples(*tuples: Tuple):
#     """
#     sums each item of the tuples. returns the new tuple.
#     :param tuples: many arguments of tuples.
#     :return:
#     """
#     try:
#         return tuple(map(sum, zip(*tuples)))
#     except TypeError:
#         raise WrongUsageError(f"problem with the arguments {list(tuples)}")
#
#
# def test_scale_tuple(scalar: float, tuple_: Tuple, round_to_integers: bool = False):
#     """
#     Multiplies every item of the tuple with a number.
#     """
#     returned = tuple(map(lambda t: reduce(mul, t), zip(([scalar] * len(tuple_)), tuple_)))
#     if round_to_integers:
#         returned = tuple(map(int, returned))
#     return returned
#
#
# def test_normal_color_to_weird_gl_color(color: T_Color, add_alpha: bool = True) -> Union[T_Color, Tuple[float, ...]]:
#     """
#     Some open GL functions require some different weird format of colors
#     """
#     r, g, b = color
#     returned = r / 255, g / 255, b / 255
#     return returned + ((1.0,) if add_alpha else ())
#
#
# def test_lighten_color(color: T_Color, diff: float = COLORS.COLOR_DIFF):
#     r, g, b = color
#     return max(min(r + diff, 255), 0), max(min(g + diff, 255), 0), max(min(b + diff, 255), 0)
#
#
# def test_darken_color(color: T_Color, diff: float = COLORS.COLOR_DIFF):
#     return lighten_color(color, -diff)
#
#
# def test_bindigits(number: int, bit_count: int):
#     """
#     Receives a number (even a negative one!!!), returns a string
#     os the binary form of that number. the string will be `bits` bits long.
#     :param number: the number
#     :param bit_count: the amount of bits to give the binary form
#     :return: `str`
#     """
#     return f"{(bin(number & int('1' * bit_count, 2))[2:]) :0>{bit_count}}"
#
#
# def test_datetime_from_string(string: str) -> datetime.datetime:
#     """
#     receives the output of a `repr(datetime.datetime)` for some datetime.datetime object,
#     returns the datetime object itself.
#     """
#     args = string[string.index('(') + 1: string.index(')')].split(', ')
#     return datetime.datetime(*map(int, args))
#
#
# def test_all_indexes(string: str, substring: str) -> Generator[int]:
#     """
#     generator that yields indexes of all of the occurrences of the substring in the string
#     """
#     last_index = -1
#     while True:
#         try:
#             last_index = string.index(substring, last_index + 1)
#             yield last_index
#         except ValueError:
#             return
#
#
# def test_my_range(start: float, end: Optional[float] = None, step: float = 1) -> Generator[float]:
#     """
#     Just like `range`, but supports non-whole `step`s
#     :param start:
#     :param end:
#     :param step:
#     :return:
#     """
#     if end is None:
#         end = start
#         start = 0
#
#     current = start
#     while current < end:
#         yield current
#         current += step
#
#
# def test_bool_(o: Any):
#     """
#     The typing module is having a hard time with the `filter` function
#     Especially with the fact that the `bool` function takes in an `str`
#
#     The `filter` function is typed like this:
#
#         filter(function: Callable[[T], bool], iterable: Iterable[T]) -> Iterable[T]
#
#         and `bool` takes in an `object`
#
#     This means that `filter` allegedly returns a `Iterable[object]`
#     That fucks up my typing - because usually it returns something with more functionality (like strings) which the type checker sadly does not like
#
#     This function is just like `bool` but it takes in `Any` and not `object`
#     """
#     return bool(o)
#
#
# def test_split_with_escaping(string: str, separator: str = ' ', escaping_char: str = '"', remove_empty_spaces: bool = True) -> List[str]:
#     """
#     Just like the builtin `split` - but can handle escaping characters like "-s and not split in between them
#
#         example:
#                         >>> split_with_escaping('and i said "hello w o r l d" ! !')
#                         >>> ['and', 'i', 'said', '"hello w o r l d"', '!', '!']
#     :param remove_empty_spaces:
#     :param string: the `str` to split
#     :param separator: the substring to split by
#     :param escaping_char: the character which in between you should not split
#     :return:
#     """
#     splitted = []
#     last_splitted = 0
#     is_escaped = False
#
#     if not string:
#         return []
#
#     if separator == escaping_char:
#         raise WrongUsageError(f"separator and escaping char must be different! not both '{separator}'")
#
#     for i, char in enumerate(string):
#         if char == escaping_char:
#             is_escaped = not is_escaped
#             continue
#         if char == separator and not is_escaped:
#             splitted.append(string[last_splitted:i])
#             last_splitted = i + 1
#     splitted.append(string[last_splitted:])
#     if remove_empty_spaces:
#         splitted = [string for string in splitted if len(string) > 0]
#     return splitted
#
#
# @contextmanager
# def test_temporary_attribute_values(object_: Any, attribute_value_mapping: Dict[str, Any]) -> Generator[Any]:
#     """
#     A `contextmanager` that takes in an instance of an object.
#     The function allows us to temporarily change the values of
#         the object's attributes - perform some logic - and set them back. Example:
#
#         >>> object_.attribute_name     # == 1
#         >>> with temporary_attribute_values(object_, {'attribute_name': 34}):
#         >>>    object_.attribute_name # ==  34
#         >>> object_.attribute_name     # ==  1
#     """
#     old_mapping = {attr: getattr(object_, attr) for attr in attribute_value_mapping}
#     try:
#         for attr, new_value in attribute_value_mapping.items():
#             setattr(object_, attr, new_value)
#         yield object_
#     finally:
#         for attr, new_value in old_mapping.items():
#             setattr(object_, attr, new_value)
#
#
# def test_reverse_dict(dict_: Dict[K, V]) -> Dict[V, K]:
#     """
#     Take in a dict and reverse the keys and the values.
#     If some values are duplicate - raise
#     """
#     reversed_dict_ = {value: [] for value in dict_.values()}
#     for key, value in dict_.items():
#         reversed_dict_[value].append(key)
#
#     if any(len(key_list) != 1 for key_list in reversed_dict_.values()):
#         raise KeyError(f"Cannot reverse dict {dict_}! Duplicate values found. Conflict: {reversed_dict_}")
#
#     return {value: key_list[0] for value, key_list in reversed_dict_.items()}
#
#
# def test_change_dict_key_names(dict_: Dict[K, V], key_name_mapping: Dict[K, K2]) -> Dict[Union[K, K2], V]:
#     """
#     Receive a dict and a mapping between old and new names
#     change the keys of the dict to their new names (if they appear in the mapping)
#     """
#     return {key_name_mapping.get(key, key): value for key, value in dict_.items()}
