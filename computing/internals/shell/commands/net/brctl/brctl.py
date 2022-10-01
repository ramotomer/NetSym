from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

from computing.internals.shell.commands.command import Command, CommandOutput
from computing.internals.shell.commands.net.brctl.brctl_showbr import BrctlShowbrCommand

if TYPE_CHECKING:
    from computing.computer import Computer
    from computing.internals.shell.shell import Shell


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
    # TODO: implement switches using the linux bridges!!!

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        redirects the action to the action of the specified `brctl` command (brctl showbr, brctl showmacs, etc...)
        """
        try:
            command_class = self.object_to_command[parsed_args.object](self.computer, self.shell)
        except KeyError:
            return CommandOutput('', f"{self._brctl_help()}")
        _, parsed_additional_args = command_class.parse(' '.join([f'brctl_{parsed_args.object}'] + parsed_args.args))
        return command_class.action(parsed_additional_args)
