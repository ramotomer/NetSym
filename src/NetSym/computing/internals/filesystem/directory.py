from __future__ import annotations

from typing import Optional, Union, Dict

from NetSym.computing.internals.filesystem.file import File, PipingFile
from NetSym.consts import FILESYSTEM
from NetSym.exceptions import NoSuchDirectoryError, NoSuchFileError, DirectoryAlreadyExistsError, WrongUsageError, \
    NoSuchItemError


class Directory:
    """
    A directory on the computers of the simulation.
    """
    def __init__(self,
                 name: str,
                 parent: Optional[Directory],
                 mount: str = FILESYSTEM.TYPE.EXT4,
                 files: Optional[Dict[str, File]] = None,
                 directories: Optional[Dict[str, Directory]] = None) -> None:
        """
        Initiated with a list of directories and files that are contained in it.

        directories and files are dicts of the form {name: Directory} or {name: File}
        """
        self.name = name
        self.mount = mount

        self.files = files if files is not None else {}
        self.directories = directories if directories is not None else {}

        self.directories[FILESYSTEM.CWD] = self
        self.directories[FILESYSTEM.PARENT_DIRECTORY] = parent if parent is not None else self

    @property
    def items(self) -> Dict[str, T_ContainedItem]:
        return {**self.directories, **self.files}

    @property
    def contained_directories(self) -> Dict[str, Directory]:
        return {name: directory for name, directory in self.directories.items()
                if name not in {FILESYSTEM.CWD, FILESYSTEM.PARENT_DIRECTORY}}

    @property
    def parent(self) -> Directory:
        return self.directories[FILESYSTEM.PARENT_DIRECTORY]

    @parent.setter
    def parent(self, dir_: Directory) -> None:
        self.directories[FILESYSTEM.PARENT_DIRECTORY] = dir_

    def at_relative_path(self, path: str) -> T_ContainedItem:
        """
        Returns a file or directory in the relative path given.
        :param path:
        :return:
        """
        if path == FILESYSTEM.PIPING_FILE:
            return PipingFile.instance()

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

    def make_sub_dir(self, name: str, mount: str = FILESYSTEM.TYPE.EXT4) -> None:
        """
        Creates a new directory under this one.
        :param name:
        :param mount:
        :return:
        """
        if name in self.directories:
            raise DirectoryAlreadyExistsError(f"{name} is already in {self.name}")

        self.directories[name] = Directory(name=name, parent=self, mount=mount)

    def make_empty_file(self, name: str, raise_on_exists: bool = True) -> Optional[File]:
        """
        Create an empty file
        """
        if name in self.files:
            if raise_on_exists:
                raise FileExistsError
        else:
            self.files[name] = File(name, '')
        return self.files[name]

    @property
    def full_path(self) -> str:
        if self.parent is self:
            return self.name
        if self.parent.parent is self.parent:
            return self.parent.name + self.name
        return f"{self.parent.full_path}{FILESYSTEM.SEPARATOR}{self.name}"

    def wipe(self) -> None:
        """
        Deletes everything from the directory
        :return:
        """
        self.files.clear()
        self.directories = {
            FILESYSTEM.CWD: self.directories[FILESYSTEM.CWD],
            FILESYSTEM.PARENT_DIRECTORY: self.directories[FILESYSTEM.PARENT_DIRECTORY],
        }

    def add_item(self, item: T_ContainedItem) -> None:
        """
        Adds an item to the directory (could be a file or a directory)
        :param item:
        :return:
        """
        if isinstance(item, File):
            self.files[item.name] = item
        elif isinstance(item, Directory):
            self.directories[item.name] = item
        else:
            raise WrongUsageError("Only use with files or directories!")

    def pop_item(self, item_name: str) -> T_ContainedItem:
        """
        Removes an item from the directory. (could be File or Directory)
        :param item_name:
        :return:
        """
        try:
            if item_name in self.directories:
                item = self.directories[item_name]
                del self.directories[item_name]
            else:
                item = self.files[item_name]
                del self.files[item_name]
        except KeyError:
            raise NoSuchItemError

        return item

    def dict_save(self) -> Dict:
        """
        Save to dict for file saving!
        :return:
        """
        return {
            "class": "Directory",
            "name": self.name,
            "mount": self.mount,
            "files": [
                file.dict_save() for file in self.files.values()
            ],
            "directories": [
                directory.dict_save() for directory in self.contained_directories.values()
            ],
        }

    @classmethod
    def from_dict_load(cls, dict_: Dict) -> Directory:
        """
        Load from json file
        :param dict_:
        :return:
        """
        loaded = cls(
            dict_["name"], None, mount=dict_["mount"],
            files={filedict["name"]: File.from_dict_load(filedict) for filedict in dict_["files"]},
            directories={dirdict["name"]: cls.from_dict_load(dirdict) for dirdict in dict_["directories"]},
        )

        for sub_dir in loaded.contained_directories.values():
            sub_dir.parent = loaded

        return loaded

    def __repr__(self) -> str:
        return f"Directory({self.name})"


T_ContainedItem = Union[Directory, File]
