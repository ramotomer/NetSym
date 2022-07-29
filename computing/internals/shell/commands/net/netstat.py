from computing.internals.shell.commands.command import Command, CommandOutput
from consts import COMPUTER


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
        headers = f"{'Proto': <{   COMPUTER.SOCKETS.REPR.PROTO_SPACE_COUNT}} " \
            f"{'Local Address': <{ COMPUTER.SOCKETS.REPR.LOCAL_ADDRESS_SPACE_COUNT}} " \
            f"{'Remote Address': <{COMPUTER.SOCKETS.REPR.REMOTE_ADDRESS_SPACE_COUNT}} " \
            f"{'State': <{         COMPUTER.SOCKETS.REPR.STATE_SPACE_COUNT}} " \
            f"PID\n"
        return headers + '\n'.join(getattr(socket, 'get_str_representation', socket.__repr__)() for socket in self.computer.sockets)

    def action(self, parsed_args):
        """
        prints out the arguments.
        """
        return CommandOutput(self.to_print(parsed_args), '')
