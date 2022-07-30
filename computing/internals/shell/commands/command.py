import argparse
from abc import ABCMeta, abstractmethod
from collections import namedtuple

from usefuls.funcs import split_with_escaping
from usefuls.print_stealer import PrintStealer

CommandOutput = namedtuple("CommandOutput", [
    "stdout",
    "stderr",
])

ParsedCommand = namedtuple("ParsedCommand", [
    "command_class",
    "parsed_args",
])

SyntaxArgumentMessage = str


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
        self.description = description

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
        args = [arg.strip('"') for arg in split_with_escaping(string)[1:]]

        stdout_stealer = PrintStealer()
        with stdout_stealer:
            try:
                parsed_args = self.parser.parse_args(args)
                return ParsedCommand(self, parsed_args)
            except SystemExit:
                pass
        return SyntaxArgumentMessage(stdout_stealer.printed)
