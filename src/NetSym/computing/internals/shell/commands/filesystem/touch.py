from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from NetSym.computing.internals.shell.commands.command import Command, CommandOutput
from NetSym.exceptions import NoSuchItemError

if TYPE_CHECKING:
    import argparse
    from NetSym.computing.computer import Computer
    from NetSym.computing.internals.shell.shell import Shell


class Touch(Command):
    """
    Change a file's timestamp and if it does not exist, create it.
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        """
        initiates the command.
        :param computer: 
        """
        super(Touch, self).__init__('touch',
                                    "Change a file's timestamp and if it does not exist, create it.",
                                    computer, shell)

        self.parser.add_argument('files', metavar='files', type=str, nargs='+', help='files to touch')

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        touches the file
        """
        stdout = ''
        stderr = ''
        for file_path in parsed_args.files:
            if self.computer.filesystem.is_file(file_path, self.shell.cwd):
                file = self.computer.filesystem.at_path(self.shell.cwd, file_path)
                file.last_edit_time = datetime.now()
                stdout += f"touched {file_path}\n"
            else:
                base_dir, filename = self.computer.filesystem.filename_and_dir_from_path(self.shell.cwd, file_path)
                try:
                    base_dir.make_empty_file(filename)
                except NoSuchItemError:
                    stderr += f"Could not touch {file_path} :(\n"
                else:
                    stdout += f"Created {file_path}\n"

        return CommandOutput(stdout[:-1], stderr[:-1])
