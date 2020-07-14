from computing.internals.shell.commands.command import Command, CommandOutput


class Echo(Command):
    """
    The command that prints the arguments that it receives.
    """
    def __init__(self, computer, shell):
        """
        initiates the command.
        :param computer:
        """
        super(Echo, self).__init__('echo', 'print out arguments', computer, shell)

        self.parser.add_argument('words', metavar='words', type=str, nargs='*', help='words to print')

    def action(self, parsed_args):
        """
        The command action
        """
        return CommandOutput(' '.join(parsed_args.words), '')
