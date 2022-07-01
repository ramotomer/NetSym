from collections import namedtuple
from contextlib import contextmanager

from consts import COMPUTER
from exceptions import NoSuchProcessError, UnknownProcessTypeError
from gui.main_loop import MainLoop
from usefuls.funcs import get_the_one

WaitingProcess = namedtuple("WaitingProcess", "process waiting_for")
# ^ a process that is currently waiting for a certain packet.


class ProcessScheduler:
    """
    Handles managing the runtime of each process in a computer
    """
    def __init__(self, computer):
        """
        self.waiting_usermode_processes: a list of `WaitingProcess` namedtuple-s. If the process is new, its `WaitingProcess.waiting_for` is None.
        self.process_last_check: the last time that the waiting_processes were checked for 'can they run?'
        self.startup_usermode_processes: a list of usermode_processes that will be run when the computer is booted
        self.__running_usermode_process : the process that is currently being run in the computer
        self.__ready_usermode_processes: usermode_processes that their conditions are met and so should be run
            in this tick of the simulation
        :param computer: The computer which the processes are running on.
        """
        self.computer = computer
        self.process_last_check = MainLoop.instance.time()

        self.waiting_usermode_processes = []
        self.startup_usermode_processes = []
        self.__running_usermode_process = None
        self.__ready_usermode_processes = []

        self.waiting_kernelmode_processes = []
        self.__running_kernelmode_process = None
        self.__ready_kernelmode_processes = []

        self.process_mode_to_waiting_processes_list = {
            COMPUTER.PROCESSES.MODES.USERMODE:   self.waiting_usermode_processes,
            COMPUTER.PROCESSES.MODES.KERNELMODE: self.waiting_kernelmode_processes,
        }

        self.process_mode_to_ready_processes_list = {
            COMPUTER.PROCESSES.MODES.USERMODE:   self.__ready_usermode_processes,
            COMPUTER.PROCESSES.MODES.KERNELMODE: self.__ready_kernelmode_processes,
        }

    @property
    def running_usermode_process(self):
        """
        Allows for getting but not setting of the attribute
        :return:
        """
        return self.__running_usermode_process

    @property
    def is_running_a_usermode_process(self):
        """
        Whether or not a process is currently running (that means all actions are indirectly performed by it)
        :return:
        """
        return self.__running_usermode_process is not None

    @property
    def is_running_a_kernelmode_process(self):
        """
        Whether or not a process is currently running (that means all actions are indirectly performed by it)
        :return:
        """
        return self.__running_kernelmode_process is not None

    @property
    def is_running_a_process(self):
        return self.is_running_a_kernelmode_process or self.is_running_a_usermode_process

    @property
    def usermode_process_count(self):
        return len(self.waiting_usermode_processes) + int(self.is_running_a_usermode_process)

    @property
    def all_usermode_processes(self):
        return [waiting_process.process for waiting_process in self.waiting_usermode_processes] + \
               ([self.running_usermode_process] if self.is_running_a_usermode_process else []) + \
               self.__ready_usermode_processes

    def __set_running_process(self, process, mode):
        if mode == COMPUTER.PROCESSES.MODES.USERMODE:
            self.__running_usermode_process = process
        elif mode == COMPUTER.PROCESSES.MODES.KERNELMODE:
            self.__running_kernelmode_process = process
        else:
            raise UnknownProcessTypeError(mode)

    @contextmanager
    def process_is_currently_running(self, process, mode):
        """
        This is a context manager that indicates that a process is currently being run by the
        process scheduler (that means that any action that is performed in the program is run by it)
        that also means it will not be in the `self.waiting_processes` list, and some actions rely on that.
        :return:
        """
        self.__set_running_process(process, mode)
        try:
            yield None
        finally:
            self.__set_running_process(None, mode)

    def _run_process(self, process, mode):
        """
        This function receives a process and runs it until yielding a `WaitingForPacket` namedtuple.
        Returns the yielded `WaitingForPacket`.
        :param process: a `Process` object.
        :return: a `WaitingForPacket` namedtuple or if the process is done, None.
        """
        if process.process is None:
            process.process = iter(process.code())

        if process.kill_me:
            return None

        with self.process_is_currently_running(process, mode):
            try:
                return next(process.process)
            except StopIteration:
                return None

    def _start_new_processes(self, mode):
        """
        Goes over the waiting processes list and returns a list of new processes that are ready to run.
        Also removes them from the waiting processes list.
        New processes - that means that they were started by `start_process` but did not run at all yet.
        :return: a list of ready `Process`-s.
        """
        waiting_processes = self.process_mode_to_waiting_processes_list[mode]

        new_processes = []
        for process, waiting_for in waiting_processes[:]:
            if waiting_for is None:  # that means the process was not yet run.
                new_processes.append(process)
                waiting_processes.remove((process, None))
        return new_processes

    def _get_ready_processes(self, mode):
        """
        Returns a list of the waiting processes that finished waiting and are ready to run.
        :return: a list of `Process` objects that are ready to run. (they will run in the next call to
        `self._handle_processes`
        """
        new_packets = self.computer.new_packets_since(self.process_last_check)
        self.process_last_check = MainLoop.instance.time()

        self._kill_dead_processes(mode)
        ready_processes = self._start_new_processes(mode)
        self._decide_ready_processes_no_packet(ready_processes, mode)

        waiting_processes = self.process_mode_to_waiting_processes_list[mode][:]
        for received_packet in new_packets[:]:
            for waiting_process in waiting_processes:
                self._decide_if_process_ready_by_packet(waiting_process, received_packet, ready_processes, mode)

        self._check_process_timeouts(ready_processes, mode)
        return ready_processes

    def _kill_dead_processes(self, mode):
        """
        Kills all of the process that have the `kill_me` attribute set.
        This allows them to terminate themselves from anywhere inside them
        :return: None
        """
        waiting_processes = self.process_mode_to_waiting_processes_list[mode]
        for waiting_process in waiting_processes[:]:
            process, _ = waiting_process
            if process.kill_me:
                self.terminate_process(waiting_process.process, mode)

    def _decide_ready_processes_no_packet(self, ready_processes, mode):
        """
        Receives a list of the already ready processes,
        Goes over the waiting processes and sees if one of them is waiting for a certain condition without a packet (if
        its `WaitingForPacket` object is actually `WaitingFor`.
        If so, it tests its condition. If the condition is true, appends the process to the `ready_processes` list and
        removes it from the `waiting_processes` list.
        :return: None
        """
        waiting_processes = self.process_mode_to_waiting_processes_list[mode]
        for waiting_process in waiting_processes[:]:
            if not hasattr(waiting_process.waiting_for, "value"):
                if waiting_process.waiting_for.condition():
                    waiting_processes.remove(waiting_process)
                    ready_processes.append(waiting_process.process)

    def _decide_if_process_ready_by_packet(self, waiting_process, received_packet, ready_processes, mode):
        """
        This method receives a waiting process, a possible packet that matches its `WaitingForPacket` condition
        and a list of already ready processes.
        If the packet matches the condition of the `WaitingForPacket` of the process, this adds the process
        to `ready_processes` and removes it from the `self.waiting_processes` list.
        It enables the same process to receive a number of different packets if the condition fits to a
        number of packets in the run. (mainly in DHCP Server when all of the computers send in the same time to the same
        process...)
        :param waiting_process: a `WaitingProcess` namedtuple.
        :param received_packet: a `ReceivedPacket` namedtuple.
        :param ready_processes: a list of already ready processes that will run in the next call to
        `self._handle_processes`.
        :return: whether or not the process is ready and was added to `ready_processes`
        """
        waiting_processes = self.process_mode_to_waiting_processes_list[mode]

        process, waiting_for = waiting_process
        packet, _, receiving_interface = received_packet

        if not hasattr(waiting_for, "value"):
            return False

        if waiting_for.condition(packet):
            waiting_for.value.packets[
                packet] = receiving_interface  # this is the behaviour the `Process` object expects

            if process not in ready_processes:  # if this is the first packet that the process received in this loop
                ready_processes.append(process)
                waiting_processes.remove(
                    waiting_process)  # the process is about to run so we remove it from the waiting process list
            return True
        return False

    def _check_process_timeouts(self, ready_processes, mode):
        """
        Tests if the waiting processes have a timeout and if so, continues them, without any packets. (inserts to the
        `ready_processes` list)
        :param ready_processes: a list of the ready processes to run.
        :return: None
        """
        waiting_processes = self.process_mode_to_waiting_processes_list[mode]
        for waiting_process in waiting_processes:
            if hasattr(waiting_process.waiting_for, "timeout"):
                if waiting_process.waiting_for.timeout:
                    ready_processes.append(waiting_process.process)
                    waiting_processes.remove(waiting_process)

    def get_usermode_process(self, pid, raises=True):
        """
        Returns a process class from its process ID
        :param pid:
        :param raises
        :return:
        """
        running_usermode_process = [self.running_usermode_process] if self.is_running_a_usermode_process else []

        return get_the_one([wp.process for wp in self.waiting_usermode_processes] + self.__ready_usermode_processes + running_usermode_process,
                           lambda process: process.pid == pid,
                           NoSuchProcessError if raises else None)

    def terminate_process(self, process, mode):
        """
        Handles closing all of the things the process was in charge of.
        (Potentially (though not implemented) file-descriptors, sockets, memory allocations etc....)
        :param process: a Process instance
        :param mode: the mode of process to terminate (one of COMPUTER.PROCESS.MODES.ALL_MODES)
        :return:
        """
        waiting_processes = self.process_mode_to_waiting_processes_list[mode]
        ready_processes = self.process_mode_to_ready_processes_list[mode]

        for socket in {**self.computer.sockets}:
            if socket.pid == process.pid:
                self.computer.remove_socket(socket)

        if process in ready_processes:
            ready_processes.remove(process)
        elif process is self.__running_usermode_process or process is self.__running_kernelmode_process:
            process.die()  # only occurs when a process calls `terminate_process` on itself
        else:
            waiting_processes.remove(
                get_the_one(waiting_processes, lambda wp: wp.process == process, NoSuchProcessError)
            )

    def terminate_all(self):
        """
        Terminates all processes
        :return:
        """
        for mode_ in COMPUTER.PROCESSES.MODES.ALL_MODES:
            waiting_processes = self.process_mode_to_waiting_processes_list[mode_]

            for process in [wp.process for wp in waiting_processes] + self.process_mode_to_ready_processes_list[mode_]:
                self.terminate_process(process, mode_)

        if self.is_running_a_usermode_process:
            self.__running_usermode_process.die()
        if self.is_running_a_kernelmode_process:
            self.__running_kernelmode_process.die()
        # ^ this code needs improvement - what if we add a new process mode? make better maybe one day

    def __get_next_usermode_pid(self):
        """
        :return: `int` - the next PID a new process should receive
        """
        return max([process.pid for process in self.all_usermode_processes] + [COMPUTER.PROCESSES.INIT_PID]) + 1

    def start_process(self, process_type, *args):
        """
        Receive a `Process` subclass class, and the arguments for it
        (not including the default Computer argument that all processes receive.)

        for example: start_process(SendPing, '1.1.1.1/24')

        For more information about processes read the documentation at 'process.py'
        :param process_type: The `type` of the process to run.
        :param args: The arguments that the `Process` subclass constructor requires.
        :return: None
        """
        pid = self.__get_next_usermode_pid()
        self.waiting_usermode_processes.append(WaitingProcess(process_type(pid, self.computer, *args), None))
        return pid

    def handle_processes(self):
        """
        Handles all of running the processes, runs the ones that should be run and puts them back to the
         `waiting_processes`
        list if they are now waiting.
        Read more about processes at 'process.py'
        :return: None
        """
        for mode in COMPUTER.PROCESSES.MODES.ALL_MODES:
            ready_processes = self.process_mode_to_ready_processes_list[mode]
            waiting_processes = self.process_mode_to_waiting_processes_list[mode]

            ready_processes[:] = self._get_ready_processes(mode)
            for process in ready_processes:
                waiting_for = self._run_process(process, mode)
                if waiting_for is not None:  # only None if the process is done!
                    waiting_processes.append(WaitingProcess(process, waiting_for))
            ready_processes.clear()
