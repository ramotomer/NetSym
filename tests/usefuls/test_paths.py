import pytest

from NetSym.usefuls.paths import _make_path_comparable, are_paths_equal, path_startswith, add_path_basename_if_needed


@pytest.mark.parametrize(
    "path1, path2, expected",
    [
        ('/hello/world',    '\\hello\\world',         True),
        ('/hello/world/hi', '\\hello\\world/hi',      True),
        ('/hello/world',    '/hello/world/',          True),
        ('/hello/world',    '/HeLlO/WoRlD',           True),
        ('C:/hello/world',  '/hello/world',           True),
        ('/hello',          '/hello/world/hi/../..',  True),
        ('/hello/world',    '/hello/world/./././.',   True),
        ('/hello',          'hello',                  False),
        ('/hello',          '/hell',                  False),
        ('/hello /world',   '/hello/world',           False),
    ]
)
def test_make_path_comparable(path1, path2, expected):
    assert (_make_path_comparable(path1) == _make_path_comparable(path2)) is expected


@pytest.mark.parametrize(
    "path1, path2, expected",
    [
        ('C:/hello/world',  'C:/hello/world',        True),
        ('/hello/world',    '\\hello\\world',        True),
        ('/hello/world/hi', '\\hello\\world/hi',     True),
        ('/hello/world',    '/hello/world/',         True),
        ('/hello/world',    '/HeLlO/WoRlD',          True),
        ('/hello/world',    '/hello/world',          True),
        ('C:/hello/world',  '/hello/world',          True),
        ('/hello',          '/hello/world/hi/../..', True),
        ('/hello/world',    '/hello/world/./././.',  True),
        ('/hello',          'hello',                 False),
        ('/hello',          '/hell',                 False),
        ('/hello /world',   '/hello/world',          False),
        ('C:hello/world',   'C:/hello/world',        False),
    ]
)
def test_are_paths_equal(path1, path2, expected):
    assert are_paths_equal(path1, path2) is expected


@pytest.mark.parametrize(
    "path, basename, expected",
    [
        ('/hello/world/hi', '/hello/world/',    True),
        ('C:/hello/world',  '/hello',           True),
        ('/hello/world/hi', '/hello/world/hi/', True),
        ('/hello/world',    '\\hello\\world',   True),
        ('/hello',          '/hellowlo',        False),
        ('/hello',          '/hell',            False),
        ('/hello/world/hi', '/hello/world/h',   False),
        ('/hello/world/',   '/hello/world/hi',  False),
    ]
)
def test_path_startswith(path, basename, expected):
    assert path_startswith(path, basename) is expected


@pytest.mark.parametrize(
    "basename, path, expected",
    [
        ("/hello/world/",   "hi",              "/hello/world/hi"),
        ("/hello/world/",   "/hello/world/hi", "/hello/world/hi"),
        ("/hello/world/",   "hello/hi",        "/hello/world/hello/hi"),
        ("/world",          "/hello/hi",       "/hello/hi"),
        ("world",           "/hello/hi",       "/hello/hi"),
    ]
)
def test_add_path_basename_if_needed(basename, path, expected):
    assert are_paths_equal(add_path_basename_if_needed(basename, path), expected)
