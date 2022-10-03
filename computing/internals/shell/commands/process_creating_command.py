from __future__ import annotations

import argparse
from abc import ABCMeta
from typing import Type, Iterable, Any, Dict, TYPE_CHECKING

from computing.internals.processes.abstracts.process import Process
from computing.internals.shell.commands.command import Command, CommandOutput

if TYPE_CHECKING:
    from computing.computer import Computer
    from computing.internals.shell.shell import Shell


class ProcessCreatingCommand(Command, metaclass=ABCMeta):
    """
    This is an easier way to write commands that all they do is run a single process :)
    """
    def __init__(self, name: str, description: str, computer: Computer, shell: Shell, process_type: Type[Process]) -> None:
        """
        Initiates the command with the class of the process to run
        :param process_type: The class of a process to start
        """
        super(ProcessCreatingCommand, self).__init__(name, description, computer, shell)
        self.process_type = process_type

    def _get_process_arguments(self, parsed_args: argparse.Namespace) -> Iterable[Any]:
        """
        Returns the arguments that will be given to the process when it is run
        """
        return []

    def _get_process_keyword_arguments(self, parsed_args: argparse.Namespace) -> Dict[str, Any]:
        """
        Returns the keyword arguments that will be given to the process when it is run
        """
        return {}

    def _get_command_output(self) -> CommandOutput:
        return CommandOutput('', '')

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        Runs the process
        """
        self.computer.process_scheduler.start_usermode_process(
            self.process_type,
            *self._get_process_arguments(parsed_args),
            **self._get_process_keyword_arguments(parsed_args),
        )
        return self._get_command_output()
