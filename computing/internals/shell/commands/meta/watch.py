from computing.internals.processes.usermode_processes.watching_process import WatchingProcess
from computing.internals.shell.commands.command import Command, CommandOutput


class Watch(Command):
    """
    Runs a command every set amount of time and prints the output
    """

    def __init__(self, computer, shell):
        super(Watch, self).__init__('watch', 'run a command periodically and print the output', computer, shell)

        self.parser.add_argument('-n', dest='interval', default=1, help='How often to run the command')
        self.parser.add_argument('command', metavar='command', type=str, nargs='*', help='the command to run')

    def action(self, parsed_args):
        command_string = ' '.join(parsed_args.command)
        self.computer.process_scheduler.start_usermode_process(WatchingProcess, self.shell, command_string, parsed_args.interval)
        return CommandOutput(f'Watching: {command_string}', '')
