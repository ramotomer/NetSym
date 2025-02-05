from __future__ import annotations

from typing import TYPE_CHECKING

from NetSym.computing.internals.shell.commands.command import Command, CommandOutput
from NetSym.consts import FILESYSTEM
from NetSym.exceptions import NoSuchItemError

if TYPE_CHECKING:
    import argparse
    from NetSym.computing.computer import Computer
    from NetSym.computing.internals.shell.shell import Shell


class Cd(Command):
    """
    Changes the current working directory.
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        """
        initiates the command.
        :param computer:
        """
        super(Cd, self).__init__('cd', 'change the cwd', computer, shell)

        self.parser.add_argument('new_dir', metavar='new_dir', type=str, nargs='?', help='directory to switch to')

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        prints out the arguments.
        """
        new_dir = parsed_args.new_dir if parsed_args.new_dir else FILESYSTEM.HOME_DIR
        try:
            self.shell.cwd = self.computer.filesystem.directory_at_path(self.shell.cwd, new_dir)
        except NoSuchItemError:
            return CommandOutput('', f"Cannot switch to directory '{parsed_args.new_dir}' :(")

        return CommandOutput(f"Switched to '{self.shell.cwd_path}'", '')
