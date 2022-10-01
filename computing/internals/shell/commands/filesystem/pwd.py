from __future__ import annotations

from typing import TYPE_CHECKING

from computing.internals.shell.commands.command import Command, CommandOutput

if TYPE_CHECKING:
    import argparse
    from computing.computer import Computer
    from computing.internals.shell.shell import Shell


class Pwd(Command):
    """
    prints out the cwd
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        """
        initiates the command.
        :param computer:
        """
        super(Pwd, self).__init__('pwd', 'print out the cwd', computer, shell)

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        prints out the cwd.
        """
        return CommandOutput(f"{self.shell.cwd_path}", '')
