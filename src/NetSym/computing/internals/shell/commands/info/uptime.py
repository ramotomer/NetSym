from __future__ import annotations

from datetime import timedelta, datetime
from typing import TYPE_CHECKING

from computing.internals.shell.commands.command import Command, CommandOutput
from consts import T_Time
from gui.main_loop import MainLoop

if TYPE_CHECKING:
    import argparse
    from computing.computer import Computer
    from computing.internals.shell.shell import Shell


class Uptime(Command):
    """
    Prints the computers name
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        """
        initiates the command.
        :param computer:
        """
        super(Uptime, self).__init__('uptime', 'print the amount of time that passed since the computer was turned on', computer, shell)

    @staticmethod
    def _to_print(uptime: T_Time) -> str:
        """
        Parses the seconds as months,days,hours,minutes and seconds
        Constructs a string that represents that data and returns it

        :return: `str` output to the screen
        """
        uptime_date = datetime(1, 1, 1) + timedelta(seconds=uptime)
        n = '\n'
        return f"UPTIME: \n" \
               f"{f'YEARS:   {uptime_date.year  - 1}{n}' if uptime_date.year  - 1 != 0 else ''}" \
               f"{f'MONTHS:  {uptime_date.month - 1}{n}' if uptime_date.month - 1 != 0 else ''}" \
               f"{f'DAYS:    {uptime_date.day   - 1}{n}' if uptime_date.day   - 1 != 0 else ''}" \
               f"{f'HOURS:   {uptime_date.hour}     {n}' if uptime_date.hour      != 0 else ''}" \
               f"{f'MINUTES: {uptime_date.minute}   {n}' if uptime_date.minute    != 0 else ''}" \
               f"{f'SECONDS: {uptime_date.second}   {n}' if uptime_date.second    != 0 else ''}"

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        prints out the arguments.
        """
        if self.computer.boot_time is None:
            return CommandOutput('', 'Computer is turned off! How did you even run this command??? should be impossible... Something went wrong')
        return CommandOutput(self._to_print(MainLoop.instance.time_since(self.computer.boot_time)), '')
