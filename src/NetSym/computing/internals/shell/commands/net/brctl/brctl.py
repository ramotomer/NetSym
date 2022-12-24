from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

from NetSym.computing.internals.shell.commands.command import Command, CommandOutput
from NetSym.computing.internals.shell.commands.net.brctl.brctl_showbr import BrctlShowbrCommand
from NetSym.exceptions import *

if TYPE_CHECKING:
    from NetSym.computing.computer import Computer
    from NetSym.computing.internals.shell.shell import Shell


class Brctl(Command):
    """
    Controls the network communication of the device.
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        """
        initiates the command.
        :param computer:
        """
        super(Brctl, self).__init__('brctl', 'manage and display bridge settings', computer, shell)
        self.parser.add_argument('object', metavar='object', type=str, nargs='?', help='type of brctl command to run')
        self.parser.add_argument('args', metavar='args', nargs='*', type=str, help='rest of the arguments')

        self.object_to_command = {
            'showbr': BrctlShowbrCommand,
        }

    @staticmethod
    def _brctl_help() -> str:
        """
        Returns a string help document
        :return:
        """
        return """Usage: brctl [OPTIONS] OBJECT { COMMAND }
where OBJECT := { showbr }
For now only showbr is implemented - NetSym does not use unix bridges to implement switches  
"""
    # TODO: FEATURE: implement switches using the linux bridges!!!

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        redirects the action to the action of the specified `brctl` command (brctl showbr, brctl showmacs, etc...)
        """
        try:
            command_class = self.object_to_command[parsed_args.object](self.computer, self.shell)
        except KeyError:
            return CommandOutput('', f"{self._brctl_help()}")

        # TODO: this code should probably be shared with the `ip` command... and all commands that have multiple commands inside them

        try:
            parsed_command = command_class.parse(' '.join([f'brctl_{parsed_args.object}'] + parsed_args.args))
        except SyntaxArgumentMessageError as e:
            return CommandOutput('', e.args[0])

        return command_class.action(parsed_command.parsed_args)
