import pytest

from NetSym.exceptions import *
from NetSym.usefuls.funcs import rangom, get_the_one


@pytest.mark.parametrize(
    "start, end, raises",
    [
        (0,   1,   False),
        (10,  100, False),
        (0.1, 0.2, False),
        (3,   1,   True),
        (0,   0,   True),
    ]
)
def test_rangom(start, end, raises):
    if raises:
        with pytest.raises(WrongUsageError):
            rangom(start, end)
        return

    for _ in range(0, 1000):
        assert start <= rangom(start, end) <= end


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
#
#
# def test_is_matching(pattern: str, string: str):
#     """
#     Takes in a regex pattern and a string.
#     Returns whether or not the string fits in the pattern
#     """
#     match = re.match(pattern, string)
#     return (match is not None) and (match.group(0) == string)
#
#
# def test_is_hex(string: str):
#     """
#     returns if a ip_layer is a hexadecimal digit or not
#     """
#     string = string[2:] if string.startswith('0x') else string
#     hex_digits = set('0123456789abcdefABCDEF')
#     return set(string) <= hex_digits
#
#
# def test_with_args(function: Callable[[...], T], *args: Any, **kwargs: Any) -> Callable[[], T]:
#     """
#     Receives a function and its arguments.
#     returns a function which when called without arguments performs `function(*args, **kwargs)`.
#     :param function: a function
#     :param args: the arguments that the function will be called with
#     :param kwargs: the key word arguments that the function will be called with.
#     :return: a function that takes no arguments.
#     """
#     def test_returned(*more_args: Any, **more_kwargs: Any):
#         return function(*args, *more_args, **kwargs, **more_kwargs)
#     return returned
#
#
# def test_distance(p1: Tuple[float, float], p2: Tuple[float, float]):
#     """
#     Returns the distance between two points.
#     :param p1:
#     :param p2: 2 tuples of numbers.
#     :return: a number
#     """
#     x1, y1 = p1
#     x2, y2 = p2
#     return sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
#
#
# def test_split_by_size(string: str, size: int) -> List[str]:
#     """
#     Takes the string and splits it up to `size` sized pieces (or less - for the last one).
#     :return: list of strings each of size `size` at most
#     """
#     return [string[i:i + size] for i in range(0, len(string), size)]
#
#
# def test_called_in_order(*functions: Callable[[], Any]) -> Callable[[], None]:
#     """
#     Receives functions and returns a function performs them one after the other in the order they were received in.
#     calls them without arguments.
#     :param functions: callable objects.
#     :return: a function
#     """
#     def test_in_order():
#         for function in functions:
#             function()
#     return in_order
#
#
# def test_get_first(iterable: Iterable[T]):
#     """
#     Returns one of the iterable's items. Usually the first one.
#     :param iterable: an iterable
#     :return:
#     """
#     for item in iterable:
#         return item
#
#
# def test_insort(list_: List[T], item: T, key: Callable[[T], Any] = lambda t: t):
#     """
#     Insert an item into a sorted list by a given key while keeping it sorted.
#     :param list_: the list (assumed to be sorted)
#     :param item: an item to insert into the list while keeping it sorted.
#     :param key: a function to check the values of the list by.
#     :return: None
#     """
#     low_index = 0
#     high_index = len(list_)
#
#     while low_index < high_index:
#         middle_index = (low_index + high_index) // 2
#         if key(item) < key(list_[middle_index]):
#             high_index = middle_index
#         else:
#             low_index = middle_index + 1
#     list_.insert(low_index, item)
#
#
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
