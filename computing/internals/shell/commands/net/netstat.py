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
        string = f"{'PORT': >6}{'STATE': >10}{'TYPE': >10}\n"
        string += '\n'.join([f"{port: >6}   LISTENING  STREAM" for port in self.computer.open_tcp_ports])
        string += ''.join([f"\n{port: >6}   LISTENING  DGRAM" for port in self.computer.open_udp_ports])
        return string

    def action(self, parsed_args):
        """
        prints out the arguments.
        """
        return CommandOutput(self.to_print(parsed_args), '')
