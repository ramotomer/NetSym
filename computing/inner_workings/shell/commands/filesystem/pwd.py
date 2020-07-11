from computing.inner_workings.shell.commands.command import Command, CommandOutput


class Pwd(Command):
    """
    prints out the cwd
    """
    def __init__(self, computer, shell):
        """
        initiates the command.
        :param computer:
        """
        super(Pwd, self).__init__('pwd', 'print out the cwd', computer, shell)

    def action(self, parsed_args):
        """
        prints out the cwd.
        """
        return CommandOutput(f"{self.shell.cwd_path}", '')
