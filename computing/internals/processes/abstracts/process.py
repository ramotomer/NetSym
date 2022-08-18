from abc import ABCMeta, abstractmethod
from collections import namedtuple, defaultdict
from typing import Iterator, Union

from recordclass import recordclass

from consts import COMPUTER
from exceptions import *
from gui.main_loop import MainLoop

WaitingForPacket = namedtuple("WaitingForPacket", "condition value")
""""
The condition function must receive one argument (a packet object) and return a bool.
the value in initialization will be a new `ReturnedPacket` object.
that object will be filled with the packets that fit the condition and returned to
the process when it continues running.

The condition should be specific so you don't accidentally catch the wrong packet!
"""

WaitingForPacketWithTimeout = namedtuple("WaitingForPacketWithTimeout", "condition value timeout")
WaitingFor = namedtuple("WaitingFor", "condition")


T_WaitingFor = Union[WaitingFor, WaitingForPacket, WaitingForPacketWithTimeout]
T_ProcessCode = Iterator[T_WaitingFor]


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
    """
    def __init__(self, pid, computer):
        """
        The process currently has access to all of the computer's resources.
        :param computer: The computer that this process is run on.
        """
        self.pid = pid
        self.computer = computer
        self.cwd = self.computer.filesystem.root
        self.process = None
        self.kill_me = False

        self.signal_handlers = defaultdict(
            lambda: self.default_signal_handler
        )
        # ^ maps {signum: handler} when handler takes in a signum and returns None
        self.set_killing_signals_handler(lambda signum: self.die())

    def default_signal_handler(self, signum):
        """
        The default signal handler. This is called when a signal is sent.
        :return: None
        """
        pass

    def die(self):
        """
        self.kill_me = True
        """
        self.kill_me = True

    def set_killing_signals_handler(self, handler):
        """
        Receives a function that is a signal handler and sets it to be the handler of all of the signals
        that kill a process
        :param handler:  func(signum) -> None
        :return:
        """
        for signum in COMPUTER.PROCESSES.SIGNALS.KILLING_SIGNALS:
            self.signal_handlers[signum] = handler

    @abstractmethod
    def code(self):
        """
        The `code` generator is the main function of the process.
        It yields the parameters it needs to continue its run.
        usually it will be to wait for some packet.
        :return:
        """
        yield WaitingFor(lambda: False)
        yield WaitingForPacket(lambda p: False, NoNeedForPacket())
        yield WaitingForPacketWithTimeout(lambda p: False, NoNeedForPacket(), Timeout(10))

    def __repr__(self):
        """The string representation of the Process"""
        return "Unnamed Process"


class Timeout:
    """
    tests if a certain time has passed since the creation of this object.
    """
    def __init__(self, seconds):
        """
        Initiates the `Timeout` object.
        :param seconds: the amount of seconds of the timeout
        """
        self.seconds = seconds
        self.init_time = MainLoop.instance.time()

    def __bool__(self):
        """
        Returns whether or not the timeout has passed yet or not
        """
        return MainLoop.instance.time_since(self.init_time) > self.seconds

    def is_done(self):
        return bool(self)

    def reset(self):
        """
        Resets the timeout object's initiation time.
        :return: None
        """
        self.init_time = MainLoop.instance.time()


PacketMetadata = recordclass("PacketMetadata", [
    "interface",
    "time",
    "direction",
])


class ReturnedPacket:
    """
    The proper way to get received packets back from the running computer.
    `self.packets` is a dictionary with `Packet` keys and the values are `PacketMetadata` objects
    """
    def __init__(self, packet=None, metadata=None):
        self.packets = {}
        self.packet_iterator = None

        if packet is not None and metadata is not None:
            self.packets[packet] = metadata

    @property
    def packet(self):
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
    def packet_and_interface(self):
        """
        just like `self.packet` but returns a tuple of (packet, interface)
        """
        packet = self.packet
        return packet, self.packets[packet].interface

    @property
    def packet_and_metadata(self):
        """
        just like `self.packet` but returns a tuple of (packet, PacketMetadata) [actually (packet, self.packets[packet])
        """
        packet = self.packet
        return packet, self.packets[packet]

    def has_packets(self):
        """Returns whether or not this has any packets inside"""
        return bool(self.packets)

    def __bool__(self):
        return bool(self.packets)

    def __iter__(self):
        """
        Returns an iterator of a list of tuples (packet, interface)
        :return:
        """
        return iter(list(self.packets.items()))


class NoNeedForPacket(ReturnedPacket):
    """
    This is the class that you generate an instance of the signal that the process is not interested in the packet
    that will be returned for it.

    A process that is waiting for some packet must yield a `ReturnedPacket` in his `WaitingForPacket`, this is the way to
    ignore that packet without raising errors.
    """
