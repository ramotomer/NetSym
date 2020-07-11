from computing.inner_workings.shell.commands.command import Command, CommandOutput


class Ls(Command):
    """
    lists the current working directory of the computer.
    """
    def __init__(self, computer, shell):
        """
        Initiates the command with the running computer.
        :param computer:
        """
        super(Ls, self).__init__("ls", "lists the cwd", computer, shell)

        self.parser.add_argument('dirname', metavar='dirname', type=str, nargs='?', help='the directory to list')

    def _list_dir(self, path):
        """
        Lists the directory at the given path.
        :param path:
        :return:
        """
        if self.computer.filesystem.is_absolute_path(path):
            return '\n'.join(self.computer.filesystem.at_absolute_path(path).items)
        return '\n'.join(self.shell.cwd.at_relative_path(path).items)

    def action(self, parsed_args):
        """
        prints out the arguments.
        """
        listed = self._list_dir(parsed_args.dirname if parsed_args.dirname else self.shell.cwd_path)
        return CommandOutput(listed, '')
