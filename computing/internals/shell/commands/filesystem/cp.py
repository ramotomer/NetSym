from computing.internals.filesystem.directory import Directory
from computing.internals.shell.commands.command import Command, CommandOutput
from exceptions import NoSuchFileError, NoSuchDirectoryError


class Cp(Command):
    """
    Copies a file to a new location or name
    """
    def __init__(self, computer, shell):
        """
        initiate command
        """
        super(Cp, self).__init__('cp', 'copy a file to a new location or name', computer, shell)

        self.parser.add_argument('src', help='the source file path')
        self.parser.add_argument('dst', help='the destination file path')

    def action(self, parsed_args):
        """
        Copy a file to a new location or name
        :return:
        """
        try:
            if isinstance(self.computer.filesystem.at_path(self.shell.cwd, parsed_args.src), Directory):
                return CommandOutput('', "Cannot copy directory!")
            self.computer.filesystem.move_file(parsed_args.src, parsed_args.dst, self.shell.cwd, True)
        except NoSuchFileError:
            return CommandOutput('', "The source file does not exist! :(")
        except NoSuchDirectoryError:
            return CommandOutput('', "The path does not exist! :(")

        return CommandOutput(f"File copied to '{parsed_args.dst}' successfully", '')
