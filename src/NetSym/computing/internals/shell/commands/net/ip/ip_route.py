from __future__ import annotations

from typing import TYPE_CHECKING

from address.ip_address import IPAddress
from computing.internals.shell.commands.command import Command, CommandOutput
from consts import ADDRESSES
from exceptions import RoutingTableError, WrongIPRouteUsageError
from usefuls.funcs import get_the_one

if TYPE_CHECKING:
    import argparse
    from computing.computer import Computer
    from computing.internals.shell.shell import Shell


class IpRouteCommand(Command):
    """
    The command that prints the arguments that it receives.
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        """
        initiates the command.
        :param computer:
        """
        super(IpRouteCommand, self).__init__('ip_route', 'manage routes of the device', computer, shell)

        self.parser.add_argument('args', metavar='args', type=str, nargs='*', help='arguments')

        self.commands = {
            'list': self._list_routes,
            'print': self._list_routes,
            'add': self._add_route,
            'del': self._del_route,
        }

    def _add_route(self, args: argparse.Namespace) -> CommandOutput:
        """
        Receives arguments, adds a route and returns a CommandOutput
        :param args:
        :return:
        """
        try:
            net = IPAddress(args[args.index('add') + 1])
            gateway = IPAddress(args[args.index('via') + 1]) if 'via' in args else ADDRESSES.IP.ON_LINK
            interface_name = args[args.index('dev') + 1]
        except IndexError:
            raise WrongIPRouteUsageError()

        interface_ip = get_the_one(self.computer.all_interfaces, lambda c: c.name == interface_name).ip
        if interface_ip is None:
            return CommandOutput('', "The interface does not have an IP address!!!")

        self.computer.routing_table.route_add(net, gateway, IPAddress.copy(interface_ip))
        return CommandOutput('OK!', '')

    def _del_route(self, args: argparse.Namespace) -> CommandOutput:
        """
        Receives arguments, deletes a route and returns CommandOutput
        :param args:
        :return:
        """
        try:
            net = args[args.index('del') + 1]
        except IndexError:
            raise WrongIPRouteUsageError()

        try:
            self.computer.routing_table.route_delete(IPAddress(net))
        except RoutingTableError:
            return CommandOutput("", "Route does not exist! did not delete :(")
        else:
            return CommandOutput("OK!", '')

    def _list_routes(self, args: argparse.Namespace) -> CommandOutput:
        """
        list the active routes
        :param args:
        :return:
        """
        return CommandOutput(repr(self.computer.routing_table), '')

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        prints out the arguments.
        """
        try:
            if not parsed_args.args:
                return self._list_routes(parsed_args.args)

            elif parsed_args.args[0] in self.commands:
                return self.commands[parsed_args.args[0]](parsed_args.args)
        except WrongIPRouteUsageError:
            pass  # vv  print the usage  vv

        return CommandOutput(
            '', """
Wrong Usage! 
The syntax is `ip route add <net> via <gateway_ip> dev <interface_name>
You can drop the `via` to create `On-Link` routes :)
Or if you want to remove a route, `ip route del <net>`
List routes by typing `ip route list` or just `ip route`"""
        )

        # syntax: `ip route add 1.1.1.1/24 via 10.0.0.20 dev ens33` for example.
