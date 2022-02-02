from computing.internals.shell.commands.command import Command, CommandOutput


class Unalias(Command):
    """
    Create a string that will be automatically translated to a command or a number of commands.
    """
    def __init__(self, computer, shell):
        super(Unalias, self).__init__('unalias', 'remove an alias for a command or string', computer, shell)

        self.parser.add_argument('alias', help="the alias to remove")

    def action(self, parsed_args):
        """
        The action of the command
        :param parsed_args:
        :return:
        """
        if parsed_args.alias not in self.shell.aliases:
            return CommandOutput('', "There is no such alias! :(")

        del self.shell.aliases[parsed_args.alias]
        return CommandOutput('Removed successfully', '')
