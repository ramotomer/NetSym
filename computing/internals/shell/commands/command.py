import argparse
from abc import ABCMeta, abstractmethod
from collections import namedtuple

from usefuls import PrintStealer

CommandOutput = namedtuple("CommandOutput", [
    "stdout",
    "stderr",
])

ParsedCommand = namedtuple("ParsedCommand", [
    "command_class",
    "parsed_args",
])

SyntaxArgumentError = str


class Command(metaclass=ABCMeta):
    """
    A command in the shell
    """
    def __init__(self, name, description, computer, shell):
        """
        Initiates the command with the computer that ran it.
        :param computer: `Computer`
        """
        self.computer = computer
        self.name = name
        self.shell = shell
        self.parser = argparse.ArgumentParser(prog=name, description=description)

    @abstractmethod
    def action(self, parsed_args) -> CommandOutput:
        """
        The action that this command activates when called.
        """

    def parse(self, string):
        """
        parses the command string!!!
        :param string:
        :return:
        """
        args = string.split()[1:]

        stdout_stealer = PrintStealer()
        with stdout_stealer:
            try:
                parsed_args = self.parser.parse_args(args)
                return ParsedCommand(self, parsed_args)
            except SystemExit:
                pass
        return SyntaxArgumentError(stdout_stealer.printed)
