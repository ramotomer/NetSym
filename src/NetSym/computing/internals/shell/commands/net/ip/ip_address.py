from __future__ import annotations

from typing import TYPE_CHECKING, List

from NetSym.address.mac_address import MACAddress
from NetSym.computing.connections.loopback_connection import LoopbackConnection
from NetSym.computing.internals.shell.commands.command import Command, CommandOutput
from NetSym.exceptions import AddressError, NoSuchInterfaceError

if TYPE_CHECKING:
    import argparse
    from NetSym.computing.internals.network_interfaces.cable_network_interface import CableNetworkInterface
    from NetSym.computing.internals.shell.shell import Shell
    from NetSym.computing.computer import Computer


class IpAddressCommand(Command):
    """
    The command that prints the arguments that it receives.
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        """
        initiates the command.
        :param computer:
        """
        super(IpAddressCommand, self).__init__('ip_address', 'manage ip addresses of the device', computer, shell)

        self.parser.add_argument('args', metavar='args', type=str, nargs='*', help='arguments')

        self.commands = {
            'show': self._list_address,
            'add': self._add_address,
            'del': self._del_address,
            'replace': self._replace_address,
        }

    @staticmethod
    def _get_interface_data(interface: CableNetworkInterface, index: int = 0) -> str:
        """
        Receives interface, returns string data
        :param interface:
        :return:
        """
        # TODO: add interface MTU-s
        type_ = 'LOOPBACK' \
            if interface.is_connected() and isinstance(interface.connection, LoopbackConnection) \
            else 'BROADCAST'
        type_2 = 'loopback' if type_ == 'LOOPBACK' else 'ether'

        is_up = 'UP' if interface.is_powered_on else 'DOWN'
        is_blocked = ',BLOCKED' if interface.is_blocked else ''
        is_no_carrier = ',NO CARRIER' if interface.no_carrier else ''

        ip_info = ""
        if interface.ip is not None:
            ip_info = f"\n    inet {repr(interface.ip)} brd {str(interface.ip.subnet_broadcast())} scope global"

        return f"""{index}: {interface.name} <{type_},{is_up}{is_blocked}{is_no_carrier}>
    link/{type_2} {interface.mac} brd {MACAddress.broadcast()}{ip_info}
"""

    def _list_address(self, args: List[str]) -> CommandOutput:
        """
        return a string that lists the interfaces of the computer
        """
        if 'dev' not in args:
            stdout = [self._get_interface_data(interface, i) for i, interface in enumerate(self.computer.all_interfaces)]
            return CommandOutput('\n'.join(stdout), '')
        else:
            return CommandOutput(self._get_interface_data(args[args.index('dev') + 1]), '')

    def _add_address(self, args: List[str]) -> CommandOutput:
        """
        for example: ip address add 1.1.1.1/24 dev work1
        only if the interface does not have an ip already
        """
        address = args[1]

        try:
            interface = self.computer.interface_by_name(args[args.index('dev') + 1])
        except NoSuchInterfaceError:
            return CommandOutput('', "No Such interface :(")
        except ValueError:
            return CommandOutput('', "Specify interface!")

        if interface.has_ip():
            return CommandOutput('', "Interface already has IP address!")

        try:
            self.computer.set_ip(interface, address)
        except AddressError:
            return CommandOutput('', "Invalid IP address!")

        return CommandOutput("Added IP address successfully! :)", '')

    def _replace_address(self, args: List[str]) -> CommandOutput:
        """
        for example: ip address replace 1.1.1.1/24 dev work1
        only if the interface has an ip already
        """
        address = args[1]

        try:
            interface = self.computer.interface_by_name(args[args.index('dev') + 1])
        except NoSuchInterfaceError:
            return CommandOutput('', "No Such interface :(")
        except ValueError:
            return CommandOutput('', "Specify interface!")

        if not interface.has_ip():
            return CommandOutput('', "Interface does not have IP address!")

        try:
            self.computer.set_ip(interface, address)
        except AddressError:
            return CommandOutput('', "Invalid IP address!")

        return CommandOutput("Replaced IP address successfully! :)", '')

    def _del_address(self, args: List[str]) -> CommandOutput:
        """
        for example: ip address add 1.1.1.1/24 dev work1
        only if the interface does not have an ip already
        :param args:
        :return:
        """
        try:
            interface = self.computer.interface_by_name(args[args.index('dev') + 1])
        except NoSuchInterfaceError:
            return CommandOutput('', "No Such interface :(")
        except ValueError:
            return CommandOutput('', "Specify interface!")

        if not interface.has_ip():
            return CommandOutput('', "Interface does not have IP address!")

        try:
            self.computer.remove_ip(interface)
        except AddressError:
            return CommandOutput('', "Invalid IP address!")

        return CommandOutput("Deleted IP address successfully! :)", '')

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        prints out the arguments.
        """
        # return self._list_interfaces()

        args = parsed_args.args

        if not args:
            return self._list_address(args)

        if args[0] in self.commands:
            return self.commands[args[0]](args)

        return CommandOutput(
            '',
            """WRONG USAGE! usage:
ip address { add | replace } IPADDR dev NAME
ip address del dev NAME
ip address [ show [ dev NAME ] ]
"""
        )
