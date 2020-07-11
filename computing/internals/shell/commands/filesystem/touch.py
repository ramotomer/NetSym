from datetime import datetime

from computing.internals.shell.commands.command import Command, CommandOutput
from exceptions import NoSuchItemError


class Touch(Command):
    """
    Change a file's timestamp and if it does not exist, create it.
    """
    def __init__(self, computer, shell):
        """
        initiates the command.
        :param computer: 
        """
        super(Touch, self).__init__('touch',
                                    "Change a file's timestamp and if it does not exist, create it.",
                                    computer, shell)

        self.parser.add_argument('files', metavar='files', type=str, nargs='+', help='files to touch')

    def action(self, parsed_args):
        """
        touches the file
        """
        stdout = ''
        stderr = ''
        for file_path in parsed_args.files:
            if self.computer.filesystem.is_file(file_path, self.shell.cwd):
                file = self.computer.filesystem.at_path(self.shell.cwd, file_path)
                file.last_edit_time = datetime.now()
                stdout += f"touched {file_path}\n"
            else:
                base_dir_path, filename = self.computer.filesystem.separate_base(file_path)
                try:
                    self.computer.filesystem.at_path(self.shell.cwd, base_dir_path).make_empty_file(filename)
                except NoSuchItemError:
                    stderr += f"could not touch {file_path}\n"
                else:
                    stdout += f"created {file_path}\n"

        return CommandOutput(stdout[:-1], stderr[:-1])
