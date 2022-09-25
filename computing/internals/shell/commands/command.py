from __future__ import annotations

import argparse
from abc import ABCMeta, abstractmethod
from typing import Union, NamedTuple, TYPE_CHECKING

from usefuls.funcs import split_with_escaping
from usefuls.print_stealer import PrintStealer

if TYPE_CHECKING:
    from computing.computer import Computer
    from computing.internals.shell.shell import Shell


class CommandOutput(NamedTuple):
    stdout: str
    stderr: str


class ParsedCommand(NamedTuple):
    command_class: Command
    parsed_args:   argparse.Namespace


SyntaxArgumentMessage = str


class Command(metaclass=ABCMeta):
    """
    A command in the shell
    """
    def __init__(self,
                 name: str,
                 description: str,
                 computer: Computer,
                 shell: Shell) -> None:
        """
        Initiates the command with the computer that ran it.
        :param computer: `Computer`
        """
        self.name: str = name
        self.description: str = description
        self.computer: Computer = computer
        self.shell: Shell = shell

        self.parser = argparse.ArgumentParser(prog=name, description=description)

    @abstractmethod
    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        The action that this command activates when called.
        """

    def parse(self, string: str) -> Union[ParsedCommand, SyntaxArgumentMessage]:
        """
        parses the command string!!!
        """
        args = [arg.strip('"') for arg in split_with_escaping(string)[1:]]

        stdout_stealer = PrintStealer()
        with stdout_stealer:
            try:
                parsed_args = self.parser.parse_args(args)
                return ParsedCommand(self, parsed_args)
            except SystemExit:
                pass
        return SyntaxArgumentMessage(stdout_stealer.printed)
