from __future__ import annotations

from typing import TYPE_CHECKING

from NetSym.computing.internals.shell.commands.command import Command, CommandOutput
from NetSym.computing.internals.shell.commands.net.ip.ip_address import IpAddressCommand
from NetSym.computing.internals.shell.commands.net.ip.ip_link import IpLinkCommand
from NetSym.computing.internals.shell.commands.net.ip.ip_route import IpRouteCommand

if TYPE_CHECKING:
    import argparse
    from NetSym.computing.computer import Computer
    from NetSym.computing.internals.shell.shell import Shell


class Ip(Command):
    """
    Controls the network communication of the device.
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        """
        initiates the command.
        :param computer:
        """
        super(Ip, self).__init__('ip', 'manage and display ip settings', computer, shell)
        self.parser.add_argument('object', metavar='object', type=str, nargs='?', help='type of ip command to run')
        self.parser.add_argument('args', metavar='args', nargs='*', type=str, help='rest of the arguments')

        self.object_to_command = {
            'address': IpAddressCommand,
            'link': IpLinkCommand,
            'route': IpRouteCommand,

            'a': IpAddressCommand,
            'l': IpLinkCommand,
            'r': IpRouteCommand,
        }

    @staticmethod
    def _ip_help() -> str:
        """
        Returns a string help document
        :return:
        """
        return """Usage: ip [OPTIONS] OBJECT { COMMAND }
where OBJECT := { link | address | route } 
"""

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        redirects the action to the action of the specified `ip` command (ip a, ip l, etc...)
        """
        try:
            command_class = self.object_to_command[parsed_args.object](self.computer, self.shell)
        except KeyError:
            return CommandOutput('', f"{self._ip_help()}")
        _, parsed_additional_args = command_class.parse(' '.join([f'ip_{parsed_args.object}'] + parsed_args.args))
        return command_class.action(parsed_additional_args)
