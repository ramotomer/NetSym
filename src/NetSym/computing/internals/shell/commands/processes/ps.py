from __future__ import annotations

from typing import TYPE_CHECKING

from NetSym.computing.internals.shell.commands.command import Command, CommandOutput
from NetSym.consts import COMPUTER

if TYPE_CHECKING:
    import argparse
    from NetSym.computing.internals.processes.abstracts.process import Process
    from NetSym.computing.internals.shell.shell import Shell
    from NetSym.computing.computer import Computer


class Ps(Command):
    """
    Prints out all of the computer's processes.
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        """
        initiates the command.
        :param computer:
        """
        super(Ps, self).__init__('ps', 'print out processes', computer, shell)
        self.parser.add_argument('-f', action='store_true')
        self.parser.add_argument('-a', action='store_true')
        self.parser.add_argument('-d', action='store_true')
        self.parser.add_argument('-e', action='store_true')

        self.parser.add_argument('--kernelmode', dest='show_kernelmode_processes', action='store_true',
                                 help='show the internal processes running inside the kernel... interesting :)')

    @staticmethod
    def _process_info(process: Process) -> str:
        """
        return an info line string about a process.
        :param process:
        :return:
        """
        return f"{process.pid: >3}\t{repr(process)}\n"

    def _list_processes(self, process_mode: str = COMPUTER.PROCESSES.MODES.USERMODE) -> CommandOutput:
        """
        lists out the processes.
        :return:
        """
        string = f"PID\tNAME\n  1\tinit\n"

        if process_mode != COMPUTER.PROCESSES.MODES.USERMODE:
            string = f"\n---------- SHOWING {process_mode.upper()} PROCESSES ---------- \n\n" + string

        for process in sorted(self.computer.process_scheduler.get_all_processes(process_mode), key=lambda wp: wp.pid):
            string += self._process_info(process)
        return CommandOutput(string, '')

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        Prints out all of the computer's processes.
        """
        if parsed_args.show_kernelmode_processes:
            return self._list_processes(COMPUTER.PROCESSES.MODES.KERNELMODE)
        return self._list_processes()
