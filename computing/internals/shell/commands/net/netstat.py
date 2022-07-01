from computing.internals.shell.commands.command import Command, CommandOutput


class Netstat(Command):
    """
    Prints the state of network ports and connection that are currently active.
    """
    def __init__(self, computer, shell):
        """
        initiates the command.
        :param computer:
        """
        super(Netstat, self).__init__('netstat', 'list network usage', computer, shell)

        self.parser.add_argument('-n', action='store_true')
        self.parser.add_argument('-o', action='store_true', dest='timers', help='display timers')
        self.parser.add_argument('-a', '--all', action='store_true', dest='all_sockets',
                                 help='display all socket (even disconnected)')

    def to_print(self, parsed_args):
        """
        The string to print
        :param parsed_args:
        :return:
        """
        headers = f"{'Proto': <7}{'Local Address': <23}{'Foreign Address': <23}{'State': <16}PID\n"
        return headers + '\n'.join(repr(socket) for socket in self.computer.sockets)

    def action(self, parsed_args):
        """
        prints out the arguments.
        """
        return CommandOutput(self.to_print(parsed_args), '')
