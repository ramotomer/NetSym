from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

from computing.internals.shell.commands.command import Command, CommandOutput

if TYPE_CHECKING:
    from computing.internals.shell.shell import Shell
    from computing.computer import Computer


class Dns(Command):
    """
    Command that prints out the arp cache
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        """
        initiates the command.
        :param computer:
        """
        super(Dns, self).__init__('dns', 'print out the dns table of the computer', computer, shell)

        self.parser.add_argument('-a', '--all', dest='is_all', action='store_true', help='print out the dns table')
        self.parser.add_argument('-d', '--delete', dest='is_delete', action='store_true', help='wipe table')

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        prints out the arguments.
        """
        if parsed_args.is_all:
            return CommandOutput(repr(self.computer.dns_table), '')

        if parsed_args.is_delete:
            self.computer.dns_table.wipe()
            return CommandOutput("DNS table wiped successfully! :)", '')

        return CommandOutput(
            '',
            """usage:
dns -a (to print out the dns table)
dns -d (delete the dns table)
"""
        )
