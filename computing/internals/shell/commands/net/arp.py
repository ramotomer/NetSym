from __future__ import annotations

from typing import TYPE_CHECKING

from computing.internals.shell.commands.command import Command, CommandOutput

if TYPE_CHECKING:
    import argparse
    from computing.computer import Computer
    from computing.internals.shell.shell import Shell


class Arp(Command):
    """
    Command that prints out the arp cache
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        """
        initiates the command.
        :param computer:
        """
        super(Arp, self).__init__('arp', 'print out arp cache', computer, shell)

        self.parser.add_argument('-a', '--all', dest='is_all', action='store_true', help='print out the arp cache')
        self.parser.add_argument('-d', '--delete', dest='is_delete', action='store_true', help='wipe dynamic items')

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        prints out the arguments.
        """
        if parsed_args.is_all:
            return CommandOutput(repr(self.computer.arp_cache), '')

        if parsed_args.is_delete:
            self.computer.arp_cache.wipe()
            return CommandOutput("Arp cache wiped successfully! :)", '')

        return CommandOutput(
            '',
            """usage:
arp -a (to print out the arp cache)
arp -d (delete the arp cache)
"""
        )
