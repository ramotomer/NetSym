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

        self.parser.add_argument('-a', '--all', dest='is_all', action='store_true')
        self.parser.add_argument('-d', '--delete', dest='is_delete', action='store_true')

    def action(self, parsed_args):
        """
        prints out the arguments.
        """
        if parsed_args.is_all:
            return CommandOutput(self.computer.arp_cache_repr(), '')

        if parsed_args.is_delete:
            self.computer.wipe_arp_cache()
            return CommandOutput("Arp cache wiped successfully! :)", '')

        return CommandOutput(
            '',
            """usage:
arp -a (to print out the arp cache)
arp -d (delete the arp cache)
"""
        )
