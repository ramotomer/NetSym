from __future__ import annotations

from typing import TYPE_CHECKING

from NetSym.computing.internals.processes.abstracts.process import Process, WaitingFor, Timeout, T_ProcessCode
from NetSym.consts import T_Time

if TYPE_CHECKING:
    from NetSym.computing.internals.shell.shell import Shell
    from NetSym.computing.computer import Computer


class WatchingProcess(Process):
    """
    This is a process object. The process it represents is one that runs a command periodically and prints the output to the screen
    """
    def __init__(self, pid: int, computer: Computer, shell: Shell, command: str, interval: T_Time) -> None:
        super(WatchingProcess, self).__init__(pid, computer)
        self.shell = shell
        self.command_string = command
        self.interval = interval

    def code(self) -> T_ProcessCode:
        while True:
            self.shell.execute(self.command_string, record_in_shell_history=False)
            yield WaitingFor(Timeout(self.interval).is_done)

    def __repr__(self) -> str:
        return f'watch -n {self.interval} "{self.command_string}"'
