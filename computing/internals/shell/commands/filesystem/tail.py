from __future__ import annotations

from typing import TYPE_CHECKING

from computing.internals.filesystem.directory import Directory
from computing.internals.shell.commands.command import Command, CommandOutput
from exceptions import NoSuchItemError

if TYPE_CHECKING:
    import argparse
    from computing.computer import Computer
    from computing.internals.shell.shell import Shell


class Tail(Command):
    """
    prints bottom rows of file
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        super(Tail, self).__init__('tail', 'print last rows of file', computer, shell)

        self.parser.add_argument('file', help='the file name to read')
        self.parser.add_argument('-n', '--number', type=int, dest='count', metavar='count', default=10,
                                 help='the amount of rows to print')

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        The action of the command
        :param parsed_args:
        :return:
        """
        try:
            file = self.computer.filesystem.at_path(self.shell.cwd, parsed_args.file)
            if isinstance(file, Directory):
                return CommandOutput('', f"'{file.name}' is a directory!")
            with file:
                return CommandOutput('\n'.join(file.read().strip().split('\n')[-parsed_args.count:]), '')
        except NoSuchItemError:
            return CommandOutput('', f"Could not read {parsed_args.file}")
