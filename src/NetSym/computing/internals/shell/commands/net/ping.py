from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Dict

from NetSym.computing.internals.processes.usermode_processes.ping_process import SendPing
from NetSym.computing.internals.shell.commands.process_creating_command import ProcessCreatingCommand
from NetSym.consts import PROTOCOLS

if TYPE_CHECKING:
    import argparse
    from NetSym.computing.computer import Computer
    from NetSym.computing.internals.shell.shell import Shell


class Ping(ProcessCreatingCommand):
    """
    Send a ping to another computer.
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        """
        initiates the command.
        :param computer:
        """
        super(Ping, self).__init__('ping', 'ping a computer', computer, shell, SendPing)

        self.parser.add_argument('destination', type=str, help='the destination hostname or IP address')
        self.parser.add_argument('-n', type=int, dest='count',  default=3, help='ping count')
        self.parser.add_argument('-l', type=int, dest='length', default=PROTOCOLS.ICMP.DEFAULT_MESSAGE_LENGTH, help='ping message length in bytes')
        self.parser.add_argument('-t', dest='count', action='store_const', const=PROTOCOLS.ICMP.INFINITY, help='ping infinitely')
        self.parser.add_argument('-f', dest='dont_fragment', action='store_true', help='Dont Fragment')

    def _get_process_arguments(self, parsed_args: argparse.Namespace) -> List[Any]:
        """"""
        return [parsed_args.destination]

    def _get_process_keyword_arguments(self, parsed_args: argparse.Namespace) -> Dict[str, Any]:
        """"""
        return {'count': parsed_args.count, 'length': parsed_args.length, 'dont_fragment': parsed_args.dont_fragment}
