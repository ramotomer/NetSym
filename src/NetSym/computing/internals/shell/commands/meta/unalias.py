from __future__ import annotations

from typing import TYPE_CHECKING

from NetSym.computing.internals.shell.commands.command import Command, CommandOutput

if TYPE_CHECKING:
    import argparse
    from NetSym.computing.computer import Computer
    from NetSym.computing.internals.shell.shell import Shell


class Unalias(Command):
    """
    Create a string that will be automatically translated to a command or a number of commands.
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        super(Unalias, self).__init__('unalias', 'remove an alias for a command or string', computer, shell)

        self.parser.add_argument('alias', help="the alias to remove")

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        The action of the command
        :param parsed_args:
        :return:
        """
        if parsed_args.alias not in self.shell.aliases:
            return CommandOutput('', "There is no such alias! :(")

        del self.shell.aliases[parsed_args.alias]
        return CommandOutput('Removed successfully', '')
