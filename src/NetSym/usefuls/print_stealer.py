import sys

from NetSym.usefuls.my_string_io import MyStringIO


class PrintStealer:
    """
    A context manager that takes what is printed to stdout and stderr inside it, traps it, and records it.
    After you step out of it, you can view what was printed, it will be save in the `self.printed` attribute.
    """
    def __init__(self) -> None:
        self.printed = ''

    def __enter__(self) -> None:
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        sys.stdout = MyStringIO()
        sys.stderr = sys.stdout

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.printed = sys.stdout.getvalue()
        sys.stdout.close()
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr
