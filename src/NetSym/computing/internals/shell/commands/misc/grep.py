from __future__ import annotations

from typing import TYPE_CHECKING, List

from NetSym.computing.internals.filesystem.directory import Directory
from NetSym.computing.internals.filesystem.file import File
from NetSym.computing.internals.shell.commands.command import Command, CommandOutput
from NetSym.exceptions import NoSuchItemError

if TYPE_CHECKING:
    import argparse
    from NetSym.computing.computer import Computer
    from NetSym.computing.internals.shell.shell import Shell


class Grep(Command):
    """
    Search a file for an expression
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        """
        initiates the grep command
        :param computer:
        :param shell:
        """
        super(Grep, self).__init__('grep', 'search a file for an expression', computer, shell)

        self.parser.add_argument('EXPRESSION', help='the expression to search')
        self.parser.add_argument('FILE', help='the file to search in')
        self.parser.add_argument('-v', dest='is_reversed', action='store_true',
                                 help='only lines that do not contain the expression')

    @staticmethod
    def _fitting_lines(expression: str, file: File, is_reversed: bool = False) -> List[str]:
        """
        Returns a list of lines
        :param expression:
        :param file: `File`
        :param is_reversed: lines that do NOT contain the expression.
        :return:
        """
        def condition(line: str) -> bool:
            if is_reversed:
                return expression not in line
            return expression in line

        with file:
            return [line for line in file.read().split('\n') if condition(line)]

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        The command action
        :param parsed_args:
        :return:
        """
        try:
            file = self.computer.filesystem.at_path(self.shell.cwd, parsed_args.FILE)
        except NoSuchItemError:
            return CommandOutput('', f"Cannot look through the file {parsed_args.FILE} :( (does it exist?)")

        if isinstance(file, Directory):
            return CommandOutput('', f"{parsed_args.FILE} is a directory! :(")

        return CommandOutput('\n'.join(self._fitting_lines(parsed_args.EXPRESSION,
                                                           file,
                                                           is_reversed=parsed_args.is_reversed)), '')
