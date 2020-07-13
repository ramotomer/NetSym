from computing.internals.shell.commands.command import Command, CommandOutput


class Tcpdump(Command):
    """
    The command that prints the arguments that it receives.
    """
    def __init__(self, computer, shell):
        """
        initiates the command.
        :param computer:
        """
        super(Tcpdump, self).__init__('tcpdump', 'sniff', computer, shell)

        self.parser.add_argument('-i', '--interface', dest='interface', type=str, help='interface to sniff on')
        self.parser.add_argument('-A', '--Any', dest='any_interface', action='store_true', help='sniff on all NICs')
        self.parser.add_argument('-p', '--promisc', dest='is_promisc', action='store_true', help='is promisc')
        self.parser.add_argument('-S', '--Stop', dest='stop', action='store_true', help='stop sniffing')

    def action(self, parsed_args):
        """
        start sniffing or stop sniffing.
        """
        if parsed_args.any_interface:
            if parsed_args.is_promisc:
                return CommandOutput('', "Cannot sniff on promisc on all interfaces!")
            if parsed_args.stop:
                self.computer.stop_sniff()
            else:
                self.computer.start_sniff()

        else:
            name = parsed_args.interface
            if not name:
                name = self.computer.interfaces[0]
            if parsed_args.stop:
                self.computer.stop_sniff(name)
            else:
                self.computer.start_sniff(name, is_promisc=parsed_args.is_promisc)

        return CommandOutput('', '')
