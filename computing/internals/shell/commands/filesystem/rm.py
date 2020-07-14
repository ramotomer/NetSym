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
        self.parser.add_argument('-r', '--recurse', dest='is_recurse', action='store_true', help='remove recursively')
        self.parser.add_argument('-f', '--force', dest='is_forced', action='store_true', help='do not prompt')

    def action(self, parsed_args):
        """
        prints out the arguments.
        """
        stdout, stderr = [], []
        for file_path in parsed_args.filenames:
            base_dir, filename = self.computer.filesystem.filename_and_dir_from_path(self.shell.cwd, file_path)
            try:
                del base_dir.files[filename]
            except KeyError:
                if filename in base_dir.directories:
                    if parsed_args.is_recurse:
                        del base_dir.directories[filename]
                        stdout.append(f"Successfully recursively deleted {filename}")
                    else:
                        stderr.append(f"{filename} is a directory! :(")
                else:
                    stderr.append(f"{filename} does not exist! :(")
            else:
                stdout.append(f"Successfully deleted {filename}")

        return CommandOutput('\n'.join(stdout), '\n'.join(stderr))
