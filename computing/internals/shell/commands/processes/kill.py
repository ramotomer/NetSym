from __future__ import annotations

from typing import TYPE_CHECKING

from computing.internals.shell.commands.command import Command, CommandOutput
from consts import COMPUTER
from exceptions import NoSuchProcessError

if TYPE_CHECKING:
    import argparse
    from computing.computer import Computer
    from computing.internals.shell.shell import Shell


class Kill(Command):
    """
    The command that prints the arguments that it receives.
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        """
        initiates the command.
        :param computer:
        """
        super(Kill, self).__init__('kill', 'send a signal to a process', computer, shell)

        self.parser.add_argument('-9', dest='force', action='store_true', help='kill harder!')
        self.parser.add_argument('PID', type=int, help='the Process ID of the process to kill')

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        prints out the arguments.
        """
        if parsed_args.PID == COMPUTER.PROCESSES.INIT_PID:
            return CommandOutput('', "Cannot kill init!")

        # TODO: learn how to make it so a custom signal can be sent using this command not just to kill
        try:
            self.computer.process_scheduler.kill_usermode_process(parsed_args.PID, force=parsed_args.force)
        except NoSuchProcessError:
            return CommandOutput('', "There is no such process!!!")

        return CommandOutput("Signal sent successfully! :)", '')
