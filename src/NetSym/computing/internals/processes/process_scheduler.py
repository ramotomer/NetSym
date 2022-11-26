from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from functools import reduce
from operator import attrgetter, concat
from typing import NamedTuple, Optional, TYPE_CHECKING, List, Type, Tuple, Generator, Any, TypeVar

from NetSym.computing.internals.processes.abstracts.process import Process, WaitingFor, ReturnedPacket
from NetSym.computing.internals.processes.abstracts.process_internal_errors import ProcessInternalError
from NetSym.consts import COMPUTER, T_Time
from NetSym.exceptions import NoSuchProcessError
from NetSym.gui.main_loop import MainLoop
from NetSym.usefuls.funcs import get_the_one, get_the_one_with_raise

if TYPE_CHECKING:
    from NetSym.computing.computer import Computer


T = TypeVar("T")


class WaitingProcess(NamedTuple):
    """
    A process that is currently waiting for a certain packet.
    """
    process:     Process
    waiting_for: Optional[WaitingFor]


class ReadyProcess(NamedTuple):
    """
    A process that is ready to run in the next 'tick' of the simulation.
    That process comes with a value that will be given to the process when it is run. In the simplest case it will be a packet that it received
    """
    process:         Process
    returned_packet: Optional[ReturnedPacket] = None


@dataclass
class SchedulerDetails:
    """
    For doc see the ProcessScheduler doc below
    """
    startup_processes:         List[Tuple[Type[Process], Tuple[...]]]
    currently_running_process: Optional[Process]
    ready_processes:           List[ReadyProcess]
    waiting_processes:         List[WaitingProcess]
    process_last_check_time:   T_Time
    latest_pid:                int

    @property
    def ready_processes_instances(self) -> List[Process]:
        return [ready_process.process for ready_process in self.ready_processes]


