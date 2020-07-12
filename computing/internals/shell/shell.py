import os

from computing.internals.shell.commands.echo import Echo
from computing.internals.shell.commands.filesystem.cat import Cat
from computing.internals.shell.commands.filesystem.cd import Cd
from computing.internals.shell.commands.filesystem.ls import Ls
from computing.internals.shell.commands.filesystem.mkdir import Mkdir
from computing.internals.shell.commands.filesystem.pwd import Pwd
from computing.internals.shell.commands.filesystem.rm import Rm
from computing.internals.shell.commands.filesystem.touch import Touch
from computing.internals.shell.commands.net.arp import Arp
from computing.internals.shell.commands.net.ip import Ip
from computing.internals.shell.commands.net.ip_address import IpAddressCommand
from computing.internals.shell.commands.net.ip_route import IpRouteCommand
from computing.internals.shell.commands.uname import Uname
from consts import CONSOLE


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
            Cd(computer, self),
            Pwd(computer, self),
            Touch(computer, self),
            Cat(computer, self),
            Mkdir(computer, self),
            Rm(computer, self),
            Uname(computer, self),
            Ip(computer, self),
            Arp(computer, self),
        ]
        self.parser_commands = {
            'clear': self.shell_graphics.clear_screen,
            'cls': self.shell_graphics.clear_screen,
            'exit': self.shell_graphics.exit,
            'history': self.write_history,
        }
        self.string_to_command = {command.name: command for command in self.commands}
        command_translations = {
            "dir": self.commands[1],
            "type": self.commands[5],
            "ifconfig": IpAddressCommand(computer, self),
            "ipconfig": IpAddressCommand(computer, self),
            "route": IpRouteCommand(computer, self),
        }

        for extra_command, translation in command_translations.items():
            self.string_to_command[extra_command] = translation

        self.cwd = self.computer.filesystem.root

        self.history = []

        self.history_index = None

        # TODO: add piping, and the commands: ps, grep, ping, tcpdump, arping
        # TODO: add some good flags like rm -r, ls -la

    @property
    def cwd_path(self):
        return self.cwd.full_path

    @staticmethod
    def _unknown_command(command):
        """
        Returns a string that says that.
        :param command:
        :return:
        """
        return f"Unknown command {command}"

    def write_output(self, command_output, filename=None, append=False):
        """
        Writes out nicely the output that is given.
        :param command_output: `CommandOutput`
        :param filename: a file to output the output to, if None, stdout
        :param append: whether or not to override the content of the file already.
        :return:
        """
        output_string = f"{command_output.stdout}" \
                        f"{os.linesep if (command_output.stdout and command_output.stderr) else ''}" \
                        f"{command_output.stderr}"

        if filename is not None:
            self.computer.filesystem.output_to_file(f"{output_string}\n", filename, self.cwd, append=append)
        else:
            self.shell_graphics.write(output_string)

    def write_history(self):
        """
        Writes out the history
        :return:
        """
        self.shell_graphics.write('\n'.join(self.history))

    @staticmethod
    def _contains_redirections(string):
        """
        Returns whether or not a command contains redirections (> or >>)
        :param string:
        :return:
        """
        return string.count(CONSOLE.SHELL.REDIRECTION) in {1, 2}

    @staticmethod
    def _handle_redirections(string):
        """
        :param string:
        :return: (filename, is_appending)
        """
        is_appending = ((2 * CONSOLE.SHELL.REDIRECTION) in string)
        splitted = string.split(CONSOLE.SHELL.REDIRECTION)
        splitted = [s for s in splitted if s]
        splitted = list(map(lambda s: s.strip(), splitted))
        new_string_command, filename = splitted
        return new_string_command, filename, is_appending

    def scroll_up_history(self):
        """
        allows to go up and down the history of commands
        :return:
        """
        if self.history_index is None:
            self.history_index = 0
        else:
            self.history_index = min(self.history_index + 1, len(self.history) - 1)

        self.shell_graphics.clear_line()
        self.shell_graphics.write_to_line(self.history[::-1][self.history_index])

    def scroll_down_history(self):
        """
        allows to go up and down the history of commands
        :return:
        """
        if self.history_index is None:
            return
        self.history_index = max(self.history_index - 1, -1)

        self.shell_graphics.clear_line()
        self.shell_graphics.write_to_line(([''] + self.history[::-1])[self.history_index + 1])

    def execute(self, string):
        """
        Receives the string of a command and returns the command and its arguments.
        :param string:
        :return:
        """
        if not string:
            return
        self.history.append(string)
        self.history_index = None
        command = string.split()[0]

        if command in self.string_to_command:
            self.execute_regular_command(command, string)

        elif command in self.parser_commands:
            self.parser_commands[command]()

        else:
            self.shell_graphics.write(self._unknown_command(command))

    def execute_regular_command(self, command, string):
        """
        operates the command, writes to file, does piping (in the future, and more!)
        :param command:
        :param string:
        :return:
        """
        filename, is_appending = None, False
        if self._contains_redirections(string):
            string, filename, is_appending = self._handle_redirections(string)

        parsed_command = self.string_to_command[command].parse(string)
        output = parsed_command.command_class.action(parsed_command.parsed_args)

        self.write_output(output, filename=filename, append=is_appending)
