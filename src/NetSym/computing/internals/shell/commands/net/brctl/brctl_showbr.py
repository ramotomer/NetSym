from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

from computing.internals.processes.kernelmode_processes.switching_process import SwitchingProcess
from computing.internals.processes.usermode_processes.stp_process import STPProcess
from computing.internals.shell.commands.command import Command, CommandOutput
from consts import COMPUTER
from gui.main_loop import MainLoop

if TYPE_CHECKING:
    from computing.computer import Computer
    from computing.internals.shell.shell import Shell


class BrctlShowbrCommand(Command):
    """
    The Command supplies information about a switch
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        """
        initiates the command.
        """
        super(BrctlShowbrCommand, self).__init__('brctl_showbr', 'display information about the bridge and its interfaces', computer, shell)

        self.parser.add_argument('bridge', metavar='bridge', type=str, nargs='?', default=None, help='the name of the desired bridge')

    def _to_print(self) -> str:
        """
        Return the string that needs to be printed when the command is run
        Extracts all of the information from the currently running stp process
        """
        stp_process = self.computer.process_scheduler.get_usermode_process_by_type(STPProcess)
        general_bridge_info = f"""
bridge:
    {'bridge id': <23}{str(stp_process.my_bid): >23}
    {'designated root id': <23}{str(stp_process.root_bid): >23}
    {'time since seen root': <23}{int(MainLoop.instance.time_since(stp_process.root_declaration_time)): >23}
    {'max root timeout': <23}{stp_process.root_timeout: >23.2}
    {'root age': <23}{stp_process.root_age: >23}
"""
        interfaces_info = []
        for id_, (port, stp_port) in enumerate(stp_process.stp_ports.items()):
            interfaces_info.append(
                f"""
{port.name} ({id_ + 1})
    {'port id': <23}{id_ + 1: >23}
    {'state': <23}{stp_port.state: >23}
    {'path cost': <23}{float(stp_port.distance_to_root): >23.2}
    {'time since last packet': <23}{MainLoop.instance.time_since(stp_port.last_time_got_packet): >23.2}
""")

        return general_bridge_info + '\n' + '\n'.join(interfaces_info)

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        Get information about the switch - especially about the STP root and ports
        """
        if parsed_args.bridge is not None:
            return CommandOutput('', 'Do not supply a bridge! Linux bridges are not yet implemented')

        if not self.computer.process_scheduler.is_process_running_by_type(SwitchingProcess, COMPUTER.PROCESSES.MODES.KERNELMODE) or \
           not self.computer.process_scheduler.is_usermode_process_running_by_type(STPProcess):
            return CommandOutput('', 'Computer is not an STP switch!!! No bridge data')

        return CommandOutput(self._to_print(), '')
