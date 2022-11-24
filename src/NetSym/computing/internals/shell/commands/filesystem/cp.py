from __future__ import annotations

from typing import TYPE_CHECKING

from NetSym.computing.internals.shell.commands.command import Command, CommandOutput
from NetSym.exceptions import NoSuchFileError

if TYPE_CHECKING:
    import argparse
    from NetSym.computing.computer import Computer
    from NetSym.computing.internals.shell.shell import Shell


class Cp(Command):
    """
    Copies a file to a new location or name
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        """
        initiate command
        """
        super(Cp, self).__init__('cp', 'copy a file to a new location or name', computer, shell)

        self.parser.add_argument('src', help='the source file path')
        self.parser.add_argument('dst', help='the destination file path')

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        Copy a file to a new location or name
        :return:
        """
        try:
            self.computer.filesystem.copy_file(parsed_args.src, parsed_args.dst, self.shell.cwd)
        except NoSuchFileError:
            return CommandOutput('', "The source file does not exist! :(")

        return CommandOutput(f"File copied to '{parsed_args.dst}' successfully", '')
