from typing import TYPE_CHECKING

from NetSym.computing.internals.processes.abstracts.process import Process, WaitingFor, T_ProcessCode

if TYPE_CHECKING:
    from NetSym.computing.computer import Computer


class NOPProcess(Process):
    """
    does nothing!
    """
    def __init__(self,
                 pid: int,
                 computer: Computer) -> None:
        super(NOPProcess, self).__init__(pid, computer)

    def code(self) -> T_ProcessCode:
        while True:
            yield WaitingFor.nothing()

    def __repr__(self) -> str:
        return "nop"
