from __future__ import annotations

from typing import TYPE_CHECKING

from NetSym.computing.internals.shell.commands.command import Command, CommandOutput
from NetSym.exceptions import DirectoryAlreadyExistsError, NoSuchDirectoryError

if TYPE_CHECKING:
    import argparse
    from NetSym.computing.computer import Computer
    from NetSym.computing.internals.shell.shell import Shell


class Mkdir(Command):
    """
    Create a directory
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        """
        initiates the command.
        :param computer: 
        """
        super(Mkdir, self).__init__('mkdir', 'create directory', computer, shell)

        self.parser.add_argument('dirnames', metavar='dirnames', type=str, nargs='+', help='directories to create')

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        Makes a directory
        """
        stdout, stderr = [], []
        for dirname in parsed_args.dirnames:
            try:
                self.computer.filesystem.make_dir(
                    self.computer.filesystem.absolute_from_relative(self.shell.cwd, dirname)
                )
            except DirectoryAlreadyExistsError:
                stderr.append(f"Directory '{dirname}' Exists! :(")
            except NoSuchDirectoryError:
                stderr.append(f"Cannot create parent directories of '{dirname}', only the directory itself!")
            else:
                stdout.append(f"Successfully Created directory '{dirname}' :)")

        return CommandOutput('\n'.join(stdout), '\n'.join(stderr))
