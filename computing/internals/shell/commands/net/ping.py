from address.ip_address import IPAddress
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

        self.parser.add_argument('ip', type=str, help='the destination ip')
        self.parser.add_argument('-n', type=int, dest='count', default=3, help='ping count')
        self.parser.add_argument('-t', dest='count', action='store_const', const=PROTOCOLS.ICMP.INFINITY,
                                 help='ping infinitely')

    def action(self, parsed_args):
        """
        prints out the arguments.
        """
        if not IPAddress.is_valid(parsed_args.ip):
            return CommandOutput('', "IP address is not valid!")

        self.computer.start_ping_process(IPAddress(parsed_args.ip), count=parsed_args.count)
        return CommandOutput('', '')
