from __future__ import annotations

from typing import TYPE_CHECKING

from NetSym.computing.internals.shell.commands.command import Command, CommandOutput

if TYPE_CHECKING:
    import argparse
    from NetSym.computing.computer import Computer
    from NetSym.computing.internals.shell.shell import Shell


class Help(Command):
    """
    Help
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        """
        initiates the command.
        :param computer:
        """
        super(Help, self).__init__('help', 'print out help', computer, shell)

    def _to_print(self) -> str:
        return "COMMANDS:\n" + '\n'.join([f"{command_name}: {command.description}"
                                          for command_name, command in self.shell.string_to_command.items()])

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        The command action
        """
        return CommandOutput(self._to_print(), '')
