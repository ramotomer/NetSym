from computing.internals.shell.commands.command import Command, CommandOutput


class Rm(Command):
    """
    The command that prints the arguments that it receives.
    """
    def __init__(self, computer, shell):
        """
        initiates the command.
        :param computer:
        """
        super(Rm, self).__init__('rm', 'remove a file', computer, shell)
        self.parser.add_argument('filenames', metavar='filenames', type=str, nargs='+', help='files to remove')

    def action(self, parsed_args):
        """
        prints out the arguments.
        """
        stdout, stderr = [], []
        for file_path in parsed_args.filenames:
            full_path = self.computer.filesystem.absolute_from_relative(self.shell.cwd, file_path)
            base_dir_path, filename = self.computer.filesystem.separate_base(full_path)
            base_dir = self.computer.filesystem.at_absolute_path(base_dir_path)
            try:
                del base_dir.files[filename]
            except KeyError:
                if filename in base_dir.directories:
                    stderr.append(f"{filename} is a directory! :(")
                else:
                    stderr.append(f"{filename} does not exist! :(")
            else:
                stdout.append(f"successfully deleted {filename}")

        return CommandOutput('\n'.join(stdout), '\n'.join(stderr))
