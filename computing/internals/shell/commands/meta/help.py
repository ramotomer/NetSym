from computing.internals.shell.commands.command import Command, CommandOutput


class Help(Command):
    """
    Help
    """
    def __init__(self, computer, shell):
        """
        initiates the command.
        :param computer:
        """
        super(Help, self).__init__('help', 'print out help', computer, shell)

    def _to_print(self):
        return "COMMANDS:\n" + '\n'.join([f"{command_name}: {command.description}"
                                          for command_name, command in self.shell.string_to_command.items()])

    def action(self, parsed_args):
        """
        The command action
        """
        return CommandOutput(self._to_print(), '')
