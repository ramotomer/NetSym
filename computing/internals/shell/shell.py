import os

from computing.internals.shell.commands.alias import Alias
from computing.internals.shell.commands.command import SyntaxArgumentMessage, CommandOutput
from computing.internals.shell.commands.echo import Echo
from computing.internals.shell.commands.filesystem.cat import Cat
from computing.internals.shell.commands.filesystem.cd import Cd
from computing.internals.shell.commands.filesystem.cp import Cp
from computing.internals.shell.commands.filesystem.ls import Ls
from computing.internals.shell.commands.filesystem.mkdir import Mkdir
from computing.internals.shell.commands.filesystem.mv import Mv
from computing.internals.shell.commands.filesystem.pwd import Pwd
from computing.internals.shell.commands.filesystem.rm import Rm
from computing.internals.shell.commands.filesystem.touch import Touch
from computing.internals.shell.commands.grep import Grep
from computing.internals.shell.commands.hostname import Hostname
from computing.internals.shell.commands.kill import Kill
from computing.internals.shell.commands.net.arp import Arp
from computing.internals.shell.commands.net.ip import Ip
from computing.internals.shell.commands.net.ip_address import IpAddressCommand
from computing.internals.shell.commands.net.ip_route import IpRouteCommand
from computing.internals.shell.commands.net.netstat import Netstat
from computing.internals.shell.commands.net.ping import Ping
from computing.internals.shell.commands.net.tcpdump import Tcpdump
from computing.internals.shell.commands.ps import Ps
from computing.internals.shell.commands.unalias import Unalias
from computing.internals.shell.commands.uname import Uname
from consts import CONSOLE, FILESYSTEM, debugp
from usefuls import called_in_order, all_indexes


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

        self.commands = [Echo, Ls, Cd, Pwd, Touch, Cat, Mkdir, Rm, Uname, Grep,
                         Ip, Arp, Ps, Ping, Tcpdump, Kill, Hostname, Netstat, Cp, Mv, Alias, Unalias]
        self.commands = [command(computer, self) for command in self.commands]

        self.parser_commands = {
            'clear': self.shell_graphics.clear_screen,
            'cls': self.shell_graphics.clear_screen,
            'exit': self.shell_graphics.exit,
            'history': self.write_history,
            'shutdown': called_in_order(self.shell_graphics.exit,
                                        self.computer.power),
            'reboot': called_in_order(self.shell_graphics.exit,
                                      self.computer.power,
                                      self.computer.power),
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

        self.aliases = {}

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

    @staticmethod
    def _contains_piping(string):
        """
        checks if the string does
        :param string:
        :return:
        """
        return CONSOLE.SHELL.PIPING_CHAR in string

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

    @staticmethod
    def _split_by_command_enders_outside_of_quotes(string):
        """"""
        indexes = [index for index in all_indexes(string, ';')
                   if string[:index].count("\'") % 2 == 0 and string[:index].count('\"') % 2 == 0]
        indexes = [-1] + indexes + [len(string)]

        returned = []
        for i in range(len(indexes) - 1):
            returned.append(string[indexes[i] + 1: indexes[i + 1]].strip())

        return returned

    @classmethod
    def _does_string_require_split_by_command_enders(cls, string):
        """
        Returns that
        :param string:
        :return:
        """
        return (CONSOLE.SHELL.END_COMMAND in string) and \
               (len(cls._split_by_command_enders_outside_of_quotes(string)) != 1)

    def execute(self, string):
        """
        Receives the string of a command and returns the command and its arguments.
        :param string:
        :return:
        """
        debugp(f"executing {string}")
        if not string:
            return

        self.history.append(string)
        self.history_index = None

        string = string.split(CONSOLE.SHELL.COMMENT_SIGN)[0]

        if self._does_string_require_split_by_command_enders(string):
            for inline_command in self._split_by_command_enders_outside_of_quotes(string):  # split by ;-s
                self.execute(inline_command)
            return

        command = string.split()[0]
        args = ' '.join(string.split()[1:])

        if command in self.aliases:
            if self.aliases[command] not in self.aliases:
                self.execute(self.aliases[command] + f" {args}")
            else:
                self.shell_graphics.write("Cannot use alias of an alias! :(")

        elif command in self.string_to_command:
            self.execute_regular_command(string)

        elif command in self.parser_commands:
            self.parser_commands[command]()

        else:
            self.shell_graphics.write(self._unknown_command(command))

    def execute_regular_command(self, full_string):
        """
        operates the command, writes to file, does piping (in the future, and more!)
        :param full_string:
        :return:
        """
        output_filename, is_appending = None, False
        if self._contains_redirections(full_string):
            full_string, output_filename, is_appending = self._handle_redirections(full_string)

        commands = [full_string]
        if self._contains_piping(full_string):
            commands = self._handle_piping(full_string)

        for command in commands[:-1]:
            self.write_output(self.output_of_command(command), filename=FILESYSTEM.PIPING_FILE)
        self.write_output(self.output_of_command(commands[-1]), filename=output_filename, append=is_appending)

    def output_of_command(self, string):
        """
        Receive a string command, return its output. (parses and runs it...)
        :param string:
        :return:
        """
        parsed_command = self.string_to_command[string.split()[0]].parse(string)
        if isinstance(parsed_command, SyntaxArgumentMessage):
            self.shell_graphics.write(parsed_command)
            return CommandOutput('', '')
        return parsed_command.command_class.action(parsed_command.parsed_args)

    @staticmethod
    def _handle_piping(string):
        """
        Runs all of the commands except the last one, returns it.
        :param string:
        :return:
        """
        splitted = string.split(CONSOLE.SHELL.PIPING_CHAR)
        return splitted[:1] + list(map(lambda s: f"{s} {FILESYSTEM.PIPING_FILE}", splitted[1:]))
