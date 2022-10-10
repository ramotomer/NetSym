from __future__ import annotations

import inspect
from abc import ABCMeta, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterator, Union, Callable, TYPE_CHECKING, Optional, Tuple, Type, Generator

from consts import COMPUTER, T_Time
from exceptions import *
from gui.main_loop import MainLoop
from packets.packet import Packet
from usefuls.iterable_dataclass import IterableDataclass

if TYPE_CHECKING:
    from computing.internals.interface import Interface
    from computing.computer import Computer


class ReturnedPacket:
    """
    The proper way to get received packets back from the running computer.
    `self.packets` is a dictionary with `Packet` keys and the values are `PacketMetadata` objects
    """
    def __init__(self, packet: Optional[Packet] = None, metadata: Optional[PacketMetadata] = None) -> None:
        self.packets = {}
        self.packet_iterator = None

        if packet is not None and metadata is not None:
            self.packets[packet] = metadata

    @property
    def packet(self) -> Packet:
        """
        Returns the a packet that was returned. The next call will give a different
        result. If there are no more packets left to return, raise `NoSuchPacketError`
        :return: a `Packet` object that was not yet used.
        """
        if len(self.packets) == 1:
            return list(self.packets)[0]

        if self.packet_iterator is None:
            self.packet_iterator = iter(self.packets)

        try:
            return next(self.packet_iterator)
        except StopIteration:
            raise NoSuchPacketError("All of the packets were requested from this object already!!")

    @property
    def packet_and_interface(self) -> Tuple[Packet, Interface]:
        """
        just like `self.packet` but returns a tuple of (packet, interface)
        """
        packet = self.packet
        return packet, self.packets[packet].interface

    @property
    def packet_and_metadata(self) -> Tuple[Packet, PacketMetadata]:
        """
        just like `self.packet` but returns a tuple of (packet, PacketMetadata) [actually (packet, self.packets[packet])
        """
        packet = self.packet
        return packet, self.packets[packet]

    def has_packets(self) -> bool:
        """Returns whether or not this has any packets inside"""
        return bool(self.packets)

    def __bool__(self) -> bool:
        return bool(self.packets)

    def __iter__(self) -> Iterator:
        """
        Returns an iterator of a list of tuples (packet, interface)
        :return:
        """
        return iter(list(self.packets.items()))


@dataclass
class WaitingFor(IterableDataclass):
    """
    Indicates the process is waiting for a certain condition
    `condition` is a function that should be called without parameters and return a `bool`
    """
    condition: Union[Callable[[], bool], Callable[[Packet], bool]]
    timeout:   Optional[Timeout] = None
    value:     Optional[ReturnedPacket] = None

    @classmethod
    def nothing(cls) -> WaitingFor:
        return WaitingFor(lambda: True)

    def is_for_a_packet(self) -> bool:
        """
        Checks the function to see what it waits for:
            A condition function that should just be called?
            Or a packet filter that should be applied to a returned packet
        """
        return len(inspect.signature(self.condition).parameters) == 1

    def has_timeout(self) -> bool:
        """
        Returns whether or not the condition has some maximum time to wait before giving control back to the process
        """
        return self.timeout is not None


T_ProcessCode = Generator[WaitingFor, ReturnedPacket, None]


