from computing.internals.shell.commands.command import Command, CommandOutput


class Arp(Command):
    """
    Command that prints out the arp cache
    """
    def __init__(self, computer, shell):
        """
        initiates the command.
        :param computer:
        """
        super(Arp, self).__init__('arp', 'print out arp cache', computer, shell)

        self.parser.add_argument('words', metavar='words', type=str, nargs='*', help='words to print')

    def action(self, parsed_args):
        """
        prints out the arguments.
        """
        return CommandOutput(self.computer.arp_cache_display(), '')
