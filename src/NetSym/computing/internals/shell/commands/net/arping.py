from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

from computing.internals.processes.kernelmode_processes.arp_process import ARPProcess
from computing.internals.shell.commands.command import Command, CommandOutput
from consts import PROTOCOLS

if TYPE_CHECKING:
    from computing.internals.shell.shell import Shell
    from computing.computer import Computer


class Arping(Command):
    """
    Command that prints out the arp cache
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        """
        initiates the command.
        :param computer:
        """
        super(Arping, self).__init__('arping', 'send an arp request to a given host', computer, shell)

        self.parser.add_argument('destination', type=str, help='the destination hostname or IP address')
        self.parser.add_argument('-n', type=int, dest='count', default=1, help='arping count')
        self.parser.add_argument('-t', dest='count', action='store_const', const=PROTOCOLS.ICMP.INFINITY,
                                 help='arping infinitely')

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        performs the action of the command
        """
        self.computer.process_scheduler.start_usermode_process(
            ARPProcess,
            parsed_args.destination,
            send_even_if_known=True,
            resend_count=parsed_args.count,
            resend_even_on_success=True,
            override_process_name="arping",
        )
        return CommandOutput('arpinging...', '')
