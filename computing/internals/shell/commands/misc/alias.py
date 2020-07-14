from computing.internals.shell.commands.command import Command, CommandOutput, ParsedCommand
from consts import CONSOLE
from exceptions import InvalidAliasCommand


class Alias(Command):
    """
    Create a string that will be automatically translated to a command or a number of commands.
    """
    def __init__(self, computer, shell):
        super(Alias, self).__init__('alias', 'create an alias for a command or string', computer, shell)

    def action(self, arguments):
        """
        The action of the command
        :param arguments: a string of the arguments that were given to the function
        :return:
        """
        if not arguments:
            return CommandOutput(self._list_aliases(), '')

        try:
            alias, value = self.parse_alias_string(arguments)
        except InvalidAliasCommand:
            return CommandOutput('', "The command is invalid! correct syntax is `alias ALIAS='VALUE'` or just alias, "
                                     "to list current aliases")

        self.shell.aliases[alias] = value
        return CommandOutput('', '')

    def _list_aliases(self):
        """
        Returns a string listing the aliases
        :return:
        """
        return 'ALIASES:\n' + '\n'.join([f"{alias}='{value}'" for alias, value in self.shell.aliases.items()])

    @staticmethod
    def parse_alias_string(string):
        """
        returns the alias, value as a tuple
        :param string:
        :return:
        """
        try:
            alias, value = string.split(CONSOLE.SHELL.ALIAS_SET_SIGN)
        except ValueError:
            raise InvalidAliasCommand()
        value = value.replace('\'', '').replace("\'", '')

        return alias, value

    def parse(self, string):
        """
        Overridden, since it does not know how to handle spaces in the
        :param string:
        :return:
        """
        return ParsedCommand(self, ' '.join(string.split()[1:]))
