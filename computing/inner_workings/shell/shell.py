import os

from computing.inner_workings.shell.commands.echo import Echo
from computing.inner_workings.shell.commands.ls import Ls
from exceptions import WrongArgumentsError


class Shell:
    """
    Receives a command string in the CLI and translates it into a command and arguments for the computer
    to run.
    """
    def __init__(self, computer, shell_graphics):
        """
        Initiates the `Shell` with the computer that it is related to.
        :param computer:
        """
        self.computer = computer
        self.shell_graphics = shell_graphics

        self.commands = [
            Echo(computer, self),
            Ls(computer, self),
        ]
        self.string_to_command = {command.name: command for command in self.commands}

        self.cwd = self.computer.filesystem.root_path

    @staticmethod
    def _unknown_command(command):
        """
        Returns a string that says that.
        :param command:
        :return:
        """
        return f"Unknown command {command}"

    def execute(self, string):
        """
        Receives the string of a command and returns the command and its arguments.
        :param string:
        :return:
        """
        command = string.split()[0]
        if command in self.string_to_command:
            try:
                parsed_command = self.string_to_command[command].parse(string)
            except WrongArgumentsError:
                self.shell_graphics.write("Wrong usage of command!")
                return

            output = parsed_command.command_class.action(parsed_command.parsed_args)

            self.shell_graphics.write(
                f"{output.stdout}{os.linesep if (output.stdout and output.stderr) else ''}{output.stderr}"
            )
        else:
            self.shell_graphics.write(self._unknown_command(command))
