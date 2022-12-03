from __future__ import annotations

from typing import TYPE_CHECKING, List, Callable, Dict

from NetSym.address.mac_address import MACAddress
from NetSym.computing.connections.loopback_connection import LoopbackConnection
from NetSym.computing.internals.shell.commands.command import Command, CommandOutput
from NetSym.exceptions import DeviceAlreadyConnectedError, NoSuchInterfaceError

if TYPE_CHECKING:
    import argparse
    from NetSym.computing.internals.network_interfaces.interface import Interface
    from NetSym.computing.internals.shell.shell import Shell
    from NetSym.computing.computer import Computer


class IpLinkCommand(Command):
    """
    The command that prints the arguments that it receives.
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        """
        initiates the command.
        :param computer:
        """
        super(IpLinkCommand, self).__init__('ip_link', 'manage ip links of the device', computer, shell)

        self.parser.add_argument('args', metavar='args', type=str, nargs='*', help='arguments')

        self.commands: Dict[str, Callable[[List[str]], CommandOutput]] = {
            'list':  self._list_links,
            'print': self._list_links,
            'add':   self._add_link,
            'del':   self._del_link,
            'set':   self._set_link,
        }

    @staticmethod
    def _link_description_from_interface(interface: Interface, index: int = 0) -> str:
        """
        returns a string description of the link, receives an interface of the computer.
        :param interface: `Interface`
        :return:
        """

        if not interface.is_connected():
            return f"""{index}: NIC: {interface.name}(DISCONNECTED)\n"""

        is_blocked = '\n    BLOCKED' if interface.connection.is_blocked else ''
        is_loopback = '\n    LOOPBACK' if isinstance(interface.connection, LoopbackConnection) else ''

        return f"""{index}: NIC: {interface.name}
link:
    speed: {interface.connection.speed}
    PL percent: {interface.connection.packet_loss}
    length: {interface.connection.length}{is_blocked}{is_loopback}
"""

    def _list_links(self, args: List[str]) -> CommandOutput:
        """
        List out the links that the computer has
        :param args:
        :return:
        """
        link_list = [self._link_description_from_interface(interface, i)
                     for i, interface in enumerate(self.computer.all_interfaces)]
        return CommandOutput('\n'.join(link_list), '')

    def _add_link(self, args: List[str]) -> CommandOutput:
        """
        Adds an interface
        :param args:
        :return:
        """
        try:
            name = args[args.index('add') + 1]
            mac = args[args.index('mac') + 1] if 'mac' in args else None
        except IndexError:
            return CommandOutput('', "Syntax error! use: 'ip link add <name> [mac <mac>]")

        if name in [nic.name for nic in self.computer.interfaces]:
            return CommandOutput('', f'An interface named {name} already exists')

        # TODO: this vvvv
        raise NotImplementedError("Must think how to register the interface created by this command... sorry...")
        # self.computer.add_interface(name, mac)
        # return CommandOutput(f"Added interface {name} successfully :)", '')

    def _del_link(self, args: List[str]) -> CommandOutput:
        """
        Delete an interface
        :param args:
        :return:
        """
        try:
            name = args[args.index('del') + 1]
        except IndexError:
            return CommandOutput('', "Syntax error! use: 'ip link del <name> [mac <mac>]")

        if name not in [nic.name for nic in self.computer.interfaces]:
            return CommandOutput('', f'An interface named {name} does not exist!')
        try:
            self.computer.remove_interface(name)
        except DeviceAlreadyConnectedError:
            return CommandOutput('', f"Cannot remove a connected interface :(")
        return CommandOutput("Interface removed successfully!", '')

    def _set_link(self, args: List[str]) -> CommandOutput:
        """
        Sets an attribute of an interface or connection
        :param args:
        :return:
        """
        try:
            interface = self.computer.interface_by_name(args[1])
        except NoSuchInterfaceError:
            return CommandOutput('', f"There is no interface named {args[0]}")

        if 'up' in args:
            interface.is_powered_on = True
        elif 'down' in args:
            interface.is_powered_on = False

        if 'block' in args:
            if args[args.index('block') + 1] == 'on':
                interface.block()
            else:
                interface.unblock()

        if 'promisc' in args:
            interface.is_promisc = (args[args.index('promisc') + 1] == 'on')
        if 'name' in args:
            interface.name = args[args.index('name') + 1]
        if 'macaddr' in args:
            interface.mac = MACAddress(args[args.index('macaddr') + 1])

        if 'connection' in args:
            return self._set_link_connection(interface, args)

        return CommandOutput("OK!", '')

    @staticmethod
    def _set_link_connection(interface: Interface, args: List[str]) -> CommandOutput:
        """
        Takes care of `ip link set <NIC> connection_side ...` commands
        """
        command = args[args.index('connection') + 1]
        value = args[args.index(command) + 1]

        if command == 'speed':
            interface.connection.set_speed(int(value))
        elif command == 'pl':
            interface.connection.set_pl(float(value))
        else:
            return CommandOutput('', "Connection commands are `pl` or `speed` only!")
        return CommandOutput("OK!", '')

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        decide what to do with the arguments and do it!
        """
        args = parsed_args.args
        if not args:
            return self._list_links(args)

        if args[0] in self.commands:
            return self.commands[args[0]](args)

        return CommandOutput(
            '', """usage:
ip link { list | print }

ip link add NAME [ mac MAC ]

ip link del NAME

ip link set NAME [ { up | down } ]
                 [ promisc { on | off } ]
                 [ block { on | off } ]
                 [ macaddr MAC ]
                 [ name NAME ]
                 [ connection [ speed SPEED ]
                              [ pl PL ] ]
"""
        )
