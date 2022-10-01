from __future__ import annotations

from typing import TYPE_CHECKING

from computing.internals.shell.commands.command import Command, CommandOutput

if TYPE_CHECKING:
    import argparse
    from computing.computer import Computer
    from computing.internals.shell.shell import Shell


class Man(Command):
    """
    The command that prints a description for another command
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        """
        initiates the command.
        :param computer:
        """
        super(Man, self).__init__('man', 'print out a manual for a command', computer, shell)
        self.parser.add_argument('command', metavar='command', type=str, help='a command to print the description for')

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        The command action
        """
        try:
            command = self.shell.string_to_command[parsed_args.command]
        except KeyError:
            return CommandOutput('', f'No man page for "{parsed_args.command}"')
        return CommandOutput(f"\nman page for '{command.name}':\n\n\t" + command.description, '')
