from __future__ import annotations

from typing import TYPE_CHECKING

from computing.internals.processes.usermode_processes.echo_server_process.echo_client_process import EchoClientProcess
from computing.internals.shell.commands.command import Command, CommandOutput
from consts import PORTS, PROTOCOLS

if TYPE_CHECKING:
    import argparse
    from computing.computer import Computer
    from computing.internals.shell.shell import Shell


class Echoc(Command):
    """
    The command that runs the echocd process - sending data to an echo server

        echo client
    """

    def __init__(self, computer: Computer, shell: Shell) -> None:
        """
        initiates the command.
        :param computer:
        """
        super(Echoc, self).__init__('echoc', 'send a string to an echo server', computer, shell)

        self.parser.add_argument('destination', type=str, help='the echo server ip address or hostname')
        self.parser.add_argument('data', type=str, nargs='*', help='the data to send to the server')

        self.parser.add_argument('-p', type=int, dest='port', default=PORTS.ECHO_SERVER, help=f'the server UDP port (default: {PORTS.ECHO_SERVER})')
        self.parser.add_argument('-c', type=int, dest='count', default=PROTOCOLS.ECHO_SERVER.DEFAULT_REQUEST_COUNT,
                                 help=f'the amount of requests to send (default: {PROTOCOLS.ECHO_SERVER.DEFAULT_REQUEST_COUNT})')

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        start the `echocd` process
        """
        self.computer.process_scheduler.start_usermode_process(
            EchoClientProcess,
            (parsed_args.destination, parsed_args.port),
            ' '.join(parsed_args.data),
            parsed_args.count,
        )
        return CommandOutput('', '')
