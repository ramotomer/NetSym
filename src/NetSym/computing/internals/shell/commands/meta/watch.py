from __future__ import annotations

from typing import TYPE_CHECKING

from NetSym.computing.internals.processes.usermode_processes.watching_process import WatchingProcess
from NetSym.computing.internals.shell.commands.command import Command, CommandOutput

if TYPE_CHECKING:
    import argparse
    from NetSym.computing.computer import Computer
    from NetSym.computing.internals.shell.shell import Shell


class Watch(Command):
    """
    Runs a command every set amount of time and prints the output
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        """
        Initiate the `watch` command
        """
        super(Watch, self).__init__('watch', 'run a command periodically and print the output', computer, shell)

        self.parser.add_argument('-n', dest='interval', type=float, default=1, help='How often to run the command')
        self.parser.add_argument('command', metavar='command', type=str, nargs='*', help='the command to run')

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        Run the actual command
            Starts a `WatchingProcess` that runs the supplied command every `interval` seconds :)
        """
        command_string = ' '.join(parsed_args.command)
        self.computer.process_scheduler.start_usermode_process(WatchingProcess, self.shell, command_string, parsed_args.interval)
        return CommandOutput(f'Watching: {command_string}', '')
