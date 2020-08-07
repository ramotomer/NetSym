from datetime import datetime

from exceptions import FileNotOpenError
from usefuls.funcs import datetime_from_string


class File:
    """
    A file in the computers filesystem.
    """
    def __init__(self, name, content=''):
        """
        Initiated with its contents
        :param content: `str`
        """
        self.name = name
        self.__content = content
        self.creation_time = datetime.now()
        self.last_edit_time = datetime.now()

        self._is_open_for_reading = False
        self._is_open_for_writing = False

    def open(self, read=True, write=True):
        """
        open the file and receive a file descriptor for it, in-order to read it.
        :return:
        """
        if read:
            self._is_open_for_reading = True
        if write:
            self._is_open_for_writing = True

    def read(self):
        """
        Read the files content
        :return:
        """
        if self._is_open_for_reading:
            return self.__content
        raise FileNotOpenError("Cannot read from closed file for reading!")

    def write(self, data):
        """
        Write data to the file
        :param data:
        :return:
        """
        if self._is_open_for_writing:
            self.__content = data
            self.last_edit_time = datetime.now()
        else:
            raise FileNotOpenError("Cannot write to closed file for writing!")

    def append(self, data):
        """
        Append data to the end of a file.
        :param data:
        :return:
        """
        self.write(self.read() + data)

    def close(self):
        """
        Close the file
        :return:
        """
        self._is_open_for_reading = False
        self._is_open_for_writing = False

    def __enter__(self):
        """
        For context-manager syntax
        :return:
        """
        self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        For context-manager syntax
        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        self.close()

    def dict_save(self):
        """
        Saves the File object as a dictionary so it could be saved in a file
        :return:
        """
        return {
            "class": "File",
            "name": self.name,
            "creation_time": repr(self.creation_time),
            "last_edit_time": repr(self.last_edit_time),
            "content": self.__content,
        }

    @classmethod
    def from_dict_load(cls, dict_):
        """
        Loads a File object from an actual dictionary from a json file
        :return:
        """
        file = cls(dict_["name"], dict_["content"])
        file.creation_time = datetime_from_string(dict_["creation_time"])
        file.last_edit_time = datetime_from_string(dict_["last_edit_time"])
        return file

    def copy(self, new_name=None):
        """
        Returns a new file object, that is identical
        :return:
        """
        name = self.name if new_name is None else new_name
        return self.__class__(name, self.__content)


class PipingFile(File):
    """
    The file that is not mapped to the filesystem. We need it for command piping (`ps | grep 'hello'`)
    """
    __instance = None

    def __init__(self, content=''):
        super(PipingFile, self).__init__('PipingFile', content)
        self.__class__.__instance = self

    @classmethod
    def instance(cls):
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance
