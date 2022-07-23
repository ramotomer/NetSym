from os.path import normcase, abspath, realpath, normpath, join


def make_path_comparable(path):
    """
    Paths can be confusing - 'C://temp\\hi/hello' can be the same as './TEMP/hi/hellO\\'
    Make them all look the same so we can compare them as we intend
    """
    return normpath(realpath(normcase(abspath(path))))


def are_paths_equal(path1, path2):
    """
    Compare the two paths after normalizing them using `make_path_comparable`
    """
    return make_path_comparable(path1) == make_path_comparable(path2)


def path_startswith(path, basename):
    """
    Return whether or not `path` startswith `basename`
    """
    return make_path_comparable(path).startswith(make_path_comparable(basename))


def add_path_basename_if_needed(basename, path):
    if path_startswith(path, basename):
        return path
    return join(basename, path)
