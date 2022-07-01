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
                self.computer.stop_sniffing()
            else:
                self.computer.start_sniffing()

        else:
            name = parsed_args.interface
            if not name:
                name = self.computer.interfaces[0].name

            if not any(interface.name == name for interface in self.computer.all_interfaces):
                return CommandOutput("", f"Interface {name} does not exist!")

            if parsed_args.stop:
                self.computer.stop_sniffing()
            else:
                self.computer.start_sniffing(name, is_promisc=parsed_args.is_promisc)
            # TODO: this does not work yet that well!!!

        return CommandOutput('', '')
