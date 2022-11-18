from __future__ import annotations

from typing import TYPE_CHECKING

from NetSym.computing.internals.shell.commands.command import Command, CommandOutput

if TYPE_CHECKING:
    import argparse
    from NetSym.computing.computer import Computer
    from NetSym.computing.internals.shell.shell import Shell


class Echo(Command):
    """
    The command that prints the arguments that it receives.
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        """
        initiates the command.
        :param computer:
        """
        super(Echo, self).__init__('echo', 'print out arguments', computer, shell)

        self.parser.add_argument('words', metavar='words', type=str, nargs='*', help='words to print')
        self.parser.add_argument('-n', dest='newline_count', type=int, default=1, help='the amount of newlines at the end')

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        The command action
        """
        return CommandOutput(' '.join(parsed_args.words) + ('\n' * (parsed_args.newline_count - 1)), '')
