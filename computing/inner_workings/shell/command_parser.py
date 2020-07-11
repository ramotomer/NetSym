import os

from computing.inner_workings.shell.commands.echo import Echo


class CommandParser:
    """
    Receives a command string in the CLI and translates it into a command and arguments for the computer
    to run.
    """
    def __init__(self, computer, shell_graphics):
        """
        Initiates the `CommandParser` with the computer that it is related to.
        :param computer:
        """
        self.computer = computer
        self.shell = shell_graphics

        self.commands = {
            Echo(computer),
        }

        self.string_to_command = {command.name: command for command in self.commands}

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
            parsed_command = self.string_to_command[command].parse(string)
            output = parsed_command.command_class.action(parsed_command.parsed_args)

            self.shell.write(f"{output.stdout}{os.linesep if (output.stdout and output.stderr) else ''}{output.stderr}")
        else:
            self.shell.write(self._unknown_command(command))
