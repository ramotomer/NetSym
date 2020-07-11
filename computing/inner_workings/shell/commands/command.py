import argparse
from abc import ABCMeta, abstractmethod
from collections import namedtuple

CommandOutput = namedtuple("CommandOutput", [
    "stdout",
    "stderr",
])

ParsedCommand = namedtuple("ParsedCommand", [
    "command_class",
    "parsed_args",
])


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

    @abstractmethod
    def parse(self, string):
        """
        Parse yourself the string that might be your command, That way, an argparse will be defined differently for each
        command class.
        :param string:
        :return:
        """
