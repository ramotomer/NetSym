from __future__ import annotations

from random import randint
from typing import TYPE_CHECKING

from NetSym.computing.internals.shell.commands.command import Command, CommandOutput

if TYPE_CHECKING:
    import argparse
    from NetSym.computing.computer import Computer
    from NetSym.computing.internals.shell.shell import Shell


class Uname(Command):
    """
    The command that prints the arguments that it receives.
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        """
        initiates the command.
        :param computer:
        """
        super(Uname, self).__init__('uname', 'print architecture name', computer, shell)

        self.parser.add_argument('-a', '--all', dest='is_extended', action='store_true', help='show extended uname')

    def to_print(self, parsed_args: argparse.Namespace) -> str:
        """
        The message to print.
        :return:
        """
        if parsed_args.is_extended:
            return f"{self.computer.os} Kernel {randint(0, 15)}.{randint(0, 9)} Compiled today just for you!"
        return self.computer.os

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        prints out the arguments.
        """
        return CommandOutput(self.to_print(parsed_args), '')
