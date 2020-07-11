from datetime import datetime

from exceptions import FileNotOpenError


class File:
    """
    A file in the computers filesystem.
    """
    def __init__(self, content):
        """
        Initiated with its contents
        :param content: `str`
        """
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
