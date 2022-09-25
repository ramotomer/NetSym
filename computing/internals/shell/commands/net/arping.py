from address.ip_address import IPAddress
from computing.internals.processes.kernelmode_processes.arp_process import ARPProcess
from computing.internals.shell.commands.command import Command, CommandOutput
from consts import PROTOCOLS


class Arping(Command):
    """
    Command that prints out the arp cache
    """
    def __init__(self, computer, shell):
        """
        initiates the command.
        :param computer:
        """
        super(Arping, self).__init__('arping', 'send an arp request to a given host', computer, shell)

        self.parser.add_argument('ip', type=str, help='the destination ip')
        self.parser.add_argument('-n', type=int, dest='count', default=1, help='arping count')
        self.parser.add_argument('-t', dest='count', action='store_const', const=PROTOCOLS.ICMP.INFINITY,
                                 help='arping infinitely')

    def action(self, parsed_args):
        """
        performs the action of the command
        """
        if not IPAddress.is_valid(parsed_args.ip):
            return CommandOutput('', "IP address is not valid!")

        self.computer.process_scheduler.start_usermode_process(
            ARPProcess,
            IPAddress(parsed_args.ip),
            send_even_if_known=True,
            resend_count=parsed_args.count,
            resend_even_on_success=True,
        )
        return CommandOutput('arpinging...', '')
