from computing.internals.processes.abstracts.process import Process, WaitingFor, Timeout


class WatchingProcess(Process):
    """
    This is a process object. The process it represents is one that runs a command periodically and prints the output to the screen
    """
    def __init__(self, pid, computer, shell, command, interval):
        super(WatchingProcess, self).__init__(pid, computer)
        self.shell = shell
        self.command_string = command
        self.interval = interval

    def code(self):
        while True:
            self.shell.execute(self.command_string, record_in_shell_history=False)
            yield WaitingFor(Timeout(self.interval).is_done)

    def __repr__(self):
        return f'watch -n {self.interval} "{self.command_string}"'
