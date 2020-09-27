from collections import namedtuple
from contextlib import contextmanager

from exceptions import NoSuchProcessError
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
        self.waiting_processes: a list of `WaitingProcess` namedtuple-s. If the process is new, its `WaitingProcess.waiting_for` is None.
        self.process_last_check: the last time that the waiting_processes were checked for 'can they run?'
        self.startup_processes: a list of processes that will be run when the computer is booted
        self.__running_process: the process that is currently being run in the computer
        self.__ready_processes: processes that their conditions are met and so should be run
            in this tick of the simulation
        :param computer: The computer which the processes are running on.
        """
        self.computer = computer
        self.waiting_processes = []
        self.process_last_check = MainLoop.instance.time()
        self.startup_processes = []
        self.__running_process = None
        self.__ready_processes = []

    @property
    def running_process(self):
        """
        Allows for getting but not setting of the attribute
        :return:
        """
        return self.__running_process

    @property
    def is_running_a_process(self):
        """
        Whether or not a process is currently running (that means all actions are indirectly performed by it)
        :return:
        """
        return self.__running_process is not None
    
    @property
    def process_count(self):
        return len(self.waiting_processes) + int(self.is_running_a_process)

    @property
    def all_processes(self):
        return [waiting_process.process for waiting_process in self.waiting_processes] + \
               ([self.running_process] if self.is_running_a_process else []) + \
               self.__ready_processes

    @contextmanager
    def process_is_currently_running(self, process):
        """
        This is a context manager that indicates that a process is currently being run by the
        process scheduler (that means that any action that is performed in the program is run by it)
        that also means it will not be in the `self.waiting_processes` list, and some actions rely on that.
        :return:
        """
        self.__running_process = process
        try:
            yield None
        finally:
            self.__running_process = None

    def _run_process(self, process):
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

        with self.process_is_currently_running(process):
            try:
                return next(process.process)
            except StopIteration:
                return None

    def _start_new_processes(self):
        """
        Goes over the waiting processes list and returns a list of new processes that are ready to run.
        Also removes them from the waiting processes list.
        New processes - that means that they were started by `start_process` but did not run at all yet.
        :return: a list of ready `Process`-s.
        """
        new_processes = []
        for process, waiting_for in self.waiting_processes[:]:
            if waiting_for is None:  # that means the process was not yet run.
                new_processes.append(process)
                self.waiting_processes.remove((process, None))
        return new_processes

    def _get_ready_processes(self):
        """
        Returns a list of the waiting processes that finished waiting and are ready to run.
        :return: a list of `Process` objects that are ready to run. (they will run in the next call to
        `self._handle_processes`
        """
        new_packets = self.computer.new_packets_since(self.process_last_check)
        self.process_last_check = MainLoop.instance.time()

        self._kill_dead_processes()
        ready_processes = self._start_new_processes()
        self._decide_ready_processes_no_packet(ready_processes)

        waiting_processes_copy = self.waiting_processes[:]
        for received_packet in new_packets[:]:
            for waiting_process in waiting_processes_copy:
                self._decide_if_process_ready_by_packet(waiting_process, received_packet, ready_processes)

        self._check_process_timeouts(ready_processes)
        return ready_processes

    def _kill_dead_processes(self):
        """
        Kills all of the process that have the `kill_me` attribute set.
        This allows them to terminate themselves from anywhere inside them
        :return: None
        """
        for waiting_process in self.waiting_processes[:]:
            process, _ = waiting_process
            if process.kill_me:
                self.terminate_process(waiting_process.process)

    def _decide_ready_processes_no_packet(self, ready_processes):
        """
        Receives a list of the already ready processes,
        Goes over the waiting processes and sees if one of them is waiting for a certain condition without a packet (if
        its `WaitingForPacket` object is actually `WaitingFor`.
        If so, it tests its condition. If the condition is true, appends the process to the `ready_processes` list and
        removes it from the `waiting_processes` list.
        :return: None
        """
        for waiting_process in self.waiting_processes[:]:
            if not hasattr(waiting_process.waiting_for, "value"):
                if waiting_process.waiting_for.condition():
                    self.waiting_processes.remove(waiting_process)
                    ready_processes.append(waiting_process.process)

    def _decide_if_process_ready_by_packet(self, waiting_process, received_packet, ready_processes):
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
        process, waiting_for = waiting_process
        packet, _, receiving_interface = received_packet

        if not hasattr(waiting_for, "value"):
            return False

        if waiting_for.condition(packet):
            waiting_for.value.packets[
                packet] = receiving_interface  # this is the behaviour the `Process` object expects

            if process not in ready_processes:  # if this is the first packet that the process received in this loop
                ready_processes.append(process)
                self.waiting_processes.remove(
                    waiting_process)  # the process is about to run so we remove it from the waiting process list
            return True
        return False

    def _check_process_timeouts(self, ready_processes):
        """
        Tests if the waiting processes have a timeout and if so, continues them, without any packets. (inserts to the
        `ready_processes` list)
        :param ready_processes: a list of the ready processes to run.
        :return: None
        """
        for waiting_process in self.waiting_processes:
            if hasattr(waiting_process.waiting_for, "timeout"):
                if waiting_process.waiting_for.timeout:
                    ready_processes.append(waiting_process.process)
                    self.waiting_processes.remove(waiting_process)

    def get_process(self, pid, raises=True):
        """
        Returns a process class from its process ID
        :param pid:
        :param raises
        :return:
        """
        running_process = [self.running_process] if self.is_running_a_process else []

        return get_the_one([wp.process for wp in self.waiting_processes] + self.__ready_processes + running_process,
                           lambda process: process.pid == pid,
                           NoSuchProcessError if raises else None)

    def terminate_process(self, process):
        """
        Handles closing all of the things the process was in charge of.
        (Potentially (though not implemented) file-descriptors, sockets, memory allocations etc....)
        :param process: a Process instance
        :return:
        """
        for socket in {**self.computer.sockets}:
            if socket.pid == process.pid:
                self.computer.remove_socket(socket)

        if process in self.__ready_processes:
            self.__ready_processes.remove(process)
        elif process is self.running_process:
            process.die()  # only occurs when a process calls `terminate_process` on itself
        else:
            self.waiting_processes.remove(
                get_the_one(self.waiting_processes, lambda wp: wp.process == process, NoSuchProcessError)
            )

    def terminate_all(self):
        """
        Terminates all processes
        :return:
        """
        for process in [wp.process for wp in self.waiting_processes] + self.__ready_processes:
            self.terminate_process(process)

        if self.is_running_a_process:
            self.running_process.die()

    def handle_processes(self):
        """
        Handles all of running the processes, runs the ones that should be run and puts them back to the
         `waiting_processes`
        list if they are now waiting.
        Read more about processes at 'process.py'
        :return: None
        """
        self.__ready_processes = self._get_ready_processes()
        for process in self.__ready_processes:
            waiting_for = self._run_process(process)
            if waiting_for is not None:  # only None if the process is done!
                self.waiting_processes.append(WaitingProcess(process, waiting_for))
        self.__ready_processes.clear()