class ProcessScheduler:
    """
    Handles managing the runtime of each process in a computer
    """
    def __init__(self, computer: Computer) -> None:
        """
        The scheduler can know the difference between different process "modes".
            for now there are only USERMODE and KERNELMODE but more can be added easily.

            Each mode of processes run separately. Only USERMODE processes should be visible to a normal user (by the `ps` or `kill` commands etc)
            The scheduler manages several different lists of processes - one for each process "mode"

            Each mode has a separate SchedulerDetails object. Each object contains the following attributes:

                startup_processes: a list containing processes that will be run when the computer is booted
                    the format is [(PROCESS_CLASS, (PROCESS_ARGUMENTS...))...]

                currently_running_process : The process that is currently being run in the computer
                    That means the currently running code is all indirectly called from within that process
                    If you go out enough of the stack - you will end up in the `code` method of the process

                ready_processes: processes that their conditions were met and so should be run in this tick of the simulation

                waiting_processes: a list of `WaitingProcess` namedtuple-s. If the process is new, its `WaitingProcess.waiting_for` is None.
                    These are all processes that are waiting for a certain packet or condition - which is not yet met.

                process_last_check_time: the last time that the `waiting_processes` were tested for 'can they run?'

        :param computer: The computer which the processes are running on.
        """
        self.computer: Computer = computer

        self.__details_by_mode = {
            COMPUTER.PROCESSES.MODES.USERMODE: SchedulerDetails(
                startup_processes=[],
                currently_running_process=None,
                ready_processes=[],
                waiting_processes=[],
                process_last_check_time=MainLoop.get_time(),
                latest_pid=COMPUTER.PROCESSES.INIT_PID,
            ),
            COMPUTER.PROCESSES.MODES.KERNELMODE: SchedulerDetails(
                startup_processes=[],
                currently_running_process=None,
                ready_processes=[],
                waiting_processes=[],
                process_last_check_time=MainLoop.get_time(),
                latest_pid=COMPUTER.PROCESSES.INIT_PID,
            ),
        }

    @property
    def waiting_usermode_processes(self) -> List[WaitingProcess]:
        return self.__details_by_mode[COMPUTER.PROCESSES.MODES.USERMODE].waiting_processes

    @property
    def startup_usermode_processes(self) -> List[Tuple[Type[Process], Tuple[...]]]:
        return self.__details_by_mode[COMPUTER.PROCESSES.MODES.USERMODE].startup_processes

    def get_currently_running_process(self, mode) -> Optional[Process]:
        """
        returns the process that is currently being run (this means that it is the one that is indirectly calling this function)
        :param mode: one of COMPUTER.PROCESSES.MODES.ALL_MODES
        :return:
        """
        return self.__details_by_mode[mode].currently_running_process

    def is_running_a_process_in_this_mode(self, mode) -> bool:
        """
        Whether or not a process is currently running (that means all actions are indirectly performed by it)
        :return:
        """
        return self.__details_by_mode[mode].currently_running_process is not None

    def is_running_a_process(self) -> bool:
        return any(self.is_running_a_process_in_this_mode(mode) for mode in COMPUTER.PROCESSES.MODES.ALL_MODES)

    def is_inside_this_process(self, process_instance: Process) -> bool:
        """
        Is the code currently running from inside the `code` function of this specific process instance?
        """
        return any(self.get_currently_running_process(mode) == process_instance for mode in COMPUTER.PROCESSES.MODES.ALL_MODES)

    def get_process_count(self, mode: str) -> int:
        return len(self.__details_by_mode[mode].waiting_processes) + int(self.is_running_a_process_in_this_mode(mode))

    def get_all_processes(self, mode: Optional[str] = None) -> List[Process]:
        """
        Returns all of the processes in the specified mode running on the computer
        :param mode: one of COMPUTER.PROCESSES.MODES.ALL_MODES
        :return: `list` of `Process` objects
        """
        if mode is None:
            return reduce(concat, [self.get_all_processes(mode_) for mode_ in COMPUTER.PROCESSES.MODES.ALL_MODES])

        return [waiting_process.process for waiting_process in self.__details_by_mode[mode].waiting_processes] + \
               ([self.get_currently_running_process(mode)] if self.is_running_a_process_in_this_mode(mode) else []) + \
               self.__details_by_mode[mode].ready_processes_instances

    @contextmanager
    def process_is_currently_running(self, process: Process, mode: str) -> Generator:
        """
        This is a context manager that indicates that a process is currently being run by the
        process scheduler (that means that any action that is performed in the program is run by it)
        that also means it will not be in the `self.waiting_processes` list, and some actions rely on that.
        :return:
        """
        self.__details_by_mode[mode].currently_running_process = process
        try:
            yield None
        finally:
            self.__details_by_mode[mode].currently_running_process = None

    def _run_process(self, process: Process, mode: str, returned_packet: Any) -> Optional[WaitingFor]:
        """
        This function receives a process and runs it until yielding a `WaitingForPacket` namedtuple.
        Returns the yielded `WaitingForPacket`.
        :param process: a `Process` object.
        :return: a `WaitingForPacket` namedtuple or if the process is done, None.
        """
        if process.process is None:
            process.process = iter(process.code())

        with self.process_is_currently_running(process, mode):
            try:
                return process.process.send(returned_packet)
            except StopIteration:
                return None
            except ProcessInternalError as error:
                if error.args:
                    self.computer.print(f"{mode} process({process.pid}): {error.args[0]!r}")
                return None

    def _start_new_processes(self, mode: str) -> List[ReadyProcess]:
        """
        Goes over the waiting processes list and returns a list of new processes that are ready to run.
        Also removes them from the waiting processes list.
        New processes - that means that they were started by `start_process` but did not run at all yet.
        :return: a list of ready `Process`-s.
        """
        waiting_processes = self.__details_by_mode[mode].waiting_processes

        new_processes = []
        for waiting_process in waiting_processes[:]:
            process, waiting_for = waiting_process
            if waiting_for is None:  # that means the process was not yet run.
                new_processes.append(ReadyProcess(process, None))
                waiting_processes.remove(waiting_process)
        return new_processes

    def _get_ready_processes(self, mode: str) -> List[ReadyProcess]:
        """
        Returns a list of the waiting processes that finished waiting and are ready to run.
        :return: a list of `Process` objects that are ready to run. (they will run in the next call to
        `self._handle_processes`
        """
        new_packets     = self.computer.new_packets_since(self.__details_by_mode[mode].process_last_check_time, is_raw=False)
        new_packets_raw = self.computer.new_packets_since(self.__details_by_mode[mode].process_last_check_time, is_raw=True)
        self.__details_by_mode[mode].process_last_check_time = MainLoop.get_time()

        ready_processes = self._start_new_processes(mode)
        self._decide_ready_processes_no_packet(ready_processes, mode)

        waiting_processes = self.__details_by_mode[mode].waiting_processes[:]
        for waiting_process in waiting_processes:
            for received_packet in (new_packets_raw if waiting_process.waiting_for.get_raw_packet else new_packets)[:]:
                self._decide_if_process_ready_by_packet(waiting_process, received_packet, ready_processes, mode)

        self._check_process_timeouts(ready_processes, mode)
        return ready_processes

    def _decide_ready_processes_no_packet(self, ready_processes: List[ReadyProcess], mode: str) -> None:
        """
        Receives a list of the already ready processes,
        Goes over the waiting processes and sees if one of them is waiting for a certain condition without a packet (if
        its `WaitingForPacket` object is actually `WaitingFor`.
        If so, it tests its condition. If the condition is true, appends the process to the `ready_processes` list and
        removes it from the `waiting_processes` list.
        :return: None
        """
        waiting_processes = self.__details_by_mode[mode].waiting_processes
        for waiting_process in waiting_processes[:]:
            if waiting_process.waiting_for.is_for_a_packet():
                continue

            if waiting_process.waiting_for.condition():
                waiting_processes.remove(waiting_process)
                ready_processes.append(ReadyProcess(waiting_process.process, ReturnedPacket()))

    def _decide_if_process_ready_by_packet(self,
                                           waiting_process: WaitingProcess,
                                           received_packet: ReturnedPacket,
                                           ready_processes: List[ReadyProcess],
                                           mode: str) -> bool:
        """
        This method receives a waiting process, a possible packet that matches its `WaitingForPacket` condition
        and a list of already ready processes.
        If the packet matches the condition of the `WaitingForPacket` of the process, this adds the process
        to `ready_processes` and removes it from the `self.waiting_processes` list.
        It enables the same process to receive a number of different packets if the condition fits to a
        number of packets in the run. (mainly in DHCP Server when all of the computers send in the same time to the same
        process...)
        :param waiting_process:
        :param received_packet:
        :param ready_processes: a list of already ready processes that will run in the next call to
        `self._handle_processes`.
        :return: whether or not the process is ready and was added to `ready_processes`
        """
        waiting_processes = self.__details_by_mode[mode].waiting_processes

        process, waiting_for = waiting_process
        packet, packet_metadata = received_packet.packet_and_metadata

        if not waiting_for.is_for_a_packet():
            return False

        if waiting_for.condition(packet):
            waiting_for.value = waiting_for.value if waiting_for.value is not None else ReturnedPacket()
            waiting_for.value.packets[packet] = packet_metadata  # this is the behaviour the `Process` object expects

            if process not in map(attrgetter("process"), ready_processes):  # if this is the first packet that the process received in this loop
                ready_processes.append(ReadyProcess(process, waiting_for.value))
                waiting_processes.remove(waiting_process)  # the process is about to run so we remove it from the waiting process list
            return True
        return False

    def _check_process_timeouts(self, ready_processes: List[ReadyProcess], mode: str) -> None:
        """
        Tests if the waiting processes have a timeout and if so, continues them, without any packets. (inserts to the
        `ready_processes` list)
        :param ready_processes: a list of the ready processes to run.
        :return: None
        """
        waiting_processes = self.__details_by_mode[mode].waiting_processes
        for waiting_process in waiting_processes:
            if waiting_process.waiting_for.has_timeout():
                if waiting_process.waiting_for.timeout:
                    ready_processes.append(ReadyProcess(waiting_process.process, ReturnedPacket()))
                    waiting_processes.remove(waiting_process)

    def get_process(self, pid: int, mode: str) -> Process:
        """
        Returns a process class from its process ID
        :param pid: `int` the process ID
        :param mode: one of COMPUTER.PROCESSES.MODES.ALL_MODES
        :return: `Process` object
        """
        return get_the_one_with_raise(self.get_all_processes(mode), lambda process: process.pid == pid, NoSuchProcessError)

    def get_process_by_type(self, process_type: Type[T], mode: Optional[str] = None) -> T:
        """
        Receives a type of a `Process` subclass and returns the process object of the `Process` that is currently
        running in the computer.
        If no such process is running in the computer, raise NoSuchProcessError
        :param process_type: a `Process` subclass (for example `SendPing` or `DHCPClientProcess`)
        :param mode: the mode of the process (one of COMPUTER.PROCESS.MODES.ALL_MODES or None - for all of them)
        :return: `WaitingProcess` namedtuple
        """
        return get_the_one_with_raise(self.get_all_processes(mode), lambda process: isinstance(process, process_type), NoSuchProcessError)

    def get_usermode_process_by_type(self, process_type: Type[T]) -> T:
        return self.get_process_by_type(process_type, COMPUTER.PROCESSES.MODES.USERMODE)

    def get_usermode_process(self, pid: int) -> Process:
        """
        exactly like `get_process` only the for the usermode
        """
        return self.get_process(pid, COMPUTER.PROCESSES.MODES.USERMODE)

    def terminate_process(self, process: Process, mode: str) -> None:
        """
        Handles closing all of the things the process was in charge of.
        (Potentially (though not implemented) file-descriptors, sockets, memory allocations etc....)
        :param process: a Process instance
        :param mode: the mode of process to terminate (one of COMPUTER.PROCESS.MODES.ALL_MODES)
        :return:
        """
        modes = COMPUTER.PROCESSES.MODES.ALL_MODES
        if mode is not None:
            modes = [mode]

        found_the_process = False
        for mode in modes:
            waiting_processes = self.__details_by_mode[mode].waiting_processes
            ready_processes = self.__details_by_mode[mode].ready_processes

            if process in ready_processes:
                found_the_process = True
                ready_processes.remove(get_the_one_with_raise(ready_processes, lambda rp: rp.process == process, NoSuchProcessError))
            elif process is self.__details_by_mode[mode].currently_running_process:
                found_the_process = True
                process.die()  # only occurs when a process calls `terminate_process` on itself
            else:
                process = get_the_one(waiting_processes, lambda wp: wp.process == process)
                if process is not None:
                    found_the_process = True
                    waiting_processes.remove(process)
        if not found_the_process:
            raise NoSuchProcessError(f"Could not find process {process} in {modes}! Thus termination failed")

    def terminate_process_by_pid(self, pid: int, mode: str) -> None:
        """
        just like `terminate_process` only receives a process ID
        :param pid: `int` - the process ID
        :param mode: one of COMPUTER.PROCESSES.MODES.ALL_MODES
        """
        self.terminate_process(self.get_process(pid, mode), mode)

    def _terminate_all(self) -> None:
        """
        Terminates all processes
        :return:
        """
        for mode in COMPUTER.PROCESSES.MODES.ALL_MODES:
            waiting_processes = self.__details_by_mode[mode].waiting_processes

            for process in list(map(attrgetter("process"), waiting_processes)) + self.__details_by_mode[mode].ready_processes_instances:
                self.terminate_process(process, mode)

            if self.__details_by_mode[mode].currently_running_process is not None:
                self.__details_by_mode[mode].currently_running_process.die()

    def on_shutdown(self) -> None:
        """
        This function should be called when the host computer is turned off
        """
        self._terminate_all()

        for mode, details in self.__details_by_mode.items():
            details.latest_pid = COMPUTER.PROCESSES.INIT_PID
            # ^ reset the PID counting

    def __get_next_pid(self, mode: str) -> int:
        """
        :return: `int` - the next PID a new process should receive
            Increases the PIDs
        """
        self.__details_by_mode[mode].latest_pid += 1
        return self.__details_by_mode[mode].latest_pid

    def start_process(self, mode: str, process_type: Type[Any], *args: Any, **kwargs: Any) -> int:
        """
        Receive a `Process` subclass class, and the arguments for it
        (not including the default Computer argument that all processes receive.)

        for example: start_process(SendPing, '1.1.1.1/24')

        For more information about processes read the documentation at 'process.py'
        :param mode: one of COMPUTER.PROCESSES.MODES.ALL_MODES
        :param process_type: The `type` of the process to run.
        :param args: The arguments that the `Process` subclass constructor requires.
        :return: `int` the process ID of the process that was started
        """
        pid = self.__get_next_pid(mode)
        self.__details_by_mode[mode].waiting_processes.append(WaitingProcess(process_type(pid, self.computer, *args, **kwargs), None))
        return pid

    def start_usermode_process(self, process_type: Type[Process], *args: Any, **kwargs: Any) -> int:
        """
        same as `start_process` - but for usermode processes
        """
        return self.start_process(COMPUTER.PROCESSES.MODES.USERMODE, process_type, *args, **kwargs)

    def start_kernelmode_process(self, process_type: Type[Process], *args: Any, **kwargs: Any) -> int:
        """
        same as `start_process` - but for kernelmode processes
        """
        return self.start_process(COMPUTER.PROCESSES.MODES.KERNELMODE, process_type, *args, **kwargs)

    def is_process_running_by_type(self, process_type: Type[Process], mode: Optional[str] = None) -> bool:
        """
        Receives a type of a `Process` subclass and returns whether or not there is a process of that type that
        is running.
        :param process_type: a `Process` subclass (for example `SendPing` or `DHCPClientProcess`)
        :param mode: one of COMPUTER.PROCESSES.MODES.ALL_MODES
        :return: `bool`
        """
        if mode is None:
            return any(self.is_process_running_by_type(process_type, any_mode) for any_mode in COMPUTER.PROCESSES.MODES.ALL_MODES)

        for process, _ in self.__details_by_mode[mode].waiting_processes:
            if isinstance(process, process_type):
                return True
        return False

    def is_process_running(self, pid: int, mode: str) -> bool:
        """
        Return whether or not that process is currently running on the computer
        """
        try:
            self.get_process(pid, mode)
        except NoSuchProcessError:
            return False
        return True

    def is_usermode_process_running(self, pid: int) -> bool:
        """
        :param pid: `int` - The process ID to check if running
        :return: `bool` - whether or not this usermode process is running
        """
        return self.is_process_running(pid, COMPUTER.PROCESSES.MODES.USERMODE)

    def is_usermode_process_running_by_type(self, process_type: Type[Process]) -> bool:
        """
        Receives a type of a `Process` subclass and returns whether or not there is a process of that type that
        is running.
        :param process_type: a `Process` subclass (for example `SendPing` or `DHCPClientProcess`)
        """
        return self.is_process_running_by_type(process_type, COMPUTER.PROCESSES.MODES.USERMODE)

    def add_startup_process(self, mode: str, process_type: Type[Process], *args: Any) -> None:
        """
        This function adds a process to the `startup_processes` list, These processes are run right when the computer is turned on.
        :param process_type: The process that one wishes to run
        :param args: its arguments
        :param mode: one of COMPUTER.PROCESSES.MODES.ALL_MODES
        """
        self.__details_by_mode[mode].startup_processes.append((process_type, args))

        if not self.is_process_running_by_type(process_type, mode):
            self.start_process(mode, process_type, *args)

    def run_startup_processes(self) -> None:
        """
        Runs all of the startup processes - in all modes
        :return:
        """
        for mode in self.__details_by_mode:
            for process, args in self.__details_by_mode[mode].startup_processes:
                self.start_process(mode, process, *args)

    def send_process_signal(self, pid: int, signum: int, mode: str) -> None:
        """
        Send a signal to a process based on the signals defined in
        COMPUTER.PROCESSES.SIGNALS
        :param mode:
        :param pid: the process ID
        :param signum:
        :return:
        """
        if signum in COMPUTER.PROCESSES.SIGNALS.UNIGNORABLE_KILLING_SIGNALS:
            self.terminate_process_by_pid(pid, mode)
        else:
            self.get_process(pid, mode).signal_handlers[signum](signum)

    def kill_usermode_process(self, pid: int, force: bool = False) -> None:
        """
        Receives a pid and kills that process
        :param pid:
        :param force: whether or not to kill the process nicely
        :return:
        """
        if force:
            self.terminate_process(self.get_usermode_process(pid), COMPUTER.PROCESSES.MODES.USERMODE)
        else:
            self.send_process_signal(pid, COMPUTER.PROCESSES.SIGNALS.SIGTERM, COMPUTER.PROCESSES.MODES.USERMODE)

    def kill_all_usermode_processes_by_type(self, process_type: Type[Process], force: bool = False) -> None:
        """
        Takes in a process type and kills all of the waiting processes of that type in this `Computer`.
        They are killed by a signal, unless specified specifically with the `force` param
        :param process_type: a `Process` subclass type (for example `SendPing` or `DHCPClientProcess`)
        :param force:
        :return: None
        """
        for waiting_process in self.waiting_usermode_processes:
            if isinstance(waiting_process.process, process_type):
                self.kill_usermode_process(waiting_process.process.pid, force)

    def handle_processes(self) -> None:
        """
        Handles all of running the processes, runs the ones that should be run and puts them back to the
         `waiting_processes`
        list if they are now waiting.
        Read more about processes at 'process.py'
        :return: None
        """
        for mode in COMPUTER.PROCESSES.MODES.ALL_MODES:
            ready_processes = self.__details_by_mode[mode].ready_processes
            waiting_processes = self.__details_by_mode[mode].waiting_processes

            ready_processes[:] = self._get_ready_processes(mode)
            for process, returned_packet in ready_processes:
                waiting_for = self._run_process(process, mode, returned_packet)
                if waiting_for is not None:  # only None if the process is done!
                    waiting_processes.append(WaitingProcess(process, waiting_for))
            ready_processes.clear()
