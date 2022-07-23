from computing.internals.shell.commands.command import Command, CommandOutput
from consts import INTERFACES


class Tcpdump(Command):
    """
    The command that starts and stops sniffing on an interface
    """
    def __init__(self, computer, shell):
        """
        initiates the command.
        :param computer:
        """
        super(Tcpdump, self).__init__('tcpdump', 'sniff', computer, shell)

        self.parser.add_argument('-i', '--interface', dest='interface', type=str, help='interface to sniff on', default=INTERFACES.NO_INTERFACE)
        self.parser.add_argument('-A', '--Any', dest='any_interface', action='store_true', help='sniff on all NICs')
        self.parser.add_argument('-p', '--promisc', dest='is_promisc', action='store_true', help='enter promiscuous mode')
        self.parser.add_argument('-S', '--Stop', dest='stop', action='store_true', help='stop ALL sniffing processes')
        # TODO: add BPF syntax (how?????)

    def action(self, parsed_args):
        """
        start sniffing or stop sniffing.
        """
        if (parsed_args.any_interface or parsed_args.interface) and parsed_args.stop:
            return CommandOutput('', "Wrong Usage!\nInterface should not be supplied when you wish to stop sniffing!")

        if parsed_args.stop:
            self.computer.stop_all_sniffing()
            return CommandOutput('', '')

        name = parsed_args.interface
        if parsed_args.any_interface:
            name = INTERFACES.ANY_INTERFACE
            if parsed_args.is_promisc:
                return CommandOutput('', "Cannot sniff on promisc on all interfaces!")

        if name == INTERFACES.NO_INTERFACE:
            name = self.computer.interfaces[0].name

        if (all(interface.name != name for interface in self.computer.all_interfaces)) and name != INTERFACES.ANY_INTERFACE:
            return CommandOutput("", f"Interface '{name}' does not exist!")

        self.computer.start_sniffing(name, is_promisc=parsed_args.is_promisc)
        return CommandOutput('', '')
