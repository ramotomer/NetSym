from __future__ import annotations

import argparse
from typing import TYPE_CHECKING, Tuple

from NetSym.computing.internals.shell.commands.command import Command, CommandOutput, ParsedCommand
from NetSym.consts import CONSOLE
from NetSym.exceptions import InvalidAliasCommand

if TYPE_CHECKING:
    from NetSym.computing.computer import Computer
    from NetSym.computing.internals.shell.shell import Shell


class Alias(Command):
    """
    Create a string that will be automatically translated to a command or a number of commands.
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        super(Alias, self).__init__('alias', 'create an alias for a command or string', computer, shell)

    def action(self, arguments: argparse.Namespace) -> CommandOutput:
        """
        The action of the command
        :param arguments: a string of the arguments that were given to the function
        :return:
        """
        if not arguments.arguments:
            return CommandOutput(self._list_aliases(), '')

        try:
            alias, value = self.parse_alias_string(arguments.arguments)
        except InvalidAliasCommand:
            return CommandOutput('', "The command is invalid! correct syntax is `alias ALIAS='VALUE'` or just alias, "
                                     "to list current aliases")

        self.shell.aliases[alias] = value
        return CommandOutput('', '')

    def _list_aliases(self) -> str:
        """
        Returns a string listing the aliases
        :return:
        """
        return 'ALIASES:\n' + '\n'.join([f"{alias}='{value}'" for alias, value in self.shell.aliases.items()])

    @staticmethod
    def parse_alias_string(string: str) -> Tuple[str, str]:
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

    def parse(self, string: str) -> ParsedCommand:
        """
        Overridden, since it does not know how to handle spaces inside one argument
        """
        return ParsedCommand(self, argparse.Namespace(arguments=' '.join(string.split()[1:])))
