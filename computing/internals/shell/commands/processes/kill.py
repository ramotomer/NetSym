from computing.internals.shell.commands.command import Command, CommandOutput
from consts import COMPUTER
from exceptions import NoSuchProcessError


class Kill(Command):
    """
    The command that prints the arguments that it receives.
    """
    def __init__(self, computer, shell):
        """
        initiates the command.
        :param computer:
        """
        super(Kill, self).__init__('kill', 'send a signal to a process', computer, shell)

        self.parser.add_argument('-9', dest='kill_harder', action='store_true', help='kill harder!')
        self.parser.add_argument('PID', type=int, help='the Process ID of the process to kill')

    def action(self, parsed_args):
        """
        prints out the arguments.
        """
        if parsed_args.PID == COMPUTER.PROCESSES.INIT_PID:
            return CommandOutput('', "Cannot kill init!")

        try:
            self.computer.kill_process(parsed_args.PID)
        except NoSuchProcessError:
            return CommandOutput('', "There is no such process!!!")

        return CommandOutput("Signal sent successfully! :)", '')
