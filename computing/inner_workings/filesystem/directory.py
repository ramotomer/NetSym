from consts import FILESYSTEM
from exceptions import NoSuchDirectoryError, NoSuchFileError, DirectoryExistsError


class Directory:
    """
    A directory on the computers of the simulation.
    """
    def __init__(self, name, parent, files=None, directories=None):
        """
        Initiated with a list of directories and files that are contained in it.

        directories and files are dicts of the form {name: Directory} or {name: File}
        """
        self.name = name

        self.files = files if files is not None else {}
        self.directories = directories if directories is not None else {}

        self.directories[FILESYSTEM.CWD] = self
        self.directories[FILESYSTEM.PARENT_DIRECTORY] = parent if parent is not None else self

    @property
    def items(self):
        return {**self.directories, **self.files}

    @property
    def parent(self):
        return self.directories[FILESYSTEM.PARENT_DIRECTORY]

    def at_relative_path(self, path):
        """
        Returns a file or directory in the relative path given.
        :param path:
        :return:
        """
        if path.endswith(FILESYSTEM.SEPARATOR):
            path = path[:len(FILESYSTEM.SEPARATOR)]

        dirs, item_name = path.split(FILESYSTEM.SEPARATOR)[:-1], path.split(FILESYSTEM.SEPARATOR)[-1]
        cwd = self

        for dir_ in dirs:
            try:
                cwd = cwd.directories[dir_]
            except KeyError:
                raise NoSuchDirectoryError(f"Directory {dir_} does not exist in {cwd.name}!!")

        try:
            return cwd.items[item_name]
        except KeyError:
            raise NoSuchFileError(f"File or Directory '{item_name}' do not exist in {cwd.name}")

    def make_sub_dir(self, name):
        """
        Creates a new directory under this one.
        :param name:
        :return:
        """
        if name in self.directories:
            raise DirectoryExistsError(f"{name} is already in {self.name}")

        self.directories[name] = Directory(name=name, parent=self)

    @property
    def full_path(self):
        if self.parent is self:
            return self.name
        return f"{self.parent.full_path}{FILESYSTEM.SEPARATOR}{self.name}"

    def __repr__(self):
        return f"Directory({self.name})"
