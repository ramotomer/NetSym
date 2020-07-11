from computing.inner_workings.shell.commands.command import Command, CommandOutput
from exceptions import DirectoryAlreadyExistsError, NoSuchDirectoryError


class Mkdir(Command):
    """
    Create a directory
    """
    def __init__(self, computer, shell):
        """
        initiates the command.
        :param computer: 
        """
        super(Mkdir, self).__init__('mkdir', 'create directory', computer, shell)

        self.parser.add_argument('dirnames', metavar='dirnames', type=str, nargs='+', help='directories to create')

    def action(self, parsed_args):
        """
        Makes a directory
        """
        stdout, stderr = [], []
        for dirname in parsed_args.dirnames:
            try:
                self.computer.filesystem.make_dir(
                    self.computer.filesystem.absolute_from_relative(self.shell.cwd, dirname)
                )
            except DirectoryAlreadyExistsError:
                stderr.append(f"Directory '{dirname}' Exists! :(")
            except NoSuchDirectoryError:
                stderr.append(f"Cannot create parent directories of '{dirname}', only the directory itself!")
            else:
                stdout.append(f"Successfully Created directory '{dirname}' :)")

        return CommandOutput('\n'.join(stdout), '\n'.join(stderr))
