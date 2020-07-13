from computing.internals.filesystem.directory import Directory
from computing.internals.filesystem.file import File
from consts import FILESYSTEM
from exceptions import PathError, NoSuchItemError


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
    # TODO: when saving computer to file, his filesystem does not save!!! work on that

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
        filesystem.make_dir('/tmp', mount=FILESYSTEM.TYPE.TMPFS)
        filesystem.make_dir(FILESYSTEM.HOME_DIR)
        return filesystem


    @staticmethod
    def is_absolute_path(path):
        """
        returns the answer to the damn question in the title of the method!!! hell, why do i even document....
        :param path:
        :return:
        """
        return path.startswith(FILESYSTEM.ROOT)

    def absolute_from_relative(self, parent: Directory, path: str):
        """
        receives relative path and prent dir and return absolute path.
        If already absolute, returns the path.
        :param parent:
        :param path:
        :return:
        """
        if self.is_absolute_path(path):
            return path

        returned = parent.full_path
        for name in path.split(FILESYSTEM.SEPARATOR):
            if name == FILESYSTEM.CWD:
                continue
            elif name == FILESYSTEM.PARENT_DIRECTORY:
                returned = FILESYSTEM.SEPARATOR.join(returned.split(FILESYSTEM.SEPARATOR)[:-1])
            else:
                returned += FILESYSTEM.SEPARATOR + name
        return returned

    def at_absolute_path(self, path):
        """
        Receives an absolute path and returns the file or directory at that location.
        :param path:
        :return:
        """
        if not self.is_absolute_path(path):
            raise PathError(f"path is not absolute! '{path}'")

        return self.root.at_relative_path(FILESYSTEM.CWD + path)

    def at_path(self, cwd: Directory, path: str):
        """
        Returns what is at a given path, it can be relative or absolute!!!
        :param cwd:
        :param path:
        :return:
        """
        if self.is_absolute_path(path):
            return self.at_absolute_path(path)
        return cwd.at_relative_path(path)

    def is_file(self, path, cwd: Directory = None):
        """
        Returns whether or not the path points to a file (and if it even exists at all).
        :param path: absolute path!
        :param cwd: if the path is not absolute, must supply the current directory.
        :return:
        """
        if cwd is None and not self.is_absolute_path(path):
            raise PathError("path must be absolute if no cwd was specified!")

        try:
            item = self.at_path(cwd, path)
        except NoSuchItemError:
            return False

        return isinstance(item, File)

    def separate_base(self, path):
        """
        Receives a path and returns a tuple of the name of the item and the name of the directory it resides in.
        for example:
        '/usr/bin/fun/echo' -> ('/usr/bin/fun/', 'echo')

        if it is a relative path with no /-s, '.' will be returned as the directory
        :param path: str
        :return: (str, str)
        """
        base_dir_path = FILESYSTEM.SEPARATOR.join(path.split(FILESYSTEM.SEPARATOR)[:-1])
        filename = path.split(FILESYSTEM.SEPARATOR)[-1]
        if FILESYSTEM.SEPARATOR not in path:
            base_dir_path = FILESYSTEM.CWD
        elif base_dir_path == '':
            base_dir_path = self.root_path
        return base_dir_path, filename

    def make_dir(self, absolute_path, mount=FILESYSTEM.TYPE.EXT4):
        """
        Creates a directory in a given path.
        :param absolute_path: absolute path to the new directory.
        :param mount: the mount of the directory, the file-system type that it is mounted on.
        :return:
        """
        parent_path, dirname = self.separate_base(absolute_path)
        parent_dir = self.at_absolute_path(parent_path)
        parent_dir.make_sub_dir(dirname, mount=mount)

    def wipe_temporary_directories(self, root_dir=None):
        """
        deletes everything that is mounted on to a temporary directory.
        :return:
        """
        if root_dir is None:
            root_dir = self.root
        for directory in root_dir.contained_directories.values():
            if directory.mount == FILESYSTEM.TYPE.TMPFS:
                directory.wipe()
            self.wipe_temporary_directories(root_dir=directory)

    def output_to_file(self, data, path, cwd: Directory = None, append=False):
        """
        Create the file if it does not exist.
        Can receive both relative or absolute paths.
        :param data:
        :param path:
        :param cwd:
        :param append:
        :return:
        """
        base_dir_path, filename = self.separate_base(path)
        base_dir = self.at_path(cwd, base_dir_path)

        if not self.is_file(path, cwd):
            base_dir.make_empty_file(filename)

        file = base_dir.files[filename]
        with file:
            if append:
                file.append(data)
            else:
                file.write(data)

    def dict_save(self):
        """
        Save to dict for json file
        :return:
        """
        return {
            "class": "Filesystem",
            "root_path": self.root_path,
            "root": self.root.dict_save(),
        }

    @classmethod
    def from_dict_load(cls, dict_):
        """
        Loads filesystem from json file dict.
        :param dict_:
        :return:
        """
        filesystem = cls()
        filesystem.root_path = dict_["root_path"]
        filesystem.root = Directory.from_dict_load(dict_["root"])
        return filesystem
