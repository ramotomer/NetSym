from computing.internals.processes.abstracts.process import Process, WaitingFor


class NOPProcess(Process):
    """
    does nothing!
    """
    def __init__(self, pid, computer):
        super(NOPProcess, self).__init__(pid, computer)

    def code(self):
        while True:
            yield WaitingFor(lambda: True)

    def __repr__(self):
        return "nop"
