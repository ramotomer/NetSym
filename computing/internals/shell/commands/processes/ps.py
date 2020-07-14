from computing.internals.shell.commands.command import Command, CommandOutput


class Ps(Command):
    """
    Prints out all of the computer's processes.
    """
    def __init__(self, computer, shell):
        """
        initiates the command.
        :param computer:
        """
        super(Ps, self).__init__('ps', 'print out processes', computer, shell)
        self.parser.add_argument('-f', action='store_true')
        self.parser.add_argument('-a', action='store_true')
        self.parser.add_argument('-d', action='store_true')
        self.parser.add_argument('-e', action='store_true')

    @staticmethod
    def _process_info(process):
        """
        return an info line string about a process.
        :param process:
        :return:
        """
        words = repr(process).lower().split()
        words.remove('process')
        name = ' '.join(words).title().replace(' ', '')

        return f"{process.pid: >3}\t{name}\n"

    def _list_processes(self):
        """
        lists out the processes.
        :return:
        """
        string = f"PID\tNAME\n  1\tinit\n"
        for process, _ in sorted(self.computer.waiting_processes, key=lambda wp: wp.process.pid):
            string += self._process_info(process)
        return CommandOutput(string, '')

    def action(self, parsed_args):
        """
        Prints out all of the computer's processes.
        """
        return self._list_processes()
