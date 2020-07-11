from computing.internals.shell.commands.command import Command, CommandOutput
from consts import FILESYSTEM
from exceptions import NoSuchItemError


class Cd(Command):
    """
    Changes the current working directory.
    """
    def __init__(self, computer, shell):
        """
        initiates the command.
        :param computer:
        """
        super(Cd, self).__init__('cd', 'change the cwd', computer, shell)

        self.parser.add_argument('new_dir', metavar='new_dir', type=str, nargs='?', help='directory to switch to')

        # TODO: doing a -h flag or giving the wrong args crashes the program!!! no good...

    def _change_dir(self, new_dir_path):
        """
        Changes the current working directory
        :param new_dir_path: new path (relative or absolute...)
        :return:
        """
        if self.computer.filesystem.is_absolute_path(new_dir_path):
            self.shell.cwd = self.computer.filesystem.at_absolute_path(new_dir_path)
            return new_dir_path
        return self._change_dir(self.computer.filesystem.absolute_from_relative(self.shell.cwd, new_dir_path))

    def action(self, parsed_args):
        """
        prints out the arguments.
        """

        try:
            new_dir = parsed_args.new_dir if parsed_args.new_dir else FILESYSTEM.HOME_DIR
            self.shell.cwd = self.computer.filesystem.at_path(self.shell.cwd, new_dir)
        except NoSuchItemError:
            return CommandOutput('', f"Cannot switch to directory '{parsed_args.new_dir}'")

        return CommandOutput(f"Switched to '{self.shell.cwd_path}'", '')
