from computing.internals.shell.commands.command import Command, CommandOutput


class Uname(Command):
    """
    The command that prints the arguments that it receives.
    """
    def __init__(self, computer, shell):
        """
        initiates the command.
        :param computer: 
        """
        super(Uname, self).__init__('uname', 'print architecture name', computer, shell)

    def action(self, parsed_args):
        """
        prints out the arguments.
        """
        return CommandOutput(self.computer.os, '')
