from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

from computing.internals.processes.usermode_processes.traceroute_process import TraceRouteProcess
from computing.internals.shell.commands.process_creating_command import ProcessCreatingCommand

if TYPE_CHECKING:
    from computing.internals.shell.shell import Shell
    from computing.computer import Computer


class Tracert(ProcessCreatingCommand):
    """
    A command that returns the path a single packet would take on its way to your destination
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        super(Tracert, self).__init__('tracert',
                                      'returns the path a single packet would take on its way to your destination',
                                      computer,
                                      shell,
                                      TraceRouteProcess)

        self.parser.add_argument('destination', type=str, help='The destination hostname or IP address')

    def _get_process_arguments(self, parsed_args: argparse.Namespace):
        return [parsed_args.destination]
