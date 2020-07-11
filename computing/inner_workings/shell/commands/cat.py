from computing.inner_workings.filesystem.directory import Directory
from computing.inner_workings.shell.commands.command import Command, CommandOutput
from exceptions import NoSuchItemError


class Cat(Command):
    """
    Prints out the content of a file.
    """
    def __init__(self, computer, shell):
        """
        initiates the command.
        :param computer:
        """
        super(Cat, self).__init__('cat', 'print out a file content', computer, shell)

        self.parser.add_argument('file', metavar='file', type=str, nargs=1, help='file to read')

    def action(self, parsed_args):
        """
        prints out the arguments.
        """
        try:
            file = self.computer.filesystem.at_path(self.shell.cwd, parsed_args.file[0])
            if isinstance(file, Directory):
                return CommandOutput('', f"'{file.name}' is a directory!")
            with file:
                return CommandOutput(file.read(), '')
        except NoSuchItemError:
            return CommandOutput('', f"Could not read {parsed_args.file}")