class Process(metaclass=ABCMeta):
    """
    This class is a process in the computer class.
    It holds a state of the process and can run and perform code, then stop, wait for a condition and
        when that condition is met it can continue running.
    It has a `code` method which is a generator function that yields `WaitingForPacket` namedtuple-s.

    The `WaitingForPacket` tuples have a condition and a value, they tell the computer
    that's running the process that the process should be stopped until the `condition`
    function is met by a packet that was received recently. Then the computer puts the
    packet in the `value` object and continues the process run.

    So the process runs the `code` method until it yields a `WaitingForPacket`, then it stops, once a packet fits the condition
    it continues running until the next yield. That is the way that a process can run smoothly in one function while waiting
    for packets without blocking the main loop.

    The `process` property of the Process is a generator of the code, the value
    of the `self.code()` method call.

    If a `ProcessInternalError` is raised within your `code` function - the process will be killed but the program will continue running! :)
    """
    def __init__(self, pid: int, computer: Computer) -> None:
        """
        The process currently has access to all of the computer's resources.
        :param computer: The computer that this process is run on.
        """
        self.pid: int = pid
        self.computer: Computer = computer
        self.cwd = self.computer.filesystem.root
        self.process = None

        self.signal_handlers = defaultdict(
            lambda: self.default_signal_handler
        )
        # ^ maps {signum: handler} when handler takes in a signum and returns None
        self.set_killing_signals_handler(lambda signum: self.die())

    def default_signal_handler(self, signum: int) -> None:
        """
        The default signal handler. This is called when a signal is sent.
        :return: None
        """
        pass

    def die(self, death_message: Optional[str] = None, raises: Optional[Type[BaseException]] = None) -> None:
        """
        Kills the process!
        After this function is called, the process will not run a single line of code - ever...
        """
        if death_message:
            self.computer.print(death_message)

        # TODO: relevant in killing signals: if self.computer.process_scheduler.is_running_a_process():
        raise (raises if raises is not None else ProcessInternalError_Suicide)

    def set_killing_signals_handler(self, handler: Callable) -> None:
        """
        Receives a function that is a signal handler and sets it to be the handler of all of the signals
        that kill a process
        :param handler:  func(signum) -> None
        :return:
        """
        for signum in COMPUTER.PROCESSES.SIGNALS.KILLING_SIGNALS:
            self.signal_handlers[signum] = handler

    @abstractmethod
    def code(self) -> T_ProcessCode:
        """
        The `code` generator is the main function of the process.
        It yields the parameters it needs to continue its run.
        usually it will be to wait for some packet.
        :return:
        """
        yield WaitingFor(lambda: False)
        packet1 = yield WaitingFor(lambda packet: False)
        packet2 = yield WaitingFor(lambda packet: False, timeout=Timeout(10))

    def __repr__(self) -> str:
        """The string representation of the Process"""
        return "Unnamed Process"


class Timeout:
    """
    tests if a certain time has passed since the creation of this object.
    """
    def __init__(self, seconds: T_Time) -> None:
        """
        Initiates the `Timeout` object.
        :param seconds: the amount of seconds of the timeout
        """
        self.seconds = seconds
        self.init_time = MainLoop.instance.time()

    def __bool__(self) -> bool:
        """
        Returns whether or not the timeout has passed yet or not
        """
        return MainLoop.instance.time_since(self.init_time) > self.seconds

    def is_done(self) -> bool:
        return bool(self)

    def reset(self) -> None:
        """
        Resets the timeout object's initiation time.
        :return: None
        """
        self.init_time = MainLoop.instance.time()


@dataclass
class PacketMetadata:
    interface: Interface
    time:      T_Time
    direction: str


class NoNeedForPacket(ReturnedPacket):
    """
    This is the class that you generate an instance of the signal that the process is not interested in the packet
    that will be returned for it.

    A process that is waiting for some packet must yield a `ReturnedPacket` in his `WaitingForPacket`, this is the way to
    ignore that packet without raising errors.
    """


class ProcessInternalError(Exception):
    """If this exception is raised inside a code of a process, the process will be terminated but the rest of NetSym will continue"""


class ProcessInternalError_Suicide(ProcessInternalError):
    """This indicates a self-inflicted death of the process"""


class ProcessInternalError_InvalidDomainHostname(ProcessInternalError_Suicide, InvalidDomainHostnameError):
    """
    This indicates a self-inflicted death of the process due to an invalid domain hostname
    """


class ProcessInternalError_NoResponseForARP(ProcessInternalError):
    """
    This indicates a self-inflicted death of the process due to an ARP that was sent but was not responded
    """


class ProcessInternalError_DNSNameErrorFromServer(ProcessInternalError):
    """
    This indicates a self-inflicted death of the process due to a DNS query that was sent but was not responded
    """


class ProcessInternalError_NoResponseForDNSQuery(ProcessInternalError):
    """
    This indicates a self-inflicted death of the process due to a DNS query that was sent but was not responded
    """


class ProcessInternalError_NoIPAddressError(ProcessInternalError, NoIPAddressError):
    """
    This indicates a self-inflicted death of the process due to a lack of an IP address
    """


class ProcessInternalError_RoutedPacketTTLExceeded(ProcessInternalError):
    """
    This indicates a self-inflicted death of the process because the packet that was routed did not have enough TTL to actually be routed
    """
