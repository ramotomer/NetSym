from __future__ import annotations

from typing import TYPE_CHECKING

from NetSym.computing.internals.processes.usermode_processes.echo_server_process.echo_server_process import EchoServerProcess
from NetSym.computing.internals.shell.commands.command import Command, CommandOutput

if TYPE_CHECKING:
    import argparse
    from NetSym.computing.computer import Computer
    from NetSym.computing.internals.shell.shell import Shell


class Echos(Command):
    """
    The command that runs the echosd process acting as an echo server

        echo server
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        """
        initiates the command.
        :param computer:
        """
        super(Echos, self).__init__('echos', 'start acting as an echo server and listening to echo clients', computer, shell)

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        start the `echosd` process
        """
        self.computer.process_scheduler.start_usermode_process(
            EchoServerProcess,
        )
        return CommandOutput('running echo server...', '')
