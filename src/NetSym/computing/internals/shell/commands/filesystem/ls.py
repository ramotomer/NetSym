from __future__ import annotations

from typing import TYPE_CHECKING, List

from NetSym.computing.internals.filesystem.directory import Directory
from NetSym.computing.internals.shell.commands.command import Command, CommandOutput
from NetSym.consts import FILESYSTEM
from NetSym.exceptions import NoSuchFileError

if TYPE_CHECKING:
    import argparse
    from NetSym.computing.computer import Computer
    from NetSym.computing.internals.shell.shell import Shell


class Ls(Command):
    """
    lists the current working directory of the computer.
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        """
        Initiates the command with the running computer.
        :param computer:
        """
        super(Ls, self).__init__("ls", "lists the cwd", computer, shell)

        self.parser.add_argument('dirname', metavar='dirname', type=str, nargs='?', help='the directory to list')
        self.parser.add_argument('-a', '--all', dest='show_hidden', action='store_true', help='show hidden dir items')
        self.parser.add_argument('-l', '--long', dest='extended', action='store_true', help='list additional details')

    def _list_dir(self, path: str, show_hidden: bool = False, extended_info: bool = False) -> str:
        """
        Lists the directory at the given path.
        :param path:
        :return:
        """
        if self.computer.filesystem.is_absolute_path(path):
            dir_ = self.computer.filesystem.directory_at_absolute_path(path)
        else:
            dir_ = self.shell.cwd.directory_at_relative_path(path)
        dir_items = list(dir_.items)

        if not show_hidden:
            dir_items = [item for item in dir_.items if not item.startswith(FILESYSTEM.CWD)]

        returned = '\t'.join(dir_items)

        if extended_info:
            returned = self._extended_list_dir(dir_, dir_items)

        return returned

    @staticmethod
    def _extended_list_dir(dir_: Directory, dir_items: List[str]) -> str:
        """
        receives a Directory object and a list of the items in the directory that
        were already listed, returns a string that should be returned.
        :param dir_:
        :param dir_items:
        :return:
        """
        for i, item in enumerate(dir_items[:]):
            if item in dir_.files:
                ctime = f"{dir_.files[item].creation_time.hour}:{dir_.files[item].creation_time.minute}"
                etime = f"{dir_.files[item].last_edit_time.hour}:{dir_.files[item].last_edit_time.minute}"
                dir_items[i] = f"F) {item: >10} {ctime: >5} {etime: >5}"
            else:
                dir_items[i] = f"D) {item: >10}"
        returned = f"TYPE     NAME CTIME ETIME\n" + '\n'.join(dir_items)
        return returned

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        prints out the arguments.
        """
        dirname = parsed_args.dirname if parsed_args.dirname else self.shell.cwd_path
        try:
            listed = self._list_dir(dirname,
                                    show_hidden=parsed_args.show_hidden,
                                    extended_info=parsed_args.extended)
        except NoSuchFileError:
            return CommandOutput('', "No Such file or directory! :(")
        return CommandOutput(listed, '')
