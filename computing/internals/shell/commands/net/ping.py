from computing.internals.shell.commands.command import Command, CommandOutput
from consts import PROTOCOLS


class Ping(Command):
    """
    Send a ping to another computer.
    """
    def __init__(self, computer, shell):
        """
        initiates the command.
        :param computer:
        """
        super(Ping, self).__init__('ping', 'ping a computer', computer, shell)

        self.parser.add_argument('destination', type=str, help='the destination hostname or IP address')
        self.parser.add_argument('-n', type=int, dest='count', default=3, help='ping count')
        self.parser.add_argument('-t', dest='count', action='store_const', const=PROTOCOLS.ICMP.INFINITY,
                                 help='ping infinitely')

    def action(self, parsed_args):
        """
        prints out the arguments.
        """
        self.computer.start_ping_process(parsed_args.destination, count=parsed_args.count)
        return CommandOutput('', '')
