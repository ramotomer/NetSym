from computing.inner_workings.shell.commands.command import Command, CommandOutput, ParsedCommand
from exceptions import WrongUsageError


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
        prints out the arguments.
        """
        return CommandOutput(' '.join(parsed_args.words), '')

    def parse(self, string):
        """
        all arguments should be printed out.
        :param string:
        :return:
        """
        command = string.split()[0]
        args = string.split()[1:]

        parsed_args = self.parser.parse_args(args)

        if command != self.name:
            raise WrongUsageError(f"wrong command given to parse! '{command}' should be '{self.name}'")

        return ParsedCommand(self, parsed_args)
