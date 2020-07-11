from computing.inner_workings.filesystem.directory import Directory
from consts import FILESYSTEM
from exceptions import PathError


class Filesystem:
    """
    The filesystem of the computer.
    """
    def __init__(self):
        """
        Initiates the filesystem with a root directory.
        """
        self.root_path = FILESYSTEM.ROOT
        self.root = Directory(name=self.root_path, parent=None)

    @classmethod
    def with_default_dirs(cls):
        """
        Creates it with some random directories in the root directory.
        :return:
        """
        filesystem = cls()
        filesystem.make_dir('/dev')
        filesystem.make_dir('/usr')
        filesystem.make_dir('/usr/bin')
        filesystem.make_dir('/var')
        filesystem.make_dir('/boot')
        filesystem.make_dir('/bin')
        return filesystem

    @staticmethod
    def is_absolute_path(path):
        """
        returns the answer to the damn question in the title of the method!!! hell, why do i even document....
        :param path:
        :return:
        """
        return path.startswith(FILESYSTEM.ROOT)

    def at_absolute_path(self, path):
        """
        Receives an absolute path and returns the file or directory at that location.
        :param path:
        :return:
        """
        if not self.is_absolute_path(path):
            raise PathError(f"path is not valid! '{path}'")

        return self.root.at_relative_path(FILESYSTEM.CWD + path)

    def make_dir(self, full_path):
        """
        Creates a directory in a given path.
        :param full_path: absolute path to the new directory.
        :return:
        """
        parent_path, dirname = full_path.split(FILESYSTEM.SEPARATOR)[1:-1], full_path.split(FILESYSTEM.SEPARATOR)[-1]
        parent_dir = self.at_absolute_path(self.root_path + FILESYSTEM.SEPARATOR.join(parent_path))
        parent_dir.make_sub_dir(dirname)
